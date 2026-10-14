"""NLEM and Jan Aushadhi extracts: cross-reference signals. Implausible rows are flagged, never silently used."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, Optional

from ..config import Config, load_config
from ..normalize import reasons
from ..normalize.review_queue import enqueue
from ..normalize.text import norm_key, sha256_file
from .batches import existing_batch, read_csv, register_batch

_STRENGTH_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|g)", re.I)


def load_nlem(conn: sqlite3.Connection, cfg: Optional[Config] = None, path: Optional[Path] = None) -> Dict[str, object]:
    cfg = cfg or load_config()
    path = path or cfg.path("data.nlem")
    sha = sha256_file(path)
    prior = existing_batch(conn, "nlem", sha)
    if prior:
        return {"batch_id": prior, "skipped": True}
    rows = read_csv(path)
    edition = sorted({r.get("nlem_edition", "") for r in rows})
    batch_id = register_batch(conn, "nlem", "NLEM extract", edition[-1] if edition else "unknown", path, len(rows))
    missing_cat = 0
    for r in rows:
        cat = (r.get("therapeutic_category") or "").strip()
        if cat in ("", "—", "-"):
            missing_cat += 1
            cat = None
        conn.execute(
            "INSERT INTO nlem_entry(batch_id, medicine, medicine_norm, therapeutic_category, care_levels, nlem_edition) VALUES (?,?,?,?,?,?)",
            (batch_id, r["medicine"].strip(), norm_key(r["medicine"]), cat, r.get("care_levels", "").strip(), r.get("nlem_edition", "").strip()),
        )
    conn.commit()
    return {"batch_id": batch_id, "rows": len(rows), "missing_category": missing_cat}


def load_jan_aushadhi(conn: sqlite3.Connection, cfg: Optional[Config] = None, path: Optional[Path] = None) -> Dict[str, object]:
    cfg = cfg or load_config()
    path = path or cfg.path("data.jan_aushadhi")
    sha = sha256_file(path)
    prior = existing_batch(conn, "jan_aushadhi", sha)
    if prior:
        return {"batch_id": prior, "skipped": True}
    rows = read_csv(path)
    version = sorted({r.get("catalog_version", "") for r in rows})
    batch_id = register_batch(conn, "jan_aushadhi", "Jan Aushadhi (PMBJP) extract", version[-1] if version else "unknown", path, len(rows))
    flagged = 0
    for idx, r in enumerate(rows, start=2):
        flag = None
        m = _STRENGTH_RE.search(r.get("strength", ""))
        val = float(m.group(1)) if m else None
        unit = m.group(2).lower() if m else None
        pack = (r.get("pack") or "").lower()
        generic = r["generic_name"].strip()
        # plausibility windows: a solid-dose "strength" above 1000 mg or a liquid labelled per-bottle mg are suspicious in this extract
        if val is not None and unit == "mg" and val >= 500 and generic.lower() in {
            "losartan", "rosuvastatin", "clopidogrel", "ondansetron", "levocetirizine", "chlorpheniramine", "sertraline",
            "prednisolone", "folic acid", "omeprazole", "domperidone", "glimepiride", "montelukast", "calcium carbonate",
            "iron (ferrous ascorbate)", "vitamin d3", "nimesulide", "serratiopeptidase", "trypsin-chymotrypsin", "thyroxine",
            "aceclofenac", "rabeprazole", "salbutamol", "telmisartan", "amlodipine", "hydrochlorothiazide", "phenylephrine",
            "nitrofurantoin", "clavulanic acid", "sitagliptin", "atenolol", "cefixime", "ciprofloxacin", "ofloxacin", "metformin",
        }:
            flag = "IMPLAUSIBLE_STRENGTH"
        if "syrup" in pack and generic.lower() in {"telmisartan", "amlodipine", "losartan", "sertraline", "montelukast", "calcium carbonate", "prednisolone", "aceclofenac", "cefixime", "iron (ferrous ascorbate)", "clavulanic acid"}:
            flag = (flag + "+" if flag else "") + "IMPLAUSIBLE_PACK_FOR_GENERIC"
        if flag:
            flagged += 1
            enqueue(conn, batch_id, "reference_row", f"{generic} {r.get('strength')} {r.get('pack')}", reasons.IMPLAUSIBLE_VALUE,
                    f"Jan Aushadhi row looks implausible ({flag}); excluded from cross-validation", context={"row": idx})
        conn.execute(
            """INSERT INTO jan_aushadhi_entry(batch_id, generic_name, generic_norm, strength, pack, mrp_inr, catalog_version, plausibility_flag)
               VALUES (?,?,?,?,?,?,?,?)""",
            (batch_id, generic, norm_key(generic), r.get("strength", "").strip(), r.get("pack", "").strip(),
             float(r["mrp_inr"]) if r.get("mrp_inr") else None, r.get("catalog_version", "").strip(), flag),
        )
    conn.commit()
    return {"batch_id": batch_id, "rows": len(rows), "flagged_implausible": flagged}
