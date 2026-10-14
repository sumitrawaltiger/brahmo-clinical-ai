"""Derive regulatory status from effective-dated events.

Algorithm (per product, per as-of date):
  1. Find every event whose structured target matches the product's ingredient set / form (see match_event).
  2. An event is *effective* if effective_date <= as_of.
  3. An effective event is *superseded* if another effective event names it in supersedes_event_id.
  4. The in-force set = effective and not superseded. Zero -> NONE. One -> its action governs.
     More than one with different actions -> SOURCE_CONFLICT (shown, never merged).
  5. Events effective after as_of are reported as 'pending' so freshness is visible.
Every result cites notification id, published and effective dates, and the supersession chain.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from ..config import Config, load_config
from ..normalize.resolver import resolve
from ..normalize.text import norm_key

ACTION_TO_STATUS = {
    "PROHIBITED": "PROHIBITED",
    "RESTRICTED": "RESTRICTED",
    "WITHDRAWN": "WITHDRAWN",
    "STAY_GRANTED": "STAYED",     # a stay suspends the superseded prohibition; the product is not legally prohibited while it holds
    "REVOKED": "NONE",
    "LIFTED": "NONE",
}


@dataclass
class EventView:
    event_id: str
    notification_id: str
    date_published: str
    effective_date: str
    action: str
    target_type: str
    target_description: str
    supersedes_event_id: Optional[str]
    note: str
    batch_id: str
    match: Dict[str, Any] = field(default_factory=dict)

    def cite(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "notification_id": self.notification_id,
            "action": self.action,
            "date_published": self.date_published,
            "effective_date": self.effective_date,
            "target": self.target_description,
            "supersedes_event_id": self.supersedes_event_id,
            "note": self.note,
            "data_batch": self.batch_id,
        }


def load_events(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    out = []
    for r in conn.execute(
        """SELECT e.*, t.ingredient_set, t.match_mode, t.form_qualifier, t.population_qualifier, t.ratio_qualifier,
                  t.parse_confidence, t.parse_method, t.unresolved_terms
           FROM regulatory_event e JOIN regulatory_target t ON t.event_id = e.event_id AND t.batch_id = e.batch_id
           ORDER BY e.effective_date, e.event_id"""
    ):
        d = dict(r)
        d["ingredient_set"] = json.loads(d["ingredient_set"] or "[]")
        d["unresolved_terms"] = json.loads(d["unresolved_terms"] or "[]")
        out.append(d)
    return out


def match_event(ev: Dict[str, Any], product_ingredients: List[str], dose_form: Optional[str], is_fdc: bool) -> Optional[Dict[str, Any]]:
    """Return a match descriptor if the event's target applies to this product, else None.

    Unresolved target terms (ingredients absent from the master) make an exact-set match impossible; such
    events are reported as 'unmatchable' by the caller rather than silently ignored.
    """
    pset: Set[str] = set(product_ingredients)
    tset: Set[str] = set(ev["ingredient_set"])
    if not tset:
        return None
    mode = ev["match_mode"]
    matched = False
    if mode == "exact_set":
        if ev["unresolved_terms"]:
            return None  # can never be an exact match while part of the target is unknown
        matched = pset == tset
    elif mode == "ingredient_any":
        matched = bool(pset & tset)
    elif mode in ("contains_all", "contains_all_fdc_only"):
        matched = tset.issubset(pset) and (is_fdc or mode == "contains_all")
    if not matched:
        return None
    desc: Dict[str, Any] = {"mode": mode, "form_applies": True, "qualifiers": []}
    if ev.get("form_qualifier"):
        desc["form_applies"] = (dose_form or "").lower() == ev["form_qualifier"].lower()
        desc["qualifiers"].append(f"form={ev['form_qualifier']}")
        if not desc["form_applies"]:
            return {"mode": mode, "form_applies": False, "qualifiers": desc["qualifiers"], "excluded_reason": f"product form '{dose_form}' is outside the event's form qualifier '{ev['form_qualifier']}'"}
    if ev.get("population_qualifier"):
        desc["qualifiers"].append(f"population={ev['population_qualifier']}")
    if ev.get("ratio_qualifier"):
        desc["qualifiers"].append(f"ratio={ev['ratio_qualifier']}")
        desc["uncertain"] = "event applies to a specific ratio that the extract does not state; applicability cannot be confirmed"
    return desc


def derive_status(matching: List[Dict[str, Any]], all_events: List[Dict[str, Any]], as_of: str) -> Dict[str, Any]:
    """Given matching events for a product, compute the in-force status as of a date."""
    by_id = {e["event_id"]: e for e in all_events}
    effective = [e for e in matching if e["effective_date"] <= as_of]
    pending = [e for e in matching if e["effective_date"] > as_of]
    # supersession is global: any effective event (matching or not) can supersede
    superseded_ids = {e["supersedes_event_id"] for e in all_events if e["effective_date"] <= as_of and e.get("supersedes_event_id")}
    in_force = [e for e in effective if e["event_id"] not in superseded_ids]
    uncertain = [e for e in in_force if e.get("_match", {}).get("uncertain")]
    actions = {ACTION_TO_STATUS.get(e["action"], e["action"]) for e in in_force}

    def chain(e: Dict[str, Any]) -> List[Dict[str, Any]]:
        out, cur, guard = [], e, 0
        while cur and guard < 20:
            out.append(_cite(cur))
            cur = by_id.get(cur.get("supersedes_event_id") or "")
            guard += 1
        return out

    result: Dict[str, Any] = {
        "as_of": as_of,
        "status": "NONE",
        "governing_events": [_cite(e) for e in in_force],
        "supersession_chains": [chain(e) for e in in_force],
        "superseded_events": [_cite(e) for e in effective if e["event_id"] in superseded_ids],
        "pending_events": [_cite(e) for e in pending],
        "uncertain_applicability": [dict(_cite(e), reason=e["_match"]["uncertain"]) for e in uncertain],
        "conflict": False,
    }
    if not in_force:
        result["status"] = "NONE"
    elif len(actions) == 1:
        result["status"] = actions.pop()
    else:
        result["status"] = "CONFLICT"
        result["conflict"] = True
        result["conflict_detail"] = f"{len(in_force)} in-force events disagree: " + ", ".join(f"{e['event_id']}={e['action']}" for e in in_force)
    return result


def _cite(e: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event_id": e["event_id"],
        "notification_id": e["notification_id"],
        "action": e["action"],
        "date_published": e["date_published"],
        "effective_date": e["effective_date"],
        "target": e["target_description"],
        "target_type": e["target_type"],
        "supersedes_event_id": e.get("supersedes_event_id"),
        "note": e.get("note"),
        "parse_confidence": e.get("parse_confidence"),
        "data_batch": e["batch_id"],
        "match": e.get("_match"),
    }


def status_for_product(conn: sqlite3.Connection, product: Dict[str, Any], as_of: str, events: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    events = events if events is not None else load_events(conn)
    ings = [i["norm"] for i in product["ingredients"]]
    is_fdc = len(ings) > 1
    matching: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    for ev in events:
        m = match_event(ev, ings, product.get("dose_form"), is_fdc)
        if m is None:
            continue
        e = dict(ev)
        e["_match"] = m
        if m.get("form_applies", True):
            matching.append(e)
        else:
            excluded.append(dict(_cite(e), excluded_reason=m["excluded_reason"]))
    out = derive_status(matching, events, as_of)
    out["product_id"] = product["product_id"]
    out["brand_name"] = product["brand_name"]
    out["ingredients"] = ings
    out["excluded_by_qualifier"] = excluded
    # targets the register names but can never match because part of the target is unknown to the master
    out["register_gaps"] = [
        {"event_id": ev["event_id"], "notification_id": ev["notification_id"], "unresolved_terms": ev["unresolved_terms"]}
        for ev in events if ev["unresolved_terms"] and set(ev["ingredient_set"]) & set(ings)
    ]
    return out


def status_for_product_text(conn: sqlite3.Connection, text: str, as_of: Optional[str] = None, cfg: Optional[Config] = None) -> Dict[str, Any]:
    from datetime import date

    cfg = cfg or load_config()
    as_of = as_of or date.today().isoformat()
    res = resolve(conn, text, None, None, cfg)
    if res.status != "RESOLVED":
        return {"resolution": res.to_dict(), "status": "UNVERIFIED_INPUT"}
    return {"resolution": {"status": res.status, "product_id": res.product["product_id"], "method": res.method, "confidence": res.confidence},
            "regulatory": status_for_product(conn, res.product, as_of)}
