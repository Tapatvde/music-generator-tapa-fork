"""User-owned solo datasets and queued local RVC training."""
import asyncio
import json
import os
import re
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from pydantic import BaseModel, Field
from . import db, voices
from .engines import EngineError

EXTENSIONS={'.wav','.mp3','.flac','.m4a','.ogg'}


class TrainingRequest(BaseModel):
    epochs: int = Field(200, ge=50, le=1000)


def dataset_path(identifier):
    if not re.fullmatch(r'Voice_[0-9a-f]{12}',identifier):
        raise ValueError('Ungültige Profilkennung.')
    return voices.contained(db.DATA/'voice-library'/identifier)


def items(removed=False):
    result=[]
    for row in db.query("SELECT * FROM voice_training WHERE status "+("=" if removed else "!=")+" 'removed' ORDER BY created_at DESC"):
        params=json.loads(row['params'])
        result.append({**{k:row[k] for k in ('id','name','status','message','created_at')},
                       'seconds':params['seconds'],'files':[{k:f[k] for k in ('name','seconds')} for f in params['files']],
                       'epochs':params.get('epochs'),'removed_at':row['removed_at']})
    return result


def remove(identifier):
    dataset_path(identifier)
    row=db.one('SELECT * FROM voice_training WHERE id=?',(identifier,))
    if not row:raise KeyError(identifier)
    if row['status'] in ('queued','running'):
        raise ValueError('Bitte das Training zuerst abbrechen und das Ende abwarten.')
    if row['status']=='removed':raise ValueError('Dieser Eintrag liegt bereits im Papierkorb.')
    for song in db.query("SELECT params FROM songs WHERE status IN ('queued','running')"):
        params=json.loads(song['params'])
        if any((params.get(key) or {}).get('profile_id')==identifier for key in ('voice','voice_after')):
            raise ValueError('Dieses Profil wird von einem wartenden oder laufenden Songauftrag verwendet. Bitte den Auftrag zuerst abschließen oder abbrechen.')
    db.execute("UPDATE voice_training SET removed_status=status,status='removed',removed_at=? WHERE id=?",
               (datetime.now().isoformat(),identifier))


def restore(identifier):
    dataset_path(identifier)
    row=db.one('SELECT * FROM voice_training WHERE id=?',(identifier,))
    if not row:raise KeyError(identifier)
    if row['status']!='removed':raise ValueError('Dieser Eintrag liegt nicht im Papierkorb.')
    if any(p['name'].casefold()==row['name'].casefold() for p in items()+voices.profile_list()):
        raise ValueError('Dieser Profilname ist inzwischen wieder vergeben. Bitte den anderen Eintrag zuerst entfernen.')
    params=json.loads(row['params'])
    required=[Path(f['path']) for f in params['files']]
    if row['removed_status']=='done':
        meta=json.loads(row['result_meta']);required += [Path(meta[k]) for k in ('model','index')]
    if any(not voices.contained(p).is_file() for p in required):
        raise ValueError('Dateien dieses Eintrags fehlen; Wiederherstellung ist nicht möglich.')
    db.execute("UPDATE voice_training SET status=removed_status,removed_status=NULL,removed_at=NULL WHERE id=?",(identifier,))


def prerequisites():
    return voices.PYTHON.is_file() and all((voices.RVC/path).is_file() for path in
        ('ffmpeg.exe','assets/pretrained_v2/f0G40k.pth','assets/pretrained_v2/f0D40k.pth',
         'assets/hubert_base/pytorch_model.bin','assets/hubert_base/config.json','assets/rmvpe/rmvpe.pt'))


async def upload(name, files: list[UploadFile]):
    name=name.strip()
    if not name or len(name)>80:raise ValueError('Profilname mit 1 bis 80 Zeichen angeben.')
    if not 1<=len(files)<=32:raise ValueError('Bitte 1 bis 32 Soloaufnahmen auswählen.')
    if any(row['name'].casefold()==name.casefold() for row in items()+voices.profile_list()):
        raise ValueError('Dieser Profilname ist bereits vergeben.')
    identifier='Voice_'+uuid.uuid4().hex[:12]
    folder=dataset_path(identifier);folder.mkdir(parents=True)
    recorded=[];total=0
    try:
        for number,file in enumerate(files):
            suffix=Path(file.filename or '').suffix.lower()
            if suffix not in EXTENSIONS:raise ValueError('Soloaufnahmen als WAV, MP3, FLAC, M4A oder OGG auswählen.')
            path=folder/f'{number:02d}{suffix}'
            count=0
            with path.open('xb') as stream:
                while chunk:=await file.read(1024*1024):
                    count+=len(chunk);total+=len(chunk)
                    if count>512*1024**2 or total>1024**3:raise ValueError('Maximal 512 MB je Aufnahme und 1 GB insgesamt.')
                    stream.write(chunk)
            probe=await asyncio.to_thread(voices.probe,path)
            if probe['seconds']>1800:raise ValueError('Eine Soloaufnahme darf höchstens 30 Minuten lang sein.')
            recorded.append({'name':Path(file.filename or 'Aufnahme').name,'path':str(path),
                             'seconds':probe['seconds'],'sha256':await asyncio.to_thread(voices.digest,path)})
        seconds=sum(f['seconds'] for f in recorded)
        if not 30<=seconds<=3600:raise ValueError('Insgesamt 30 Sekunden bis 60 Minuten Soloaufnahmen verwenden.')
        params={'files':recorded,'seconds':seconds}
        db.execute('INSERT INTO voice_training(id,name,created_at,status,params) VALUES(?,?,?,?,?)',
                   (identifier,name,datetime.now().isoformat(),'draft',json.dumps(params)))
        return next(r for r in items() if r['id']==identifier)
    except Exception:
        # Roll back only newly uploaded files, never an existing dataset.
        for path in folder.iterdir():
            if path.is_file():path.unlink()
        folder.rmdir()
        raise
    finally:
        for file in files:await file.close()


class TrainingEngine(voices.VoiceEngine):
    name='rvc_training'

    async def generate(self,params,progress):
        run=dataset_path(self.sid)/'run'
        run.mkdir(exist_ok=True)
        spec={'root':str(db.ROOT),'run':str(run),'experiment':self.sid,'name':params['name'],
              'files':params['files'],'epochs':params['epochs'],'seconds':params['seconds']}
        request=run/'request.json'
        request.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
        self.process=await asyncio.create_subprocess_exec(str(voices.PYTHON),'-u',
            str(db.ROOT/'scripts/train-voice-profile.py'),str(request),cwd=voices.RVC,
            env=voices.runtime_environment(),stdout=asyncio.subprocess.PIPE,stderr=subprocess.STDOUT,
            **({'creationflags':0x08000000} if os.name=='nt' else {}))
        started=time.monotonic();stage='Training vorbereiten'
        try:
            with (run/'worker.log').open('w',encoding='utf-8') as log:
                while True:
                    try:line=await asyncio.wait_for(self.process.stdout.readline(),2)
                    except asyncio.TimeoutError:
                        await progress(f'{stage} · {int(time.monotonic()-started)} s vergangen');continue
                    if not line:break
                    text=line.decode('utf-8',errors='replace').strip()
                    log.write(text+'\n');log.flush()
                    if text.startswith('TRAIN_PROGRESS '):
                        stage=json.loads(text[15:])['message'];await progress(stage)
                code=await self.process.wait()
            if code:
                error=run/'error.json'
                raise EngineError(json.loads(error.read_text(encoding='utf-8'))['error'] if error.is_file()
                                  else 'Training fehlgeschlagen; Details im Trainingsprotokoll.')
            return b'','',json.loads((run/'result.json').read_text(encoding='utf-8'))
        except asyncio.CancelledError:
            await self.cancel();raise
