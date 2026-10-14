"""Regulatory gazette events: stored verbatim, plus a structured target interpretation with confidence.

Nothing here decides a status. Status derivation lives in brahmo.regulatory.status and is computed per query date.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import Config, load_config
from ..normalize import reasons
from ..normalize.review_queue import enqueue
from ..normalize.text import norm_key, sha256_file
from .batches import existing_batch, read_csv, register_batch

DATASET = "gazette"
VALID_ACTIONS = {"PROHIBITED", "RESTRICTED", "WITHDRAWN", "STAY_GRANTED", "REVOKED", "LIFTED"}
VALID_TARGET_TYPES = {"FDC", "INGREDIENT", "PRODUCT"}

_PAREN_RE = re.compile(r"\(([^)]*)\)")
_FORM_WORDS = {"suspension": "Suspension", "suspensions": "Suspension", "syrup": "Syrup", "tablet": "Tablet", "tablets": "Tablet", "capsule": "Capsule"}


def parse_target(description: str, target_type: str, known_ingredients: Dict[str, str]) -> Dict[str, object]:
    """Interpret a free-text gazette target. Returns dict for regulatory_target + a list of problems."""
    problems: List[str] = []
    quals = [q.strip().lower() for q in _PAREN_RE.findall(description)]
    core = _PAREN_RE.sub("", description)
    form_q: Optional[str] = None
    pop_q: Optional[str] = None
    ratio_q: Optional[str] = None
    fdc_only = False

    # qualifiers in parentheses
    for q in quals:
        if "ratio" in q:
            ratio_q = q
            problems.append(f"ratio qualifier '{q}' cannot be resolved from the extract")
        if "paediatric" in q or "pediatric" in q:
            pop_q = "paediatric"
        for w, f in _FORM_WORDS.items():
            if w in q:
                form_q = f
        # 'all strengths', 'all products', '4-way', 'Schedule H1 enforcement' carry no matching constraint

    # form words in the core text (e.g. "Ofloxacin + Ornidazole Suspension")
    core_words = core.replace("+", " + ").split()
    cleaned = []
    for w in core_words:
        lw = w.lower().strip(",")
        if lw in _FORM_WORDS:
            form_q = _FORM_WORDS[lw]
            continue
        cleaned.append(w)
    core = " ".join(cleaned)

    # "Codeine-based cough FDCs" -> ingredient Codeine, FDC-only
    m = re.match(r"^\s*([A-Za-z][A-Za-z \-]*?)-based\b(.*)$", core)
    if m:
        core = m.group(1)
        fdc_only = True

    terms = [t.strip() for t in core.split("+") if t.strip()]
    ing_set: List[str] = []
    unresolved: List[str] = []
    for t in terms:
        k = norm_key(t)
        if k in known_ingredients:
            ing_set.append(k)
        else:
            unresolved.append(t)
            problems.append(f"ingredient term '{t}' is not in the drug master")
    if target_type == "FDC":
        match_mode = "exact_set"
    elif target_type == "INGREDIENT":
        match_mode = "ingredient_any"
    elif target_type == "PRODUCT":
        match_mode = "exact_set"
    else:
        match_mode = "exact_set"
        problems.append(f"unknown target_type '{target_type}'")
    if fdc_only:
        match_mode = "contains_all_fdc_only"

    confidence = 0.95
    if unresolved:
        confidence = 0.4
    if ratio_q:
        confidence = min(confidence, 0.5)
    return {
        "ingredient_set": sorted(set(ing_set)),
        "match_mode": match_mode,
        "form_qualifier": form_q,
        "population_qualifier": pop_q,
        "ratio_qualifier": ratio_q,
        "parse_confidence": confidence,
        "parse_method": "rule_parser_v1",
        "unresolved_terms": unresolved,
        "problems": problems,
    }


def load(conn: sqlite3.Connection, cfg: Optional[Config] = None, path: Optional[Path] = None) -> Dict[str, object]:
    cfg = cfg or load_config()
    path = path or cfg.path("data.gazette")
    sha = sha256_file(path)
    prior = existing_batch(conn, DATASET, sha)
    if prior:
        return {"batch_id": prior, "skipped": True}
    rows = read_csv(path)
    latest_pub = max((r.get("date_published", "") for r in rows), default="unknown")
    batch_id = register_batch(conn, DATASET, "Gazette of India notifications (assessment extract)", f"extract-through-{latest_pub}", path, len(rows),
                              notes="source_version = latest date_published in the extract; the file carries no explicit version")
    known = {r["norm_name"]: r["canonical_name"] for r in conn.execute("SELECT norm_name, canonical_name FROM ingredient")}
    ids = {r["event_id"].strip() for r in rows}
    stats = {"events": 0, "targets_uncertain": 0, "problems": []}
    for idx, r in enumerate(rows, start=2):
        action = r["action"].strip().upper()
        ttype = r["target_type"].strip().upper()
        sup = (r.get("supersedes_event_id") or "").strip() or None
        problems: List[str] = []
        if action not in VALID_ACTIONS:
            problems.append(f"unknown action '{action}'")
        if ttype not in VALID_TARGET_TYPES:
            problems.append(f"unknown target_type '{ttype}'")
        if sup and sup not in ids:
            problems.append(f"supersedes unknown event '{sup}'")
        if r["effective_date"] < r["date_published"]:
            problems.append("effective_date precedes date_published")
        conn.execute(
            """INSERT INTO regulatory_event(event_id, batch_id, notification_id, date_published, effective_date, action, target_type,
                                            target_description, supersedes_event_id, note, source) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (r["event_id"].strip(), batch_id, r["notification_id"].strip(), r["date_published"].strip(), r["effective_date"].strip(),
             action, ttype, r["target_description"].strip(), sup, (r.get("note") or "").strip(), "Gazette of India (assessment extract)"),
        )
        t = parse_target(r["target_description"], ttype, known)
        problems.extend(t["problems"])
        conn.execute(
            """INSERT INTO regulatory_target(event_id, batch_id, ingredient_set, match_mode, form_qualifier, population_qualifier,
                                             ratio_qualifier, parse_confidence, parse_method, unresolved_terms) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (r["event_id"].strip(), batch_id, json.dumps(t["ingredient_set"]), t["match_mode"], t["form_qualifier"], t["population_qualifier"],
             t["ratio_qualifier"], t["parse_confidence"], t["parse_method"], json.dumps(t["unresolved_terms"])),
        )
        stats["events"] += 1
        if problems:
            stats["targets_uncertain"] += 1
            stats["problems"].append({"event_id": r["event_id"], "problems": problems})
            enqueue(conn, batch_id, "regulatory_target", f"{r['event_id']} {r['notification_id']}: {r['target_description']}",
                    reasons.TARGET_PARSE_UNCERTAIN, "; ".join(problems), context={"row": idx, "event_id": r["event_id"]})
    conn.commit()
    stats["batch_id"] = batch_id
    return stats
