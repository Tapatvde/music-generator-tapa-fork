"""Local voice profiles and a cancellable adapter for the shared GPU queue."""
import asyncio
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from . import db
from .engines import EngineError
from .chorus import ALIGNMENT_VERSION, selected_lyrics, validate_auto_lyrics, section_catalog

RVC = db.ROOT / "engine/rvc"
PYTHON = RVC / ".venv/Scripts/python.exe"
FFPROBE = RVC / "ffprobe.exe"
RECIPE = "bs368-v2"


def contained(path: Path) -> Path:
    path = path.resolve()
    if not path.is_relative_to(db.ROOT.resolve()):
        raise ValueError("Alle Dateien müssen im Music Generator Fork bleiben.")
    return path


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def note_number(value: str) -> int:
    m = re.fullmatch(r"([A-Ga-g])([#b]?)(-?\d)", value.strip())
    if not m:
        raise ValueError("Ton als G2, C#4 oder Bb3 angeben; C4 ist das mittlere C.")
    letter, accidental, octave = m.groups()
    return 12 * (int(octave) + 1) + dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)[letter.upper()] + {"":0,"#":1,"b":-1}[accidental]


class RangeSettings(BaseModel):
    enabled: bool = False
    min_note: str = "C2"
    max_note: str = "C5"

    @model_validator(mode="after")
    def validate_range(self):
        low, high = note_number(self.min_note), note_number(self.max_note)
        if low < 32 or high > 84 or high - low < 12:
            raise ValueError("Stimmumfang zwischen G#1 und C6 mit mindestens einer Oktave angeben.")
        return self


class ChorusRegion(BaseModel):
    start: float = Field(ge=0, le=36000, allow_inf_nan=False)
    end: float = Field(gt=0, le=36000, allow_inf_nan=False)

    @model_validator(mode="after")
    def ordered(self):
        if self.end - self.start < .5:
            raise ValueError("Ein Refrainbereich muss mindestens eine halbe Sekunde lang sein.")
        return self


class HarmonySettings(BaseModel):
    enabled: bool = False
    interval: Literal[-12, -7, 7, 12] = -12
    gain_db: float = Field(-12, ge=-24, le=0, allow_inf_nan=False)
    regions: list[ChorusRegion] = Field(default_factory=list, max_length=24)
    mode: Literal['manual','lyrics'] = 'manual'

    @model_validator(mode="after")
    def ordered(self):
        self.regions.sort(key=lambda r: r.start)
        if self.enabled and self.mode=='manual' and not self.regions:
            raise ValueError("Bitte die Zeitbereiche der Refrains für die zweite Stimme angeben.")
        if any(a.end > b.start for a, b in zip(self.regions, self.regions[1:])):
            raise ValueError("Refrainbereiche dürfen sich nicht überschneiden.")
        return self


Register = Literal['auto','low','middle','high']


class SectionRegister(BaseModel):
    section: int = Field(ge=0,le=63)
    tag: str = Field(min_length=1,max_length=120)
    level: Register = 'auto'


class SectionPitchSettings(BaseModel):
    enabled: bool = False
    strict: bool = True
    verse: Register = 'middle'
    chorus: Register = 'high'
    overrides: list[SectionRegister] = Field(default_factory=list,max_length=64)

    @model_validator(mode='after')
    def unique(self):
        if len({r.section for r in self.overrides})!=len(self.overrides):
            raise ValueError('Jeder Textabschnitt darf nur eine Tonlage bekommen.')
        return self


from .mix_settings import MixSettings


class VoiceRequest(RangeSettings):
    profile_id: str
    quality: Literal["standard", "best"] = "standard"
    preview: bool = False
    preview_start: float = Field(0, ge=0, le=36000, allow_inf_nan=False)
    preview_seconds: float = Field(20, ge=5, le=30, allow_inf_nan=False)
    base_song_id: str | None = None
    lead_octave: Literal[0, 12] = 0
    stable_register: bool = True
    harmony: HarmonySettings = Field(default_factory=HarmonySettings)
    section_pitch: SectionPitchSettings = Field(default_factory=SectionPitchSettings)
    instrumental_song_id: str | None = None
    mix_levels: MixSettings = Field(default_factory=MixSettings)

    @model_validator(mode='after')
    def section_range(self):
        if self.section_pitch.enabled and not self.enabled:
            raise ValueError('Für tief/mittel/hoch bitte den Stimmumfang aktivieren.')
        return self


def validate_sections(req: VoiceRequest, duration: float):
    if req.harmony.enabled and req.harmony.mode=='manual' and any(r.end > duration + .01 for r in req.harmony.regions):
        raise ValueError("Ein Refrainbereich reicht über das Songende hinaus.")


def auto_chorus(req):
    return req.harmony.enabled and req.harmony.mode=='lyrics'


def needs_alignment(req):
    return auto_chorus(req) or req.section_pitch.enabled


def validate_lyrics(req, lyrics):
    if needs_alignment(req):
        validate_auto_lyrics(lyrics,require_chorus=auto_chorus(req))
        catalog=section_catalog(lyrics)
        if req.section_pitch.enabled:
            if not any(s['tag']!='untagged' for s in catalog):
                raise ValueError('Für Abschnittstonlagen fehlen markierte Lyrics wie [verse] und [chorus].')
            for override in req.section_pitch.overrides:
                if override.section>=len(catalog) or catalog[override.section]['tag']!=override.tag:
                    raise ValueError('Der Textabschnitt hat sich geändert. Bitte die Tonlagen neu zuordnen.')
            overrides={r.section:r.level for r in req.section_pitch.overrides}
            if not any(overrides.get(s['section'],getattr(req.section_pitch,s['kind'],'auto'))!='auto' for s in catalog):
                raise ValueError('Bitte mindestens einem Textabschnitt tief, mittel oder hoch zuweisen.')
        if not (db.ROOT/'engine/chorus-aligner/model.pt').is_file():
            raise ValueError('Das lokale Modell für den Refrainabgleich fehlt.')


def chorus_cache(source_hash, lyrics, quality):
    key=hashlib.sha256(lyrics.encode('utf-8')).hexdigest()
    return db.DATA/'chorus-cache'/source_hash/f'{ALIGNMENT_VERSION}-{RECIPE}-{quality}-{key}.json'


def profile_list() -> list[dict]:
    result = []
    for model in sorted((RVC / "assets/weights").glob("*.pth")):
        indexes = sorted((RVC / "assets/indices").glob(f"{model.stem}*.index"))
        if not indexes:
            continue
        override = db.DATA / "voice-profiles" / f"{model.stem}.json"
        saved = json.loads(override.read_text(encoding="utf-8")) if override.is_file() else {}
        sidecar = model.with_suffix(".voice.json")
        original = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.is_file() else {}
        # Application defaults preserve natural low attacks; the RVC sidecar stays untouched.
        result.append({"id":model.stem, "name":saved.get("name", model.stem),
                       "enabled":saved.get("enabled", original.get("enabled", False)),
                       "min_note":saved.get("min_note", original.get("min_note", "C2")),
                       "max_note":saved.get("max_note", original.get("max_note", "C5")),
                       "model":str(contained(model)), "index":str(contained(indexes[0]))})
    for row in db.query("SELECT id,name,result_meta FROM voice_training WHERE status='done'"):
        meta=json.loads(row['result_meta'] or '{}')
        if not meta.get('model') or not meta.get('index'):continue
        model,index=contained(Path(meta['model'])),contained(Path(meta['index']))
        if not model.is_file() or not index.is_file():continue
        override=db.DATA/'voice-profiles'/(row['id']+'.json')
        saved=json.loads(override.read_text(encoding='utf-8')) if override.is_file() else meta['range']
        result.append({'id':row['id'],'name':row['name'],'enabled':saved.get('enabled',True),
                       'min_note':saved['min_note'],'max_note':saved['max_note'],
                       'model':str(model),'index':str(index)})
    return result


def get_profile(profile_id: str) -> dict:
    for profile in profile_list():
        if profile["id"] == profile_id:
            return profile
    raise ValueError("Stimmprofil nicht gefunden. Ein trainiertes RVC-Modell mit Index ist erforderlich.")


def conversion_source(sid, backing_id=None):
    """For a saved backing, follow its exact vocal version, including edits and octave changes."""
    selected=db.one('SELECT * FROM songs WHERE id=?',(sid,))
    if not selected:raise ValueError('Song fehlt.')
    params=json.loads(selected['params'])
    backing_id=backing_id or (sid if params.get('job_type')=='instrumental' else params.get('backing_song_id'))
    if not backing_id:return original_song(sid)
    backing=db.one('SELECT * FROM songs WHERE id=?',(backing_id,))
    if not backing or backing['status']!='done':raise ValueError('Instrumentalgrundlage fehlt oder ist nicht fertig.')
    params=json.loads(backing['params'])
    if params.get('job_type')!='instrumental':raise ValueError('Ungültige Instrumentalgrundlage.')
    source=db.one('SELECT * FROM songs WHERE id=?',(params['source_song_id'],))
    if not source or source['status']!='done' or not source['file'] or not contained(db.songs_dir()/source['file']).is_file():
        raise ValueError('Die Gesangsvorlage der Instrumentalversion fehlt.')
    return source


def save_profile(profile_id: str, settings: RangeSettings):
    profile = get_profile(profile_id)
    path = db.DATA / "voice-profiles" / f"{profile_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"name":profile["name"], **settings.model_dump()}, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return get_profile(profile_id)


def original_song(sid: str) -> dict:
    seen = set()
    while sid not in seen:
        seen.add(sid)
        song = db.one("SELECT * FROM songs WHERE id=?", (sid,))
        if not song:
            raise ValueError("Der ursprüngliche Song ist nicht mehr in der Bibliothek.")
        params = json.loads(song["params"])
        if params.get('job_type')=='instrumental':
            sid=params['vocal_source_song_id'];continue
        if params.get("job_type") != "voice":
            if song["status"] != "done" or not song["file"]:
                raise ValueError("Der ursprüngliche Song ist noch nicht fertig.")
            if not contained(db.songs_dir() / song["file"]).is_file():
                raise ValueError("Die ursprüngliche Audiodatei fehlt.")
            return song
        sid = params["source_song_id"]
    raise ValueError("Ungültige Versionsverknüpfung.")


def probe(path: Path) -> dict:
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries", "format=duration:stream=sample_rate,channels", "-of", "json", str(contained(path))],
                       capture_output=True, text=True, timeout=30, creationflags=0x08000000 if os.name == "nt" else 0)
    if r.returncode:
        raise ValueError("Audiodatei konnte nicht gelesen werden.")
    info = json.loads(r.stdout)
    seconds = float(info["format"]["duration"])
    if not math.isfinite(seconds) or seconds <= 0 or seconds > 36000:
        raise ValueError("Ungültige Audiodauer (maximal 10 Stunden).")
    return {"seconds":seconds, "streams":info.get("streams", [])}


def cache_path(source_hash: str, req: VoiceRequest) -> Path:
    scope = f"preview-{req.preview_start:.3f}-{req.preview_seconds:.3f}" if req.preview else "full"
    return db.DATA / "voice-cache" / source_hash / f"{RECIPE}-{req.quality}-{scope}"


def estimate(path: Path, req: VoiceRequest, lyrics='') -> dict:
    info = probe(path)
    validate_sections(req, info["seconds"])
    validate_lyrics(req, lyrics)
    seconds = min(req.preview_seconds, info["seconds"] - req.preview_start) if req.preview else info["seconds"]
    if seconds < 1:
        raise ValueError("Die Vorschau beginnt hinter dem Songende.")
    sha = digest(path)
    cached = (cache_path(sha, req) / "complete.json").is_file()
    result = estimate_duration(seconds, req.quality, cached, req.harmony.enabled)
    if needs_alignment(req):
        alignment_cached=chorus_cache(sha,lyrics,req.quality).is_file()
        extra=0 if alignment_cached else 20+info['seconds']*.15
        if req.preview and (not alignment_cached or req.section_pitch.enabled):
            full=cache_path(sha,req.model_copy(update={'preview':False}))
            if not (full/'complete.json').is_file():
                result['stages']['separation']+=estimate_duration(info['seconds'],req.quality)['stages']['separation']
        if req.section_pitch.enabled and not (cache_path(sha,req.model_copy(update={'preview':False}))/'section-f0-rmvpe-v1.npy').is_file():
            result['stages']['conversion']+=6+info['seconds']*.05
        stages=result['stages'];result['stages']={'separation':stages['separation'],'alignment':round(extra,1),'conversion':stages['conversion'],'mix':stages['mix']}
        total=sum(result['stages'].values());result.update(seconds_low=round(total*.65),seconds_high=round(total*1.75),chorus_cached=alignment_cached)
    result.update(source_hash=sha, source_seconds=seconds)
    if req.section_pitch.enabled:
        result['section_plan'] = cached_section_plan(sha, lyrics, req)
    return result


def cached_section_plan(source_hash, lyrics, req):
    alignment = chorus_cache(source_hash, lyrics, req.quality)
    cache = cache_path(source_hash, req.model_copy(update={'preview': False}))
    required = [alignment, cache/'complete.json', cache/'vocals.wav',
                cache/'section-f0-rmvpe-v1.npy', cache/'section-f0-rmvpe-v1.json']
    if not all(path.is_file() for path in required):
        return {'available': False, 'reason': 'not_analyzed'}
    spec = {'alignment':str(alignment), 'cache':str(cache), 'lyrics':lyrics, 'request':req.model_dump()}
    try:
        result = subprocess.run([str(PYTHON), '-I', str(db.ROOT/'scripts/section-pitch-plan.py')],
                                input=json.dumps(spec), capture_output=True, text=True, timeout=20,
                                creationflags=0x08000000 if os.name=='nt' else 0)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return {'available': False, 'reason': 'analysis_unavailable'}


def estimate_duration(seconds: float, quality: str, cached=False, harmony=False) -> dict:
    # Bootstrap from local trials; completed jobs then calibrate each stage.
    defaults = {"separation": (2., .25 if quality == "standard" else 1.5), "conversion":(6., .07 if quality == "standard" else .12), "mix":(.3, .005)}
    preserve_timings()
    records = db.query("SELECT result_meta FROM voice_timings ORDER BY rowid")
    observations = []
    for row in records:
        meta = json.loads(row["result_meta"])
        compatible = meta.get("recipe", RECIPE) == RECIPE or (quality == "standard" and meta.get("recipe") == "bs368-v1")
        if not meta.get("section_patch") and not meta.get("harmony", {}).get("enabled") and meta.get("quality") == quality and compatible and meta.get("source_seconds", 0) > 0:
            observations.append(meta)
    stages = {}
    measured = 0
    for stage, (startup, factor) in defaults.items():
        if stage == "separation" and cached:
            stages[stage] = 0
            continue
        samples = [(m["stage_seconds"][stage], m["source_seconds"]) for m in observations if stage in m.get("stage_seconds", {}) and m["stage_seconds"][stage] > 0]
        if samples:
            buckets = {}
            for elapsed, duration in samples[-20:]:
                buckets.setdefault(round(duration, 1), []).append(elapsed)
            points = sorted((duration, statistics.median(values)) for duration, values in buckets.items())
            before = [p for p in points if p[0] <= seconds]
            after = [p for p in points if p[0] >= seconds]
            if before and after:
                left, right = before[-1], after[0]
                value = left[1] if left[0] == right[0] else left[1] + (right[1]-left[1])*(seconds-left[0])/(right[0]-left[0])
            else:
                duration, elapsed = points[0] if not before else points[-1]
                startup = min(startup, elapsed*.7)
                value = startup + max(.001, elapsed-startup)*seconds/duration
            stages[stage] = round(value, 1)
            measured += len(samples)
        else:
            stages[stage] = round(startup + seconds * factor, 1)
    if harmony:
        stages["conversion"] = round(stages["conversion"] * 2, 1)
    total = sum(stages.values())
    return {"seconds_low":round(total * .65), "seconds_high":round(total * 1.75), "stages":stages,
            "basis":"measured" if measured else "initial", "cached_stems":cached,
            "note":"Schätzung ohne Wartezeit; andere GPU-Aufgaben und Modellladezeiten können sie verändern."}


def preserve_timings():
    db.execute("INSERT OR IGNORE INTO voice_timings SELECT id,result_meta FROM songs WHERE engine='rvc' AND status='done' AND result_meta IS NOT NULL")


def recover_timings():
    """Recover completed measurements from retained job logs, including deleted songs."""
    preserve_timings()
    for result in (db.DATA/"voice-jobs").glob("*/result.json"):
        try:
            meta=json.loads(result.read_text(encoding="utf-8"))
            if meta.get("stage_seconds") and meta.get("source_seconds",0)>0 and not meta.get("section_patch"):
                db.execute("INSERT OR IGNORE INTO voice_timings(id,result_meta) VALUES(?,?)",(result.parent.name,json.dumps(meta)))
        except (OSError,ValueError,TypeError):
            continue


def record_timing(sid, meta):
    if meta.get("stage_seconds") and not meta.get("section_patch"):
        db.execute("INSERT INTO voice_timings(id,result_meta) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET result_meta=excluded.result_meta", (sid,json.dumps(meta)))


def section_pair(base_id, preview_id):
    base = db.one("SELECT * FROM songs WHERE id=?", (base_id,))
    preview = db.one("SELECT * FROM songs WHERE id=?", (preview_id,))
    if not base or not preview or base_id == preview_id:
        raise ValueError("Vollfassung oder Abschnittsvorschau fehlt.")
    for row in (base, preview):
        if row["status"] != "done" or row["engine"] != "rvc" or not row["file"]:
            raise ValueError("Bitte eine fertige Stimmversion und eine fertige Abschnittsvorschau verwenden.")
        if not contained(db.songs_dir() / row["file"]).is_file():
            raise ValueError("Eine Audiodatei fehlt.")
    bm, pm = [json.loads(row["result_meta"] or "{}") for row in (base, preview)]
    bp, pp = [json.loads(row["params"]) for row in (base, preview)]
    if bm.get("preview") or not pm.get("preview") or pp.get("voice", {}).get("base_song_id") != base_id:
        raise ValueError("Diese Vorschau wurde nicht für die gewählte Vollfassung erstellt.")
    if original_song(base_id)["id"] != original_song(preview_id)["id"] or not bm.get("source_hash") or bm["source_hash"] != pm.get("source_hash"):
        raise ValueError("Vorschau und Vollfassung gehören nicht zum selben Original.")
    start, duration = pm.get("preview_start", -1), pm.get("duration", 0)
    if start < 0 or duration < 1 or duration > 30.1 or start + duration > bm.get("duration", 0) + .01:
        raise ValueError("Der Abschnitt liegt außerhalb der Vollfassung.")
    if not all((db.DATA/"voice-jobs"/preview_id/name).is_file() for name in ("patch-mix.wav","patch-vocals.wav")) or not (db.DATA/"voice-jobs"/base_id/"vocals.wav").is_file():
        raise ValueError("Die benötigten Abschnitts- oder Gesangsspuren fehlen.")
    return base, preview


def runtime_environment() -> dict:
    cache = db.ROOT / "engine/rvc-runtime/cache"
    tmp = db.DATA / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONPATH":str(RVC), "PYTHONNOUSERSITE":"1", "PYTHONUTF8":"1",
           "HF_HOME":str(cache / "huggingface"), "TORCH_HOME":str(cache / "torch"), "XDG_CACHE_HOME":str(cache),
           "MPLCONFIGDIR":str(cache / "matplotlib"), "NUMBA_CACHE_DIR":str(cache / "numba"),
           "HF_HUB_OFFLINE":"1", "TRANSFORMERS_OFFLINE":"1", "HF_HUB_DISABLE_TELEMETRY":"1",
           "GRADIO_ANALYTICS_ENABLED":"False", "DO_NOT_TRACK":"1", "TEMP":str(tmp), "TMP":str(tmp),
           "OMP_NUM_THREADS":"4", "OPENBLAS_NUM_THREADS":"4", "PATH":str(RVC) + os.pathsep + os.environ.get("PATH", "")}
    return env


class VoiceEngine:
    name = "rvc"

    def __init__(self, sid: str):
        self.sid = sid
        self.process = None

    async def cancel(self):
        if self.process and self.process.returncode is None:
            if os.name == "nt":
                killer = await asyncio.create_subprocess_exec("taskkill", "/PID", str(self.process.pid), "/T", "/F", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL, creationflags=0x08000000)
                await killer.wait()
            else:
                self.process.kill()
            await self.process.wait()

    async def generate(self, params, progress):
        request = VoiceRequest(**params["voice"])
        root = conversion_source(params["source_song_id"], request.instrumental_song_id)
        profile = get_profile(request.profile_id)
        run = db.DATA / "voice-jobs" / self.sid
        run.mkdir(parents=True, exist_ok=True)
        spec = {"root":str(db.ROOT), "run":str(run), "source":str(contained(db.songs_dir() / root["file"])),
                "request":request.model_dump(), "profile":profile, "recipe":RECIPE,
                "lyrics":selected_lyrics(root)}
        if request.instrumental_song_id:
            backing=db.one('SELECT * FROM songs WHERE id=?',(request.instrumental_song_id,))
            if not backing or backing['status']!='done' or json.loads(backing['params']).get('job_type')!='instrumental':
                raise EngineError('Instrumentalgrundlage fehlt oder ist nicht fertig.')
            spec['backing_override']=str(contained(db.songs_dir()/backing['file']))
            spec['backing_song_id']=backing['id']
        script = "voice-job.py"
        if params.get("operation") == "section_patch":
            base, preview = section_pair(params["base_song_id"], params["preview_song_id"])
            spec.update(base=str(contained(db.songs_dir()/base["file"])),
                        base_run=str(db.DATA/"voice-jobs"/base["id"]),
                        preview_run=str(db.DATA/"voice-jobs"/preview["id"]),
                        base_meta=json.loads(base["result_meta"]), preview_meta=json.loads(preview["result_meta"]),
                        base_song_id=base["id"], preview_song_id=preview["id"])
            script = "voice-apply.py"
        (run / "request.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        await progress("Stimmumwandlung wird vorbereitet …")
        prediction = await asyncio.to_thread(estimate, Path(spec["source"]), request, spec['lyrics'])
        self.process = await asyncio.create_subprocess_exec(str(PYTHON), "-u", str(db.ROOT / "scripts" / script), str(run / "request.json"),
                       cwd=RVC, env=runtime_environment(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
                       **({"creationflags":0x08000000} if os.name == "nt" else {}))
        stage = "Vorbereitung"
        started = time.monotonic()
        phase = None
        phase_started = started
        phases = list(prediction['stages'])
        try:
            with (run / "worker.log").open("w", encoding="utf-8") as log:
                while True:
                    try:
                        line = await asyncio.wait_for(self.process.stdout.readline(), timeout=2)
                    except asyncio.TimeoutError:
                        remaining = sum(prediction["stages"][p] for p in phases[phases.index(phase)+1:]) if phase else sum(prediction["stages"].values())
                        if phase:
                            remaining += max(3., prediction["stages"][phase]-(time.monotonic()-phase_started))
                        await progress(f"{stage} · {int(time.monotonic()-started)} s vergangen · noch etwa {int(remaining*.65)}–{int(remaining*1.75)} s")
                        continue
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace").rstrip()
                    log.write(text + "\n"); log.flush()
                    if text.startswith("VOICE_PROGRESS "):
                        stage = json.loads(text[15:])["message"]
                        next_phase = "separation" if "Gesang trennen" in stage else "alignment" if "Refrains" in stage and 'alignment' in phases else "conversion" if "Stimme umwandeln" in stage or "Tonhöhen" in stage or "Tonlagen" in stage or "Vorhandene Gesangstrennung" in stage else "mix" if "Song zusammenfügen" in stage else phase
                        if next_phase != phase:
                            phase, phase_started = next_phase, time.monotonic()
                        await progress(stage)
            code = await self.process.wait()
            if code:
                error_file = run / "error.json"
                message = json.loads(error_file.read_text(encoding="utf-8"))["error"] if error_file.is_file() else f"Stimmumwandlung beendet (Code {code}). Details im Auftragsprotokoll."
                raise EngineError(message)
            meta = json.loads((run / "result.json").read_text(encoding="utf-8"))
            meta = {**json.loads(root["result_meta"] or "{}"), **meta}
            return (run / "mix.wav").read_bytes(), "wav", meta
        except asyncio.CancelledError:
            await self.cancel()
            raise


class InstrumentalEngine(VoiceEngine):
    name='instrumental'

    async def generate(self,params,progress):
        source=db.one('SELECT * FROM songs WHERE id=?',(params['source_song_id'],))
        if not source or source['status']!='done':raise EngineError('Ausgangsversion fehlt.')
        run=db.DATA/'voice-jobs'/self.sid;run.mkdir(parents=True,exist_ok=True)
        spec={'root':str(db.ROOT),'run':str(run),'source':str(contained(db.songs_dir()/source['file'])),
              'request':{'quality':params['quality'],'preview':False},'recipe':RECIPE}
        request=run/'request.json';request.write_text(json.dumps(spec),encoding='utf-8')
        self.process=await asyncio.create_subprocess_exec(str(PYTHON),'-u',str(db.ROOT/'scripts/instrumental-job.py'),str(request),
            cwd=RVC,env=runtime_environment(),stdout=asyncio.subprocess.PIPE,stderr=subprocess.STDOUT,
            **({'creationflags':0x08000000} if os.name=='nt' else {}))
        stage='Instrumentalversion vorbereiten';started=time.monotonic()
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
            code=await self.process.wait()
            if code:
                error=run/'error.json'
                raise EngineError(json.loads(error.read_text(encoding='utf-8'))['error'] if error.is_file() else 'Gesangstrennung fehlgeschlagen.')
            meta=json.loads((run/'result.json').read_text(encoding='utf-8'))
            meta['vocal_source_song_id']=params['vocal_source_song_id']
            return (run/'mix.wav').read_bytes(),'wav',meta
        except asyncio.CancelledError:
            await self.cancel();raise
