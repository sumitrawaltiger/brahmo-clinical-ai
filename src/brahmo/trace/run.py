"""End-to-end trace. Thin by design: it calls the rail and the answerer and staples the versions together."""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any, Dict, Optional

from .. import __version__
from ..config import Config, load_config
from ..ingest.batches import data_versions
from ..normalize.text import sha256_file, sha256_text
from ..rag.answer import answer_question
from ..rag.index import load_index
from ..rail.engine import ENGINE_VERSION, Rail


def trace(conn: sqlite3.Connection, rx: Dict[str, Any], question: str, cfg: Optional[Config] = None, as_of: Optional[str] = None, mode: Optional[str] = None) -> Dict[str, Any]:
    cfg = cfg or load_config()
    as_of = as_of or date.today().isoformat()
    index = load_index(cfg)
    rail_out = Rail(conn, cfg).run(rx, as_of)
    qa_out = answer_question(conn, question, cfg, mode=mode, index=index, as_of=as_of)
    rules = cfg.load_json("rail.rule_set_path")
    prompt_path = cfg.path("answering.prompt_path")
    return {
        # deterministic: the trace is a pure function of its two run replay keys, so checked-in traces are stable
        "trace_id": "trace-" + sha256_text(rail_out["run_id"] + "|" + qa_out["run_id"])[:16],
        "schema_version": cfg["trace.schema_version"],
        "as_of": as_of,
        "input": {"prescription": rx, "question": question},
        "normalization": rail_out["normalization"],
        "safety_checks": rail_out["checks"],
        "safety_overall": rail_out["overall"],
        "item_states": rail_out["item_states"],
        "grounded_answer": {k: qa_out.get(k) for k in ("route", "answer_type", "claims", "labels", "notes", "abstention", "superseded_editions", "comparison", "guard", "analysis")},
        "versions": {
            "package": __version__,
            "rail_engine": ENGINE_VERSION,
            "rule_set": {"id": rules["rule_set_id"], "version": rules["rule_set_version"], "rules": {k: v["version"] for k, v in rules["rules"].items()}},
            "datasets": data_versions(conn),
            "freshness": rail_out.get("freshness"),
            "rag_index": index.version,
            "chunker": index.meta["chunker_version"],
            "embedding": {"provider": index.meta["embedding_provider"], "model": index.meta["embedding_model"]},
            "answering": {"mode": qa_out["mode"], "model": qa_out["versions"].get("model"), "prompt_version": qa_out["versions"].get("prompt_version"),
                          "prompt_file_sha256": sha256_file(prompt_path)[:12] if prompt_path.exists() else None},
            "config_sha256": sha256_file(cfg.root / "config" / "settings.json")[:12],
        },
        "run_ids": {"rail_run_id": rail_out["run_id"], "qa_run_id": qa_out["run_id"]},
        "doctor_decides": "Nothing here is final. Every state above is a draft check or a cited excerpt for the prescribing doctor to confirm or reject.",
    }
