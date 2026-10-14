"""SQLite access and numbered migrations."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from .config import Config, load_config


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(cfg: Optional[Config] = None, path: Optional[Path] = None) -> sqlite3.Connection:
    cfg = cfg or load_config()
    db_path = path or cfg.path("db.path")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def list_migrations(cfg: Optional[Config] = None) -> List[Path]:
    cfg = cfg or load_config()
    mdir = cfg.path("db.migrations_dir")
    return sorted(p for p in mdir.glob("*.sql") if p.name[:3].isdigit())


def migrate(conn: sqlite3.Connection, cfg: Optional[Config] = None) -> List[str]:
    """Apply every migration not yet recorded. Returns the ids applied in this call."""
    cfg = cfg or load_config()
    applied: List[str] = []
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS schema_migrations (migration_id TEXT PRIMARY KEY, applied_at TEXT NOT NULL);"
    )
    done = {r[0] for r in conn.execute("SELECT migration_id FROM schema_migrations")}
    for path in list_migrations(cfg):
        mid = path.stem
        if mid in done:
            continue
        sql = path.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations(migration_id, applied_at) VALUES (?, ?)", (mid, utcnow_iso())
        )
        conn.commit()
        applied.append(mid)
    return applied


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return row is not None


def rows(conn: sqlite3.Connection, sql: str, params: Iterable = ()) -> List[sqlite3.Row]:
    return list(conn.execute(sql, tuple(params)))
