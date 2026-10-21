"""SQLite-Speicher für Songs (Metadaten) und Einstellungen."""
import json
import os
import sqlite3
import threading
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("MUSIC_GENERATOR_DATA", str(ROOT / "data"))).resolve()
if not DATA.is_relative_to(ROOT.resolve()):
    raise ValueError("Daten müssen innerhalb des Music Generator Fork liegen.")
SONGS_DIR = DATA / "songs"
MODELS_DIR = ROOT / "engine" / "acestep.cpp" / "models"
DB_PATH = DATA / "music.db"
MODELS_DIR = ROOT / 'engine/acestep.cpp/models'

def _engine_conf() -> dict:
    """Vom Installer geschrieben (data/engine.conf): MODE=single|split, LM_FILE=…"""
    conf = {}
    try:
        for line in (DATA / "engine.conf").read_text(encoding="utf-8-sig").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    except OSError:
        pass
    return conf


_conf = _engine_conf()
if _conf.get("LM_DEVICE") == "cpu":
    _conf["MODE"] = "split"   # Sprachmodell erzwungen auf der CPU (Einstellung oder Installer)


def lm_device() -> str:
    """„cpu“ = Sprachmodell erzwungen auf der CPU, sonst „auto“ (Wert aus data/engine.conf, immer frisch gelesen)."""
    return "cpu" if _engine_conf().get("LM_DEVICE") == "cpu" else "auto"


def set_lm_device(value: str) -> None:
    """Change only LM_DEVICE, retaining other configuration bytes and using an atomic replacement."""
    if value not in ('auto', 'cpu'):
        raise ValueError('Expected auto or cpu.')
    path = DATA / "engine.conf"
    try:
        original = path.read_bytes()
    except FileNotFoundError:
        original = b''
    bom = b'\xef\xbb\xbf' if original.startswith(b'\xef\xbb\xbf') else b''
    raw = original[len(bom):]
    newline = b'\r\n' if b'\r\n' in raw else b'\n'
    lines = [line for line in raw.splitlines(keepends=True) if not line.lstrip().startswith(b'LM_DEVICE=')]
    updated = b''.join(lines)
    if value == "cpu":
        if updated and not updated.endswith((b'\r', b'\n')):
            updated += newline
        updated += b'LM_DEVICE=cpu' + newline
    updated = bom + updated
    if updated == original:
        return
    DATA.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=DATA, prefix='.engine-conf-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(updated)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

DEFAULT_SETTINGS = {
    "server_url": "http://127.0.0.1:8087",   # Eigener Fork-Server, startet pro Auftrag
    # Sprachmodell: eigener CPU-Server (Modus split) oder leer = gleicher Server wie Synthese (single)
    "lm_url": "",
    "lm_model": _conf.get("LM_FILE", ""),     # leer = erstes Sprachmodell im Modellordner
    "poll_interval": 1.5,
    "timeout_minutes": 30,
    "dit": "standard",
    "songs_dir": "",                   # leer = data/songs im Programmordner, sonst absoluter Pfad
}

_lock = threading.Lock()


def songs_dir() -> Path:
    """Ordner für die fertigen Songs: Einstellung oder data/songs."""
    custom = ""
    try:
        r = one("SELECT value FROM settings WHERE key='songs_dir'")
        custom = json.loads(r["value"]) if r else ""
    except Exception:  # noqa: BLE001 – vor der ersten Initialisierung oder bei kaputtem Wert
        custom = ""
    d = (Path(custom).expanduser() if custom else SONGS_DIR).resolve()
    if not d.is_relative_to(ROOT.resolve()):
        raise ValueError("Song-Ordner muss innerhalb des Music Generator Fork liegen.")
    d.mkdir(parents=True, exist_ok=True)
    return d


def connect() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    SONGS_DIR.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


_con = connect()


def init():
    with _lock:
        _con.executescript(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id          TEXT PRIMARY KEY,
                group_id    TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                finished_at TEXT,
                status      TEXT NOT NULL,          -- queued | running | done | error | cancelled
                message     TEXT,
                title       TEXT,
                caption     TEXT NOT NULL,
                lyrics      TEXT,
                seed        INTEGER NOT NULL,
                params      TEXT NOT NULL,          -- JSON: vollständige Anfrage
                result_meta TEXT,                   -- JSON: vom Modell ergänzte Werte (bpm, key, lyrics …)
                engine      TEXT,
                file        TEXT,
                favorite    INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_songs_status ON songs(status);
            CREATE INDEX IF NOT EXISTS idx_songs_group ON songs(group_id);
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS folders (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS voice_timings (id TEXT PRIMARY KEY, result_meta TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS voice_training (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL,
                status TEXT NOT NULL, message TEXT, params TEXT NOT NULL, result_meta TEXT,
                finished_at TEXT
            );
            """
        )
        # Ordner der Bibliothek (nur in der App; die Dateien bleiben, wo sie sind). NULL = unsortiert
        if "folder_id" not in [r["name"] for r in _con.execute("PRAGMA table_info(songs)")]:
            _con.execute("ALTER TABLE songs ADD COLUMN folder_id TEXT")
        training_columns={r['name'] for r in _con.execute('PRAGMA table_info(voice_training)')}
        for column in ('removed_at','removed_status'):
            if column not in training_columns:
                _con.execute(f'ALTER TABLE voice_training ADD COLUMN {column} TEXT')
        # Nach einem Absturz hängengebliebene Jobs wieder einreihen
        _con.execute("UPDATE songs SET status='queued', message=NULL WHERE status='running'")
        _con.execute("UPDATE voice_training SET status='error', message='Training durch Programmende unterbrochen; vorhandene Daten bleiben erhalten.' WHERE status='running'")
        _con.execute("INSERT OR IGNORE INTO voice_timings SELECT id,result_meta FROM songs WHERE engine='rvc' AND status='done' AND result_meta IS NOT NULL")
        _con.commit()


def execute(sql: str, args: tuple = ()) -> None:
    with _lock:
        _con.execute(sql, args)
        _con.commit()


def query(sql: str, args: tuple = ()) -> list[dict]:
    with _lock:
        return [dict(r) for r in _con.execute(sql, args).fetchall()]


def one(sql: str, args: tuple = ()) -> dict | None:
    rows = query(sql, args)
    return rows[0] if rows else None


def get_settings() -> dict:
    s = dict(DEFAULT_SETTINGS)
    for r in query("SELECT key, value FROM settings"):
        s[r["key"]] = json.loads(r["value"])
    # Früher gespeicherte Standardadresse des CPU-Servers: im Ein-Server-Modus läuft dort nichts
    if _conf.get("MODE") == "single" and s["lm_url"].rstrip("/") == "http://127.0.0.1:8086":
        s["lm_url"] = ""
    return s


def save_settings(values: dict) -> dict:
    for k, v in values.items():
        if k not in DEFAULT_SETTINGS:
            continue
        if v == DEFAULT_SETTINGS[k]:
            # Vorgaben nicht festschreiben, sonst überstimmen sie später den Installer (engine.conf)
            execute("DELETE FROM settings WHERE key=?", (k,))
        else:
            execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (k, json.dumps(v)),
            )
    return get_settings()
