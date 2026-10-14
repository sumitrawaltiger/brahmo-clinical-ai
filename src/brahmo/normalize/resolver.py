"""Brand -> product resolution.

Contract: a resolution is RESOLVED only when exactly one composition survives deterministic filters.
Everything else is AMBIGUOUS or UNRESOLVED and carries a reason code + candidates for the review queue.
Fuzzy matching only ever produces *suggestions* (reason FUZZY_ONLY); it never resolves.
"""
from __future__ import annotations

import difflib
import re
import sqlite3
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from ..config import Config, load_config
from ..ingest.batches import latest_batch
from . import reasons
from .text import norm_key

RESOLVED = "RESOLVED"
AMBIGUOUS = "AMBIGUOUS"
UNRESOLVED = "UNRESOLVED"

_STRENGTH_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(mg|mcg|µg|ug|g|ml|iu)?\s*$", re.I)
_TRAILING_STRENGTH_RE = re.compile(r"^(.*?)[\s-]+(\d+(?:\.\d+)?)\s*(mg|mcg|µg|ug|g)\s*$", re.I)

FORM_TOKENS = {
    "TAB": "Tablet", "TABS": "Tablet", "TABLET": "Tablet", "TABLETS": "Tablet",
    "CAP": "Capsule", "CAPS": "Capsule", "CAPSULE": "Capsule", "CAPSULES": "Capsule",
    "SYP": "Syrup", "SYR": "Syrup", "SYRUP": "Syrup",
    "SUSP": "Suspension", "SUSPENSION": "Suspension",
}
# Colloquial prescription prefixes/suffixes ("Tab. Dolo 650", "T. Azee 500", "Combiflam tab", "Syp Calpol 250").
# Keys are norm_key tokens. Single letters are accepted only as a LEADING token (the Indian "T./C." convention).
_LEAD_FORM = {"tab": "Tablet", "tabs": "Tablet", "tablet": "Tablet", "t": "Tablet", "cap": "Capsule", "caps": "Capsule", "capsule": "Capsule",
              "c": "Capsule", "syp": "Syrup", "syr": "Syrup", "syrup": "Syrup", "susp": "Suspension", "suspension": "Suspension", "inj": "Injection", "injection": "Injection"}
_TRAIL_FORM = {k: v for k, v in _LEAD_FORM.items() if len(k) > 1}


def strip_form_tokens(text: str) -> Tuple[str, Optional[str]]:
    """'Tab. Dolo 650' -> ('dolo 650', 'Tablet'); 'Combiflam tab' -> ('combiflam', 'Tablet'); 'Dolo 650' -> ('dolo 650', None).
    Returns the normalized core key and the form the doctor implied (None when no token). 'Inj' maps to Injection so a brand the master only knows as a tablet becomes FORM_MISMATCH, not a silent tablet."""
    toks = norm_key(text).split()
    hint: Optional[str] = None
    while len(toks) > 1 and toks[0] in _LEAD_FORM:
        hint = hint or _LEAD_FORM[toks[0]]
        toks.pop(0)
    while len(toks) > 1 and toks[-1] in _TRAIL_FORM:
        hint = hint or _TRAIL_FORM[toks[-1]]
        toks.pop()
    return " ".join(toks), hint


@dataclass
class Candidate:
    product_id: str
    batch_id: str
    brand_name: str
    dose_form: str
    strength_text: str
    ingredients: List[Dict[str, Any]]
    score: float = 1.0
    note: str = ""


@dataclass
class Resolution:
    input_text: str
    status: str
    norm_key: str
    product: Optional[Dict[str, Any]] = None
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    method: str = ""
    reason_code: Optional[str] = None
    reason_detail: str = ""
    strength_given: Optional[Dict[str, Any]] = None
    form_given: Optional[str] = None
    equivalent_product_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_strength(text: Optional[str]) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    m = _STRENGTH_RE.match(text)
    if not m:
        return {"raw": text, "value": None, "unit": None, "parseable": False}
    unit = (m.group(2) or "").lower().replace("µg", "mcg").replace("ug", "mcg")
    return {"raw": text, "value": float(m.group(1)), "unit": unit or None, "parseable": True}


def _load_candidates(conn: sqlite3.Connection, key: str, batch_id: Optional[str]) -> List[Candidate]:
    sql = """SELECT p.product_id, p.batch_id, p.brand_name, p.dose_form, p.strength_text
             FROM product p WHERE p.brand_norm = ?"""
    params: List[Any] = [key]
    if batch_id:
        sql += " AND p.batch_id = ?"
        params.append(batch_id)
    out: List[Candidate] = []
    for r in conn.execute(sql, params):
        ings = [
            {
                "ingredient": i["canonical_name"],
                "norm": i["norm_name"],
                "strength_value": i["strength_value"],
                "strength_unit": i["strength_unit"],
                "confidence": i["confidence"],
                "method": i["method"],
            }
            for i in conn.execute(
                """SELECT ing.canonical_name, ing.norm_name, pi.strength_value, pi.strength_unit, pi.confidence, pi.method
                   FROM product_ingredient pi JOIN ingredient ing ON ing.ingredient_id = pi.ingredient_id
                   WHERE pi.product_id=? AND pi.batch_id=? ORDER BY pi.position""",
                (r["product_id"], r["batch_id"]),
            )
        ]
        out.append(Candidate(r["product_id"], r["batch_id"], r["brand_name"], r["dose_form"], r["strength_text"], ings))
    return out


def _alias_lookup(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT brand_norm FROM brand_alias WHERE alias_norm=?", (key,)).fetchone()
    return row[0] if row else None


def _all_brand_norms(conn: sqlite3.Connection, batch_id: Optional[str]) -> List[str]:
    if batch_id:
        return [r[0] for r in conn.execute("SELECT DISTINCT brand_norm FROM product WHERE batch_id=?", (batch_id,))]
    return [r[0] for r in conn.execute("SELECT DISTINCT brand_norm FROM product")]


def _cand_dict(c: Candidate) -> Dict[str, Any]:
    return {
        "product_id": c.product_id,
        "batch_id": c.batch_id,
        "brand_name": c.brand_name,
        "dose_form": c.dose_form,
        "strength_text": c.strength_text,
        "ingredients": c.ingredients,
        "score": c.score,
        "note": c.note,
    }


def resolve(
    conn: sqlite3.Connection,
    text: str,
    strength_as_written: Optional[str] = None,
    form: Optional[str] = None,
    cfg: Optional[Config] = None,
    batch_id: Optional[str] = None,
) -> Resolution:
    cfg = cfg or load_config()
    mconf: Dict[str, float] = cfg["resolver.method_confidence"]
    if batch_id is None:
        # only the serving (latest) drug-master batch is ever consulted, so a reload never mixes old and new rows
        lb = latest_batch(conn, "cdci")
        batch_id = lb["batch_id"] if lb else None
    key = norm_key(text)
    strength = parse_strength(strength_as_written)
    res = Resolution(input_text=text, status=UNRESOLVED, norm_key=key, strength_given=strength, form_given=form)

    if not key:
        res.reason_code = reasons.UNKNOWN_BRAND
        res.reason_detail = "empty product text"
        return res

    method = "exact_brand"
    cands: List[Candidate] = []

    # Text variants in priority order: as written, then with colloquial form tokens stripped ("Tab. Dolo 650").
    # The stripped variant may also carry the form the doctor implied, used as a filter later.
    core_key, form_hint = strip_form_tokens(text)
    variants: List[Tuple[str, Optional[str]]] = [(key, None)]
    if core_key != key:
        variants.append((core_key, form_hint))
    for vkey, vform in variants:
        cands = _load_candidates(conn, vkey, batch_id)
        if cands:
            key = vkey
            if vform and not form:
                form, res.form_given = vform, vform
            break
        # strength glued to the brand, e.g. "Telma 40 mg" / "Dolo 650mg" -> brand "Telma 40" / "Dolo 650"
        m = _TRAILING_STRENGTH_RE.match(vkey)
        if m:
            alt_key = norm_key(f"{m.group(1)} {m.group(2)}")
            cands = _load_candidates(conn, alt_key, batch_id)
            if cands:
                key = alt_key
                if strength is None:
                    strength = parse_strength(f"{m.group(2)} {m.group(3)}")
                    res.strength_given = strength
                if vform and not form:
                    form, res.form_given = vform, vform
                break
    if not cands:
        for vkey, vform in variants:
            alias_target = _alias_lookup(conn, vkey)
            if alias_target:
                cands = _load_candidates(conn, alias_target, batch_id)
                method = "alias_table"
                key = alias_target
                if vform and not form:
                    form, res.form_given = vform, vform
                break

    # brand family: "Telma" -> Telma 20 / Telma 40 / Telma 80 / Telma-H 40. A family is a real, nameable ambiguity
    # (strength or variant missing), which is more useful to a reviewer than a fuzzy near-miss. A family with exactly
    # ONE variant ("Sinarest" -> Sinarest Tablet, "Dolo" -> Dolo 650 in this master) is not ambiguous and resolves
    # with its own method tag so the lower confidence is visible.
    if not cands:
        family: List[str] = []
        for vkey, vform in variants:
            family = [b for b in _all_brand_norms(conn, batch_id) if b.startswith(vkey + " ")]
            if family:
                key = vkey
                if vform and not form:
                    form, res.form_given = vform, vform
                break
        if family:
            fam_cands: List[Candidate] = []
            for b in family:
                fam_cands.extend(_load_candidates(conn, b, batch_id))
            # apply the strength filter to the family if a strength was written
            if strength and strength.get("parseable") and strength.get("value") is not None:
                sv, su = strength["value"], strength.get("unit")
                narrowed = [c for c in fam_cands if any(i["strength_value"] is not None and abs(float(i["strength_value"]) - sv) < 1e-9
                                                        and (su is None or (i["strength_unit"] or "").lower() == su) for i in c.ingredients)]
                if len({c.brand_name for c in narrowed}) == 1:
                    cands = narrowed
                    key = norm_key(narrowed[0].brand_name)
                    method = "brand_family_strength"
            if not cands and len({c.brand_name for c in fam_cands}) == 1:
                cands = fam_cands
                key = norm_key(fam_cands[0].brand_name)
                method = "brand_family_unique"
            if not cands:
                res.status = AMBIGUOUS
                res.candidates = [_cand_dict(c) for c in fam_cands]
                res.reason_code = reasons.AMBIGUOUS_STRENGTH_MISSING
                res.reason_detail = (f"'{key}' names a brand family with {len({c.brand_name for c in fam_cands})} variants "
                                     f"({sorted({c.brand_name for c in fam_cands})[:6]}); strength/variant needed to pick one")
                res.method = "brand_family"
                return res

    if not cands:
        pool = _all_brand_norms(conn, batch_id)
        sugg = difflib.get_close_matches(key, pool, n=int(cfg["resolver.fuzzy_max_candidates"]), cutoff=float(cfg["resolver.fuzzy_cutoff"]))
        for s in sugg:
            ratio = difflib.SequenceMatcher(None, key, s).ratio()
            for c in _load_candidates(conn, s, batch_id):
                c.score = round(ratio, 3)
                c.note = "fuzzy suggestion only"
                res.candidates.append(_cand_dict(c))
        res.reason_code = reasons.FUZZY_ONLY if res.candidates else reasons.UNKNOWN_BRAND
        res.reason_detail = (
            f"no drug-master brand equals '{key}'; {len(res.candidates)} near-miss candidate(s) listed for human review"
            if res.candidates
            else f"no drug-master brand equals '{key}' and no near-miss candidate above cutoff {cfg['resolver.fuzzy_cutoff']}"
        )
        res.confidence = float(mconf["fuzzy_suggestion"]) if res.candidates else 0.0
        res.method = "fuzzy_suggestion" if res.candidates else "none"
        return res

    pre_filter = list(cands)
    filtered = cands

    # a strength that was written but cannot be read is never ignored: that would resolve as if nothing had been written
    if strength and not strength.get("parseable"):
        res.status = UNRESOLVED
        res.reason_code = reasons.STRENGTH_UNPARSEABLE
        res.reason_detail = f"written strength '{strength['raw']}' could not be parsed (expected '<number> <unit>'); brand '{key}' matched {len(cands)} row(s) but the strength was not checked"
        res.candidates = [_cand_dict(c) for c in cands]
        res.method = method
        return res

    # strength filter
    if strength and strength.get("parseable") and strength.get("value") is not None:
        sv, su = strength["value"], strength.get("unit")
        kept = []
        for c in filtered:
            ok = False
            for ing in c.ingredients:
                if ing["strength_value"] is not None and abs(float(ing["strength_value"]) - sv) < 1e-9:
                    if su is None or (ing["strength_unit"] or "").lower() == su:
                        ok = True
            if ok:
                kept.append(c)
        if not kept:
            res.status = UNRESOLVED
            res.reason_code = reasons.STRENGTH_MISMATCH
            unit_hint = ""
            units_in_master = sorted({(i["strength_unit"] or "?") for c in filtered for i in c.ingredients})
            if su and su not in units_in_master:
                unit_hint = f"; written unit '{su}' vs master unit(s) {units_in_master} — possible unit conflict in source"
            res.reason_detail = f"written strength '{strength['raw']}' matches no master row for brand '{key}'{unit_hint}"
            res.candidates = [_cand_dict(c) for c in filtered]
            res.method = method
            return res
        filtered = kept
        method = method + "_strength"

    # form filter
    if form:
        kept = [c for c in filtered if (c.dose_form or "").lower() == form.lower()]
        if not kept:
            res.status = UNRESOLVED
            res.reason_code = reasons.FORM_MISMATCH
            res.reason_detail = f"billed/written form '{form}' matches none of {sorted({c.dose_form for c in filtered})} for brand '{key}'"
            res.candidates = [_cand_dict(c) for c in filtered]
            res.method = method
            return res
        filtered = kept
        method = method + "_form"

    # group by composition + form
    groups: Dict[str, List[Candidate]] = {}
    for c in filtered:
        comp = "|".join(f"{i['norm']}:{i['strength_value']}{i['strength_unit']}" for i in c.ingredients) + f"#{(c.dose_form or '').lower()}"
        groups.setdefault(comp, []).append(c)

    res.candidates = [_cand_dict(c) for c in filtered]
    if len(groups) == 1:
        chosen = filtered[0]
        res.status = RESOLVED
        res.product = _cand_dict(chosen)
        res.equivalent_product_ids = [c.product_id for c in filtered]
        if len(filtered) > 1:
            res.product["note"] = f"{len(filtered)} master rows share this exact composition+form; any is equivalent for salt-level checks"
        if method == "exact_brand_strength_form":
            res.method, res.confidence = "exact_brand_strength_form", mconf["exact_brand_strength_form"]
        elif method == "exact_brand_strength":
            res.method, res.confidence = "exact_brand_strength", mconf["exact_brand_strength"]
        elif method == "exact_brand_form":
            res.method, res.confidence = "exact_brand_form", mconf["exact_brand_form"]
        elif method.startswith("alias_table"):
            res.method, res.confidence = "alias_table", mconf["alias_table"]
        elif method.startswith("brand_family_strength"):
            res.method, res.confidence = "exact_brand_strength", mconf["exact_brand_strength"]
        elif method.startswith("brand_family_unique"):
            res.method, res.confidence = "brand_family_unique", mconf["brand_family_unique"]
        else:
            res.method, res.confidence = "exact_brand_unique", mconf["exact_brand_unique"]
        if res.confidence < float(cfg["resolver.auto_accept_min"]):
            res.status = AMBIGUOUS
            res.reason_code = reasons.AMBIGUOUS_BRAND_MULTI_COMPOSITION
            res.reason_detail = f"method confidence {res.confidence} below auto_accept_min"
        return res

    # multiple compositions survive -> ambiguous, never guess
    res.status = AMBIGUOUS
    res.method = method
    res.confidence = 0.0
    forms = sorted({c.dose_form for c in filtered})
    comps = sorted({c.strength_text for c in filtered})
    if strength is None and len(comps) > 1:
        res.reason_code = reasons.AMBIGUOUS_STRENGTH_MISSING
        res.reason_detail = f"brand '{key}' has {len(groups)} compositions in the master ({len(pre_filter)} rows); no strength given to pick one"
    elif form is None and len(forms) > 1 and len(comps) == 1:
        res.reason_code = reasons.AMBIGUOUS_FORM_MISSING
        res.reason_detail = f"brand '{key}' composition is unique but exists as {forms}; no form given"
    else:
        res.reason_code = reasons.AMBIGUOUS_BRAND_MULTI_COMPOSITION
        res.reason_detail = f"brand '{key}' maps to {len(groups)} distinct compositions after filters: {comps[:6]}"
    return res
