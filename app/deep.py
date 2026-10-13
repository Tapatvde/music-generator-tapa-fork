"""Original-based editing and separately recorded harmonic guidance."""
import asyncio
import json
import os
import re
import time
import uuid
import wave
from io import BytesIO
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field
from . import db, voices
from .chorus import selected_lyrics
from .engines import EngineError, DIT_MODELS
from .managed_engine import ManagedAce
from .mix_settings import MixSettings

CHORD=re.compile(r'[A-H](?:#|b)?(?:maj|min|m|M|dim|aug|sus|add|\+|°|ø)?\d{0,2}(?:(?:[#b]|sus|add)\d{1,2})*(?:\([^\]\s]+\))?(?:/[A-H](?:#|b)?)?')
INLINE=re.compile(r'\[([^\[\]\n]+)\]')


def separate_chords(text):
    output=[];found=[];section='Song'
    for number,line in enumerate(text.splitlines()):
        stripped=line.strip()
        if re.fullmatch(r'\[(?:verse|chorus|bridge|intro|outro|pre-chorus|instrumental)(?:[^\]]*)\]',stripped,re.I):
            section=stripped;output.append(line);continue
        tokens=[v for v in re.split(r'[\s|]+',stripped) if v]
        if tokens and all(CHORD.fullmatch(v) for v in tokens) and (len(tokens)>1 or '|' in line or len(tokens[0])>1):
            found.append({'section':section,'source_line':number+1,'lyric_line':len(output)+1,'chords':tokens});continue
        inline=[m.group(1) for m in INLINE.finditer(line) if CHORD.fullmatch(m.group(1))]
        if inline:
            found.append({'section':section,'source_line':number+1,'lyric_line':len(output)+1,'chords':inline})
            line=INLINE.sub(lambda m:'' if CHORD.fullmatch(m.group(1)) else m.group(0),line)
        output.append(line)
    return {'lyrics':'\n'.join(output).strip(),'chords':'\n'.join(f"{r['section']} · Textzeile {r['lyric_line']}: "+' | '.join(r['chords']) for r in found),'rows':found}


class ParseRequest(BaseModel):
    text: str=Field(max_length=20000)


class EditRequest(BaseModel):
    source_song_id: str
    mode: Literal['cover-nofsq','cover']='cover-nofsq'
    title: str=Field('',max_length=160)
    caption: str=Field(min_length=1,max_length=6000)
    lyrics: str=Field('',max_length=20000)
    chords: str=Field('',max_length=6000)
    instrumental: bool=False
    source_strength: float=Field(.8,ge=0,le=.95,allow_inf_nan=False)
    bpm: int=Field(0,ge=0,le=300)
    keyscale: str=Field('',max_length=40)
    timesignature: str=Field('4',max_length=8)
    preview: bool=True
    preview_start: float=Field(0,ge=0,le=600,allow_inf_nan=False)
    preview_seconds: float=Field(20,ge=5,le=30,allow_inf_nan=False)
    seed: int=Field(1234,ge=0,le=2147483647)
    voice_after: voices.VoiceRequest|None=None
    mix_levels: MixSettings=Field(default_factory=MixSettings)
    sound_model: Literal['standard','xl']|None=None


def source_song(sid):
    row=db.one('SELECT * FROM songs WHERE id=?',(sid,))
    if not row or row['status']!='done' or not row['file']:raise ValueError('Bitte eine fertige Originalaufnahme auswählen.')
    params=json.loads(row['params'])
    if params.get('voice',{}).get('preview') or params.get('deep',{}).get('preview'):
        raise ValueError('Bitte eine vollständige Ausgangsfassung auswählen.')
    voices.contained(db.songs_dir()/row['file'])
    return row


def prepare_request(req,source,info):
    sound_model=req.sound_model or db.get_settings().get('dit','standard')
    if sound_model=='xl' and not (db.MODELS_DIR/DIT_MODELS['xl']).is_file():raise ValueError('XL-Klangmodell fehlt. Bitte zuerst herunterladen.')
    if info['seconds']>600:raise ValueError('Originalbearbeitung unterstützt höchstens zehn Minuten je Song.')
    if req.preview and req.preview_start+req.preview_seconds>info['seconds']+.01:
        raise ValueError('Die Vorschau reicht über das Songende hinaus.')
    parsed=separate_chords(req.lyrics or selected_lyrics(source))
    lyrics='[Instrumental]' if req.instrumental else parsed['lyrics']
    if not req.instrumental and not lyrics:
        raise ValueError('Bitte den Gesangstext angeben oder Instrumental auswählen.')
    if req.voice_after:
        voices.get_profile(req.voice_after.profile_id)
        if req.instrumental:raise ValueError('Ein Stimmprofil benötigt eine Gesangsfassung.')
        if req.preview:raise ValueError('Das Stimmprofil bitte nach dem Anhören der Vorschau anwenden oder eine Vollfassung wählen.')
        voices.validate_lyrics(req.voice_after,lyrics)
    chords='\n'.join(x for x in (req.chords.strip(),parsed['chords']) if x)
    caption=req.caption.strip()
    if not caption:raise ValueError('Bitte die gewünschte Bearbeitung beschreiben.')
    if chords:caption+='\nHarmonic guidance for the accompaniment (not sung):\n'+chords
    original=json.loads(source['params']);meta=json.loads(source['result_meta'] or '{}')
    return {'task_type':req.mode,'caption':caption,'lyrics':lyrics,
            'duration':req.preview_seconds if req.preview else info['seconds'],
            'bpm':req.bpm or meta.get('bpm') or original.get('bpm') or 0,
            'keyscale':req.keyscale or meta.get('keyscale') or original.get('keyscale') or '',
            'timesignature':req.timesignature,'seed':req.seed,'inference_steps':50,
            'audio_cover_strength':1.,'cover_noise_strength':req.source_strength},parsed,chords


def enqueue(req,source,info,created_at):
    req.sound_model=req.sound_model or db.get_settings().get('dit','standard')
    if req.voice_after:req.voice_after.mix_levels=req.mix_levels
    request,parsed,chords=prepare_request(req,source,info)
    identifier=uuid.uuid4().hex[:12]
    params={'job_type':'deep','source_song_id':source['id'],'deep':req.model_dump(),
            'request':request,'lyrics':request['lyrics'],'chords':chords,'chord_rows':parsed['rows'],
            'duration':request['duration'],'imported':True,'mix_levels':req.mix_levels.model_dump(),'sound_model':req.sound_model}
    if req.voice_after:params['voice_after']=req.voice_after.model_dump()
    db.execute('INSERT INTO songs(id,group_id,created_at,status,title,caption,lyrics,seed,params,folder_id) VALUES(?,?,?,?,?,?,?,?,?,?)',
        (identifier,source['group_id'],created_at,'queued',req.title.strip() or source['title'],req.caption.strip(),
         request['lyrics'],req.seed,json.dumps(params),source['folder_id']))
    return {'id':identifier}


class OriginalEdit(ManagedAce):
    name='acestep_original'

    def __init__(self,sid):
        super().__init__(db.get_settings());self.sid=sid

    async def generate(self,params,progress):
        started=time.monotonic();req=EditRequest(**params['deep'])
        self.delegate.dit_model=DIT_MODELS[params.get('sound_model') or req.sound_model or self.settings.get('dit','standard')]
        source=source_song(params['source_song_id']);path=voices.contained(db.songs_dir()/source['file'])
        info=await asyncio.to_thread(voices.probe,path)
        request,_,_=prepare_request(req,source,info)
        protected=await asyncio.to_thread(voices.digest,path)
        run=db.DATA/'deep-jobs'/self.sid;run.mkdir(parents=True,exist_ok=True)
        prepared=run/'source.wav';await progress('Originalaufnahme vorbereiten')
        args=[str(voices.RVC/'ffmpeg.exe'),'-nostdin','-y','-hide_banner','-loglevel','error']
        if req.preview:args+=['-ss',str(req.preview_start)]
        args+=['-i',str(path)]
        if req.preview:args+=['-t',str(req.preview_seconds)]
        args+=['-ac','2','-ar','48000','-c:a','pcm_s16le',str(prepared)]
        self.process=await asyncio.create_subprocess_exec(*args,stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.PIPE,
            **({'creationflags':0x08000000} if os.name=='nt' else {}))
        try:
            _,error=await self.process.communicate()
            if self.process.returncode:raise EngineError('Originalaufnahme konnte nicht vorbereitet werden: '+error.decode(errors='replace')[-300:])
            (run/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
            audio,ext=await self._operate(lambda:self.delegate.edit_original(request,prepared.read_bytes(),progress),progress)
            if ext!='wav':raise EngineError('Musikmodell lieferte kein verlustfreies WAV.')
            with wave.open(BytesIO(audio),'rb') as check:
                seconds=check.getnframes()/check.getframerate()
                if check.getframerate()!=48000 or check.getnchannels()!=2 or abs(seconds-request['duration'])>.5:
                    raise EngineError('Originalbearbeitung lieferte eine abweichende Länge oder Abtastrate.')
            if await asyncio.to_thread(voices.digest,path)!=protected:raise EngineError('Originalaufnahme wurde verändert.')
            (run/'mix.wav').write_bytes(audio)
            warnings=['Akkorde sind Begleitungsvorgaben; keine verbindliche Akkord- oder Melodietreueprüfung.'] if params.get('chords') else []
            metadata={k:request[k] for k in ('bpm','keyscale','timesignature','lyrics')}
            metadata.update(duration=seconds,source_seconds=info['seconds'],generation_seconds=time.monotonic()-started,
                original_edit=True,edit_mode=req.mode,preview=req.preview,preview_start=req.preview_start if req.preview else 0,
                sound_model=self.delegate.dit_model,
                source_strength=req.source_strength,source_hash=protected,protected_unchanged=True,warnings=warnings)
            (run/'result.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
            return audio,ext,metadata
        except asyncio.CancelledError:
            await self.cancel();raise
