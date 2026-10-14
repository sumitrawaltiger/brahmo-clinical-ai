"""The 8-state check contract. Every check result is built through CheckResult so the vocabulary cannot drift."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

HIT = "HIT"
CHECKED_NO_HIT = "CHECKED_NO_HIT"
PARTIAL_COVERAGE = "PARTIAL_COVERAGE"
UNVERIFIED_INPUT = "UNVERIFIED_INPUT"
NOT_CHECKED = "NOT_CHECKED"
DATA_EXPIRED = "DATA_EXPIRED"
SOURCE_CONFLICT = "SOURCE_CONFLICT"
SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

STATUSES = [HIT, CHECKED_NO_HIT, PARTIAL_COVERAGE, UNVERIFIED_INPUT, NOT_CHECKED, DATA_EXPIRED, SOURCE_CONFLICT, SERVICE_UNAVAILABLE]

# Severity vocabulary for HITs; NONE for everything that is not a hit.
SEVERE, MODERATE, INFO, NONE = "SEVERE", "MODERATE", "INFO", "NONE"

# Ordering used when one check has several per-item outcomes and must report a single status.
# Rationale: an operational failure must never be hidden by a hit; a hit must never be hidden by "unknown";
# "unknown" must never be hidden by "no hit".
PRECEDENCE = [SERVICE_UNAVAILABLE, DATA_EXPIRED, SOURCE_CONFLICT, HIT, UNVERIFIED_INPUT, PARTIAL_COVERAGE, NOT_CHECKED, CHECKED_NO_HIT]


def worst(statuses: List[str]) -> str:
    for s in PRECEDENCE:
        if s in statuses:
            return s
    return NOT_CHECKED


@dataclass
class CheckResult:
    check_id: str
    name: str
    rule_version: str
    status: str
    severity: str = NONE
    summary: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    unverified_items: List[Dict[str, Any]] = field(default_factory=list)
    data_versions: Dict[str, str] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"illegal status {self.status!r}; must be one of {STATUSES}")
        if self.status != HIT and self.severity != NONE:
            # a non-hit cannot carry a severity; it would read as a (partial) verdict
            self.severity = NONE

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
