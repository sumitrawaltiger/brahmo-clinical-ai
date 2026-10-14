"""Resolver eval: messy real-world spellings vs. the resolution the system must give.

Scoring mirrors the held-out rule: correct (+1) when status and product/reason match; unknown (0) when the system
is AMBIGUOUS/UNRESOLVED where a resolution was expected; WRONG (-1) when it resolves to a different product or
resolves something that must stay ambiguous — the resolver's version of a confident wrong answer.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import Config, load_config
from .resolver import RESOLVED, resolve

RESOLVER_EVAL_VERSION = "resolver-eval-1.0.0"


def score_case(case: Dict[str, Any], res) -> Dict[str, Any]:
    got = res.status
    pid = res.product["product_id"] if res.product else None
    if case["expect"] == "RESOLVED":
        if got == RESOLVED and pid == case["product_id"]:
            verdict = "correct"
        elif got == RESOLVED:
            verdict = "wrong"            # resolved to a different product
        else:
            verdict = "unknown"          # queued instead of resolved: safe, scores 0
    else:
        if got == RESOLVED:
            verdict = "wrong"            # resolved something that must not be
        elif got == case["expect"] and (not case.get("reason_code") or res.reason_code == case["reason_code"]):
            verdict = "correct"
        else:
            verdict = "unknown"          # queued, but with a different status/reason than expected
    return {"id": case["id"], "written": case["written"], "strength": case.get("strength"), "expected": case["expect"],
            "expected_product": case.get("product_id"), "expected_reason": case.get("reason_code"), "got": got, "got_product": pid,
            "got_reason": res.reason_code, "method": res.method, "confidence": res.confidence, "verdict": verdict,
            "score": {"correct": 1, "unknown": 0, "wrong": -1}[verdict], "note": case.get("note", "")}


def run_resolver_eval(conn: sqlite3.Connection, cfg: Optional[Config] = None, out_dir: Optional[str] = None) -> Dict[str, Any]:
    cfg = cfg or load_config()
    spec = cfg.load_json("eval.messy_spellings_path")
    rows = [score_case(c, resolve(conn, c["written"], c.get("strength"), None, cfg)) for c in spec["cases"]]
    tally = {k: sum(r["verdict"] == k for r in rows) for k in ("correct", "unknown", "wrong")}
    summary = {"eval_version": RESOLVER_EVAL_VERSION, "n": len(rows), "tally": tally, "score_total": sum(r["score"] for r in rows), "results": rows}
    od = Path(out_dir) if out_dir else cfg.path("trace.output_dir") / "eval"
    od.mkdir(parents=True, exist_ok=True)
    (od / "resolver_eval_results.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    md = ["# Resolver eval — messy prescription spellings", "",
          f"**{tally['correct']} correct · {tally['unknown']} unknown (queued) · {tally['wrong']} wrong** of {len(rows)} (held-out-style total {summary['score_total']})", "",
          "| id | written | strength | expected | got | method | conf | verdict | note |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        exp = r["expected"] + (f" {r['expected_product']}" if r["expected_product"] else (f" {r['expected_reason']}" if r["expected_reason"] else ""))
        got = r["got"] + (f" {r['got_product']}" if r["got_product"] else (f" {r['got_reason']}" if r["got_reason"] else ""))
        md.append(f"| {r['id']} | `{r['written']}` | {r['strength'] or '—'} | {exp} | {got} | {r['method']} | {r['confidence']:.2f} | **{r['verdict']}** | {r['note']} |")
    (od / "resolver_eval_results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return dict(summary, output_dir=str(od))
