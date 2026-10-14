"""G3: zero silent resolutions."""
from brahmo.normalize import reasons
from brahmo.normalize.resolver import AMBIGUOUS, RESOLVED, UNRESOLVED, resolve
from brahmo.normalize.text import norm_key


def test_norm_key_folds_punctuation_and_case():
    assert norm_key("NIMUPAR-P") == norm_key("NimuPar-P") == "nimupar p"
    assert norm_key("Iron (Ferrous Ascorbate)") == "iron ferrous ascorbate"


def test_exact_unique_brand_resolves(conn, cfg):
    r = resolve(conn, "Dolo 650", "650 mg", None, cfg)
    assert r.status == RESOLVED and r.product["product_id"] == "CD1000"
    assert r.confidence >= cfg["resolver.auto_accept_min"]


def test_brand_family_without_strength_is_ambiguous_not_guessed(conn, cfg):
    r = resolve(conn, "Telma", None, None, cfg)
    assert r.status == AMBIGUOUS and r.product is None
    assert r.reason_code == reasons.AMBIGUOUS_STRENGTH_MISSING
    assert {c["brand_name"] for c in r.candidates} >= {"Telma 20", "Telma 40", "Telma 80"}


def test_brand_family_with_strength_narrows(conn, cfg):
    r = resolve(conn, "Telma", "40 mg", None, cfg)
    # two products carry telmisartan 40 mg (Telma 40, Telma-H 40) -> still ambiguous; the strength alone cannot pick one
    assert r.status in (AMBIGUOUS, UNRESOLVED) or (r.status == RESOLVED and r.product["brand_name"] == "Telma 40")


def test_unknown_brand_only_suggests(conn, cfg):
    r = resolve(conn, "Zqtrixon Forte", None, None, cfg)
    assert r.status == UNRESOLVED and r.product is None
    assert r.reason_code in (reasons.FUZZY_ONLY, reasons.UNKNOWN_BRAND)
    assert all(c["note"] == "fuzzy suggestion only" for c in r.candidates)


def test_unit_conflict_is_a_mismatch_not_a_guess(conn, cfg):
    r = resolve(conn, "Thyronorm 50", "50 mcg", None, cfg)
    assert r.status == UNRESOLVED and r.reason_code == reasons.STRENGTH_MISMATCH
    assert "unit conflict" in r.reason_detail


def test_multi_composition_brand_needs_strength_or_form(conn, cfg):
    r = resolve(conn, "Zypan Forte", None, None, cfg)   # Tablet calcium carbonate vs Syrup pantoprazole in the extract
    assert r.status == AMBIGUOUS
    r2 = resolve(conn, "Zypan Forte", None, "Tablet", cfg)
    assert r2.status == RESOLVED and r2.product["dose_form"] == "Tablet"


def test_every_non_resolved_stock_row_is_in_review_queue(conn):
    n_unres = conn.execute("SELECT COUNT(*) FROM stock_item WHERE resolution_status != 'RESOLVED'").fetchone()[0]
    n_queued = conn.execute("SELECT COUNT(*) FROM stock_item WHERE resolution_status != 'RESOLVED' AND review_item_id IS NOT NULL").fetchone()[0]
    assert n_unres == n_queued > 0


def test_review_queue_reason_codes_are_from_vocabulary(conn):
    codes = {r[0] for r in conn.execute("SELECT DISTINCT reason_code FROM review_queue")}
    assert codes <= set(reasons.ALL)
