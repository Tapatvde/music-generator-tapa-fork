"""Queue-owned post processing for songs that do not use RVC voice conversion."""
import asyncio
import json
import os
import time

from . import db
from .engines import EngineError
from .mix_settings import MixSettings


def wrap_engine(engine, sid, params):
    settings=MixSettings(**params.get('mix_levels',{}))
    if engine.name in ('rvc','instrumental') or not settings.active() or params.get('voice_after'):
        return engine
    return LevelEngine(engine,sid)


class LevelEngine:
    def __init__(self,delegate,sid):
        self.delegate=delegate;self.sid=sid;self.name=delegate.name;self.process=None

    async def cancel(self):
        await self.delegate.cancel()
        if self.process and self.process.returncode is None:
            if os.name=='nt':
                killer=await asyncio.create_subprocess_exec('taskkill','/PID',str(self.process.pid),'/T','/F',
                    stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL,creationflags=0x08000000)
                await killer.wait()
            else:self.process.kill()
            await self.process.wait()

    async def generate(self,params,progress):
        from . import voices
        audio,ext,meta=await self.delegate.generate(params,progress)
        run=db.DATA/'level-jobs'/self.sid;run.mkdir(parents=True,exist_ok=True)
        # Keep the generator output even if separation or post processing fails.
        source=run/('generated.'+ext)
        if ext not in ('wav','mp3','flac','ogg','m4a'):raise EngineError('Unbekanntes Audioformat für Pegelkorrektur.')
        source.write_bytes(audio)
        spec={'root':str(db.ROOT),'run':str(run),'source':str(source),
              'request':{'quality':'standard','preview':False},'recipe':voices.RECIPE,
              'mix_levels':MixSettings(**params.get('mix_levels',{})).model_dump(),
              'instrumental':bool(params.get('instrumental') or params.get('deep',{}).get('instrumental') or params.get('lyrics','').strip().lower()=='[instrumental]')}
        request=run/'request.json';request.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
        started=time.monotonic();await progress('Gesang und Begleitung für Pegelkorrektur vorbereiten')
        self.process=await asyncio.create_subprocess_exec(str(voices.PYTHON),'-u',str(db.ROOT/'scripts/level-job.py'),str(request),
            cwd=voices.RVC,env=voices.runtime_environment(),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT,
            **({'creationflags':0x08000000} if os.name=='nt' else {}))
        stage='Pegelkorrektur vorbereiten'
        try:
            with (run/'worker.log').open('w',encoding='utf-8') as log:
                while True:
                    try:line=await asyncio.wait_for(self.process.stdout.readline(),2)
                    except asyncio.TimeoutError:
                        await progress(f'{stage} · {int(time.monotonic()-started)} s vergangen');continue
                    if not line:break
                    text=line.decode('utf-8',errors='replace').strip();log.write(text+'\n');log.flush()
                    if text.startswith('VOICE_PROGRESS '):
                        stage=json.loads(text[15:])['message'];await progress(stage)
            if await self.process.wait():
                error=run/'error.json'
                raise EngineError(json.loads(error.read_text(encoding='utf-8'))['error'] if error.is_file() else 'Pegelkorrektur fehlgeschlagen; erzeugtes Original im Auftragsordner erhalten.')
            result=json.loads((run/'result.json').read_text(encoding='utf-8'))
            return (run/'mix.wav').read_bytes(),'wav',{**meta,'mix_levels':result,'level_seconds':time.monotonic()-started,
                'warnings':[*meta.get('warnings',[]),'Pegelkorrektur verwendet getrennte Spuren; Trennartefakte sind möglich.']}
        except asyncio.CancelledError:
            await self.cancel();raise
