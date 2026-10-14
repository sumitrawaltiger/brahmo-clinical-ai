"""Claim-level guards. Every number in an answer claim must appear in the cited unit text (G6)."""
from __future__ import annotations

import re
from typing import Dict, List

_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")


def numbers_in(text: str) -> List[str]:
    return [n.replace(",", ".") for n in _NUM_RE.findall(text or "")]


def uncited_numbers(claim_text: str, cited_texts: List[str]) -> List[str]:
    pool = set()
    for t in cited_texts:
        pool.update(numbers_in(t))
    return [n for n in numbers_in(claim_text) if n not in pool]


def verify_claims(claims: List[Dict], chunks_by_id: Dict[str, Dict]) -> Dict:
    """Return {ok_claims, dropped} — a claim is dropped if any citation is unknown or any number is uncited."""
    ok, dropped = [], []
    for c in claims:
        ids = [x["chunk_id"] if isinstance(x, dict) else x for x in c.get("citations", [])]
        missing = [i for i in ids if i not in chunks_by_id]
        if missing or not ids:
            dropped.append({"claim": c.get("text"), "reason": f"unknown or missing citation ids {missing or '[]'}"})
            continue
        bad = uncited_numbers(c.get("text", ""), [chunks_by_id[i]["text"] for i in ids])
        if bad:
            dropped.append({"claim": c.get("text"), "reason": f"numbers not present in cited text: {bad}"})
            continue
        ok.append(c)
    return {"ok_claims": ok, "dropped": dropped}
