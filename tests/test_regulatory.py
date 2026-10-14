"""Event-sourced status: supersession chains, stays, form qualifiers, pending events, conflicts."""
from brahmo.regulatory.status import derive_status, load_events, status_for_product_text


def _status(conn, brand, as_of):
    out = status_for_product_text(conn, brand, as_of)
    assert "regulatory" in out, out
    return out["regulatory"]


def test_nimesulide_paracetamol_chain_today(conn):
    r = _status(conn, "NimuPar-P", "2026-10-14")
    assert r["status"] == "PROHIBITED"
    assert r["governing_events"][0]["notification_id"] == "GSR 411(E)"
    assert r["governing_events"][0]["effective_date"] == "2023-06-15"
    chain = [e["event_id"] for e in r["supersession_chains"][0]]
    assert chain == ["EV003", "EV002", "EV001"]


def test_stay_period_is_visible_not_hidden(conn):
    r = _status(conn, "NimuPar-P", "2020-01-01")
    assert r["status"] == "STAYED"
    assert r["governing_events"][0]["action"] == "STAY_GRANTED"


def test_before_any_event_status_is_none_with_pending_listed(conn):
    r = _status(conn, "NimuPar-P", "2018-09-10")   # published 2018-09-07, effective 2018-09-12
    assert r["status"] == "NONE"
    assert any(p["event_id"] == "EV001" for p in r["pending_events"])


def test_ingredient_level_prohibition_hits_fdc_containing_it(conn):
    r = _status(conn, "Ranidom", "2026-10-14")
    assert r["status"] == "PROHIBITED"
    assert r["governing_events"][0]["notification_id"] == "GSR 1012(E)"
    assert [e["event_id"] for e in r["superseded_events"]] == ["EV005"]


def test_restriction_before_prohibition(conn):
    r = _status(conn, "Ranidom", "2024-12-01")
    assert r["status"] == "RESTRICTED"


def test_form_qualifier_excludes_adult_tablet(conn):
    r = _status(conn, "Combiflam", "2026-10-14")
    assert r["status"] == "NONE"
    assert any(e["event_id"] == "EV012" for e in r["excluded_by_qualifier"])


def test_conflict_is_reported_not_resolved():
    base = {"notification_id": "X", "date_published": "2020-01-01", "target_description": "t", "target_type": "FDC", "batch_id": "b",
            "supersedes_event_id": None, "note": "", "parse_confidence": 1.0}
    e1 = dict(base, event_id="A", action="PROHIBITED", effective_date="2020-02-01")
    e2 = dict(base, event_id="B", action="STAY_GRANTED", effective_date="2020-03-01")   # does NOT supersede A
    r = derive_status([e1, e2], [e1, e2], "2021-01-01")
    assert r["status"] == "CONFLICT" and r["conflict"]


def test_events_loaded_with_targets(conn):
    evs = load_events(conn)
    assert len(evs) == 12
    assert all("ingredient_set" in e for e in evs)


def test_revoking_a_stay_restores_the_prohibition():
    base = {"notification_id": "X", "date_published": "2018-01-01", "target_description": "t", "target_type": "FDC", "batch_id": "b", "note": "", "parse_confidence": 1.0}
    p = dict(base, event_id="P", action="PROHIBITED", effective_date="2018-02-01", supersedes_event_id=None)
    s = dict(base, event_id="S", action="STAY_GRANTED", effective_date="2019-02-01", supersedes_event_id="P")
    r = dict(base, event_id="R", action="REVOKED", effective_date="2020-02-01", supersedes_event_id="S")
    assert derive_status([p, s], [p, s, r], "2019-06-01")["status"] == "STAYED"
    out = derive_status([p, s, r], [p, s, r], "2020-06-01")
    assert out["status"] == "PROHIBITED" and out["governing_events"][0]["event_id"] == "P"
    assert [e["event_id"] for e in out["restored_by_revocation"]] == ["P"]


def test_lifting_a_prohibition_leaves_nothing_in_force():
    base = {"notification_id": "X", "date_published": "2018-01-01", "target_description": "t", "target_type": "FDC", "batch_id": "b", "note": "", "parse_confidence": 1.0}
    p = dict(base, event_id="P", action="PROHIBITED", effective_date="2018-02-01", supersedes_event_id=None)
    l = dict(base, event_id="L", action="LIFTED", effective_date="2020-02-01", supersedes_event_id="P")
    out = derive_status([p, l], [p, l], "2020-06-01")
    assert out["status"] == "NONE" and out["governing_events"] == []
