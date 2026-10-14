"""Deterministic safety rail.

Input: a draft prescription (brand-level items). Output: normalization results + four checks, each in the
8-state contract with severity, evidence, rule version and data versions. Pure lookup logic; no model call.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import uuid
from datetime import date, datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import Config, load_config
from ..db import table_exists, utcnow_iso
from ..ingest.batches import latest_batch
from ..normalize import reasons
from ..normalize.resolver import RESOLVED, resolve
from ..normalize.review_queue import enqueue
from ..regulatory.status import load_events, status_for_product
from .contract import (CHECKED_NO_HIT, DATA_EXPIRED, HIT, INFO, MODERATE, NONE, NOT_CHECKED, PARTIAL_COVERAGE,
                       SERVICE_UNAVAILABLE, SEVERE, SOURCE_CONFLICT, UNVERIFIED_INPUT, CheckResult, worst)
from .frequency import FrequencyParser

_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_YEAR_RE = re.compile(r"(20\d{2})")

ENGINE_VERSION = "rail-engine-1.0.0"


# --------------------------------------------------------------------------- helpers

def _version_date(source_version: str) -> Optional[date]:
    m = _DATE_RE.search(source_version or "")
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    y = _YEAR_RE.search(source_version or "")
    if y:
        return date(int(y.group(1)), 1, 1)
    return None


def _freshness(conn: sqlite3.Connection, cfg: Config, as_of: date) -> Dict[str, Dict[str, Any]]:
    limits = {
        "cdci": int(cfg["freshness.drug_master_max_age_days"]),
        "gazette": int(cfg["freshness.regulatory_max_age_days"]),
        "interactions": int(cfg["freshness.interaction_seed_max_age_days"]),
    }
    out: Dict[str, Dict[str, Any]] = {}
    for ds, limit in limits.items():
        b = latest_batch(conn, ds)
        if b is None:
            out[ds] = {"present": False, "expired": True, "reason": "dataset not loaded"}
            continue
        vd = _version_date(b["source_version"])
        age = (as_of - vd).days if vd else None
        expired = age is None or age > limit or age < 0
        out[ds] = {
            "present": True,
            "batch_id": b["batch_id"],
            "source_version": b["source_version"],
            "version_date": vd.isoformat() if vd else None,
            "age_days_at_as_of": age,
            "max_age_days": limit,
            "expired": expired,
            "reason": (None if not expired else (
                "no parseable version date" if age is None else
                ("check date precedes data version" if age < 0 else f"age {age}d exceeds max {limit}d"))),
        }
    return out


def _replay_key(rx: Dict[str, Any], as_of: str, rule_version: str, data_versions: Dict[str, Any]) -> str:
    payload = json.dumps({"rx": rx, "as_of": as_of, "rules": rule_version, "data": data_versions}, sort_keys=True, ensure_ascii=False, default=str)
    return "rail-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _dedup_enqueue(conn: sqlite3.Connection, batch_id: str, entity_type: str, raw: str, reason: str, detail: str, candidates, context) -> int:
    row = conn.execute(
        "SELECT item_id FROM review_queue WHERE status='OPEN' AND entity_type=? AND raw_input=? AND reason_code=?",
        (entity_type, raw, reason),
    ).fetchone()
    if row:
        return int(row[0])
    return enqueue(conn, batch_id, entity_type, raw, reason, detail, candidates=candidates, context=context)


# --------------------------------------------------------------------------- engine

class Rail:
    def __init__(self, conn: sqlite3.Connection, cfg: Optional[Config] = None):
        self.conn = conn
        self.cfg = cfg or load_config()
        self.rules = self.cfg.load_json("rail.rule_set_path")
        self.ceilings = self.cfg.load_json("rail.reference_ceilings_path").get("ceilings", [])
        self.freq = FrequencyParser(self.cfg.load_json("rail.frequency_patterns_path"))
        self.sev = {
            "PROHIBITED": self.cfg["rail.prohibited_severity"],
            "RESTRICTED": self.cfg["rail.restricted_severity"],
            "WITHDRAWN": self.cfg["rail.withdrawn_severity"],
            "STAYED": INFO,
        }

    # ----- public
    def run(self, rx: Dict[str, Any], as_of: Optional[str] = None) -> Dict[str, Any]:
        as_of_d = date.fromisoformat(as_of) if as_of else date.today()
        run_id = str(uuid.uuid4())
        rx_id = rx.get("rx_id") or "RX"
        base = {
            "run_id": run_id,
            "rx_id": rx_id,
            "as_of": as_of_d.isoformat(),
            "engine_version": ENGINE_VERSION,
            "rule_set": {"id": self.rules["rule_set_id"], "version": self.rules["rule_set_version"]},
            "patient_population": rx.get("patient_population"),
        }
        svc = self._service_check()
        if svc:
            checks = [self._service_unavailable(cid, svc) for cid in self.rules["rules"]]
            return dict(base, normalization=None, checks=[c.to_dict() for c in checks], data_versions={}, overall=SERVICE_UNAVAILABLE,
                        item_states=[], service_error=svc)

        fresh = _freshness(self.conn, self.cfg, as_of_d)
        data_versions = {ds: f.get("batch_id") for ds, f in fresh.items() if f.get("present")}
        items = self._normalize(rx, rx_id)
        events = load_events(self.conn)   # latest gazette batch only (see regulatory.status.load_events)

        # replay key: same prescription + date + rule set + data batches => same run_id (audit rows keep their own uuid)
        base["run_id"] = _replay_key(rx, as_of_d.isoformat(), self.rules["rule_set_version"], data_versions)
        checks: List[CheckResult] = [
            self._check_duplicate(items, fresh, rx.get("patient_population")),
            self._check_regulatory(items, events, as_of_d.isoformat(), fresh),
            self._check_interactions(items, fresh),
            self._check_cumulative(items, fresh, rx.get("patient_population")),
        ]
        for c in checks:
            c.data_versions = {k: v for k, v in data_versions.items()}
        out = dict(
            base,
            normalization={"items": [self._item_public(i) for i in items],
                           "unresolved_count": sum(1 for i in items if i["resolution"]["status"] != RESOLVED)},
            freshness=fresh,
            checks=[c.to_dict() for c in checks],
            data_versions=data_versions,
            overall=worst([c.status for c in checks]),
        )
        out["item_states"] = self._item_states(items, checks)
        self._audit(out, rx)
        return out

    # ----- preflight
    def _service_check(self) -> Optional[str]:
        for t in ("product", "product_ingredient", "regulatory_event", "regulatory_target", "interaction_pair", "load_batch"):
            if not table_exists(self.conn, t):
                return f"required table '{t}' missing — run `brahmo setup`"
        if self.conn.execute("SELECT COUNT(*) FROM product").fetchone()[0] == 0:
            return "drug master is empty — run `brahmo setup`"
        return None

    def _service_unavailable(self, cid: str, why: str) -> CheckResult:
        r = self.rules["rules"][cid]
        return CheckResult(cid, r["name"], r["version"], SERVICE_UNAVAILABLE, summary=why)

    # ----- normalization
    def _normalize(self, rx: Dict[str, Any], rx_id: str) -> List[Dict[str, Any]]:
        items = []
        batch = latest_batch(self.conn, "cdci")
        for it in rx.get("items", []):
            res = resolve(self.conn, it.get("written_product", ""), it.get("strength_as_written") or None, it.get("form") or None, self.cfg)
            freq = self.freq.parse(it.get("dose_frequency"))
            review_id = None
            if res.status != RESOLVED:
                review_id = _dedup_enqueue(
                    self.conn, batch["batch_id"] if batch else "n/a", "prescription_item",
                    f"{it.get('written_product','')} | {it.get('strength_as_written') or ''}".strip(" |"),
                    res.reason_code or reasons.UNKNOWN_BRAND, res.reason_detail,
                    [{k: c[k] for k in ("product_id", "brand_name", "dose_form", "strength_text", "score")} for c in res.candidates],
                    {"rx_id": rx_id, "item_no": it.get("item_no")},
                )
            items.append({"input": it, "resolution": res.to_dict(), "frequency": freq, "review_item_id": review_id})
        self.conn.commit()
        return items

    @staticmethod
    def _item_public(i: Dict[str, Any]) -> Dict[str, Any]:
        r = i["resolution"]
        pub = {
            "item_no": i["input"].get("item_no"),
            "written_product": i["input"].get("written_product"),
            "strength_as_written": i["input"].get("strength_as_written"),
            "dose_frequency": i["input"].get("dose_frequency"),
            "frequency_parsed": i["frequency"],
            "resolution_status": r["status"],
            "method": r["method"],
            "confidence": r["confidence"],
            "reason_code": r["reason_code"],
            "reason_detail": r["reason_detail"],
            "review_item_id": i["review_item_id"],
        }
        if r["product"]:
            p = r["product"]
            pub["product"] = {
                "product_id": p["product_id"], "batch_id": p["batch_id"], "brand_name": p["brand_name"], "dose_form": p["dose_form"],
                "strength_text": p["strength_text"], "is_fdc": len(p["ingredients"]) > 1,
                "salts": [{"ingredient": x["ingredient"], "strength_value": x["strength_value"], "strength_unit": x["strength_unit"],
                           "decomposition_confidence": x["confidence"], "decomposition_method": x["method"]} for x in p["ingredients"]],
                "equivalent_product_ids": r.get("equivalent_product_ids", []),
            }
        else:
            pub["candidates"] = [{"product_id": c["product_id"], "brand_name": c["brand_name"], "dose_form": c["dose_form"],
                                  "strength_text": c["strength_text"], "score": c["score"]} for c in r["candidates"][:6]]
        return pub

    @staticmethod
    def _unverified(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{"item_no": i["input"].get("item_no"), "written_product": i["input"].get("written_product"),
                 "reason_code": i["resolution"]["reason_code"], "reason_detail": i["resolution"]["reason_detail"],
                 "review_item_id": i["review_item_id"]} for i in items if i["resolution"]["status"] != RESOLVED]

    @staticmethod
    def _resolved(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [i for i in items if i["resolution"]["status"] == RESOLVED]

    def _rule(self, cid: str) -> Tuple[str, str]:
        r = self.rules["rules"][cid]
        return r["name"], r["version"]

    def _expired(self, fresh: Dict[str, Any], *datasets: str) -> Optional[str]:
        bad = [f"{ds}: {fresh[ds]['reason']}" for ds in datasets if fresh.get(ds, {}).get("expired")]
        return "; ".join(bad) if bad else None

    # ----- exposure table shared by DUP and CUM
    def _exposure(self, items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        table: Dict[str, Dict[str, Any]] = {}
        for i in self._resolved(items):
            p = i["resolution"]["product"]
            upd = i["frequency"]["units_per_day"]
            for s in p["ingredients"]:
                key = s["norm"]
                ent = table.setdefault(key, {"ingredient": s["ingredient"], "contributions": [], "total_mg_per_day": 0.0,
                                             "lower_bound": False, "unit": s["strength_unit"], "unit_conflict": False})
                mg = None
                if upd is not None and s["strength_value"] is not None:
                    mg = round(float(s["strength_value"]) * float(upd), 3)
                    ent["total_mg_per_day"] = round(ent["total_mg_per_day"] + mg, 3)
                else:
                    ent["lower_bound"] = True
                if s["strength_unit"] != ent["unit"]:
                    ent["unit_conflict"] = True
                ent["contributions"].append({
                    "item_no": i["input"].get("item_no"), "written_product": i["input"].get("written_product"),
                    "product_id": p["product_id"], "brand_name": p["brand_name"], "is_fdc": len(p["ingredients"]) > 1,
                    "strength_per_unit": s["strength_value"], "unit": s["strength_unit"],
                    "units_per_day": upd, "frequency_kind": i["frequency"]["kind"], "mg_per_day": mg,
                })
        for ent in table.values():
            ent["distinct_items"] = len({c["item_no"] for c in ent["contributions"]})
            if ent["unit_conflict"]:
                ent["lower_bound"] = True
        return table

    def _ceiling_note(self, ingredient_norm: str, total: float, lower_bound: bool, population: Optional[str]) -> Dict[str, Any]:
        for c in self.ceilings:
            if c["ingredient"].lower() == ingredient_norm:
                cite = {"source_doc": c["source_doc"], "source_version": c["source_version"], "section": c["source_section"],
                        "as_written": c["as_written"], "population": c["population"]}
                exceeds = total > float(c["max_mg_per_day"])
                pop_ok = population is not None and population.lower() == c["population"].lower()
                return {"found": True, "citation": cite, "max_mg_per_day": c["max_mg_per_day"], "exceeds": exceeds,
                        "population_matches_input": pop_ok,
                        "note": (f"aggregate {'≥' if lower_bound else ''}{total} mg/day {'EXCEEDS' if exceeds else 'is within'} the cited "
                                 f"{c['population']} ceiling ({c['as_written']}, {c['source_doc']} v{c['source_version']})"
                                 + ("" if pop_ok else "; patient population not supplied, ceiling applicability not confirmed"))}
        return {"found": False, "note": "no cited reference ceiling in the corpus for this ingredient; total reported without judgement"}

    # ----- checks
    def _check_duplicate(self, items: List[Dict[str, Any]], fresh: Dict[str, Any], population: Optional[str]) -> CheckResult:
        name, ver = self._rule("DUP-001")
        exp = self._expired(fresh, "cdci")
        if exp:
            return CheckResult("DUP-001", name, ver, DATA_EXPIRED, summary=f"drug master data expired: {exp}", unverified_items=self._unverified(items))
        table = self._exposure(items)
        hits = []
        for key, ent in table.items():
            if ent["distinct_items"] >= 2:
                ceiling = self._ceiling_note(key, ent["total_mg_per_day"], ent["lower_bound"], population)
                hits.append({
                    "ingredient": ent["ingredient"],
                    "items": ent["contributions"],
                    "aggregate_mg_per_day": ent["total_mg_per_day"],
                    "aggregate_is_lower_bound": ent["lower_bound"],
                    "aggregate_note": ("some contributions have no quantifiable frequency (as-needed/unparseable); total is a lower bound"
                                       if ent["lower_bound"] else "all contributions quantified"),
                    "visible_only_after_fdc_decomposition": any(c["is_fdc"] for c in ent["contributions"]),
                    "reference_ceiling": ceiling,
                })
        unverified = self._unverified(items)
        if hits:
            return CheckResult("DUP-001", name, ver, HIT, severity=self.cfg["rail.duplicate_severity"],
                               summary=f"{len(hits)} ingredient(s) appear in more than one item: " + ", ".join(h["ingredient"] for h in hits),
                               evidence={"hits": hits}, unverified_items=unverified,
                               notes=(["one or more items are unresolved; further duplicates may exist"] if unverified else []))
        if unverified:
            return CheckResult("DUP-001", name, ver, UNVERIFIED_INPUT, summary=f"{len(unverified)} item(s) could not be resolved to a product; duplicate check incomplete",
                               evidence={"resolved_ingredients": sorted(table)}, unverified_items=unverified)
        return CheckResult("DUP-001", name, ver, CHECKED_NO_HIT, summary="no active ingredient is shared across items",
                           evidence={"resolved_ingredients": sorted(table)})

    def _check_regulatory(self, items: List[Dict[str, Any]], events: List[Dict[str, Any]], as_of: str, fresh: Dict[str, Any]) -> CheckResult:
        name, ver = self._rule("FDC-001")
        exp = self._expired(fresh, "cdci", "gazette")
        if exp:
            return CheckResult("FDC-001", name, ver, DATA_EXPIRED, summary=f"data expired: {exp}", unverified_items=self._unverified(items))
        per_item, hits, partial, conflicts = [], [], [], []
        for i in self._resolved(items):
            p = i["resolution"]["product"]
            st = status_for_product(self.conn, p, as_of, events)
            entry = {"item_no": i["input"].get("item_no"), "written_product": i["input"].get("written_product"), "product_id": p["product_id"],
                     "ingredients": st["ingredients"], "status_as_of": st["status"], "governing_events": st["governing_events"],
                     "supersession_chains": st["supersession_chains"], "superseded_events": st["superseded_events"],
                     "pending_events": st["pending_events"], "excluded_by_qualifier": st["excluded_by_qualifier"],
                     "uncertain_applicability": st["uncertain_applicability"], "register_gaps": st["register_gaps"]}
            per_item.append(entry)
            if st["conflict"]:
                conflicts.append(dict(entry, conflict_detail=st["conflict_detail"]))
            elif st["status"] in ("PROHIBITED", "RESTRICTED", "WITHDRAWN", "STAYED"):
                hits.append(dict(entry, severity=self.sev[st["status"]]))
            if st["uncertain_applicability"]:
                partial.append({"item_no": entry["item_no"], "why": [u["reason"] for u in st["uncertain_applicability"]]})
            # a register target that overlaps this product but contains terms unknown to the master
            for g in st["register_gaps"]:
                known = set(next(e["ingredient_set"] for e in events if e["event_id"] == g["event_id"]))
                if known.issubset(set(st["ingredients"])):
                    partial.append({"item_no": entry["item_no"], "why": [f"{g['event_id']} ({g['notification_id']}) names {g['unresolved_terms']} which the drug master does not know; applicability to this product cannot be confirmed"]})
        unverified = self._unverified(items)
        ev = {"items": per_item}
        if conflicts:
            return CheckResult("FDC-001", name, ver, SOURCE_CONFLICT, summary="in-force regulatory events disagree for " + ", ".join(c["written_product"] for c in conflicts),
                               evidence=dict(ev, conflicts=conflicts), unverified_items=unverified)
        if hits:
            sev = SEVERE if any(h["severity"] == SEVERE for h in hits) else (MODERATE if any(h["severity"] == MODERATE for h in hits) else INFO)
            return CheckResult("FDC-001", name, ver, HIT, severity=sev,
                               summary="; ".join(f"{h['written_product']}: {h['status_as_of']} per {', '.join(g['notification_id'] + ' (eff. ' + g['effective_date'] + ')' for g in h['governing_events'])}" for h in hits),
                               evidence=dict(ev, hits=hits, partial=partial), unverified_items=unverified)
        if unverified:
            return CheckResult("FDC-001", name, ver, UNVERIFIED_INPUT, summary=f"{len(unverified)} item(s) unresolved; regulatory status cannot be checked for them",
                               evidence=dict(ev, partial=partial), unverified_items=unverified)
        if partial:
            return CheckResult("FDC-001", name, ver, PARTIAL_COVERAGE, summary="no in-force event matched, but one or more register targets could not be fully interpreted for these items",
                               evidence=dict(ev, partial=partial))
        return CheckResult("FDC-001", name, ver, CHECKED_NO_HIT, summary=f"no in-force PROHIBITED/RESTRICTED/WITHDRAWN event matches any item as of {as_of}", evidence=ev)

    def _check_interactions(self, items: List[Dict[str, Any]], fresh: Dict[str, Any]) -> CheckResult:
        name, ver = self._rule("INT-001")
        exp = self._expired(fresh, "cdci", "interactions")
        if exp:
            return CheckResult("INT-001", name, ver, DATA_EXPIRED, summary=f"data expired: {exp}", unverified_items=self._unverified(items))
        ib = latest_batch(self.conn, "interactions")
        pairs = {r["pair_key"]: dict(r) for r in self.conn.execute("SELECT * FROM interaction_pair WHERE batch_id=?", (ib["batch_id"] if ib else "",))}
        covered = set()
        for r in pairs.values():
            covered.add(r["a_norm"]); covered.add(r["b_norm"])
        # class members (e.g. Nitrates -> nitroglycerin) from the supplement. Only SIGNED mappings may fire; unsigned
        # ones are reported as a coverage gap so a candidate-added reading of a class never produces a verdict.
        members: Dict[str, str] = {}
        unsigned_members: Dict[str, str] = {}
        if table_exists(self.conn, "ingredient_class_member"):
            sb = latest_batch(self.conn, "ingredient_supplement")
            for r in self.conn.execute("SELECT class_norm, member_norm, requires_signoff FROM ingredient_class_member WHERE batch_id=?", (sb["batch_id"] if sb else "",)):
                if int(r["requires_signoff"]) and not bool(self.cfg.get("rail.allow_unsigned_class_members", False)):
                    unsigned_members[r["member_norm"]] = r["class_norm"]
                else:
                    members[r["member_norm"]] = r["class_norm"]
                    covered.add(r["member_norm"])
        present: List[Tuple[str, str, int, str]] = []  # (norm, display, item_no, product_id)
        for i in self._resolved(items):
            p = i["resolution"]["product"]
            for s in p["ingredients"]:
                present.append((s["norm"], s["ingredient"], i["input"].get("item_no"), p["product_id"]))
        hits, unsigned_matches, checked_pairs = [], [], 0
        for (an, ad, ai, ap), (bn, bd, bi, bp) in combinations(present, 2):
            if an == bn:
                continue
            checked_pairs += 1
            direct = "|".join(sorted([an, bn]))
            keys = {direct: True}
            for x, y, mapping, signed in ((an, bn, members, True), (bn, an, members, True), (an, bn, unsigned_members, False), (bn, an, unsigned_members, False)):
                if x in mapping:
                    keys.setdefault("|".join(sorted([mapping[x], y])), signed)
            for k, signed in keys.items():
                if k not in pairs:
                    continue
                r = pairs[k]
                rec = {"ingredient_a": ad, "ingredient_b": bd, "items": sorted({ai, bi}), "within_single_product": ai == bi,
                       "severity": r["severity"], "note": r["note"], "source_tag": r["source_tag"], "seed_pair": f"{r['ingredient_a']} + {r['ingredient_b']}",
                       "matched_via_class": k != direct}
                if signed:
                    hits.append(rec)
                else:
                    unsigned_matches.append(dict(rec, blocked_reason="class membership is candidate-added and awaits clinical sign-off; not served as a verdict"))
        uncovered = sorted({d for n, d, _, _ in present if n not in covered})
        unverified = self._unverified(items)
        ev = {"pairs_evaluated": checked_pairs, "seed_pairs_available": len(pairs), "seed_batch": ib["batch_id"] if ib else None,
              "ingredients_not_in_seed": uncovered, "unsigned_class_matches": unsigned_matches,
              "coverage_note": f"the seed list has {len(pairs)} ingredient-level pairs; an ingredient absent from it has NOT been screened for interactions"}
        if hits:
            sev = SEVERE if any(h["severity"] == "SEVERE" for h in hits) else MODERATE
            return CheckResult("INT-001", name, ver, HIT, severity=sev, summary="; ".join(f"{h['ingredient_a']} + {h['ingredient_b']} ({h['severity']}: {h['note']})" for h in hits),
                               evidence=dict(ev, hits=hits), unverified_items=unverified)
        if unverified:
            return CheckResult("INT-001", name, ver, UNVERIFIED_INPUT, summary=f"{len(unverified)} item(s) unresolved; their ingredients could not be screened", evidence=ev, unverified_items=unverified)
        if unsigned_matches:
            return CheckResult("INT-001", name, ver, PARTIAL_COVERAGE,
                               summary="a seed pair would match through a class mapping that awaits clinical sign-off: " + "; ".join(f"{u['ingredient_a']} + {u['ingredient_b']} via {u['seed_pair']}" for u in unsigned_matches),
                               evidence=ev)
        if uncovered and bool(self.cfg["rail.interaction_require_ingredient_coverage"]):
            return CheckResult("INT-001", name, ver, PARTIAL_COVERAGE, summary=f"no seed pair matched, but {len(uncovered)} ingredient(s) are not covered by the seed list: {', '.join(uncovered)}", evidence=ev)
        return CheckResult("INT-001", name, ver, CHECKED_NO_HIT, summary="no severe seed interaction among the resolved ingredients", evidence=ev)

    def _check_cumulative(self, items: List[Dict[str, Any]], fresh: Dict[str, Any], population: Optional[str]) -> CheckResult:
        name, ver = self._rule("CUM-001")
        exp = self._expired(fresh, "cdci")
        if exp:
            return CheckResult("CUM-001", name, ver, DATA_EXPIRED, summary=f"drug master data expired: {exp}", unverified_items=self._unverified(items))
        table = self._exposure(items)
        totals, hits, partial_reasons = [], [], []
        for key, ent in table.items():
            ceiling = self._ceiling_note(key, ent["total_mg_per_day"], ent["lower_bound"], population)
            row = {"ingredient": ent["ingredient"], "distinct_items": ent["distinct_items"], "shared_across_items": ent["distinct_items"] >= 2,
                   "total_mg_per_day": ent["total_mg_per_day"], "is_lower_bound": ent["lower_bound"], "contributions": ent["contributions"],
                   "reference_ceiling": ceiling}
            totals.append(row)
            if ent["distinct_items"] >= 2:
                if ceiling["found"] and ceiling["exceeds"]:
                    hits.append(row)
                if ent["lower_bound"]:
                    partial_reasons.append(f"{ent['ingredient']}: an as-needed/unparseable frequency makes the daily total a lower bound")
                if not ceiling["found"]:
                    partial_reasons.append(f"{ent['ingredient']}: no cited reference ceiling available; total reported only")
                elif not ceiling["population_matches_input"]:
                    partial_reasons.append(f"{ent['ingredient']}: ceiling is for '{ceiling['citation']['population']}' and the prescription does not state the patient population")
        unverified = self._unverified(items)
        ev = {"per_ingredient": totals, "method": "sum over items of (units/day x strength per unit); frequency parsed from dose_frequency with config/frequency_patterns.json"}
        if hits:
            return CheckResult("CUM-001", name, ver, HIT, severity=MODERATE,
                               summary="; ".join(f"{h['ingredient']} {'≥' if h['is_lower_bound'] else ''}{h['total_mg_per_day']} mg/day exceeds cited ceiling {h['reference_ceiling']['max_mg_per_day']} mg/day ({h['reference_ceiling']['citation']['source_doc']})" for h in hits),
                               evidence=dict(ev, hits=hits, partial=partial_reasons), unverified_items=unverified)
        if unverified:
            return CheckResult("CUM-001", name, ver, UNVERIFIED_INPUT, summary=f"{len(unverified)} item(s) unresolved; totals exclude them", evidence=ev, unverified_items=unverified)
        if partial_reasons:
            return CheckResult("CUM-001", name, ver, PARTIAL_COVERAGE, summary="; ".join(partial_reasons), evidence=ev)
        if any(t["shared_across_items"] for t in totals):
            return CheckResult("CUM-001", name, ver, CHECKED_NO_HIT, summary="shared-ingredient totals are within cited ceilings for the stated population", evidence=ev)
        return CheckResult("CUM-001", name, ver, CHECKED_NO_HIT, summary="no ingredient is contributed by more than one item", evidence=ev)

    # ----- per-item roll-up (for the seed template columns)
    @staticmethod
    def _hit_item_nos(h: Dict[str, Any]) -> set:
        """Item numbers a hit record refers to, across the four checks' evidence shapes."""
        if isinstance(h.get("items"), list):
            return {x["item_no"] if isinstance(x, dict) else x for x in h["items"]}
        if isinstance(h.get("contributions"), list):          # CUM-001
            return {x["item_no"] for x in h["contributions"]}
        if "item_no" in h:                                      # FDC-001
            return {h["item_no"]}
        return set()

    def _item_states(self, items: List[Dict[str, Any]], checks: List[CheckResult]) -> List[Dict[str, Any]]:
        """Per-item roll-up for the seed template. A resolved item is CHECKED_NO_HIT only when every check actually
        ran to completion for the whole prescription: a check that is UNVERIFIED_INPUT / PARTIAL_COVERAGE /
        SOURCE_CONFLICT / DATA_EXPIRED because of *another* item still means this item was not fully screened."""
        out = []
        for i in items:
            no = i["input"].get("item_no")
            if i["resolution"]["status"] != RESOLVED:
                out.append({"item_no": no, "state": UNVERIFIED_INPUT, "note": f"{i['resolution']['reason_code']}: {i['resolution']['reason_detail']}"})
                continue
            involved, notes = [], []
            for c in checks:
                if c.status == HIT:
                    for h in c.evidence.get("hits", []):
                        if no in self._hit_item_nos(h):
                            involved.append(c.check_id)
                            notes.append(f"{c.check_id} {c.severity}: {self._hit_note(c, h)}")
            per_check = ", ".join(f"{c.check_id}={c.status}" for c in checks)
            if involved:
                out.append({"item_no": no, "state": HIT, "note": " | ".join(notes) + f" ({per_check})"})
                continue
            # statuses that limit how completely THIS item was screened
            limiting: List[str] = []
            for c in checks:
                if c.status == HIT:
                    if c.unverified_items:       # the hit is real for other items; this one was not screened against the unresolved ones
                        limiting.append(UNVERIFIED_INPUT)
                elif c.status != CHECKED_NO_HIT:
                    limiting.append(c.status)
            if limiting:
                state = worst(limiting)
                reasons_txt = " | ".join(f"{c.check_id}: {c.summary}" for c in checks if c.status not in (CHECKED_NO_HIT, HIT))
                out.append({"item_no": no, "state": state, "note": f"resolved, but not fully screened ({per_check}); {reasons_txt}".rstrip("; ")})
            else:
                out.append({"item_no": no, "state": CHECKED_NO_HIT, "note": f"resolved; {per_check}"})
        return out

    @staticmethod
    def _hit_note(c: CheckResult, h: Dict[str, Any]) -> str:
        if c.check_id == "DUP-001":
            return (f"{h['ingredient']} in items {[x['item_no'] for x in h['items']]}; aggregate {'≥' if h['aggregate_is_lower_bound'] else ''}"
                    f"{h['aggregate_mg_per_day']} mg/day; {h['reference_ceiling']['note']}")
        if c.check_id == "FDC-001":
            g = h["governing_events"]
            return f"{h['status_as_of']} — " + "; ".join(f"{x['notification_id']} published {x['date_published']} effective {x['effective_date']}" for x in g)
        if c.check_id == "INT-001":
            return f"{h['ingredient_a']} + {h['ingredient_b']} {h['severity']} ({h['note']}; {h['source_tag']})"
        if c.check_id == "CUM-001":
            return f"{h['ingredient']} total {h['total_mg_per_day']} mg/day vs ceiling {h['reference_ceiling']['max_mg_per_day']}"
        return c.summary

    def _audit(self, out: Dict[str, Any], rx: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO rail_run(audit_id, run_id, rx_id, as_of_date, rule_set_version, data_versions, input_json, output_json, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), out["run_id"], out["rx_id"], out["as_of"], out["rule_set"]["version"], json.dumps(out["data_versions"]),
             json.dumps(rx, ensure_ascii=False), json.dumps(out, ensure_ascii=False, default=str), utcnow_iso()),
        )
        self.conn.commit()


# --------------------------------------------------------------------------- runners

def run_prescription_file(conn: sqlite3.Connection, path: Path, cfg: Optional[Config] = None, as_of: Optional[str] = None) -> Dict[str, Any]:
    rx = json.loads(path.read_text(encoding="utf-8"))
    return Rail(conn, cfg).run(rx, as_of)


def read_seed_prescriptions(path: Path) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            g = groups.setdefault(r["rx_id"], {"rx_id": r["rx_id"], "items": []})
            g["items"].append({"item_no": int(r["item_no"]), "written_product": r["written_product"], "strength_as_written": r["strength_as_written"] or None,
                               "dose_frequency": r["dose_frequency"], "clinical_note": r["clinical_note"]})
    return list(groups.values())


def run_seed_prescriptions(conn: sqlite3.Connection, cfg: Optional[Config] = None, as_of: Optional[str] = None, out_dir: Optional[str] = None) -> Dict[str, Any]:
    cfg = cfg or load_config()
    src = cfg.path("data.seed_prescriptions")
    out_root = Path(out_dir) if out_dir else cfg.path("trace.output_dir")
    rail_dir = out_root / "rail"
    rail_dir.mkdir(parents=True, exist_ok=True)
    rail = Rail(conn, cfg)
    results = []
    for rx in read_seed_prescriptions(src):
        res = rail.run(rx, as_of)
        (rail_dir / f"{rx['rx_id']}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        results.append(res)
    # completed template
    completed = out_root / "seed_prescriptions_completed.csv"
    with open(src, "r", encoding="utf-8-sig", newline="") as fh, open(completed, "w", encoding="utf-8", newline="") as out:
        reader = csv.DictReader(fh)
        writer = csv.DictWriter(out, fieldnames=reader.fieldnames)
        writer.writeheader()
        by_rx = {r["rx_id"]: r for r in results}
        for row in reader:
            res = by_rx[row["rx_id"]]
            st = next(s for s in res["item_states"] if s["item_no"] == int(row["item_no"]))
            row["candidate_rail_output_state"] = st["state"]
            row["candidate_evidence_note"] = st["note"]
            writer.writerow(row)
    # summary markdown
    lines = ["# Seeded rail demonstration — summary", "", f"as_of: {results[0]['as_of'] if results else as_of}", "",
             "| rx | overall | DUP-001 | FDC-001 | INT-001 | CUM-001 | unresolved items |", "|---|---|---|---|---|---|---|"]
    for r in results:
        cs = {c["check_id"]: c for c in r["checks"]}
        lines.append(f"| {r['rx_id']} | {r['overall']} | " + " | ".join(f"{cs[k]['status']}{(' ('+cs[k]['severity']+')') if cs[k]['status']=='HIT' else ''}" for k in ("DUP-001", "FDC-001", "INT-001", "CUM-001"))
                     + f" | {r['normalization']['unresolved_count']} |")
    lines += ["", "## Per-line states (template columns)", "", "| rx | item | written | state | evidence note |", "|---|---|---|---|---|"]
    for r in results:
        for it, st in zip(r["normalization"]["items"], r["item_states"]):
            lines.append(f"| {r['rx_id']} | {it['item_no']} | {it['written_product']} | {st['state']} | {st['note'].replace('|', '/')} |")
    (out_root / "seed_rail_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"count": len(results), "outputs": str(out_root), "overall": {r["rx_id"]: r["overall"] for r in results}}
