"""Command-line entry point: python -m brahmo <command>."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .db import connect, migrate


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def cmd_migrate(args) -> int:
    cfg = load_config()
    conn = connect(cfg)
    applied = migrate(conn, cfg)
    _print({"db": str(cfg.path("db.path")), "applied": applied})
    return 0


def cmd_ingest(args) -> int:
    from .ingest.run_all import run_all
    from .normalize.review_queue import summary

    cfg = load_config()
    conn = connect(cfg)
    migrate(conn, cfg)
    out = run_all(conn, cfg)
    out["review_queue"] = summary(conn)
    _print(out)
    return 0


def cmd_setup(args) -> int:
    rc = cmd_ingest(args)
    if rc:
        return rc
    from .rag.index import build_index

    cfg = load_config()
    _print({"rag_index": build_index(cfg)})
    return 0


def cmd_review(args) -> int:
    from .normalize.review_queue import list_items, summary

    cfg = load_config()
    conn = connect(cfg)
    if args.list:
        _print(list_items(conn, limit=args.limit, reason=args.reason))
    else:
        _print(summary(conn))
    return 0


def cmd_resolve(args) -> int:
    from .normalize.resolver import resolve

    cfg = load_config()
    conn = connect(cfg)
    _print(resolve(conn, args.text, args.strength, args.form, cfg).to_dict())
    return 0


def cmd_status(args) -> int:
    from .regulatory.status import status_for_product_text

    cfg = load_config()
    conn = connect(cfg)
    _print(status_for_product_text(conn, args.text, args.as_of, cfg))
    return 0


def cmd_rail(args) -> int:
    from .rail.engine import run_prescription_file, run_seed_prescriptions

    cfg = load_config()
    conn = connect(cfg)
    if args.seed:
        _print(run_seed_prescriptions(conn, cfg, as_of=args.as_of, out_dir=args.out))
    else:
        _print(run_prescription_file(conn, Path(args.rx), cfg, as_of=args.as_of))
    return 0


def cmd_index(args) -> int:
    from .rag.index import build_index

    _print(build_index(load_config()))
    return 0


def cmd_ask(args) -> int:
    from .rag.answer import answer_question

    cfg = load_config()
    conn = connect(cfg)
    _print(answer_question(conn, args.question, cfg, mode=args.mode))
    return 0


def cmd_eval(args) -> int:
    from .rag.evaluate import run_eval

    cfg = load_config()
    conn = connect(cfg)
    _print(run_eval(conn, cfg, mode=args.mode, out_dir=args.out, as_of=args.as_of))
    return 0


def cmd_trace(args) -> int:
    from .trace.run import trace

    cfg = load_config()
    conn = connect(cfg)
    rx = json.loads(Path(args.rx).read_text(encoding="utf-8"))
    out = trace(conn, rx, args.question, cfg, as_of=args.as_of, mode=args.mode)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    _print(out)
    return 0


def cmd_versions(args) -> int:
    from .ingest.batches import data_versions

    cfg = load_config()
    conn = connect(cfg)
    _print(data_versions(conn))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="brahmo", description="BRAHMO clinical AI — assessment build")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("migrate", help="apply numbered migrations").set_defaults(fn=cmd_migrate)
    sub.add_parser("ingest", help="migrate + load every provided dataset").set_defaults(fn=cmd_ingest)
    sub.add_parser("setup", help="ingest + build the Module B index (everything needed to run)").set_defaults(fn=cmd_setup)
    sub.add_parser("versions", help="show loaded data versions").set_defaults(fn=cmd_versions)

    r = sub.add_parser("review", help="review queue summary / listing")
    r.add_argument("--list", action="store_true")
    r.add_argument("--reason")
    r.add_argument("--limit", type=int, default=25)
    r.set_defaults(fn=cmd_review)

    rs = sub.add_parser("resolve", help="resolve one brand text")
    rs.add_argument("text")
    rs.add_argument("--strength")
    rs.add_argument("--form")
    rs.set_defaults(fn=cmd_resolve)

    st = sub.add_parser("status", help="event-sourced regulatory status for a brand text")
    st.add_argument("text")
    st.add_argument("--as-of", dest="as_of")
    st.set_defaults(fn=cmd_status)

    ra = sub.add_parser("rail", help="run the deterministic safety rail")
    ra.add_argument("--rx", help="prescription JSON file")
    ra.add_argument("--seed", action="store_true", help="run the 10 seeded prescriptions and write outputs/")
    ra.add_argument("--as-of", dest="as_of")
    ra.add_argument("--out", default=None)
    ra.set_defaults(fn=cmd_rail)

    sub.add_parser("index", help="(re)build the Module B chunk index").set_defaults(fn=cmd_index)

    ask = sub.add_parser("ask", help="grounded answer for one question")
    ask.add_argument("question")
    ask.add_argument("--mode", default=None, help="extractive | llm (default from config)")
    ask.set_defaults(fn=cmd_ask)

    ev = sub.add_parser("eval", help="run the Module B mini-eval")
    ev.add_argument("--mode", default=None)
    ev.add_argument("--out", default=None)
    ev.add_argument("--as-of", dest="as_of", default=None, help="date for any structured-fact (regulatory) question in the set")
    ev.set_defaults(fn=cmd_eval)

    tr = sub.add_parser("trace", help="Module C: one prescription + one question -> one JSON trace")
    tr.add_argument("--rx", required=True)
    tr.add_argument("--question", required=True)
    tr.add_argument("--as-of", dest="as_of")
    tr.add_argument("--mode", default=None)
    tr.add_argument("--out", default=None)
    tr.set_defaults(fn=cmd_trace)

    args = p.parse_args(argv)
    return int(args.fn(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
