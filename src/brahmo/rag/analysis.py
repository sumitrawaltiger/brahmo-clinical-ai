"""Deterministic question analysis: which corpus condition(s) a question is about, which markers it carries,
and whether it is a structured-fact question that must be answered from the drug master instead of retrieval.

Matching is on word boundaries, never raw substrings: 'uti' must not fire inside 'routine', 'ors' not inside
'factors'. Marker terms may be prefixes of a word ('pregnan' -> pregnancy/pregnant) but still start on a boundary.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from ..config import Config

_STRUCTURED_RE = re.compile(
    r"\b(banned|prohibited|restricted|withdrawn|legal status|regulatory status|is .* allowed|"
    r"what does .* contain|composition of|ingredients? (of|in)|salts? (of|in)|what is in|strength of|contains?)\b", re.I)
_EDITION_RE = re.compile(r"\b(edition|editions|version|versions|previous|older|archive|archived|20\d\d)\b", re.I)
_NATIONAL_RE = re.compile(r"\b(national|icmr|stw|workflow pack|standard treatment)\b", re.I)
_PATIENT_RE = re.compile(r"\b\d+\s*-?\s*(year|yr|month)s?[- ]old\b|\b\d+\s*kg\b|\bmy patient\b", re.I)

_cache: Dict[str, re.Pattern] = {}


def _term_re(term: str, prefix: bool) -> re.Pattern:
    key = f"{int(prefix)}:{term}"
    if key not in _cache:
        t = re.escape(term.strip().lower())
        _cache[key] = re.compile(r"(?<![a-z0-9])" + t + (r"[a-z]*" if prefix else r"(?![a-z0-9])"))
    return _cache[key]


def _any(q: str, terms: List[str], prefix: bool = False) -> bool:
    return any(_term_re(t, prefix).search(q) for t in terms if t.strip())


def analyze(question: str, cfg: Config) -> Dict[str, Any]:
    syn = cfg.load_json("retrieval.condition_synonyms_path")
    q = question.lower()
    present = [c for c, words in syn["conditions"].items() if _any(q, words)]
    absent = [c for c, words in syn["absent_conditions"].items() if _any(q, words)]
    markers = {
        "dose": _any(q, syn["dose_markers"], prefix=True),
        "paediatric": _any(q, syn["paediatric_markers"], prefix=True),
        "pregnancy": _any(q, syn["pregnancy_markers"], prefix=True),
        "local_protocol": _any(q, syn["local_protocol_markers"], prefix=True),
        "national": bool(_NATIONAL_RE.search(question)),
        "editions": bool(_EDITION_RE.search(question)),
        "patient_specific": bool(_PATIENT_RE.search(question)),
    }
    structured = bool(_STRUCTURED_RE.search(question)) and not present
    return {
        "conditions_in_corpus": present,
        "conditions_absent_from_corpus": absent,
        "markers": markers,
        "route": "module_a_structured" if structured else ("abstain_no_corpus" if (absent and not present) else "retrieval"),
    }
