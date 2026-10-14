"""Mini-eval harness: runs the sample questions and scores correct / abstained / wrong against data/eval expectations.
Also enforces G6 mechanically: every number in every claim must appear in the cited unit text."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import Config, load_config
from .answer import answer_question
from .guard import uncited_numbers
from .index import load_index

EVAL_VERSION = "mini-eval-1.0.0"


def _claim_texts(out: Dict[str, Any]) -> List[str]:
    return [c["text"] for c in out.get("claims", [])]


def _cited_docs(out: Dict[str, Any]) -> Dict[str, set]:
    docs: Dict[str, set] = {}
    for c in out.get("claims", []):
        for cit in c.get("citations", []):
            docs.setdefault(cit.get("document"), set()).add(cit.get("version"))
    return docs


def score_one(spec: Dict[str, Any], out: Dict[str, Any], index) -> Dict[str, Any]:
    got = out.get("answer_type")
    texts = _claim_texts(out)
    joined = "\n".join(texts)
    docs = _cited_docs(out)
    checks: List[str] = []
    # G6 numeric guard over the actual output
    chunks_by_id = {c["chunk_id"]: c for c in index.chunks}
    uncited: List[str] = []
    for c in out.get("claims", []):
        texts_cited = [chunks_by_id[x["chunk_id"]]["text"] for x in c.get("citations", []) if x.get("chunk_id") in chunks_by_id]
        if texts_cited:
            uncited.extend(uncited_numbers(c["text"], texts_cited))
    if uncited:
        checks.append(f"uncited numbers in claims: {uncited}")

    if spec["expected"] == "abstain":
        verdict = "correct" if got == "abstain" else "wrong"
        if got != "abstain":
            checks.append("expected abstention but an answer was produced")
    else:
        if got == "abstain":
            verdict = "abstained"
        else:
            ok = True
            for d in spec.get("must_cite", []):
                if d not in docs:
                    ok = False; checks.append(f"missing citation to {d}")
            for d, v in spec.get("must_cite_version", {}).items():
                if v not in docs.get(d, set()):
                    ok = False; checks.append(f"{d} not cited at version {v}")
            for s in spec.get("must_include", []):
                if s not in joined:
                    ok = False; checks.append(f"missing text: {s!r}")
            for s in spec.get("must_not_include", []):
                if s in joined:
                    ok = False; checks.append(f"forbidden text present in current claims: {s!r}")
            if spec.get("require_dose_note") and not any("No dose has been calculated" in n for n in out.get("notes", [])):
                ok = False; checks.append("dose-as-written note missing")
            if spec.get("require_superseded_shown") and not out.get("superseded_editions"):
                ok = False; checks.append("superseded edition not surfaced")
            if spec.get("require_local_label") and not any("CLINIC PROTOCOL" in c.get("label", "") for c in out.get("claims", [])):
                ok = False; checks.append("clinic protocol not labelled")
            if spec.get("require_national_comparison") and not out.get("comparison"):
                ok = False; checks.append("national comparison missing")
            verdict = "correct" if ok and not uncited else "wrong"
    held_out = {"correct": 1, "abstained": 0, "wrong": -1}[verdict]
    if spec["expected"] == "abstain" and verdict == "correct":
        held_out = 0  # the brief scores a correct refusal as 0
    return {"id": spec["id"], "question": spec["question"], "expected": spec["expected"], "got": got, "verdict": verdict,
            "held_out_style_score": held_out, "checks": checks, "cited": {k: sorted(v) for k, v in docs.items()},
            "claims": texts, "labels": out.get("labels", []), "route": out.get("route")}


def run_eval(conn: Optional[sqlite3.Connection], cfg: Optional[Config] = None, mode: Optional[str] = None, out_dir: Optional[str] = None) -> Dict[str, Any]:
    cfg = cfg or load_config()
    spec = cfg.load_json("eval.expected_path")
    index = load_index(cfg)
    results = []
    full = []
    for q in spec["questions"]:
        out = answer_question(conn, q["question"], cfg, mode=mode, index=index)
        full.append(out)
        results.append(score_one(q, out, index))
    tally = {"correct": sum(r["verdict"] == "correct" for r in results), "abstained": sum(r["verdict"] == "abstained" for r in results),
             "wrong": sum(r["verdict"] == "wrong" for r in results)}
    summary = {"eval_version": EVAL_VERSION, "mode": mode or cfg["answering.mode"], "index_version": index.version, "n": len(results), "tally": tally,
               "held_out_style_total": sum(r["held_out_style_score"] for r in results), "uncited_numbers_total": sum(1 for r in results for c in r["checks"] if c.startswith("uncited")),
               "results": results}
    od = Path(out_dir) if out_dir else cfg.path("trace.output_dir") / "eval"
    od.mkdir(parents=True, exist_ok=True)
    (od / "mini_eval_results.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (od / "answers_full.json").write_text(json.dumps(full, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    md = [f"# Mini-eval results ({summary['mode']} mode)", "", f"index: `{index.version}`", "",
          f"**{tally['correct']} correct · {tally['abstained']} abstained · {tally['wrong']} wrong** (held-out-style total {summary['held_out_style_total']}; uncited numbers: {summary['uncited_numbers_total']})", "",
          "| id | expected | got | verdict | cited | checks |", "|---|---|---|---|---|---|"]
    for r in results:
        cited = ", ".join("{} v{}".format(d, "/".join(v)) for d, v in r["cited"].items()) or "—"
        checks = "; ".join(r["checks"]) or "—"
        md.append(f"| {r['id']} | {r['expected']} | {r['got']} | **{r['verdict']}** | {cited} | {checks} |")
    md += ["", "## Answers (claim texts, verbatim from cited units)", ""]
    for r, o in zip(results, full):
        md.append(f"### {r['id']} — {r['question']}")
        md.append("")
        if o.get("answer_type") == "abstain":
            md.append(f"**ABSTAIN:** {o['abstention']['reason']}. Missing: {o['abstention']['missing']}")
        for c in o.get("claims", []):
            cit = c["citations"][0]
            md.append(f"- {c['text']}  \n  ↳ *{c['label']}* — {cit.get('document')} v{cit.get('version')}, {cit.get('section')}, p{cit.get('page')} ({cit.get('anchor')})")
        for n in o.get("notes", []):
            md.append(f"- _note: {n}_")
        for s in o.get("superseded_editions", []) or []:
            md.append(f"- _archived edition (not merged):_ {s['text']} — {s['citation']['document']} v{s['citation']['version']} (superseded by {s['citation']['superseded_by']})")
        if o.get("comparison"):
            md.append(f"- _national comparison:_ {o['comparison']['statement']}")
            for u in o["comparison"].get("national_units", []):
                md.append(f"  - {u['text']} — {u['citation']['document']} v{u['citation']['version']}")
        md.append("")
    (od / "mini_eval_results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return dict(summary, output_dir=str(od))
