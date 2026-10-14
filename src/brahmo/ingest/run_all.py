"""Run every loader in dependency order."""
from __future__ import annotations

import sqlite3
from typing import Any, Dict, Optional

from ..config import Config, load_config
from . import cdci, gazette, interactions, references, stock, supplement


def run_all(conn: sqlite3.Connection, cfg: Optional[Config] = None) -> Dict[str, Any]:
    cfg = cfg or load_config()
    out: Dict[str, Any] = {}
    out["cdci"] = cdci.load(conn, cfg)              # ingredients must exist before gazette/interaction mapping
    out["ingredient_supplement"] = supplement.load(conn, cfg)  # candidate-added names (provenance per row); before gazette/interactions
    out["nlem"] = references.load_nlem(conn, cfg)
    out["jan_aushadhi"] = references.load_jan_aushadhi(conn, cfg)
    out["gazette"] = gazette.load(conn, cfg)
    out["interactions"] = interactions.load(conn, cfg)
    out["pharmacy_stock"] = stock.load(conn, cfg)
    return out
