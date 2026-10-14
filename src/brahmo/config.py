"""Configuration loader.

Rules:
  * Everything tunable lives in config/settings.json (and the files it points at).
  * Any key can be overridden with an environment variable BRAHMO_<SECTION>__<KEY>
    e.g. BRAHMO_ANSWERING__MODE=llm, BRAHMO_DB__PATH=/tmp/x.sqlite
  * Paths in config are relative to the repository root (the directory containing config/).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


_ENV_PREFIX = "BRAHMO_"


def repo_root() -> Path:
    env = os.environ.get("BRAHMO_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    for parent in [here] + list(here.parents):
        if (parent / "config" / "settings.json").exists():
            return parent
    return Path.cwd()


class Config:
    def __init__(self, data: Dict[str, Any], root: Path):
        self._data = data
        self.root = root

    # -- access -----------------------------------------------------------
    def get(self, dotted: str, default: Any = None) -> Any:
        env_key = _ENV_PREFIX + dotted.upper().replace(".", "__")
        if env_key in os.environ:
            return _coerce(os.environ[env_key])
        node: Any = self._data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def __getitem__(self, dotted: str) -> Any:
        val = self.get(dotted, _MISSING)
        if val is _MISSING:
            raise KeyError(dotted)
        return val

    def path(self, dotted: str) -> Path:
        return self.resolve_path(self[dotted])

    def resolve_path(self, p: str) -> Path:
        pp = Path(p)
        return pp if pp.is_absolute() else (self.root / pp)

    def load_json(self, dotted: str) -> Any:
        with open(self.path(dotted), "r", encoding="utf-8") as fh:
            return json.load(fh)

    def section(self, name: str) -> Dict[str, Any]:
        return dict(self._data.get(name, {}))

    def as_dict(self) -> Dict[str, Any]:
        return json.loads(json.dumps(self._data))


_MISSING = object()


def _coerce(raw: str) -> Any:
    low = raw.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


_cached: Optional[Config] = None


def load_config(path: Optional[str] = None, fresh: bool = False) -> Config:
    global _cached
    if _cached is not None and not fresh and path is None:
        return _cached
    root = repo_root()
    cfg_path = Path(path) if path else root / "config" / "settings.json"
    with open(cfg_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    cfg = Config(data, root)
    if path is None:
        _cached = cfg
    return cfg
