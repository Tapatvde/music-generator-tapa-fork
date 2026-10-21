"""Start the fork's own ACE server per operation, then release its GPU memory."""
import asyncio
import os
import subprocess
import time

from . import db
from .engines import AceStepCpp, EngineError, make_engine


class ManagedAce:
    name = "acestep_cpp"

    def __init__(self, settings):
        self.settings = settings
        device = settings.get('lm_device', db.lm_device())
        self.lm_on_cpu = device == 'cpu' or (device == 'auto' and db._engine_conf().get('MODE') == 'split')
        lm_url = 'http://127.0.0.1:8088' if self.lm_on_cpu else ''
        self.delegate = AceStepCpp("http://127.0.0.1:8087", lm_url, settings["poll_interval"], settings["timeout_minutes"], settings.get("lm_model", ""), settings.get('dit','standard'))
        self.process = None
        self.lm_process = None
        self.binary = db.ROOT / "engine/acestep.cpp/build/Release/ace-server.exe"

    async def health(self):
        return {"ok":self.binary.is_file(), "health":{"status":"Startet bei Bedarf", "managed":True, 'lm_device':'cpu' if self.lm_on_cpu else 'auto'}}

    async def cancel(self):
        try:
            await self._stop_owned(self.lm_process)
        finally:
            await self._stop_owned(self.process)

    async def _stop_owned(self, process):
        if process and process.returncode is None:
            if os.name == 'nt':
                killer = await asyncio.create_subprocess_exec('taskkill', '/PID', str(process.pid), '/T', '/F', stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL, creationflags=0x08000000)
                await killer.wait()
            else:
                process.kill()
            await process.wait()

    def server_arguments(self, port=8087):
        arguments=[str(self.binary), '--host','127.0.0.1','--port',str(port),'--models',str(db.MODELS_DIR),'--max-batch','1']
        if self.delegate.dit_model.endswith('xl-sft-Q8_0.gguf'):
            arguments.extend(['--vae-chunk','256'])
        return arguments

    async def _start_owned(self, port, cpu=False):
        environment = dict(os.environ)
        arguments = self.server_arguments(port)
        if cpu:
            environment['GGML_BACKEND'] = 'CPU'
            # The pinned 6013134 runtime selects devices through its CLI.
            arguments.extend(['--device', 'CPU'])
        name = 'ace-lm-fork.log' if cpu else 'ace-fork.log'
        with (db.DATA / name).open('ab') as log:
            return await asyncio.create_subprocess_exec(*arguments,
                cwd=db.ROOT, env=environment, stdout=log, stderr=asyncio.subprocess.STDOUT,
                **({'creationflags':0x08000000} if os.name=='nt' else {}))

    async def _operate(self, operation, progress):
        if not self.binary.is_file():
            raise EngineError("Der lokale ACE-Modellserver im Fork fehlt.")
        for port in ([8087, 8088] if self.lm_on_cpu else [8087]):
            try:
                reader, writer = await asyncio.open_connection('127.0.0.1', port)
            except OSError:
                continue
            writer.close(); await writer.wait_closed()
            raise EngineError(f'Port {port} ist bereits belegt. Der vorhandene Dienst wurde nicht verändert.')
        await progress("Musikmodell wird geladen …")
        # Bound XL decoder working memory on 16 GB GPUs.
        try:
            if self.lm_on_cpu:
                self.lm_process = await self._start_owned(8088, cpu=True)
            self.process = await self._start_owned(8087)
            for _ in range(120):
                if self.process.returncode is not None or (self.lm_process and self.lm_process.returncode is not None):
                    raise EngineError('Musikmodell konnte nicht starten; siehe data/ace-fork.log beziehungsweise data/ace-lm-fork.log.')
                try:
                    await self.delegate.health()
                    break
                except Exception:
                    await asyncio.sleep(.5)
            else:
                raise EngineError('Musikmodell antwortet nicht rechtzeitig.')
            return await operation()
        finally:
            await self.cancel()

    async def generate(self, params, progress):
        start = time.monotonic()
        audio, ext, meta = await self._operate(lambda:self.delegate.generate(params, progress), progress)
        meta["generation_seconds"] = time.monotonic()-start
        return audio, ext, meta

    async def analyze(self, data, filename):
        async def progress(message):
            pass
        return await self._operate(lambda:self.delegate.analyze(data,filename), progress)


def make_fork_engine(settings):
    if settings.get("server_url", "").rstrip("/") == "http://127.0.0.1:8087" and not settings.get("lm_url"):
        return ManagedAce(settings)
    return make_engine(settings)
