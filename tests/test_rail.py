"""G4: known-bad seeds flagged, unknowns rendered as unknowns, never 'safe'; every result in the 8-state contract."""
import json

import pytest

from brahmo.rail.contract import (CHECKED_NO_HIT, DATA_EXPIRED, HIT, PARTIAL_COVERAGE, SERVICE_UNAVAILABLE, STATUSES,
                                  UNVERIFIED_INPUT, CheckResult)
from brahmo.rail.engine import Rail, read_seed_prescriptions

AS_OF = "2026-10-14"


@pytest.fixture(scope="module")
def seeds(conn, cfg):
    rail = Rail(conn, cfg)
    return {rx["rx_id"]: rail.run(rx, AS_OF) for rx in read_seed_prescriptions(cfg.path("data.seed_prescriptions"))}


def _check(res, cid):
    return next(c for c in res["checks"] if c["check_id"] == cid)


def test_contract_rejects_unknown_status():
    with pytest.raises(ValueError):
        CheckResult("X", "x", "1", "SAFE")


def test_non_hit_cannot_carry_severity():
    c = CheckResult("X", "x", "1", CHECKED_NO_HIT, severity="SEVERE")
    assert c.severity == "NONE"


def test_all_statuses_in_vocabulary(seeds):
    for res in seeds.values():
        for c in res["checks"]:
            assert c["status"] in STATUSES
            assert c["rule_version"] and c["data_versions"]


def test_rx01_duplicate_paracetamol_via_fdc_with_aggregate(seeds):
    d = _check(seeds["RX01"], "DUP-001")
    assert d["status"] == HIT
    hit = d["evidence"]["hits"][0]
    assert hit["ingredient"] == "Paracetamol"
    assert hit["aggregate_mg_per_day"] == 2300.0           # Dolo 650 x2 + Sinarest 500 x2
    assert hit["visible_only_after_fdc_decomposition"] is True
    assert hit["reference_ceiling"]["citation"]["source_doc"] == "STW-GP-01"


def test_rx02_prohibited_fdc_cites_notification(seeds):
    f = _check(seeds["RX02"], "FDC-001")
    assert f["status"] == HIT and f["severity"] == "SEVERE"
    g = f["evidence"]["hits"][0]["governing_events"][0]
    assert g["notification_id"] == "GSR 411(E)" and g["effective_date"] == "2023-06-15"


def test_rx03_severe_interaction(seeds):
    i = _check(seeds["RX03"], "INT-001")
    assert i["status"] == HIT and i["severity"] == "SEVERE"
    assert {i["evidence"]["hits"][0]["ingredient_a"], i["evidence"]["hits"][0]["ingredient_b"]} == {"Warfarin", "Azithromycin"}


def test_rx04_ambiguous_brand_is_unverified_everywhere(seeds):
    res = seeds["RX04"]
    assert res["overall"] == UNVERIFIED_INPUT
    assert all(c["status"] == UNVERIFIED_INPUT for c in res["checks"])
    assert res["normalization"]["items"][0]["review_item_id"] is not None


def test_rx07_as_needed_makes_total_a_lower_bound(seeds):
    d = _check(seeds["RX07"], "DUP-001")
    assert d["status"] == HIT
    hit = d["evidence"]["hits"][0]
    assert hit["aggregate_is_lower_bound"] is True and hit["aggregate_mg_per_day"] == 1950.0


def test_rx08_unknown_brand_never_safe(seeds):
    res = seeds["RX08"]
    assert res["overall"] == UNVERIFIED_INPUT
    assert not any(c["status"] == CHECKED_NO_HIT for c in res["checks"])


def test_rx09_fdc_plus_plain_brand_share_telmisartan(seeds):
    d = _check(seeds["RX09"], "DUP-001")
    assert d["status"] == HIT
    hit = d["evidence"]["hits"][0]
    assert hit["ingredient"] == "Telmisartan" and hit["aggregate_mg_per_day"] == 80.0
    assert hit["visible_only_after_fdc_decomposition"] is True


def test_rx10_unit_conflict_is_unverified(seeds):
    res = seeds["RX10"]
    st = {s["item_no"]: s["state"] for s in res["item_states"]}
    assert st[2] == UNVERIFIED_INPUT and st[1] in (CHECKED_NO_HIT, PARTIAL_COVERAGE, UNVERIFIED_INPUT)


def test_no_known_bad_seed_is_missed(seeds):
    known_bad = {"RX01", "RX02", "RX03", "RX07", "RX09"}
    for rx in known_bad:
        assert seeds[rx]["overall"] == HIT, rx


def test_interaction_coverage_is_declared(seeds):
    i = _check(seeds["RX05"], "INT-001")
    assert i["status"] == PARTIAL_COVERAGE
    assert set(i["evidence"]["ingredients_not_in_seed"]) == {"Atorvastatin", "Metformin"}


def test_data_expired_when_check_date_far_ahead(conn, cfg):
    rail = Rail(conn, cfg)
    res = rail.run({"rx_id": "T", "items": [{"item_no": 1, "written_product": "Dolo 650", "strength_as_written": "650 mg", "dose_frequency": "1-0-1"}]}, "2031-01-01")
    assert all(c["status"] == DATA_EXPIRED for c in res["checks"])


def test_service_unavailable_on_empty_db(cfg, tmp_path):
    import sqlite3

    empty = sqlite3.connect(str(tmp_path / "empty.sqlite"))
    empty.row_factory = sqlite3.Row
    res = Rail(empty, cfg).run({"rx_id": "T", "items": [{"item_no": 1, "written_product": "Dolo 650"}]}, AS_OF)
    assert res["overall"] == SERVICE_UNAVAILABLE and all(c["status"] == SERVICE_UNAVAILABLE for c in res["checks"])


def test_rail_output_is_replayable_from_audit(conn, seeds):
    row = conn.execute("SELECT output_json, data_versions FROM rail_run WHERE rx_id='RX02' ORDER BY created_at DESC LIMIT 1").fetchone()
    out = json.loads(row["output_json"])
    assert out["rule_set"]["version"] and json.loads(row["data_versions"])["gazette"]


def test_no_llm_import_in_rail_package():
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[1] / "src" / "brahmo" / "rail"
    for p in src.glob("*.py"):
        text = p.read_text(encoding="utf-8")
        assert "anthropic" not in text and "openai" not in text and "llm" not in text.lower().replace("no llm", "").replace("no model call", "")
