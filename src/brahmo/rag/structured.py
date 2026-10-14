"""Structured-fact route: drug identity, composition and regulatory status answer from Module A, never from retrieval."""
from __future__ import annotations

import re
import sqlite3
from datetime import date
from typing import Any, Dict, List, Optional

from ..config import Config
from ..normalize.resolver import RESOLVED, resolve
from ..regulatory.status import status_for_product

_SKIP = {"what", "which", "is", "does", "do", "can", "the", "are", "in", "india", "why", "how", "when", "a", "an", "of", "for", "and", "or", "to", "it", "this", "that", "status"}


def _brand_candidates(question: str) -> List[str]:
    """Word n-grams (3,2,1) that start with a capitalised token: 'Is NimuPar-P banned?' -> ['NimuPar-P banned', 'NimuPar-P', ...].
    Longer n-grams first so 'Telma-H 40' beats 'Telma-H'. Resolution decides; this only proposes."""
    words = [w.strip("?.,;:!()\"'") for w in question.split()]
    words = [w for w in words if w]
    out: List[str] = []
    for n in (3, 2, 1):
        for i in range(len(words) - n + 1):
            gram = words[i:i + n]
            if not gram[0][:1].isupper() or gram[0].lower() in _SKIP:
                continue
            if any(w.lower() in _SKIP for w in gram[1:]):
                continue
            out.append(" ".join(gram))
    return out


def answer_structured(conn: Optional[sqlite3.Connection], question: str, cfg: Config, as_of: Optional[str] = None) -> Dict[str, Any]:
    as_of = as_of or date.today().isoformat()
    if conn is None:
        return {"answer_type": "abstain", "claims": [], "abstention": {"reason": "drug master unavailable", "missing": "database connection"}}
    tried = []
    for cand in _brand_candidates(question):
        res = resolve(conn, cand, None, None, cfg)
        tried.append({"text": cand, "status": res.status, "reason": res.reason_code})
        if res.status != RESOLVED:
            continue
        p = res.product
        st = status_for_product(conn, p, as_of)
        claims = [{
            "text": f"{p['brand_name']} ({p['dose_form']}) = " + " + ".join(f"{s['ingredient']} {s['strength_value']:g} {s['strength_unit']}" for s in p["ingredients"]),
            "citations": [{"source_type": "drug_master", "document": "CDCI subset", "product_id": p["product_id"], "batch_id": p["batch_id"], "method": res.method, "confidence": res.confidence}],
            "label": "DRUG MASTER (structured fact)", "verbatim": True,
        }]
        if st["status"] == "NONE":
            claims.append({"text": f"No in-force PROHIBITED/RESTRICTED/WITHDRAWN event matches this product as of {as_of} in the loaded register (extract through its latest published notification).",
                           "citations": [{"source_type": "regulatory_register", "document": "gazette extract", "events_checked": len(st["superseded_events"]) + len(st["pending_events"]), "as_of": as_of}],
                           "label": "REGULATORY REGISTER (event-sourced)", "verbatim": True})
        else:
            for g in st["governing_events"]:
                claims.append({"text": f"Status {st['status']} as of {as_of}: {g['notification_id']} ({g['action']}), published {g['date_published']}, effective {g['effective_date']} — target: {g['target']}",
                               "citations": [{"source_type": "regulatory_register", "document": g["notification_id"], "event_id": g["event_id"], "effective_date": g["effective_date"], "batch_id": g["data_batch"]}],
                               "label": "REGULATORY REGISTER (event-sourced)", "verbatim": True})
        return {"answer_type": "answer", "claims": claims, "regulatory": st, "resolution": {"status": res.status, "method": res.method, "confidence": res.confidence}, "tried": tried}
    return {"answer_type": "abstain", "claims": [],
            "abstention": {"reason": "no brand in the question resolved unambiguously in the drug master", "missing": "an exact brand (with strength) present in the CDCI subset", "tried": tried}}
