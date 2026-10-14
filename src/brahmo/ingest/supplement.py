"""Candidate-added ingredient vocabulary (names only, no products). Provenance per row; disable via config."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Optional

from ..config import Config, load_config
from ..normalize.text import norm_key, sha256_file
from .batches import existing_batch, read_csv, register_batch

DATASET = "ingredient_supplement"


def load(conn: sqlite3.Connection, cfg: Optional[Config] = None, path: Optional[Path] = None) -> Dict[str, object]:
    cfg = cfg or load_config()
    if not cfg.get("data.supplements_enabled", True):
        return {"skipped": True, "reason": "data.supplements_enabled=false"}
    path = path or cfg.path("data.ingredient_supplement")
    if not path.exists():
        return {"skipped": True, "reason": f"{path} missing"}
    sha = sha256_file(path)
    prior = existing_batch(conn, DATASET, sha)
    if prior:
        return {"batch_id": prior, "skipped": True}
    rows = read_csv(path)
    batch_id = register_batch(conn, DATASET, "candidate-added ingredient vocabulary", rows[0]["added_on"] if rows else "unknown", path, len(rows),
                              notes="names only; no products; see DESIGN.md D-006")
    added, members = 0, 0
    for r in rows:
        term, kind = r["term"].strip(), r["kind"].strip()
        key = norm_key(term)
        iid = None
        if kind == "ingredient":
            row = conn.execute("SELECT ingredient_id FROM ingredient WHERE norm_name=?", (key,)).fetchone()
            if row:
                iid = row[0]
            else:
                iid = conn.execute("INSERT INTO ingredient(canonical_name, norm_name, first_seen_batch) VALUES (?,?,?)", (term, key, batch_id)).lastrowid
                added += 1
        conn.execute(
            "INSERT INTO ingredient_supplement(batch_id, term, kind, source, source_version, added_on, reason, ingredient_id) VALUES (?,?,?,?,?,?,?,?)",
            (batch_id, term, kind, r["source"], r["source_version"], r["added_on"], r["reason"], iid),
        )
        if kind == "class":
            for m in [x.strip() for x in (r.get("class_members") or "").split(";") if x.strip()]:
                conn.execute(
                    "INSERT INTO ingredient_class_member(batch_id, class_norm, member_name, member_norm, source, requires_signoff) VALUES (?,?,?,?,?,1)",
                    (batch_id, key, m, norm_key(m), r["source"]),
                )
                members += 1
    conn.commit()
    return {"batch_id": batch_id, "ingredients_added": added, "class_members": members}
