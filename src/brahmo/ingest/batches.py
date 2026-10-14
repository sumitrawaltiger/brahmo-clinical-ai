"""load_batch registration shared by all loaders."""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from ..db import utcnow_iso
from ..normalize.text import sha256_file

LOADER_VERSION = "ingest-1.0.0"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def existing_batch(conn: sqlite3.Connection, dataset: str, sha: str) -> Optional[str]:
    row = conn.execute(
        "SELECT batch_id FROM load_batch WHERE dataset=? AND file_sha256=? ORDER BY loaded_at DESC LIMIT 1",
        (dataset, sha),
    ).fetchone()
    return row[0] if row else None


def register_batch(
    conn: sqlite3.Connection,
    dataset: str,
    source_name: str,
    source_version: str,
    path: Path,
    row_count: int,
    notes: str = "",
) -> str:
    sha = sha256_file(path)
    batch_id = f"{dataset}:{source_version}:{sha[:8]}"
    conn.execute(
        """INSERT OR REPLACE INTO load_batch(batch_id, dataset, source_name, source_version, file_path, file_sha256,
                                  row_count, loaded_at, loader_version, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (batch_id, dataset, source_name, source_version, str(path), sha, row_count, utcnow_iso(), LOADER_VERSION, notes),
    )
    return batch_id


def latest_batch(conn: sqlite3.Connection, dataset: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM load_batch WHERE dataset=? ORDER BY loaded_at DESC, batch_id DESC LIMIT 1", (dataset,)
    ).fetchone()


def data_versions(conn: sqlite3.Connection) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for r in conn.execute(
        "SELECT dataset, batch_id, source_name, source_version, file_sha256, loaded_at FROM load_batch ORDER BY loaded_at"
    ):
        out[r["dataset"]] = {
            "batch_id": r["batch_id"],
            "source": r["source_name"],
            "source_version": r["source_version"],
            "file_sha256": r["file_sha256"],
            "loaded_at": r["loaded_at"],
        }
    return out
