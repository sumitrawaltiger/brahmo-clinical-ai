"""Stretch: freshness mechanism demonstration — what happens when a new gazette notification arrives.

Runs in a throw-away database (config freshness_demo.db_path):
  1. full setup from the provided pack (register v1);
  2. a *synthetic* v2 register = v1 + one new effective-dated event (file in config) is loaded as a NEW batch;
  3. the probe brand's status and the probe seed prescription are shown before and after;
  4. replay: the v1 batch is still queryable, so the pre-change answer can be reproduced exactly.
Nothing in the serving database is touched. The added event is labelled synthetic in the data and in the output.
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import Config, load_config
from ..db import connect, migrate
from ..ingest import gazette
from ..ingest.batches import latest_batch, read_csv
from ..ingest.run_all import run_all
from ..normalize.resolver import resolve
from ..rail.engine import Rail, read_seed_prescriptions
from .status import load_events, status_for_product


def _status(conn, brand: str, as_of: str, cfg: Config, batch_id: Optional[str] = None) -> Dict[str, Any]:
    res = resolve(conn, brand, None, None, cfg)
    st = status_for_product(conn, res.product, as_of, load_events(conn, batch_id))
    return {"batch": batch_id or "latest", "status": st["status"],
            "governing": [{"notification_id": g["notification_id"], "effective_date": g["effective_date"], "action": g["action"], "note": g["note"]} for g in st["governing_events"]],
            "pending": [{"notification_id": p["notification_id"], "effective_date": p["effective_date"]} for p in st["pending_events"]]}


def run_demo(cfg: Optional[Config] = None, as_of: str = "2026-10-14", out_dir: Optional[str] = None) -> Dict[str, Any]:
    cfg = cfg or load_config()
    db_path = cfg.path("freshness_demo.db_path")
    if db_path.exists():
        db_path.unlink()
    conn = connect(cfg, path=db_path)
    migrate(conn, cfg)
    run_all(conn, cfg)
    brand, rx_id = cfg["freshness_demo.probe_brand"], cfg["freshness_demo.probe_rx_id"]
    v1 = latest_batch(conn, "gazette")["batch_id"]
    rail = Rail(conn, cfg)
    seeds = {r["rx_id"]: r for r in read_seed_prescriptions(cfg.path("data.seed_prescriptions"))}
    before_status = _status(conn, brand, as_of, cfg)
    before_rail = rail.run(seeds[rx_id], as_of)

    # --- a new notification arrives: v2 = v1 + delta, loaded as a new batch (never an edit of v1)
    v2_dir = db_path.parent / "freshness_demo"
    v2_dir.mkdir(parents=True, exist_ok=True)
    v2_path = v2_dir / "regulatory_gazette_events_v2.csv"
    rows = read_csv(cfg.path("data.gazette")) + read_csv(cfg.path("freshness_demo.synthetic_event_file"))
    with open(v2_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    load_out = gazette.load(conn, cfg, v2_path)
    v2 = load_out["batch_id"]
    after_status = _status(conn, brand, as_of, cfg)
    after_rail = Rail(conn, cfg).run(seeds[rx_id], as_of)
    replay_v1 = _status(conn, brand, as_of, cfg, batch_id=v1)
    before_effective = _status(conn, brand, "2026-09-20", cfg)   # published but not yet effective

    def fdc(r):
        c = next(x for x in r["checks"] if x["check_id"] == "FDC-001")
        return {"status": c["status"], "severity": c["severity"], "summary": c["summary"], "data_versions": c["data_versions"], "run_id": r["run_id"]}

    report = {
        "as_of": as_of, "probe_brand": brand, "probe_rx": rx_id, "demo_db": str(db_path),
        "register_v1_batch": v1, "register_v2_batch": v2, "v2_added_event": rows[-1],
        "status_before": before_status, "status_after": after_status,
        "status_after_but_as_of_before_effective_date": before_effective,
        "replay_against_v1_after_v2_loaded": replay_v1,
        "rail_fdc_before": fdc(before_rail), "rail_fdc_after": fdc(after_rail),
        "what_the_mechanism_guarantees": [
            "a new register is a new load_batch (sha256 + version); v1 rows are never edited",
            "every check reads the serving (latest) batch and records its id in data_versions",
            "an event published before but effective after the check date is reported as pending, not in force",
            "the v1 batch stays queryable, so any pre-change output can be replayed against exactly what produced it",
            "in production this load sits behind a re-evaluation gate (seed rail + eval must pass) before the batch is promoted — see PART2_PLAN §1.3",
        ],
    }
    od = Path(out_dir) if out_dir else cfg.path("trace.output_dir")
    od.mkdir(parents=True, exist_ok=True)
    (od / "freshness_demo.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    md = [
        "# Freshness demo — a new gazette notification arrives", "",
        f"Probe: `{brand}` in seed prescription {rx_id}; check date {as_of}. Demo database `{db_path.name}` (serving data untouched).", "",
        f"**Added event (synthetic, labelled as such):** {rows[-1]['notification_id']} — {rows[-1]['action']} {rows[-1]['target_description']}, published {rows[-1]['date_published']}, effective {rows[-1]['effective_date']}.", "",
        "| step | register batch | status | governing / pending |", "|---|---|---|---|",
        f"| before | `{v1}` | {before_status['status']} | {before_status['governing'] or before_status['pending'] or '—'} |",
        f"| after v2 loaded | `{v2}` | **{after_status['status']}** | {[(g['notification_id'], g['effective_date']) for g in after_status['governing']]} |",
        f"| after v2, check date 2026-09-20 (published, not yet effective) | `{v2}` | {before_effective['status']} | pending {[(p['notification_id'], p['effective_date']) for p in before_effective['pending']]} |",
        f"| replay against v1 after v2 exists | `{v1}` | {replay_v1['status']} | — |", "",
        f"**Rail FDC-001 on {rx_id}:** before `{report['rail_fdc_before']['status']}` (data `{report['rail_fdc_before']['data_versions'].get('gazette')}`) → after `{report['rail_fdc_after']['status']}` {report['rail_fdc_after']['severity']} — {report['rail_fdc_after']['summary']} (data `{report['rail_fdc_after']['data_versions'].get('gazette')}`)", "",
        "What the mechanism guarantees:", *[f"- {g}" for g in report["what_the_mechanism_guarantees"]],
    ]
    (od / "freshness_demo.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    conn.close()
    return report
