"""CDCI subset loader: products, ingredients, FDC decomposition rows.

Decomposition method: the extract carries structured ingredient_N / strength_N_mg columns AND a free-text
strength_text. We treat the structured columns as primary (method=structured_columns, confidence 0.98) and
cross-check them against strength_text; a disagreement lowers confidence and lands the row in the review queue.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import Config, load_config
from ..normalize import reasons
from ..normalize.review_queue import enqueue
from ..normalize.text import norm_key
from .batches import existing_batch, read_csv, register_batch
from ..normalize.text import sha256_file

DATASET = "cdci"
_PART_RE = re.compile(r"^(?P<name>.+?)\s+(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|g|ml|iu)\s*$", re.I)


def parse_strength_text(text: str) -> List[Tuple[str, Optional[float], Optional[str]]]:
    parts = []
    for raw in text.split("+"):
        raw = raw.strip()
        m = _PART_RE.match(raw)
        if m:
            parts.append((m.group("name").strip(), float(m.group("val")), m.group("unit").lower()))
        else:
            parts.append((raw, None, None))
    return parts


def _get_or_create_ingredient(conn: sqlite3.Connection, name: str, batch_id: str, cache: Dict[str, int]) -> int:
    key = norm_key(name)
    if key in cache:
        return cache[key]
    row = conn.execute("SELECT ingredient_id FROM ingredient WHERE norm_name=?", (key,)).fetchone()
    if row:
        cache[key] = row[0]
        return row[0]
    cur = conn.execute(
        "INSERT INTO ingredient(canonical_name, norm_name, first_seen_batch) VALUES (?,?,?)", (name.strip(), key, batch_id)
    )
    cache[key] = int(cur.lastrowid)
    return cache[key]


def load(conn: sqlite3.Connection, cfg: Optional[Config] = None, path: Optional[Path] = None) -> Dict[str, object]:
    cfg = cfg or load_config()
    path = path or cfg.path("data.cdci")
    sha = sha256_file(path)
    prior = existing_batch(conn, DATASET, sha)
    if prior:
        return {"batch_id": prior, "skipped": True}

    rows = read_csv(path)
    versions = sorted({r.get("source_version", "") for r in rows})
    sources = sorted({r.get("source", "") for r in rows})
    source_version = versions[-1] if versions else "unknown"
    batch_id = register_batch(conn, DATASET, sources[0] if sources else "CDCI", source_version, path, len(rows),
                              notes=f"declared sources={sources} versions={versions}")

    dc = cfg.get("ingest.decomposition_confidence", {})
    c_ok, c_bad, c_impl = float(dc.get("structured_columns", 0.98)), float(dc.get("source_row_inconsistent", 0.6)), float(dc.get("implausible_strength", 0.7))
    max_mg = float(cfg.get("ingest.strength_plausible_max_mg", 5000))
    cache: Dict[str, int] = {}
    stats = {"products": 0, "fdc": 0, "ingredient_rows": 0, "review_items": 0, "duplicate_product_ids": 0}
    seen_ids = set()
    for idx, r in enumerate(rows, start=2):
        pid = r["product_id"].strip()
        if pid in seen_ids:
            stats["duplicate_product_ids"] += 1
            enqueue(conn, batch_id, "product_row", pid, reasons.DUPLICATE_SOURCE_ROW, "product_id repeated in extract",
                    context={"row": idx})
            stats["review_items"] += 1
            continue
        seen_ids.add(pid)
        structured = []
        for i in (1, 2, 3):
            name = (r.get(f"ingredient_{i}") or "").strip()
            sval = (r.get(f"strength_{i}_mg") or "").strip()
            if name:
                try:
                    val: Optional[float] = float(sval) if sval else None
                except ValueError:
                    val = None
                structured.append((name, val, "mg" if val is not None else None))
        parsed = parse_strength_text(r.get("strength_text", ""))

        confidence, method, problem = c_ok, "structured_columns", ""
        if not structured:
            problem = "no structured ingredient columns"
            confidence, method = 0.0, "none"
        elif len(parsed) != len(structured):
            problem = f"strength_text has {len(parsed)} parts, structured columns have {len(structured)}"
            confidence = c_bad
        else:
            for (pn, pv, pu), (sn, sv, su) in zip(parsed, structured):
                if norm_key(pn) != norm_key(sn) or (pv is not None and sv is not None and abs(pv - sv) > 1e-9) or (pu and su and pu != su):
                    problem = f"strength_text part '{pn} {pv}{pu}' disagrees with structured '{sn} {sv}{su}'"
                    confidence = c_bad
                    break
        for name, val, unit in structured:
            if val is not None and (val <= 0 or val > max_mg):
                problem = problem or f"implausible strength {val} {unit} for {name}"
                confidence = min(confidence, c_impl)

        brand = r["brand_name"].strip()
        conn.execute(
            """INSERT INTO product(product_id, batch_id, brand_name, brand_norm, manufacturer, dose_form, strength_text,
                                   source, source_version, effective_from, is_fdc, ingredient_count)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (pid, batch_id, brand, norm_key(brand), r.get("manufacturer", "").strip(), r.get("dose_form", "").strip(),
             r.get("strength_text", "").strip(), r.get("source", "").strip(), r.get("source_version", "").strip(),
             r.get("effective_from", "").strip(), 1 if len(structured) > 1 else 0, len(structured)),
        )
        stats["products"] += 1
        if len(structured) > 1:
            stats["fdc"] += 1
        for pos, (name, val, unit) in enumerate(structured, start=1):
            iid = _get_or_create_ingredient(conn, name, batch_id, cache)
            conn.execute(
                """INSERT INTO product_ingredient(product_id, batch_id, position, ingredient_id, strength_value, strength_unit,
                                                  confidence, method) VALUES (?,?,?,?,?,?,?,?)""",
                (pid, batch_id, pos, iid, val, unit, confidence, method),
            )
            stats["ingredient_rows"] += 1
        if problem:
            enqueue(conn, batch_id, "product_row", f"{pid} {brand} | {r.get('strength_text','')}",
                    reasons.SOURCE_ROW_INCONSISTENT if "disagree" in problem or "parts" in problem else reasons.IMPLAUSIBLE_VALUE,
                    problem, context={"row": idx, "product_id": pid})
            stats["review_items"] += 1
    conn.commit()
    stats["batch_id"] = batch_id
    return stats
