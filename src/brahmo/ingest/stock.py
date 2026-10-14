"""Pharmacy stock loader: parses billing strings, resolves against the drug master, queues every uncertainty."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import Dict, Optional, Tuple

from ..config import Config, load_config
from ..normalize import reasons
from ..normalize.resolver import FORM_TOKENS, RESOLVED, resolve
from ..normalize.review_queue import enqueue
from ..normalize.text import sha256_file
from .batches import existing_batch, read_csv, register_batch

DATASET = "pharmacy_stock"
_PACK_RE = re.compile(r"^(STRIP|\d+'S|\d+S|\d+\s?ML|\d+ML|BOTTLE|BOTT|VIAL|AMP)$", re.I)


def parse_billing_string(s: str) -> Dict[str, Optional[str]]:
    """'ZYPAN-FORTE TAB 10'S' -> brand_text='ZYPAN-FORTE', form='Tablet', pack=\"10'S\"."""
    toks = s.strip().split()
    brand, form, pack = [], None, []
    for t in toks:
        up = t.upper().strip(",")
        if up in FORM_TOKENS:
            form = FORM_TOKENS[up]
        elif _PACK_RE.match(up):
            pack.append(up)
        else:
            brand.append(t)
    return {"brand_text": " ".join(brand), "form": form, "pack": " ".join(pack) or None}


def _expiry_flag(expiry: str, ref: date) -> Optional[str]:
    try:
        y, m = expiry.split("-")[:2]
        exp = date(int(y), int(m), 1)
    except Exception:
        return "UNPARSEABLE_EXPIRY"
    # a YYYY-MM expiry is taken as valid through the end of that month
    if (exp.year, exp.month) < (ref.year, ref.month):
        return "EXPIRED"
    months_ahead = (exp.year - ref.year) * 12 + (exp.month - ref.month)
    if months_ahead <= 3:
        return "EXPIRING_90D"
    return None


def load(conn: sqlite3.Connection, cfg: Optional[Config] = None, path: Optional[Path] = None) -> Dict[str, object]:
    cfg = cfg or load_config()
    path = path or cfg.path("data.pharmacy_stock")
    sha = sha256_file(path)
    prior = existing_batch(conn, DATASET, sha)
    if prior:
        return {"batch_id": prior, "skipped": True}
    rows = read_csv(path)
    ref = date.fromisoformat(str(cfg["data.stock_reference_date"]))
    batch_id = register_batch(conn, DATASET, "clinic pharmacy stock export", f"snapshot-ref-{ref.isoformat()}", path, len(rows),
                              notes="file carries no export date; reference date from config data.stock_reference_date")
    stats = {"rows": len(rows), "resolved": 0, "ambiguous": 0, "unresolved": 0, "expired": 0, "expiring_90d": 0, "by_reason": {}}
    for idx, r in enumerate(rows, start=2):
        name = r["item_name_as_billed"]
        parsed = parse_billing_string(name)
        res = resolve(conn, parsed["brand_text"], None, parsed["form"], cfg)
        review_id = None
        if res.status != RESOLVED:
            review_id = enqueue(conn, batch_id, "stock_item", name, res.reason_code or reasons.UNKNOWN_BRAND, res.reason_detail,
                                candidates=[{k: c[k] for k in ("product_id", "brand_name", "dose_form", "strength_text", "score")} for c in res.candidates],
                                context={"row": idx, "parsed": parsed})
            stats["by_reason"][res.reason_code] = stats["by_reason"].get(res.reason_code, 0) + 1
            stats["ambiguous" if res.status == "AMBIGUOUS" else "unresolved"] += 1
        else:
            stats["resolved"] += 1
        flag = _expiry_flag(r.get("expiry", ""), ref)
        if flag == "EXPIRED":
            stats["expired"] += 1
            enqueue(conn, batch_id, "stock_item", name, reasons.EXPIRED_STOCK, f"expiry {r.get('expiry')} is before reference month {ref.isoformat()[:7]}",
                    context={"row": idx, "batch_no": r.get("batch")})
        elif flag == "EXPIRING_90D":
            stats["expiring_90d"] += 1
        try:
            qty = int(r.get("qty_units") or 0)
        except ValueError:
            qty = None
        try:
            mrp = float(r.get("mrp_inr")) if r.get("mrp_inr") else None
        except ValueError:
            mrp = None
        conn.execute(
            """INSERT INTO stock_item(batch_id, row_no, item_name_as_billed, qty_units, mrp_inr, batch_no, expiry, parsed_brand_text, parsed_form,
                                      parsed_pack, resolution_status, resolved_product_id, resolved_batch_id, confidence, method, review_item_id, expiry_flag)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (batch_id, idx, name, qty, mrp, r.get("batch"), r.get("expiry"), parsed["brand_text"], parsed["form"], parsed["pack"],
             res.status, res.product["product_id"] if res.product else None, res.product["batch_id"] if res.product else None,
             res.confidence, res.method, review_id, flag),
        )
    conn.commit()
    stats["batch_id"] = batch_id
    return stats
