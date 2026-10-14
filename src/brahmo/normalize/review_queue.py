"""The review queue: the single destination for anything the pipeline could not resolve with confidence."""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional

from ..db import utcnow_iso


def enqueue(
    conn: sqlite3.Connection,
    batch_id: str,
    entity_type: str,
    raw_input: str,
    reason_code: str,
    reason_detail: str = "",
    candidates: Optional[List[Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> int:
    cur = conn.execute(
        """INSERT INTO review_queue(batch_id, entity_type, raw_input, context, reason_code, reason_detail,
                                    candidates, status, created_at)
           VALUES (?,?,?,?,?,?,?,'OPEN',?)""",
        (
            batch_id,
            entity_type,
            raw_input,
            json.dumps(context or {}, ensure_ascii=False),
            reason_code,
            reason_detail,
            json.dumps(candidates or [], ensure_ascii=False),
            utcnow_iso(),
        ),
    )
    return int(cur.lastrowid)


def summary(conn: sqlite3.Connection) -> Dict[str, Any]:
    by_reason = {
        r["reason_code"]: r["n"]
        for r in conn.execute(
            "SELECT reason_code, COUNT(*) n FROM review_queue WHERE status='OPEN' GROUP BY reason_code ORDER BY n DESC"
        )
    }
    by_entity = {
        r["entity_type"]: r["n"]
        for r in conn.execute(
            "SELECT entity_type, COUNT(*) n FROM review_queue WHERE status='OPEN' GROUP BY entity_type ORDER BY n DESC"
        )
    }
    total = conn.execute("SELECT COUNT(*) FROM review_queue WHERE status='OPEN'").fetchone()[0]
    return {"open_total": total, "by_reason": by_reason, "by_entity": by_entity}


def list_items(conn: sqlite3.Connection, status: str = "OPEN", limit: int = 50, reason: Optional[str] = None):
    sql = "SELECT * FROM review_queue WHERE status=?"
    params: List[Any] = [status]
    if reason:
        sql += " AND reason_code=?"
        params.append(reason)
    sql += " ORDER BY item_id LIMIT ?"
    params.append(limit)
    out = []
    for r in conn.execute(sql, params):
        d = dict(r)
        d["candidates"] = json.loads(d["candidates"] or "[]")
        d["context"] = json.loads(d["context"] or "{}")
        out.append(d)
    return out
