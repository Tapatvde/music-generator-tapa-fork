"""Separate the selected exact version and retain an instrumental plus vocal reference."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
import soundfile as sf

spec=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
ROOT=Path(spec['root']).resolve();RUN=Path(spec['run']).resolve();SOURCE=Path(spec['source']).resolve()
RVC=ROOT/'engine/rvc'
if not all(path.is_relative_to(ROOT) for path in (RUN,SOURCE)):raise ValueError('Pfad außerhalb des Forks.')


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def command(args):
    subprocess.run(list(map(str,args)),check=True,creationflags=0x08000000 if os.name=='nt' else 0)


def progress(message):
    print('VOICE_PROGRESS '+json.dumps({'message':message},ensure_ascii=False),flush=True)


try:
    protected=sha(SOURCE);quality=spec['request']['quality']
    cache=ROOT/'data/voice-cache'/protected/f"{spec['recipe']}-{quality}-full"
    marker=cache/'complete.json';saved=json.loads(marker.read_text()) if marker.is_file() else {}
    cached=all((cache/name).is_file() and sha(cache/name)==saved.get('hashes',{}).get(name) for name in ('vocals.wav','instrumental.wav'))
    if not cached:
        progress('Gesang und Begleitung trennen')
        command([RVC/'ffmpeg.exe','-nostdin','-y','-hide_banner','-loglevel','error','-i',SOURCE,
                 '-ac','2','-ar','44100','-c:a','pcm_f32le',RUN/'input.wav'])
        command([RVC/'.venv/Scripts/python.exe','-u',ROOT/'scripts/voice-separate.py',RUN/'request.json'])
        cache.mkdir(parents=True,exist_ok=True)
        for name in ('vocals','instrumental'):
            matches=list((RUN/'stems').glob('*_'+name+'.wav'))
            if len(matches)!=1:raise ValueError('Unvollständige Gesangstrennung.')
            temporary=cache/(name+'.tmp');shutil.copyfile(matches[0],temporary);temporary.replace(cache/(name+'.wav'))
        marker.write_text(json.dumps({'recipe':spec['recipe'],'quality':quality,'hashes':{name:sha(cache/name) for name in ('vocals.wav','instrumental.wav')}}),encoding='utf-8')
    progress('Instrumentalversion exportieren')
    backing,rate=sf.read(cache/'instrumental.wav',always_2d=True)
    vocal,vr=sf.read(cache/'vocals.wav',always_2d=True)
    if rate!=44100 or vr!=rate or len(backing)!=len(vocal) or not np.isfinite(backing).all() or not np.isfinite(vocal).all():
        raise ValueError('Ungültige getrennte Begleitung.')
    if np.sqrt(np.mean(backing**2))<1e-5:raise ValueError('Keine nutzbare Begleitung gefunden.')
    gain=min(1.,.7/max(1e-9,float(np.max(np.abs(backing)))))
    sf.write(RUN/'mix.wav',backing*gain,rate,subtype='PCM_24')
    sf.write(RUN/'vocals-reference.wav',vocal,rate,subtype='PCM_24')
    command([RVC/'ffmpeg.exe','-nostdin','-y','-hide_banner','-loglevel','error','-i',RUN/'mix.wav',
             '-codec:a','libmp3lame','-b:a','320k',RUN/'mix.mp3'])
    if sha(SOURCE)!=protected:raise ValueError('Ausgangssong wurde verändert.')
    (RUN/'result.json').write_text(json.dumps({'duration':len(backing)/rate,'instrumental_version':True,
        'source_hash':protected,'cached_stems':cached,'instrumental_gain':gain,
        'lyrics':'','warnings':['Gesangstrennung kann Reste oder Trennartefakte enthalten; bitte anhören.'],
        'sha256':sha(RUN/'mix.wav'),'protected_unchanged':True},ensure_ascii=False,indent=2),encoding='utf-8')
    progress('Fertig')
except Exception as error:
    (RUN/'error.json').write_text(json.dumps({'error':str(error)},ensure_ascii=False),encoding='utf-8')
    raise
