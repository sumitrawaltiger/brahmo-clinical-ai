"""Severe-interaction seed loader. Declares, per pair, whether each side maps to a drug-master ingredient,
so the rail can state coverage honestly instead of implying a complete interaction database."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Optional

from ..config import Config, load_config
from ..normalize import reasons
from ..normalize.review_queue import enqueue
from ..normalize.text import norm_key, sha256_file
from .batches import existing_batch, read_csv, register_batch

DATASET = "interactions"


def load(conn: sqlite3.Connection, cfg: Optional[Config] = None, path: Optional[Path] = None) -> Dict[str, object]:
    cfg = cfg or load_config()
    path = path or cfg.path("data.interactions")
    sha = sha256_file(path)
    prior = existing_batch(conn, DATASET, sha)
    if prior:
        return {"batch_id": prior, "skipped": True}
    rows = read_csv(path)
    tags = sorted({r.get("source_tag", "") for r in rows})
    batch_id = register_batch(conn, DATASET, "severe interaction seed (ingredient-level)", tags[-1] if tags else "unknown", path, len(rows))
    known = {r["norm_name"] for r in conn.execute("SELECT norm_name FROM ingredient")}
    unmapped = set()
    for r in rows:
        a, b = r["ingredient_a"].strip(), r["ingredient_b"].strip()
        an, bn = norm_key(a), norm_key(b)
        key = "|".join(sorted([an, bn]))
        a_in, b_in = int(an in known), int(bn in known)
        conn.execute(
            """INSERT INTO interaction_pair(batch_id, ingredient_a, ingredient_b, a_norm, b_norm, pair_key, severity, note, source_tag, a_in_master, b_in_master)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (batch_id, a, b, an, bn, key, r["severity"].strip().upper(), (r.get("note") or "").strip(), r.get("source_tag", "").strip(), a_in, b_in),
        )
        for name, ok in ((a, a_in), (b, b_in)):
            if not ok and name not in unmapped:
                unmapped.add(name)
                enqueue(conn, batch_id, "interaction_term", name, reasons.INTERACTION_TERM_UNMAPPED,
                        "seed term has no drug-master ingredient (class name or ingredient absent from the CDCI subset); pair kept, cannot fire until mapped")
    conn.commit()
    return {"batch_id": batch_id, "pairs": len(rows), "unmapped_terms": sorted(unmapped)}
