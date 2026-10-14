"""Module C: one JSON trace with every version used."""
import json

from brahmo.trace.run import trace


def test_trace_contains_all_sections_and_versions(conn, cfg, index):
    rx = json.loads((cfg.root / "data" / "trace_sample_rx.json").read_text(encoding="utf-8"))
    t = trace(conn, rx, "Which analgesic class must be avoided in suspected dengue, and why?", cfg, as_of="2026-10-14")
    assert t["normalization"]["unresolved_count"] == 1          # 'Telma' is ambiguous
    assert {c["check_id"] for c in t["safety_checks"]} == {"DUP-001", "FDC-001", "INT-001", "CUM-001"}
    assert t["grounded_answer"]["answer_type"] == "answer"
    v = t["versions"]
    assert v["datasets"]["cdci"]["file_sha256"] and v["rag_index"] and v["rule_set"]["version"] and v["config_sha256"]
    assert v["answering"]["mode"] in ("extractive", "llm")
    json.dumps(t)  # serializable
