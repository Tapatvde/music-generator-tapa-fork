"""FastAPI-Backend: Job-Queue, Bibliothek, Einstellungen."""
import asyncio
import json
import logging
import os
import random
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid
import zipfile
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import FastAPI, Header, HTTPException, UploadFile, Form, File
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from . import db, updater, voices, voice_training, deep
from .chorus import selected_lyrics, lyric_sections, section_catalog, chorus_regions
from .engines import EngineError, make_engine, DIT_MODELS
from .managed_engine import make_fork_engine
from .mix_settings import MixSettings
from .levels import wrap_engine
from .klang import hoehen_ausgleichen
from .messages import tr

log = logging.getLogger('uvicorn.error')

STATIC = db.ROOT / "static"
(db.DATA / "tmp").mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(db.DATA / "tmp")
_wakeup = asyncio.Event()
_running: dict = {}   # laufender Auftrag: {"sid", "task", "engine"} – zum Abbrechen
_gpu_lock = asyncio.Lock()


async def run_gpu(engine, params, progress):
    async with _gpu_lock:
        return await engine.generate(params, progress)


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- Worker

class WachHalten:
    """Verhindert den Ruhezustand, solange Songs gerechnet werden (sonst bleibt die Berechnung
    nach 10-20 Minuten Inaktivität einfach stehen). Mac: caffeinate, Windows: SetThreadExecutionState."""
    def __init__(self):
        self._proc = None

    def an(self):
        try:
            if sys.platform == "darwin" and self._proc is None:
                self._proc = subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())],
                                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif sys.platform == "win32":
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        except Exception:  # noqa: BLE001 – Wachhalten ist Komfort, kein Grund zum Abbruch
            pass

    def aus(self):
        try:
            if self._proc is not None:
                self._proc.terminate(); self._proc = None
            elif sys.platform == "win32":
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)   # ES_CONTINUOUS
        except Exception:  # noqa: BLE001
            pass


_wach = WachHalten()


async def worker():
    """Arbeitet die Queue strikt nacheinander ab (eine GPU, ein Job)."""
    while True:
        job = db.one("SELECT * FROM songs WHERE status='queued' ORDER BY created_at, rowid LIMIT 1")
        training=db.one("SELECT * FROM voice_training WHERE status='queued' ORDER BY created_at,rowid LIMIT 1")
        is_training=training is not None and (job is None or training['created_at']<job['created_at'])
        if is_training:job=training
        if not job:
            _wach.aus()
            _wakeup.clear()
            await _wakeup.wait()
            continue
        _wach.an()
        sid = job["id"]
        table='voice_training' if is_training else 'songs'
        if is_training:
            db.execute("UPDATE voice_training SET status='running', message='0:00' WHERE id=?", (sid,))
        else:
            db.execute("UPDATE songs SET status='running', message='0:00', started_at=? WHERE id=?", (now(),sid))
        job_settings = db.get_settings()
        params = json.loads(job["params"])
        if is_training:
            params['name']=job['name'];engine=voice_training.TrainingEngine(sid)
        elif params.get('job_type')=='instrumental':engine=voices.InstrumentalEngine(sid)
        elif params.get('job_type')=='deep':engine=deep.OriginalEdit(sid)
        else:engine = voices.VoiceEngine(sid) if params.get("job_type") == "voice" else make_fork_engine({**db.get_settings(),'dit':params.get('sound_model') or db.get_settings().get('dit','standard')})
        if not is_training:engine=wrap_engine(engine,sid,params)

        async def progress(msg: str):
            db.execute(f"UPDATE {table} SET message=? WHERE id=? AND status='running'", (msg, sid))

        try:
            gen = asyncio.create_task(run_gpu(engine, params, progress))
            _running.update(sid=sid, task=gen, engine=engine)
            try:
                audio, ext, meta = await gen
            except asyncio.CancelledError:
                if not gen.cancelled() or asyncio.current_task().cancelling():
                    raise                   # die App selbst wird beendet
                await engine.cancel()       # vom Nutzer abgebrochen (Status steht schon auf "cancelled")
                continue
            finally:
                _running.clear()
            if not is_training and ext == "wav" and job_settings.get("highs") == "on" and params.get('job_type') in (None,'deep'):
                audio = await asyncio.to_thread(hoehen_ausgleichen, audio)
                meta['highs_applied'] = True
            fname = f"{sid}.{ext}"
            if is_training:
                db.execute("UPDATE voice_training SET status='done',message=NULL,result_meta=?,finished_at=? WHERE id=? AND status='running'",
                           (json.dumps(meta),now(),sid))
                continue
            if db.one("SELECT status FROM songs WHERE id=?", (sid,))["status"] == "running":
                (db.songs_dir() / fname).write_bytes(audio)
                db.execute(
                    "UPDATE songs SET status='done', message=NULL, file=?, engine=?, result_meta=?, finished_at=? WHERE id=?",
                    (fname, engine.name, json.dumps(meta), now(), sid),
                )
                if engine.name == "rvc":
                    voices.record_timing(sid, meta)
                if engine.name not in ("rvc","instrumental") and params.get("voice_after"):
                    try:
                        enqueue_voice(sid, voices.VoiceRequest(**params["voice_after"]))
                    except ValueError as error:
                        meta['warnings']=[*meta.get('warnings',[]),f'Automatische Stimmfassung nicht gestartet: {error}']
                        db.execute('UPDATE songs SET result_meta=? WHERE id=?',(json.dumps(meta),sid))
        except (EngineError, Exception) as e:  # noqa: BLE001 – Fehler landen sichtbar im UI
            text = str(e) or e.__class__.__name__
            if "ConnectError" in repr(e) or "connect" in text.lower():
                text = f"Modellserver nicht erreichbar ({db.get_settings()['server_url']}). Läuft ace-server?"
            db.execute(f"UPDATE {table} SET status='error', message=?, finished_at=? WHERE id=? AND status='running'", (text, now(), sid))


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    voices.recover_timings()
    for old in db.DATA.glob("mg-*.zip"):   # Reste abgebrochener Downloads
        old.unlink(missing_ok=True)
    if sys.platform == "darwin":   # Symbole der Start-Dateien erneuern (Git/ZIP setzen sie zurück)
        subprocess.Popen(["bash", str(Path(__file__).resolve().parent.parent / "scripts" / "symbole.sh")],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    task = asyncio.create_task(worker())
    _wakeup.set()
    if db.get_settings().get("remote") == "on":
        try:
            await _fern.start()
        except OSError as e:
            log.warning("Handy-Zugriff ließ sich nicht starten (Port %s): %s", REMOTE_PORT, e)
    yield
    await _fern.stop()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    finally:
        _wach.aus()


app = FastAPI(title="Music Generator", lifespan=lifespan)


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    """Unerwartete Fehler: ins Log schreiben und eine verständliche Meldung in der Sprache der Oberfläche liefern."""
    log.exception("Unerwarteter Fehler bei %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": tr(request.headers.get("x-lang", "en"), "unexpected", e=type(exc).__name__)})

app.include_router(updater.router)


@app.middleware("http")
async def no_cache(request, call_next):
    """Oberfläche nie aus dem Browser-Cache laden, sonst sieht man alte Stände."""
    resp = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        resp.headers["Cache-Control"] = "no-cache"
    return resp


# ---------------------------------------------------------------- Handy-Zugriff

REMOTE_PORT = 8767   # 8766 is the fork's local UI; never require a token for its loopback access.
# Über den Handy-Zugriff gesperrt: alles, was den Rechner selbst betrifft
REMOTE_BLOCKED = ("/api/shutdown", "/api/update/", "/api/remote")


@app.middleware("http")
async def zugang(request, call_next):
    """Der normale Zugang nimmt nur Aufrufe an localhost an: schützt gegen DNS-Rebinding (fremde Domain, die auf 127.0.0.1
    zeigt). Der Handy-Zugriff (eigener Port) liefert nur die API und verlangt den Zugangsschlüssel."""
    lang = request.headers.get("x-lang", "en")
    if (request.scope.get("server") or (None, None))[1] != REMOTE_PORT:
        if request.headers.get("host", "").rsplit(":", 1)[0] not in ("localhost", "127.0.0.1"):
            return PlainTextResponse("Invalid host header", status_code=400)
        return await call_next(request)
    token = db.get_settings().get("remote_token") or ""
    sent = request.headers.get("authorization", "")
    if not token or not secrets.compare_digest(sent.encode(), f"Bearer {token}".encode()):
        return JSONResponse(status_code=401, content={"detail": tr(lang, "remote_denied")})
    path = request.url.path
    allowed = path in ('/api/settings','/api/health','/api/queue','/api/songs','/api/folders','/api/generate','/api/analyze','/api/download') or re.fullmatch(r'/api/(?:songs/[\w-]+(?:/(?:audio|retry))?|folders/[\w-]+)',path)
    if not allowed or path.startswith(REMOTE_BLOCKED) or (path == "/api/settings" and request.method != "GET"):
        return JSONResponse(status_code=403, content={"detail": tr(lang, "remote_blocked")})
    return await call_next(request)


class _Nebenserver(uvicorn.Server):
    @contextmanager
    def capture_signals(self):   # Signale (Strg+C, Beenden) gehören dem Hauptserver
        yield


class Fernzugriff:
    """Zweiter Zugang auf allen Netzwerkschnittstellen im selben Prozess, damit das Handy im Heimnetz die Bibliothek
    abspielen und Songs erzeugen kann. Lässt sich ohne Neustart ein- und ausschalten."""
    def __init__(self):
        self._server: _Nebenserver | None = None
        self._task: asyncio.Task | None = None

    @property
    def an(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self):
        if self.an:
            return
        # Den Port selbst öffnen: scheitert uvicorn beim Binden, beendet es mit sys.exit den ganzen Prozess
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if sys.platform != "win32":   # unter Windows erlaubt SO_REUSEADDR das doppelte Belegen eines Ports
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", REMOTE_PORT))
        except OSError:
            sock.close()
            raise
        # log_config/log_level None: die Protokoll-Einstellungen des Hauptservers nicht überschreiben
        config = uvicorn.Config(app, lifespan="off", log_config=None, log_level=None, timeout_graceful_shutdown=2)
        self._server = _Nebenserver(config)
        self._task = asyncio.create_task(self._server.serve(sockets=[sock]))
        log.info("Handy-Zugriff an, Port %s", REMOTE_PORT)

    async def stop(self):
        if not self._task:
            return
        self._server.should_exit = True
        try:
            await asyncio.wait_for(self._task, 5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            self._task.cancel()
        self._server = self._task = None
        log.info("Handy-Zugriff aus")


_fern = Fernzugriff()


def _adressen() -> list[str]:
    """Adressen, unter denen das Handy diesen Rechner im Heimnetz findet."""
    names = []
    if sys.platform == "darwin":
        try:
            n = subprocess.run(["scutil", "--get", "LocalHostName"], capture_output=True, text=True, timeout=3).stdout.strip()
            if n:
                names.append(f"{n}.local")
        except (OSError, subprocess.TimeoutExpired):
            pass
    else:
        names.append(socket.gethostname())
    try:   # eigene Adresse im Heimnetz: Route zu einer privaten Adresse nachschlagen, es wird nichts gesendet
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            names.append(s.getsockname()[0])
    except OSError:
        pass
    return [f"http://{n}:{REMOTE_PORT}" for n in dict.fromkeys(names) if n and not n.startswith("127.")]


class RemoteIn(BaseModel):
    enabled: bool | None = None
    new_token: bool = False


@app.get("/api/remote")
def remote_status():
    return {"enabled": _fern.an, "port": REMOTE_PORT, "token": db.get_settings().get("remote_token", ""),
            "addresses": _adressen()}


@app.post("/api/remote")
async def remote_set(r: RemoteIn, x_lang: str = Header("de")):
    if r.new_token or (r.enabled and not db.get_settings().get("remote_token")):
        db.save_settings({"remote_token": secrets.token_urlsafe(18)})
    if r.enabled is not None:
        if r.enabled:
            try:
                await _fern.start()
            except OSError as e:
                raise HTTPException(409, tr(x_lang, "remote_port_busy", port=REMOTE_PORT, e=e.strerror or e)) from e
        else:
            await _fern.stop()
        db.save_settings({"remote": "on" if r.enabled else "off"})
    return remote_status()


# ---------------------------------------------------------------- Modelle

class GenerateRequest(BaseModel):
    prompt: str = ""               # Idee / Beschreibung für den Song
    style: str = ""                # Stilrichtung (Genre-Tags)
    caption: str = ""              # nur für ältere Songs: fertiger Text; sonst aus style + prompt gebaut
    lyrics: str = ""
    instrumental: bool = True
    keep_caption: bool = True      # True = Modell schreibt die Beschreibung nicht um
    title: str = ""
    duration: float = 0            # 0 = Modell entscheidet
    bpm: int = 0
    keyscale: str = ""
    timesignature: str = ""
    vocal_language: str = ""
    seed: int = -1                 # -1 = zufällig (wird trotzdem gespeichert)
    variants: int = Field(1, ge=1, le=50)
    inference_steps: int = 0
    lm_temperature: float | None = None
    group_id: str | None = None    # für "weitere Variante" einer bestehenden Gruppe
    folder_id: str | None = None   # Ordner der Bibliothek, in dem die neuen Songs landen
    voice_after: voices.VoiceRequest | None = None
    mix_levels: MixSettings = Field(default_factory=MixSettings)
    sound_model: Literal['standard','xl'] | None = None


class SongPatch(BaseModel):
    favorite: bool | None = None
    title: str | None = None
    folder_id: str | None = None   # None/"" = unsortiert (nur ausgewertet, wenn mitgeschickt)
    library_role: Literal["final", "test", "original"] | None = None


class FolderIn(BaseModel):
    name: str


class VoicePlan(BaseModel):
    seconds: float = Field(ge=5, le=36000, allow_inf_nan=False)
    quality: Literal["standard", "best"] = "standard"
    harmony: bool = False
    auto_chorus: bool = False
    section_pitch: bool = False


def letters() -> dict:
    """Versionen desselben Prompts heißen in Entstehungsreihenfolge A, B, C … (über alle Ordner hinweg)."""
    groups: dict = {}
    for r in db.query("SELECT id, group_id FROM songs ORDER BY created_at, rowid"):
        groups.setdefault(r["group_id"], []).append(r["id"])
    return {sid: chr(65 + i) for ids in groups.values() if len(ids) > 1 for i, sid in enumerate(ids) if i < 26}


def folder_where(folder: str) -> tuple[str, list]:
    """Filter der Bibliothek: "" = alle, "none" = unsortiert, sonst Ordner-ID."""
    if folder == "none":
        return " AND folder_id IS NULL", []
    if folder:
        return " AND folder_id=?", [folder]
    return "", []


def song_out(r: dict, letter: dict | None = None) -> dict:
    r["letter"] = (letter or {}).get(r["id"], "")
    r["params"] = json.loads(r["params"])
    r["result_meta"] = json.loads(r["result_meta"]) if r["result_meta"] else None
    r["favorite"] = bool(r["favorite"])
    r["url"] = f"/api/songs/{r['id']}/audio" if r["file"] else None
    return r


# ---------------------------------------------------------------- API

@app.post("/api/generate")
async def generate(req: GenerateRequest, x_lang: str = Header('de')):
    req.sound_model=req.sound_model or db.get_settings().get('dit','standard')
    if req.sound_model=='xl' and not (db.MODELS_DIR/DIT_MODELS['xl']).is_file():
        raise HTTPException(400,tr(x_lang,'xl_missing'))
    if req.voice_after:req.voice_after.mix_levels=req.mix_levels
    if req.voice_after:
        if voices.needs_alignment(req.voice_after) and req.lyrics.strip():
            try:
                voices.validate_lyrics(req.voice_after, req.lyrics)
            except ValueError as e:
                raise HTTPException(422, str(e)) from e
        try:
            voices.validate_sections(req.voice_after, req.duration)
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        try:
            voices.get_profile(req.voice_after.profile_id)
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        if req.instrumental or req.voice_after.preview:
            raise HTTPException(422, "Automatische Stimmumwandlung benötigt einen Song mit Gesang und eine vollständige Fassung.")
        if req.voice_after.base_song_id:
            raise HTTPException(422, "Abschnittsbearbeitung ist nur bei einer vorhandenen Vollfassung möglich.")
    group = req.group_id or uuid.uuid4().hex[:12]
    lyrics = "[Instrumental]" if req.instrumental else req.lyrics.strip()
    parts = [p.strip().strip(",") for p in (req.style, req.prompt) if p.strip()]
    caption = ", ".join(parts) if parts else req.caption.strip()
    if not caption:
        raise HTTPException(422, tr(x_lang, "no_prompt"))
    base = req.model_dump(exclude={"variants", "group_id", "folder_id", "instrumental", "title", "keep_caption"})
    base["caption"] = caption
    base["use_cot_caption"] = not req.keep_caption
    base["lyrics"] = lyrics
    folder = req.folder_id if req.folder_id and db.one("SELECT id FROM folders WHERE id=?", (req.folder_id,)) else None
    ids = []
    for i in range(req.variants):
        # Erste Variante nimmt den festen Seed, weitere zählen hoch -> alles reproduzierbar
        seed = random.randint(0, 2**31 - 1) if req.seed < 0 else req.seed + i
        params = {**base, "seed": seed}
        sid = uuid.uuid4().hex[:12]
        db.execute(
            "INSERT INTO songs(id, group_id, created_at, status, title, caption, lyrics, seed, params, folder_id) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (sid, group, now(), "queued", req.title.strip() or None, caption, lyrics, seed, json.dumps(params), folder),
        )
        ids.append(sid)
    _wakeup.set()
    return {"group_id": group, "ids": ids}


@app.get("/api/songs")
def list_songs(q: str = "", favorites: bool = False, group: str = "", folder: str = ""):
    sql, args = "SELECT * FROM songs WHERE 1=1", []
    if q:
        sql += " AND (caption LIKE ? OR lyrics LIKE ? OR title LIKE ?)"
        args += [f"%{q}%"] * 3
    if favorites:
        sql += " AND favorite=1"
    if group:
        sql += " AND group_id=?"
        args.append(group)
    fw, fa = folder_where(folder)
    sql += fw + " ORDER BY created_at DESC, rowid DESC LIMIT 500"
    lt = letters()
    return [song_out(r, lt) for r in db.query(sql, tuple(args + fa))]


@app.get("/api/songs/{sid}")
def get_song(sid: str):
    r = db.one("SELECT * FROM songs WHERE id=?", (sid,))
    if not r:
        raise HTTPException(404)
    return song_out(r)


@app.patch("/api/songs/{sid}")
def patch_song(sid: str, p: SongPatch):
    if p.favorite is not None:
        db.execute("UPDATE songs SET favorite=? WHERE id=?", (int(p.favorite), sid))
    if p.title is not None:
        db.execute("UPDATE songs SET title=? WHERE id=?", (p.title.strip() or None, sid))
    if "folder_id" in p.model_fields_set:
        db.execute("UPDATE songs SET folder_id=? WHERE id=?", (p.folder_id or None, sid))
    if "library_role" in p.model_fields_set:
        row=db.one("SELECT params FROM songs WHERE id=?",(sid,))
        if not row:
            raise HTTPException(404)
        params=json.loads(row["params"])
        params["library_role"]=p.library_role
        db.execute("UPDATE songs SET params=? WHERE id=?",(json.dumps(params),sid))
    return get_song(sid)


@app.post("/api/songs/{sid}/retry")
async def retry_song(sid: str):
    db.execute("UPDATE songs SET status='queued', message=NULL, finished_at=NULL WHERE id=? AND status IN ('error','cancelled')", (sid,))
    _wakeup.set()
    return get_song(sid)


@app.delete("/api/songs/{sid}")
async def delete_song(sid: str):
    r = db.one("SELECT * FROM songs WHERE id=?", (sid,))
    if not r:
        raise HTTPException(404)
    dependants = [x for x in db.query("SELECT id, params, status FROM songs WHERE id<>?", (sid,))
                  if json.loads(x["params"]).get("source_song_id") == sid
                  or json.loads(x["params"]).get('backing_song_id') == sid
                  or json.loads(x["params"]).get('vocal_source_song_id') == sid
                  or (x["status"] != "done" and sid in [json.loads(x["params"]).get(key) for key in ("base_song_id","preview_song_id")])
                  or json.loads(x["params"]).get("voice",{}).get("base_song_id") == sid]
    if dependants:
        raise HTTPException(409, "Dieser Eintrag wird noch als Vorlage für eine andere Fassung benötigt. Bitte zuerst die abhängigen Einträge entfernen.")
    if r["status"] == "queued":
        db.execute("UPDATE songs SET status='cancelled' WHERE id=?", (sid,))
        return {"cancelled": True}
    if r["status"] == "running":
        db.execute("UPDATE songs SET status='cancelled', message=NULL, finished_at=? WHERE id=?", (now(), sid))
        if _running.get("sid") == sid:
            _running["task"].cancel()
        return {"cancelled": True}
    if r["file"]:
        voices.preserve_timings()
        (db.songs_dir() / r["file"]).unlink(missing_ok=True)
    for old in (db.DATA / "export").glob(f"{sid}_*.mp3"):   # umgewandelte MP3-Kopien des Downloads
        old.unlink(missing_ok=True)
    db.execute("DELETE FROM songs WHERE id=?", (sid,))
    return {"deleted": True}


# ---------------------------------------------------------------- Stimmen

def enqueue_voice(sid: str, req: voices.VoiceRequest):
    selected=db.one('SELECT * FROM songs WHERE id=?',(sid,))
    if not selected:raise ValueError('Song fehlt.')
    selected_params=json.loads(selected['params'])
    backing_id=req.instrumental_song_id or (sid if selected_params.get('job_type')=='instrumental' else selected_params.get('backing_song_id'))
    if backing_id:
        backing=db.one('SELECT * FROM songs WHERE id=?',(backing_id,))
        if not backing or backing['status']!='done' or json.loads(backing['params']).get('job_type')!='instrumental':
            raise ValueError('Instrumentalgrundlage fehlt oder ist nicht fertig.')
        if voices.original_song(backing_id)['id']!=voices.original_song(sid)['id']:
            raise ValueError('Instrumentalgrundlage und Gesangsvorlage gehören zu unterschiedlichen Songs.')
        req=req.model_copy(update={'instrumental_song_id':backing_id})
    source = voices.conversion_source(sid,req.instrumental_song_id)
    voices.validate_lyrics(req, selected_lyrics(source))
    profile = voices.get_profile(req.profile_id)
    if req.base_song_id:
        base = db.one("SELECT * FROM songs WHERE id=?", (req.base_song_id,))
        if not req.preview or not base or base["status"]!="done" or base["engine"]!="rvc" or json.loads(base["result_meta"] or "{}").get("preview"):
            raise ValueError("Eine Abschnittsvorschau benötigt eine fertige vollständige Stimmversion.")
        if voices.original_song(req.base_song_id)["id"] != source["id"]:
            raise ValueError("Die Vollfassung gehört zu einem anderen Original.")
    params = json.loads(source["params"])
    params.pop("voice_after", None)
    params.pop("library_role", None)
    params.update(job_type="voice", source_song_id=source["id"], voice=req.model_dump())
    if backing_id:params['backing_song_id']=backing_id
    version = uuid.uuid4().hex[:12]
    db.execute("INSERT INTO songs(id, group_id, created_at, status, title, caption, lyrics, seed, params, folder_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
               (version, source["group_id"], now(), "queued", source["title"], source["caption"], source["lyrics"], source["seed"], json.dumps(params), base["folder_id"] if req.base_song_id else selected["folder_id"]))
    _wakeup.set()
    return {"id":version, "source_song_id":source["id"], "profile":profile["name"]}


@app.get("/api/voices")
def list_voices():
    return {"profiles":[{k:v for k,v in p.items() if k not in ("model", "index")} for p in voices.profile_list()],
            "ready":voices.PYTHON.is_file() and voices.FFPROBE.is_file()}


@app.get('/api/voice-training')
def training_list():
    return {'items':voice_training.items(),'removed':voice_training.items(removed=True),'ready':voice_training.prerequisites()}


@app.post('/api/deep/separate-chords')
def deep_chords(req: deep.ParseRequest):
    return deep.separate_chords(req.text)


@app.post('/api/deep/generate')
async def deep_generate(req: deep.EditRequest):
    try:
        source=deep.source_song(req.source_song_id)
        info=await asyncio.to_thread(voices.probe,voices.contained(db.songs_dir()/source['file']))
        result=deep.enqueue(req,source,info,now());_wakeup.set();return result
    except ValueError as error:raise HTTPException(422,str(error)) from error


@app.delete('/api/voice-training/{identifier}')
async def training_remove(identifier: str):
    try:
        if _running.get('sid')==identifier:
            raise ValueError('Das Training wird noch beendet. Bitte kurz warten.')
        voice_training.remove(identifier)
        return {'removed':True,'recoverable':True}
    except KeyError as error:raise HTTPException(404,'Stimmprofil nicht gefunden.') from error
    except ValueError as error:raise HTTPException(409,str(error)) from error


@app.post('/api/voice-training/{identifier}/restore')
async def training_restore(identifier: str):
    try:
        voice_training.restore(identifier)
        return {'restored':True}
    except KeyError as error:raise HTTPException(404,'Stimmprofil nicht gefunden.') from error
    except ValueError as error:raise HTTPException(409,str(error)) from error


@app.post('/api/voice-training/import')
async def training_import(name: str=Form(...), files: list[UploadFile]=File(...)):
    try:return await voice_training.upload(name,files)
    except ValueError as error:raise HTTPException(422,str(error)) from error


@app.post('/api/voice-training/{identifier}/start')
async def training_start(identifier: str,req: voice_training.TrainingRequest):
    row=db.one('SELECT * FROM voice_training WHERE id=?',(identifier,))
    if not row:raise HTTPException(404)
    if row['status']!='draft':raise HTTPException(409,'Dieser Trainingslauf wurde bereits gestartet. Für eine weitere Fassung ein neues Profil anlegen.')
    if not voice_training.prerequisites():raise HTTPException(422,'Die lokalen RVC-Trainingsbestandteile fehlen.')
    params=json.loads(row['params']);params['epochs']=req.epochs
    db.execute("UPDATE voice_training SET status='queued',message=NULL,params=? WHERE id=? AND status='draft'",(json.dumps(params),identifier))
    _wakeup.set()
    return {'id':identifier,'status':'queued'}


@app.post('/api/voice-training/{identifier}/cancel')
async def training_cancel(identifier: str):
    row=db.one('SELECT status FROM voice_training WHERE id=?',(identifier,))
    if not row:raise HTTPException(404)
    if row['status'] not in ('queued','running'):raise HTTPException(409,'Dieser Auftrag läuft nicht.')
    db.execute("UPDATE voice_training SET status='cancelled',message='Training abgebrochen',finished_at=? WHERE id=?",(now(),identifier))
    if _running.get('sid')==identifier:_running['task'].cancel()
    return {'cancelled':True}


class InstrumentalRequest(BaseModel):
    quality: Literal['standard','best']='best'


@app.post('/api/songs/{sid}/instrumental')
async def instrumental_version(sid: str,req: InstrumentalRequest):
    source=db.one('SELECT * FROM songs WHERE id=?',(sid,))
    if not source or source['status']!='done' or not source['file']:raise HTTPException(422,'Bitte einen fertigen Song auswählen.')
    params=json.loads(source['params'])
    if params.get('job_type')=='instrumental' or params.get('voice',{}).get('preview') or params.get('deep',{}).get('preview') or source['lyrics']=='[Instrumental]':raise HTTPException(422,'Bitte eine vollständige Fassung mit Gesang auswählen.')
    try:
        original=voices.original_song(sid)
        await asyncio.to_thread(voices.probe, voices.contained(db.songs_dir()/source['file']))
    except ValueError as error:
        raise HTTPException(422,str(error)) from error
    params={k:v for k,v in params.items() if k not in ('voice_after','voice','library_role','backing_song_id')}
    params.update(job_type='instrumental',source_song_id=sid,vocal_source_song_id=original['id'],quality=req.quality,instrumental=True,imported=True)
    version=uuid.uuid4().hex[:12]
    db.execute("INSERT INTO songs(id,group_id,created_at,status,title,caption,lyrics,seed,params,folder_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
               (version,source['group_id'],now(),'queued',source['title'],source['caption'],'[Instrumental]',source['seed'],json.dumps(params),source['folder_id']))
    _wakeup.set()
    return {'id':version,'vocal_source_song_id':original['id']}


@app.post("/api/voice-plan")
def voice_plan(req: VoicePlan):
    result=voices.estimate_duration(req.seconds, req.quality, harmony=req.harmony)
    if (req.harmony and req.auto_chorus) or req.section_pitch:
        result['stages']['alignment']=round(20+req.seconds*.15,1)
        total=sum(result['stages'].values());result.update(seconds_low=round(total*.65),seconds_high=round(total*1.75))
    if req.section_pitch:
        result['stages']['conversion']+=round(6+req.seconds*.05,1)
        total=sum(result['stages'].values());result.update(seconds_low=round(total*.65),seconds_high=round(total*1.75))
    return result


@app.get('/api/songs/{sid}/choruses')
async def song_choruses(sid: str):
    try:
        source=voices.conversion_source(sid);lyrics=selected_lyrics(source)
        tagged=sum(s['chorus'] for s in lyric_sections(lyrics))
        sha=await asyncio.to_thread(voices.digest,db.songs_dir()/source['file'])
        results={}
        for quality in ('standard','best'):
            path=voices.chorus_cache(sha,lyrics,quality)
            if path.is_file():
                data=json.loads(path.read_text(encoding='utf-8'))
                regions,rejected=chorus_regions(lyric_sections(lyrics),data.get('lines',[]),data.get('duration',0),all_sections=True)
                results[quality]={**{k:data[k] for k in ('regions','rejected')},'sections':regions,'sections_rejected':rejected}
        return {'tagged_count':tagged,'sections':section_catalog(lyrics),'model_ready':(db.ROOT/'engine/chorus-aligner/model.pt').is_file(),'results':results}
    except ValueError as error:
        raise HTTPException(422,str(error)) from error


@app.put("/api/voices/{profile_id}")
def update_voice(profile_id: str, req: voices.RangeSettings):
    try:
        p = voices.save_profile(profile_id, req)
        return {k:v for k,v in p.items() if k not in ("model", "index")}
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@app.post("/api/songs/{sid}/voice-estimate")
async def estimate_voice(sid: str, req: voices.VoiceRequest):
    try:
        voices.get_profile(req.profile_id)
        source = voices.conversion_source(sid,req.instrumental_song_id)
        return await asyncio.to_thread(voices.estimate, db.songs_dir() / source["file"], req, selected_lyrics(source))
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@app.post("/api/songs/{sid}/voice")
async def convert_voice(sid: str, req: voices.VoiceRequest):
    try:
        source = voices.conversion_source(sid,req.instrumental_song_id)
        # Validate real duration before queueing, not only the metadata.
        estimate = await asyncio.to_thread(voices.estimate, db.songs_dir() / source["file"], req, selected_lyrics(source))
        plan = estimate.get('section_plan', {})
        if plan.get('available'):
            from .register_policy import require_section_plan
            require_section_plan(req.section_pitch.model_dump(), selected_lyrics(source), plan['sections'])
        return enqueue_voice(sid, req)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@app.get("/api/songs/{sid}/voice-audio")
def voice_audio(sid: str, kind: str = "vocals"):
    row = db.one("SELECT * FROM songs WHERE id=?", (sid,))
    if not row or row["status"] != "done" or row["engine"] not in ("rvc", "instrumental") or kind not in ("vocals", "mp3", "lead", "harmony"):
        raise HTTPException(404)
    if row['engine'] == 'instrumental' and kind != 'mp3':
        raise HTTPException(404)
    path = db.DATA / "voice-jobs" / sid / {"vocals":"vocals.wav", "mp3":"mix.mp3", "lead":"lead.wav", "harmony":"harmony.wav"}[kind]
    if not path.is_file():
        raise HTTPException(404)
    return FileResponse(path, filename=f"{sid}_{kind}{path.suffix}")


class SectionApply(BaseModel):
    preview_song_id: str


@app.post("/api/songs/{sid}/apply-section")
async def apply_section(sid: str, req: SectionApply):
    try:
        base, preview = voices.section_pair(sid, req.preview_song_id)
        params=json.loads(base["params"])
        params.pop("library_role",None)
        params["voice"]={**params["voice"],"preview":False,"base_song_id":None}
        params.update(operation="section_patch",base_song_id=sid,preview_song_id=preview["id"])
        version=uuid.uuid4().hex[:12]
        db.execute("INSERT INTO songs(id,group_id,created_at,status,title,caption,lyrics,seed,params,folder_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (version,base["group_id"],now(),"queued",base["title"],base["caption"],base["lyrics"],base["seed"],json.dumps(params),base["folder_id"]))
        _wakeup.set()
        return {"id":version}
    except ValueError as e:
        raise HTTPException(422,str(e)) from e


@app.post("/api/library/import")
async def import_song(audio: UploadFile):
    """Import a finished song for voice conversion, distinct from prompt analysis."""
    suffix = Path(audio.filename or "").suffix.lower()
    if suffix not in (".wav", ".mp3", ".flac", ".m4a", ".ogg"):
        raise HTTPException(415, "Bitte WAV, MP3, FLAC, M4A oder OGG importieren.")
    sid = uuid.uuid4().hex[:12]
    path = db.songs_dir() / f"{sid}{suffix}"
    try:
        size = 0
        with path.open("wb") as stream:
            while chunk := await audio.read(1024 * 1024):
                size += len(chunk)
                if size > 512 * 1024 * 1024:
                    raise HTTPException(413, "Datei zu groß (maximal 512 MB).")
                stream.write(chunk)
        info = await asyncio.to_thread(voices.probe, path)
        title = Path(audio.filename).stem[:160]
        db.execute("INSERT INTO songs(id, group_id, created_at, finished_at, status, title, caption, lyrics, seed, params, result_meta, engine, file) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (sid, sid, now(), now(), "done", title, title, "", -1, json.dumps({"imported":True, "duration":info["seconds"]}), json.dumps({"duration":info["seconds"]}), "import", path.name))
        return get_song(sid)
    except Exception as e:
        path.unlink(missing_ok=True)
        if isinstance(e, ValueError):
            raise HTTPException(422, str(e)) from e
        raise
    finally:
        await audio.close()


MP3_KBPS = 192
FFMPEG = voices.RVC / ('ffmpeg.exe' if os.name == 'nt' else 'ffmpeg')


def _mp3_tool() -> Path | None:
    """Der MP3-Wandler der Engine (mp3-codec), wenn er mitgeliefert wurde."""
    b = db.ROOT / "engine" / "acestep.cpp" / "build"
    for p in (b / "mp3-codec", b / "mp3-codec.exe", b / "Release" / "mp3-codec.exe", b / "bin" / "mp3-codec.exe"):
        if p.is_file():
            return p
    if FFMPEG.is_file():
        return FFMPEG
    return None


def _export_file(r: dict, lang: str = "de") -> Path:
    """Datei für den Download: das Original (WAV) oder, wenn unter Einstellungen MP3 gewählt ist, eine umgewandelte Kopie.
    Die Bibliothek behält immer das verlustfreie Original; die MP3 liegt nur als Zwischenspeicher in data/export."""
    src = db.songs_dir() / r["file"]
    if db.get_settings().get("export_format") != "mp3" or src.suffix.lower() == ".mp3":
        return src
    tool = _mp3_tool()
    if src.suffix.lower() != '.wav' and FFMPEG.is_file():
        tool = FFMPEG
    if not tool:
        raise HTTPException(500, tr(lang, "mp3_failed"))
    cache = db.DATA / "export"
    cache.mkdir(exist_ok=True)
    out = cache / f"{r['id']}_{MP3_KBPS}.mp3"
    if out.is_file() and out.stat().st_mtime >= src.stat().st_mtime:
        return out
    part = cache / f"{r['id']}_{uuid.uuid4().hex}.part.mp3"
    command = [str(tool), '-i', str(src), '-o', str(part), '-b', str(MP3_KBPS)]
    if tool.name.lower() in ('ffmpeg','ffmpeg.exe'):
        command = [str(tool),'-nostdin','-hide_banner','-loglevel','error','-y','-i',str(src),'-vn','-codec:a','libmp3lame','-b:a',f'{MP3_KBPS}k',str(part)]
    try:
        res = subprocess.run(command, capture_output=True, timeout=180,
                             **({'creationflags':0x08000000} if os.name=='nt' else {}))
    except (OSError, subprocess.TimeoutExpired) as e:
        log.warning("MP3-Wandler %s ließ sich nicht ausführen: %r", tool, e)   # z. B. Virenscanner oder fehlende Rechte
        part.unlink(missing_ok=True)
        raise HTTPException(500, tr(lang, "mp3_failed"))
    if res.returncode or not part.is_file() or part.stat().st_size < 1000:
        log.warning("MP3-Wandler %s: Rückgabewert %s, Ausgabe %s Byte, Quelle %s, Meldung: %s", tool, res.returncode,
                    part.stat().st_size if part.is_file() else "keine", src,
                    (res.stderr or b"").decode("utf-8", "replace").strip()[-400:])
        part.unlink(missing_ok=True)
        raise HTTPException(500, tr(lang, "mp3_failed"))
    part.replace(out)
    return out


@app.get("/api/songs/{sid}/audio")
def song_audio(sid: str, download: bool = False, x_lang: str = Header("de")):
    r = db.one("SELECT * FROM songs WHERE id=?", (sid,))
    if not r or not r["file"]:
        raise HTTPException(404)
    path = _export_file(r, x_lang) if download else db.songs_dir() / r["file"]
    name = None
    if download:
        base = r["title"] or r["caption"][:40]
        base = re.sub(r"[^\w\- ]+", "", base).strip().replace(" ", "_") or "song"
        name = f"{base}_{r['seed']}{path.suffix}"
    return FileResponse(path, filename=name)


# ---------------------------------------------------------------- Ordner

@app.get("/api/folders")
def list_folders():
    counts = {r["folder_id"]: r["n"] for r in db.query("SELECT folder_id, COUNT(*) AS n FROM songs GROUP BY folder_id")}
    folders = db.query("SELECT id, name FROM folders ORDER BY name COLLATE NOCASE")
    known = {f["id"] for f in folders}
    for f in folders:
        f["count"] = counts.get(f["id"], 0)
    # Songs, deren Ordner es nicht mehr gibt, zählen als unsortiert
    return {"folders": folders, "all": sum(counts.values()), "none": sum(n for k, n in counts.items() if k not in known)}


@app.post("/api/folders")
def create_folder(f: FolderIn, x_lang: str = Header("de")):
    name = f.name.strip()[:60]
    if not name:
        raise HTTPException(422, tr(x_lang, "no_name"))
    fid = uuid.uuid4().hex[:12]
    db.execute("INSERT INTO folders(id, name, created_at) VALUES(?,?,?)", (fid, name, now()))
    return {"id": fid, "name": name}


@app.patch("/api/folders/{fid}")
def rename_folder(fid: str, f: FolderIn, x_lang: str = Header("de")):
    name = f.name.strip()[:60]
    if not name:
        raise HTTPException(422, tr(x_lang, "no_name"))
    db.execute("UPDATE folders SET name=? WHERE id=?", (name, fid))
    return {"id": fid, "name": name}


@app.delete("/api/folders/{fid}")
def delete_folder(fid: str):
    """Löscht nur den Ordner; seine Songs werden wieder unsortiert."""
    db.execute("UPDATE songs SET folder_id=NULL WHERE folder_id=?", (fid,))
    db.execute("DELETE FROM folders WHERE id=?", (fid,))
    return {"deleted": True}


@app.get("/api/download")
def download_zip(folder: str = "", x_lang: str = Header("de")):
    """Alle fertigen Songs der Ansicht (alle / unsortiert / ein Ordner) als ZIP mit lesbaren Dateinamen."""
    fw, fa = folder_where(folder)
    rows = db.query("SELECT * FROM songs WHERE status='done' AND file IS NOT NULL" + fw + " ORDER BY created_at, rowid", tuple(fa))
    rows = [r for r in rows if (db.songs_dir() / r["file"]).is_file()]
    if not rows:
        raise HTTPException(404, tr(x_lang, "no_done_songs"))
    clean = lambda s: re.sub(r"[^\w\- ]+", "", s).strip()   # noqa: E731
    f = db.one("SELECT name FROM folders WHERE id=?", (folder,)) if folder not in ("", "none") else None
    zip_name = clean(f["name"] if f else "Music Generator") or "Music Generator"
    lt, used = letters(), set()
    tmp = tempfile.NamedTemporaryFile(prefix="mg-", suffix=".zip", dir=db.DATA, delete=False)
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as z:   # WAV und MP3 lassen sich kaum packen -> nur bündeln
        for r in rows:
            path = _export_file(r, x_lang)
            base = " ".join(x for x in (clean(r["title"] or r["caption"][:40]) or "Song", lt.get(r["id"], "")) if x)
            name = f"{base}{path.suffix}"
            if name.lower() in used:
                name = f"{base} {r['seed']}{path.suffix}"
            used.add(name.lower())
            z.write(path, f"{zip_name}/{name}")
    tmp.close()
    return FileResponse(tmp.name, filename=f"{zip_name}.zip", media_type="application/zip",
                        background=BackgroundTask(Path(tmp.name).unlink, missing_ok=True))


@app.get("/api/queue")
def queue():
    rows = db.query("SELECT id, status, message, caption FROM songs WHERE status IN ('queued','running') ORDER BY created_at, rowid")
    rows += [{**r,'caption':'Stimmtraining: '+r['name']} for r in db.query("SELECT id,name,status,message FROM voice_training WHERE status IN ('queued','running')")]
    files = [f.stat().st_size for f in db.songs_dir().iterdir() if f.is_file()]
    return {"running": [r for r in rows if r["status"] == "running"], "queued": len([r for r in rows if r["status"] == "queued"]),
            "library": {"count": len(files), "bytes": sum(files)}}


@app.get("/api/settings")
def get_settings():
    return {**db.get_settings(), "lm_device": db.lm_device(), "mp3_available": _mp3_tool() is not None, "songs_dir_default": str(db.SONGS_DIR),
            "dit_xl_available": (db.MODELS_DIR / DIT_MODELS["xl"]).is_file()}


@app.put("/api/settings")
def put_settings(values: dict, x_lang: str = Header("de")):
    if any(key in values for key in ('remote','remote_token')):
        raise HTTPException(422, 'Handy-Zugriff bitte über den eigenen Schalter ändern. / Use the dedicated remote-access switch.')
    has_lm_device = 'lm_device' in values
    device = values.pop('lm_device', None)
    if has_lm_device and (not isinstance(device, str) or device not in ('auto', 'cpu')):
        raise HTTPException(422, tr(x_lang, 'fork_unknown_lm_device'))
    for k in ("timeout_minutes", "poll_interval"):   # Zahlen prüfen: ein Textwert würde später jede Erzeugung abbrechen
        if k in values:
            try:
                if isinstance(values[k], bool):
                    raise ValueError
                values[k] = float(values[k])
                if not (0 < values[k] < float("inf")):
                    raise ValueError
            except (TypeError, ValueError):
                raise HTTPException(422, tr(x_lang, "bad_number", field=k))
            if k == "timeout_minutes" and values[k].is_integer():
                values[k] = int(values[k])
    if 'dit' in values:
        if not isinstance(values['dit'],str) or values['dit'] not in DIT_MODELS:raise HTTPException(422,tr(x_lang,'fork_unknown_model'))
        if values['dit']=='xl' and not (db.MODELS_DIR/DIT_MODELS['xl']).is_file():
            raise HTTPException(400,tr(x_lang,'xl_missing'))
    for key,allowed in (('highs',('off','on')),('export_format',('wav','mp3'))):
        if key in values and (not isinstance(values[key],str) or values[key] not in allowed):
            raise HTTPException(422, 'Ungültige Einstellung. / Invalid setting: '+key)
    if values.get('export_format')=='mp3' and not _mp3_tool():
        raise HTTPException(400,tr(x_lang,'mp3_failed'))
    if "songs_dir" in values:
        values["songs_dir"] = _move_songs(str(values["songs_dir"] or "").strip(), x_lang)
    if has_lm_device:
        db.set_lm_device(device)
    return {**db.save_settings(values), 'lm_device':db.lm_device()}


def _move_songs(new: str, lang: str) -> str:
    """Song-Ordner wechseln: prüfen, anlegen, vorhandene Songs hinüber verschieben. Gibt den zu speichernden Wert zurück."""
    old_dir = db.songs_dir()
    new_dir = Path(new).expanduser() if new else db.SONGS_DIR
    if new and not new_dir.is_absolute():
        raise HTTPException(400, tr(lang, 'path_abs'))
    if not new_dir.resolve().is_relative_to(db.ROOT.resolve()):
        raise HTTPException(400, tr(lang,'fork_song_path'))
    try:
        new_dir.mkdir(parents=True, exist_ok=True)
        probe = new_dir / ".schreibtest"
        probe.write_text("ok"); probe.unlink()
    except OSError as e:
        raise HTTPException(400, tr(lang, "folder_unusable", e=e.strerror or e)) from e
    if new_dir.resolve() != old_dir.resolve():
        busy = db.one("SELECT COUNT(*) AS n FROM songs WHERE status IN ('queued','running')")["n"]
        if busy:
            raise HTTPException(409, tr(lang, "busy"))
        for r in db.query("SELECT file FROM songs WHERE file IS NOT NULL"):
            src = old_dir / r["file"]
            if src.is_file() and not (new_dir / r["file"]).exists():
                try:
                    shutil.move(str(src), str(new_dir / r["file"]))
                except OSError as e:
                    raise HTTPException(400, tr(lang, "move_failed", f=r["file"], e=e)) from e
    return "" if new_dir.resolve() == db.SONGS_DIR.resolve() else str(new_dir)


@app.post("/api/analyze")
async def analyze(audio: UploadFile, x_lang: str = Header("de")):
    """Song hochladen -> Modell liefert Stil, Tempo, Tonart, Lyrics als Vorschlag fürs Formular."""
    if not (audio.content_type or "").startswith("audio/") and not audio.filename.lower().endswith((".wav", ".mp3", ".flac", ".m4a", ".ogg")):
        raise HTTPException(415, tr(x_lang, "audio_only"))
    data = await audio.read()
    if len(data) > 60 * 1024 * 1024:
        raise HTTPException(413, tr(x_lang,'too_big'))
    engine = make_fork_engine(db.get_settings())
    try:
        async with _gpu_lock:
            result = await engine.analyze(data, audio.filename or "upload")
    except EngineError as e:
        raise HTTPException(502, str(e) or "Analyse fehlgeschlagen") from e
    return {
        "caption": result.get("caption", ""),
        "lyrics": result.get("lyrics", ""),
        "bpm": result.get("bpm") or 0,
        "keyscale": result.get("keyscale") or "",
        "timesignature": result.get("timesignature") or "",
        "vocal_language": result.get("vocal_language") or "",
        "duration": result.get("duration") or 0,
    }


@app.post("/api/shutdown")
async def shutdown(x_lang: str = Header()):   # Pflicht-Header: fremde Webseiten können ihn nicht mitschicken
    if sys.platform == "win32":
        name = "scripts/fork-control.ps1"
    elif sys.platform == "darwin":
        name = "Music Generator OFF.command"
    elif (db.ROOT / "Music Generator OFF.sh").is_file():
        name = "Music Generator OFF.sh"
    else:
        name = "Music Generator OFF.command"
    script = db.ROOT / name
    if not script.is_file():
        raise HTTPException(404, tr(x_lang, "script_missing", name=name))
    # abgekoppelt und leicht verzögert, damit diese Antwort noch ankommt, bevor die App beendet wird
    if sys.platform == "win32":
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
               f'Start-Sleep -Milliseconds 500; & "{script}" -Action Stop']
        # CREATE_NO_WINDOW (eigene unsichtbare Konsole), nicht DETACHED_PROCESS: ohne Konsole startet
        # PowerShell 5.1 zwar, führt den Befehl aber nicht aus (Exit 0, keine Ausgabe).
        flags = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP}
    else:
        cmd = ["/bin/sh", "-c", 'sleep 0.5; exec bash "$0"', str(script)]
        flags = {"start_new_session": True}
    subprocess.Popen(cmd, cwd=db.ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **flags)
    return {"ok": True}


@app.get("/api/health")
async def health():
    s = db.get_settings()
    try:
        return await make_fork_engine(s).health()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e) or e.__class__.__name__}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
