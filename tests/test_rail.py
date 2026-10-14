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


def test_rx10_unit_conflict_is_unverified_for_both_lines(seeds):
    # Thyronorm is unresolved, so Pan 40 was never screened against it: the sibling line must NOT read as clean
    res = seeds["RX10"]
    st = {s["item_no"]: s["state"] for s in res["item_states"]}
    assert st[2] == UNVERIFIED_INPUT and st[1] == UNVERIFIED_INPUT


def test_no_line_reads_clean_when_any_check_is_unverified(seeds):
    for rx, res in seeds.items():
        if any(c["status"] == UNVERIFIED_INPUT for c in res["checks"]):
            assert not any(s["state"] == CHECKED_NO_HIT for s in res["item_states"]), rx


def test_run_id_is_a_replay_key(conn, cfg):
    rail = Rail(conn, cfg)
    rx = {"rx_id": "T", "items": [{"item_no": 1, "written_product": "Dolo 650", "strength_as_written": "650 mg", "dose_frequency": "1-0-1"}]}
    a, b = rail.run(rx, AS_OF), rail.run(rx, AS_OF)
    assert a["run_id"] == b["run_id"] and a["run_id"].startswith("rail-")
    assert rail.run(rx, "2026-10-15")["run_id"] != a["run_id"]
    assert conn.execute("SELECT COUNT(*) FROM rail_run WHERE run_id=?", (a["run_id"],)).fetchone()[0] >= 2  # audit keeps every execution


def test_dup_uses_stated_population(conn, cfg):
    rail = Rail(conn, cfg)
    rx = {"rx_id": "T", "patient_population": "adult", "items": [
        {"item_no": 1, "written_product": "Dolo 650", "strength_as_written": "650 mg", "dose_frequency": "1-0-1"},
        {"item_no": 2, "written_product": "Sinarest Tablet", "dose_frequency": "1-0-1"}]}
    d = next(c for c in rail.run(rx, AS_OF)["checks"] if c["check_id"] == "DUP-001")
    assert d["evidence"]["hits"][0]["reference_ceiling"]["population_matches_input"] is True


def test_cumulative_breach_is_attributed_to_items(conn, cfg):
    rail = Rail(conn, cfg)
    rx = {"rx_id": "T", "patient_population": "adult", "items": [
        {"item_no": 1, "written_product": "Dolo 650", "strength_as_written": "650 mg", "dose_frequency": "1-1-1-1"},
        {"item_no": 2, "written_product": "Combiflam", "dose_frequency": "1-1-1"}]}   # 2600 + 975 = 3575 mg/day paracetamol
    res = rail.run(rx, AS_OF)
    cum = next(c for c in res["checks"] if c["check_id"] == "CUM-001")
    assert cum["status"] == HIT
    assert all("CUM-001" in s["note"] for s in res["item_states"])


def _fake_item(no, ingredient_norms):
    return {"input": {"item_no": no, "written_product": ingredient_norms[0]}, "review_item_id": None,
            "frequency": {"units_per_day": 1.0, "kind": "fixed", "raw": "OD", "duration_days": None},
            "resolution": {"status": "RESOLVED", "reason_code": None, "reason_detail": "", "method": "test", "confidence": 1.0, "candidates": [],
                           "product": {"product_id": f"T{no}", "batch_id": "t", "brand_name": ingredient_norms[0].title(), "dose_form": "Tablet", "strength_text": "",
                                       "ingredients": [{"norm": n, "ingredient": n.title(), "strength_value": 10.0, "strength_unit": "mg", "confidence": 1.0, "method": "test"} for n in ingredient_norms]}}}


def test_unsigned_class_mapping_never_fires_as_hit(conn, cfg, monkeypatch):
    # Sildenafil + Isosorbide Dinitrate matches the seed pair Sildenafil+Nitrates ONLY through the candidate-added,
    # unsigned 'Nitrates' class mapping -> must be PARTIAL_COVERAGE (named), never a HIT
    rail = Rail(conn, cfg)
    fresh = {"cdci": {"expired": False}, "interactions": {"expired": False}, "gazette": {"expired": False}}
    items = [_fake_item(1, ["sildenafil"]), _fake_item(2, ["isosorbide dinitrate"])]
    c = rail._check_interactions(items, fresh)
    assert c.status == PARTIAL_COVERAGE and c.evidence["unsigned_class_matches"]
    assert "sign-off" in c.summary
    monkeypatch.setenv("BRAHMO_RAIL__ALLOW_UNSIGNED_CLASS_MEMBERS", "true")
    c2 = Rail(conn, cfg)._check_interactions(items, fresh)
    assert c2.status == HIT and c2.evidence["hits"][0]["matched_via_class"] is True


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
