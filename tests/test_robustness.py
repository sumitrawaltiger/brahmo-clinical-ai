"""Stretch/robustness: messy spellings, paraphrased questions, and the freshness mechanism."""
from brahmo.normalize.evaluate import run_resolver_eval
from brahmo.normalize.resolver import strip_form_tokens
from brahmo.rag.evaluate import run_eval


def test_strip_form_tokens():
    assert strip_form_tokens("Tab. Dolo 650") == ("dolo 650", "Tablet")
    assert strip_form_tokens("T. Azee 500") == ("azee 500", "Tablet")
    assert strip_form_tokens("Combiflam tab") == ("combiflam", "Tablet")
    assert strip_form_tokens("Syp Calpol 250") == ("calpol 250", "Syrup")
    assert strip_form_tokens("Inj Azee") == ("azee", "Injection")
    assert strip_form_tokens("Dolo 650") == ("dolo 650", None)
    assert strip_form_tokens("Tab") == ("tab", None)          # a lone form token is not a brand


def test_messy_spellings_never_resolve_wrongly(conn, cfg):
    out = run_resolver_eval(conn, cfg)
    assert out["tally"]["wrong"] == 0
    assert out["tally"]["correct"] >= 40


def test_paraphrase_questions_never_wrong(conn, cfg, index):
    out = run_eval(conn, cfg, as_of="2026-10-14", question_set="paraphrase")
    assert out["tally"]["wrong"] == 0
    assert out["uncited_numbers_total"] == 0
    assert out["tally"]["correct"] >= 30


def test_freshness_demo_flips_status_and_replays(cfg, tmp_path, monkeypatch):
    monkeypatch.setenv("BRAHMO_FRESHNESS_DEMO__DB_PATH", str(tmp_path / "fresh.sqlite"))
    from brahmo.config import load_config
    from brahmo.regulatory.freshness_demo import run_demo

    rep = run_demo(load_config(fresh=True), as_of="2026-10-14", out_dir=str(tmp_path))
    assert rep["status_before"]["status"] == "NONE"
    assert rep["status_after"]["status"] == "RESTRICTED"
    assert rep["status_after_but_as_of_before_effective_date"]["status"] == "NONE"      # published, not yet effective
    assert rep["replay_against_v1_after_v2_loaded"]["status"] == "NONE"                 # old batch still answers as before
    assert rep["register_v1_batch"] != rep["register_v2_batch"]
    assert rep["rail_fdc_before"]["status"] == "CHECKED_NO_HIT" and rep["rail_fdc_after"]["status"] == "HIT"
    assert rep["rail_fdc_after"]["data_versions"]["gazette"] == rep["register_v2_batch"]
