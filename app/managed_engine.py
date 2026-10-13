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
        self.delegate = AceStepCpp("http://127.0.0.1:8087", "", settings["poll_interval"], settings["timeout_minutes"], settings.get("lm_model", ""), settings.get('dit','standard'))
        self.process = None
        self.binary = db.ROOT / "engine/acestep.cpp/build/Release/ace-server.exe"

    async def health(self):
        return {"ok":self.binary.is_file(), "health":{"status":"Startet bei Bedarf", "managed":True}}

    async def cancel(self):
        if self.process and self.process.returncode is None:
            if os.name == "nt":
                killer = await asyncio.create_subprocess_exec("taskkill", "/PID", str(self.process.pid), "/T", "/F", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL, creationflags=0x08000000)
                await killer.wait()
            else:
                self.process.kill()
            await self.process.wait()

    def server_arguments(self):
        arguments=[str(self.binary), '--host','127.0.0.1','--port','8087','--models',str(db.MODELS_DIR),'--max-batch','1']
        if self.delegate.dit_model.endswith('xl-sft-Q8_0.gguf'):
            arguments.extend(['--vae-chunk','256'])
        return arguments

    async def _operate(self, operation, progress):
        if not self.binary.is_file():
            raise EngineError("Der lokale ACE-Modellserver im Fork fehlt.")
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", 8087)
        except OSError:
            pass
        else:
            writer.close(); await writer.wait_closed()
            raise EngineError("Port 8087 ist bereits belegt. Der vorhandene Dienst wurde nicht verändert.")
        await progress("Musikmodell wird geladen …")
        # Bound XL decoder working memory on 16 GB GPUs.
        arguments=self.server_arguments()
        with (db.DATA / "ace-fork.log").open("ab") as log:
            self.process = await asyncio.create_subprocess_exec(*arguments,
                cwd=db.ROOT, stdout=log, stderr=asyncio.subprocess.STDOUT,
                **({"creationflags":0x08000000} if os.name=="nt" else {}))
            try:
                for _ in range(120):
                    if self.process.returncode is not None:
                        raise EngineError("Musikmodell konnte nicht starten; siehe data/ace-fork.log.")
                    try:
                        await self.delegate.health()
                        break
                    except Exception:
                        await asyncio.sleep(.5)
                else:
                    raise EngineError("Musikmodell antwortet nicht rechtzeitig.")
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
