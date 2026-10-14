"""Deterministic question analysis: which corpus condition(s) a question is about, which markers it carries,
and whether it is a structured-fact question that must be answered from the drug master instead of retrieval."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from ..config import Config

_STRUCTURED_RE = re.compile(
    r"\b(banned|prohibited|restricted|withdrawn|legal status|regulatory status|is .* allowed|"
    r"what does .* contain|composition of|ingredients? (of|in)|salts? (of|in)|what is in|strength of|contains?)\b", re.I)
_BRANDISH_RE = re.compile(r"\b([A-Z][a-zA-Z]+(?:[- ][A-Z0-9][a-zA-Z0-9]*)?\s?\d{0,4})\b")
_EDITION_RE = re.compile(r"\b(edition|editions|version|versions|previous|older|archive|archived|20\d\d)\b", re.I)
_NATIONAL_RE = re.compile(r"\b(national|icmr|stw|workflow pack|standard treatment)\b", re.I)


def analyze(question: str, cfg: Config) -> Dict[str, Any]:
    syn = cfg.load_json("retrieval.condition_synonyms_path")
    q = " " + question.lower() + " "
    present = [c for c, words in syn["conditions"].items() if any(w in q for w in words)]
    absent = [c for c, words in syn["absent_conditions"].items() if any(w in q for w in words)]
    markers = {
        "dose": any(w in q for w in syn["dose_markers"]),
        "paediatric": any(w in q for w in syn["paediatric_markers"]),
        "pregnancy": any(w in q for w in syn["pregnancy_markers"]),
        "local_protocol": any(w in q for w in syn["local_protocol_markers"]),
        "national": bool(_NATIONAL_RE.search(question)),
        "editions": bool(_EDITION_RE.search(question)),
        "patient_specific": bool(re.search(r"\b\d+\s*-?\s*(year|yr|month)s?[- ]old\b|\b\d+\s*kg\b|\bmy patient\b", q)),
    }
    structured = bool(_STRUCTURED_RE.search(question)) and not present
    return {
        "question": question,
        "conditions_in_corpus": present,
        "conditions_absent_from_corpus": absent,
        "markers": markers,
        "route": "module_a_structured" if structured else ("abstain_no_corpus" if (absent and not present) else "retrieval"),
    }
