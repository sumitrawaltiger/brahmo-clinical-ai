"""Parse dose-frequency strings into units/day using config-driven patterns. Unknown -> None (never guessed)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class FrequencyParser:
    def __init__(self, spec: Dict[str, Any]):
        self.as_needed = {t.upper() for t in spec.get("as_needed_tokens", [])}
        self.patterns = [(re.compile(p["regex"], re.I), p) for p in spec.get("patterns", [])]

    def parse(self, text: Optional[str]) -> Dict[str, Any]:
        raw = (text or "").strip()
        if not raw:
            return {"raw": raw, "units_per_day": None, "kind": "missing", "duration_days": None}
        up = raw.upper()
        if any(tok in up.split() or up == tok for tok in self.as_needed):
            return {"raw": raw, "units_per_day": None, "kind": "as_needed", "duration_days": None}
        for rx, spec in self.patterns:
            m = rx.match(raw)
            if not m:
                continue
            if spec["kind"] == "morning_noon_night":
                groups = [g for g in m.groups()[:4] if g is not None]
                units = sum(float(g) for g in groups)
                dur = m.group(5) if m.lastindex and m.lastindex >= 5 and m.group(5) else None
                return {"raw": raw, "units_per_day": units, "kind": "schedule", "duration_days": int(dur) if dur else None}
            return {"raw": raw, "units_per_day": float(spec["units_per_day"]), "kind": "fixed", "duration_days": None}
        return {"raw": raw, "units_per_day": None, "kind": "unparseable", "duration_days": None}
