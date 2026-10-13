"""Train a new local RVC profile in isolated directories; publish only after validation."""
import hashlib
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

spec=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
ROOT=Path(spec['root']).resolve();RUN=Path(spec['run']).resolve()
RVC=ROOT/'engine/rvc';NAME=spec['experiment']
if not RUN.is_relative_to(ROOT) or not re.fullmatch(r'Voice_[0-9a-f]{12}',NAME):
    raise ValueError('Ungültiger Trainingsauftrag.')
EXP=RVC/'logs'/NAME
sys.argv=[sys.argv[0]]
sys.path.insert(0,str(RVC));os.chdir(RVC)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def progress(message):
    print('TRAIN_PROGRESS '+json.dumps({'message':message},ensure_ascii=False),flush=True)


def stage(name,args):
    progress(name)
    with (RUN/(args[0].replace('/','-')+'.log')).open('w',encoding='utf-8') as log:
        subprocess.run([str(RVC/'.venv/Scripts/python.exe'),'-u','-m',args[0].removesuffix('.py').replace('/','.'),
                        *map(str,args[1:])],cwd=RVC,env=environment,stdout=log,stderr=subprocess.STDOUT,
                       check=True,creationflags=0x08000000 if os.name=='nt' else 0)


environment={**os.environ,'RVC_TRAIN_EXPORT_DIR':str(RUN/'model-export')}


def main():
    import numpy as np
    import soundfile as sf
    import torch
    import faiss
    if not torch.cuda.is_available():raise ValueError('Für das integrierte Training wird eine verfügbare NVIDIA-GPU benötigt.')
    if EXP.exists():raise ValueError('Dieser Trainingslauf existiert bereits. Vorhandene Trainingsstände werden nicht überschrieben.')
    EXP.mkdir(parents=True);inputs=RUN/'input';inputs.mkdir(exist_ok=True)
    for number,entry in enumerate(spec['files']):
        source=Path(entry['path']).resolve()
        if not source.is_relative_to(ROOT) or sha(source)!=entry['sha256']:
            raise ValueError('Soloaufnahme fehlt oder wurde nach dem Import verändert.')
        output=inputs/f'{number:02d}.wav'
        subprocess.run([str(RVC/'ffmpeg.exe'),'-nostdin','-y','-hide_banner','-loglevel','error',
            '-i',str(source),'-ac','1','-ar','40000','-c:a','pcm_f32le',str(output)],check=True,
            creationflags=0x08000000 if os.name=='nt' else 0)
        audio,rate=sf.read(output)
        if not np.isfinite(audio).all() or np.sqrt(np.mean(audio**2))<1e-5:
            raise ValueError('Eine Aufnahme enthält keine nutzbaren Audiodaten.')
    stage('Soloaufnahmen vorbereiten',['train/preprocess.py',inputs,40000,4,EXP,'False',3.7])
    stage('Gesangstonhöhen analysieren',['train/dataset/extract_f0.py','cuda',1,0,0,EXP,'true'])
    stage('Stimmmerkmale extrahieren',['train/dataset/extract_hubert_feature.py','cuda:0',1,0,0,EXP,'v2','true'])
    lines=[];notes=[];voiced_frames=0
    for wav in sorted((EXP/'0_gt_wavs').glob('*.wav')):
        feature=EXP/'3_feature768'/(wav.stem+'.npy')
        coarse=EXP/'2a_f0'/(wav.name+'.npy')
        f0=EXP/'2b-f0nsf'/(wav.name+'.npy')
        if not all(path.is_file() for path in (feature,coarse,f0)):continue
        arrays=[np.load(path,allow_pickle=False) for path in (feature,coarse,f0)]
        if any(not array.size or not np.isfinite(array).all() for array in arrays):continue
        if arrays[0].ndim!=2 or arrays[0].shape[1]!=768:continue
        pitched=arrays[2][arrays[2]>0];voiced_frames+=len(pitched)
        if len(pitched):notes.extend((69+12*np.log2(pitched/440)).tolist())
        lines.append('|'.join([path.as_posix() for path in (wav,feature,coarse,f0)]+['0']))
    if len(lines)<4 or voiced_frames<1000:
        raise ValueError('Zu wenig erkennbarer Gesang nach der Aufbereitung. Bitte längere, deutliche Soloaufnahmen verwenden.')
    mute=RVC/'logs/mute'
    lines+=['|'.join([path.as_posix() for path in
        (mute/'0_gt_wavs/mute40k.wav',mute/'3_feature768/mute.npy',mute/'2a_f0/mute.wav.npy',mute/'2b-f0nsf/mute.wav.npy')]+['0'])]*2
    random.Random(1234).shuffle(lines)
    (EXP/'filelist.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    config=json.loads((RVC/'configs/v1/40k.json').read_text(encoding='utf-8'))
    config['train']['log_interval']=25
    (EXP/'config.json').write_text(json.dumps(config),encoding='utf-8')
    epochs=int(spec['epochs'])
    if not 1<=epochs<=1000:raise ValueError('Ungültige Trainingsdauer.')
    stage(f'Stimmprofil trainieren · {epochs} Trainingsrunden',
          ['train/train.py','-e',NAME,'-sr','40k','-f0',1,'-bs',4,'-g',0,
           '-te',epochs,'-se',max(1,min(25,epochs)),'-pg','assets/pretrained_v2/f0G40k.pth',
           '-pd','assets/pretrained_v2/f0D40k.pth','-l',1,'-c',0,'-sw',0,'-v','v2'])
    model=RUN/'model-export'/(NAME+'.pth')
    if not model.is_file():raise ValueError('Trainiertes Stimmprofil wurde nicht exportiert.')
    checkpoint=torch.load(model,map_location='cpu',weights_only=False)
    if checkpoint.get('version')!='v2' or checkpoint.get('f0')!=1 or not checkpoint.get('weight'):
        raise ValueError('Exportiertes Stimmprofil ist unvollständig.')
    if not all(torch.isfinite(value).all().item() for value in checkpoint['weight'].values()):
        raise ValueError('Ungültige Werte im trainierten Stimmprofil.')
    del checkpoint
    stage('Stimmindex erstellen',['train/train_index.py',NAME,'v2',RUN/'indices',4,'single'])
    indices=list((RUN/'indices').glob('*.index'))
    if len(indices)!=1:raise ValueError('Stimmindex fehlt oder ist mehrdeutig.')
    index=faiss.read_index(str(indices[0]))
    if index.d!=768 or index.ntotal<1:raise ValueError('Stimmindex ist unvollständig.')
    progress('Trainierte Stimme mit Soloaufnahme prüfen')
    sample=RUN/'training-check.wav'
    subprocess.run([str(RVC/'.venv/Scripts/python.exe'),'-u','-m','infer.cli','--model',str(model),
        '--input',str(next(inputs.glob('*.wav'))),'--output',str(sample),'--index',str(indices[0]),
        '--index-rate','0.5','--pitch','0','--f0-method','rmvpe'],cwd=RVC,env=environment,
        stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,check=True,
        creationflags=0x08000000 if os.name=='nt' else 0)
    audio,rate=sf.read(sample)
    if not np.isfinite(audio).all() or np.max(np.abs(audio))<1e-5:raise ValueError('Funktionsprüfung der trainierten Stimme fehlgeschlagen.')
    from infer.voice_range import midi_note
    lower,center,upper=np.percentile(notes,[1,50,99])
    low=max(32,min(72,int(np.floor(lower))))
    high=min(84,max(low+12,int(np.ceil(upper))))
    profile={'schema_version':1,'enabled':True,'min_note':midi_note(low),'max_note':midi_note(high),
             'mode':'melody_phrases','preserve_unvoiced':True,'stable_register':True,
             'register_center_midi':float(center),'basis':'Vorläufiger beobachteter Bereich; keine Messung der singbaren Grenzen.'}
    model.with_suffix('.voice.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8')
    if not all(sha(entry['path'])==entry['sha256'] for entry in spec['files']):
        raise ValueError('Eine importierte Aufnahme wurde verändert.')
    result={'id':NAME,'name':spec['name'],'model':str(model),'index':str(indices[0]),
            'model_sha256':sha(model),'index_sha256':sha(indices[0]),'epochs':epochs,
            'seconds':spec['seconds'],'segments':len(lines)-2,'index_vectors':int(index.ntotal),
            'range':profile,'training_check':str(sample),'held_out_validation':False,
            'warning':'Funktionsprüfung mit Trainingsmaterial; Stimmähnlichkeit bitte an einem anderen Song anhören.'}
    (RUN/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    progress('Stimmprofil fertig')


try:main()
except Exception as error:
    (RUN/'error.json').write_text(json.dumps({'error':str(error)},ensure_ascii=False),encoding='utf-8')
    raise
