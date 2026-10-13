"""Standalone separation and independent level processing for a generated mix."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

spec=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
ROOT=Path(spec['root']).resolve();RUN=Path(spec['run']).resolve();SOURCE=Path(spec['source']).resolve()
RVC=ROOT/'engine/rvc'
sys.path.insert(0,str(ROOT))
from app.level_dsp import stabilize_layers
import numpy as np
import soundfile as sf


def sha(path):
    with Path(path).open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def command(args):
    subprocess.run(list(map(str,args)),check=True,creationflags=0x08000000 if os.name=='nt' else 0)


def progress(message):
    print('VOICE_PROGRESS '+json.dumps({'message':message},ensure_ascii=False),flush=True)


try:
    if not all(p.is_relative_to(ROOT) for p in (RUN,SOURCE)):raise ValueError('Pfad außerhalb des Forks.')
    protected=sha(SOURCE);cached=False
    if spec.get('instrumental'):
        command([RVC/'ffmpeg.exe','-nostdin','-y','-hide_banner','-loglevel','error','-i',SOURCE,
                 '-ac','2','-ar','44100','-c:a','pcm_f32le',RUN/'input.wav'])
        backing,sr=sf.read(RUN/'input.wav',always_2d=True);lead=np.zeros_like(backing)
    else:
        cache=ROOT/'data/voice-cache'/protected/f"{spec['recipe']}-{spec['request']['quality']}-full"
        marker=cache/'complete.json';saved=json.loads(marker.read_text()) if marker.is_file() else {}
        cached=all((cache/n).is_file() and sha(cache/n)==saved.get('hashes',{}).get(n) for n in ('vocals.wav','instrumental.wav'))
        if not cached:
            progress('Gesang und Begleitung trennen · zusätzliche Verarbeitung')
            command([RVC/'ffmpeg.exe','-nostdin','-y','-hide_banner','-loglevel','error','-i',SOURCE,
                     '-ac','2','-ar','44100','-c:a','pcm_f32le',RUN/'input.wav'])
            command([RVC/'.venv/Scripts/python.exe','-u',ROOT/'scripts/voice-separate.py',RUN/'request.json'])
            cache.mkdir(parents=True,exist_ok=True)
            for name in ('vocals','instrumental'):
                matches=list((RUN/'stems').glob('*_'+name+'.wav'))
                if len(matches)!=1:raise ValueError('Unvollständige Gesangstrennung.')
                tmp=cache/(name+'.tmp');shutil.copyfile(matches[0],tmp);tmp.replace(cache/(name+'.wav'))
            tmp=cache/'complete.tmp'
            tmp.write_text(json.dumps({'recipe':spec['recipe'],'quality':spec['request']['quality'],
                'hashes':{n:sha(cache/n) for n in ('vocals.wav','instrumental.wav')}}),encoding='utf-8');tmp.replace(marker)
        backing,sr=sf.read(cache/'instrumental.wav',always_2d=True)
        lead,vr=sf.read(cache/'vocals.wav',always_2d=True)
        if vr!=sr:raise ValueError('Abweichende Abtastrate der Mischspuren.')
    progress('Gesang und Begleitung unabhängig stabilisieren')
    lead,harmony,backing,result=stabilize_layers(lead,np.zeros_like(lead),backing,sr,spec['mix_levels'])
    mix=backing+lead+harmony
    gain=min(1.,.95/max(1e-9,float(np.max(np.abs(mix)))))
    mix*=gain
    sf.write(RUN/'mix.wav',mix,sr,subtype='PCM_24')
    command([RVC/'ffmpeg.exe','-nostdin','-y','-hide_banner','-loglevel','error','-i',RUN/'mix.wav',
             '-af','volume=-1.5dB','-codec:a','libmp3lame','-b:a','320k',RUN/'mix.mp3'])
    check,cr=sf.read(RUN/'mix.wav',always_2d=True)
    if cr!=sr or check.shape!=mix.shape or not np.isfinite(check).all() or np.max(np.abs(check))>.951:raise ValueError('Exportprüfung fehlgeschlagen.')
    if sha(SOURCE)!=protected:raise ValueError('Erzeugtes Original wurde verändert.')
    result.update(duration=len(mix)/sr,sample_rate=sr,common_gain=gain,source_hash=protected,cached_stems=cached,
                  protected_unchanged=True,sha256=sha(RUN/'mix.wav'))
    (RUN/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    progress('Fertig')
except Exception as error:
    (RUN/'error.json').write_text(json.dumps({'error':str(error)},ensure_ascii=False),encoding='utf-8')
    raise
