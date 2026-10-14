"""Module B: decision-unit chunking, retrieval filters, grounded answering, abstention, G6 numeric guard."""
from brahmo.rag.answer import answer_question
from brahmo.rag.evaluate import run_eval
from brahmo.rag.guard import uncited_numbers, verify_claims
from brahmo.rag.retrieval import retrieve


def test_chunks_are_decision_units_with_metadata(index):
    assert len(index.chunks) > 60
    for c in index.chunks:
        assert c["code"] and c["version"] and c["effective_date"] and c["section"] and c["anchor"] and c["file_sha256"]
        assert c["unit_type"] in {"assessment", "red_flag_referral", "recommendation", "contraindication", "target", "monitoring", "status_note", "other"}
        assert len(c["text"]) < 400   # never a blind slice of the page


def test_superseded_edition_marked(index):
    old = [c for c in index.chunks if c["code"] == "STW-GP-02" and c["version"] == "2021.1"]
    assert old and all(not c["is_current"] and c["superseded_by"] == "STW-GP-02 v2025.2" for c in old)


def test_retrieval_respects_filters(index, cfg):
    hits = retrieve(index, "first-line hypertension", cfg, conditions=["hypertension"], current_only=True)
    assert hits and all(h["condition"] == "hypertension" and h["is_current"] for h in hits)
    old = retrieve(index, "atenolol", cfg, conditions=["hypertension"], current_only=False)
    assert any(h["version"] == "2021.1" for h in old)


def test_abstains_on_condition_outside_corpus(conn, cfg, index):
    out = answer_question(conn, "What is the standard drug regimen for newly diagnosed pulmonary tuberculosis?", cfg, index=index)
    assert out["answer_type"] == "abstain" and out["route"] == "abstain_no_corpus"
    assert "tuberculosis" in out["abstention"]["reason"]


def test_dose_question_quotes_text_and_adds_note(conn, cfg, index):
    out = answer_question(conn, "A 6-year-old with non-severe community pneumonia: what is the amoxicillin dose exactly as the workflow states it?", cfg, index=index)
    assert out["answer_type"] == "answer"
    assert any("40 mg/kg/day" in c["text"] for c in out["claims"])
    assert any("No dose has been calculated" in n for n in out["notes"])
    assert all(c["verbatim"] for c in out["claims"])


def test_current_edition_answers_and_archive_is_separate(conn, cfg, index):
    out = answer_question(conn, "What is the first-line initial drug therapy for newly diagnosed adult hypertension?", cfg, index=index)
    assert all(c["citations"][0]["version"] == "2025.2" for c in out["claims"])
    assert out["superseded_editions"] and out["superseded_editions"][0]["citation"]["version"] == "2021.1"
    assert not any("Atenolol" in c["text"] for c in out["claims"])


def test_local_protocol_is_labelled_and_compared(conn, cfg, index):
    out = answer_question(conn, "Per the clinic's own protocol, when are empirical antibiotics started in adult acute undifferentiated fever — and does the national workflow pack say the same?", cfg, index=index)
    assert any("CLINIC PROTOCOL" in c["label"] for c in out["claims"])
    assert out["comparison"] and out["comparison"]["national_units"] == []
    assert "no workflow" in out["comparison"]["statement"]


def test_structured_question_routes_to_module_a(conn, cfg, index):
    out = answer_question(conn, "Is NimuPar-P banned?", cfg, index=index, as_of="2026-10-14")
    assert out["route"] == "module_a_structured" and out["answer_type"] == "answer"
    assert any("GSR 411(E)" in c["text"] for c in out["claims"])


def test_numeric_guard():
    assert uncited_numbers("give 500 mg twice daily for 5 days", ["Amoxicillin 500 mg three times daily for 5 days"]) == []
    assert uncited_numbers("give 750 mg", ["Amoxicillin 500 mg"]) == ["750"]
    v = verify_claims([{"text": "x 750 mg", "citations": ["a"]}], {"a": {"text": "500 mg"}})
    assert v["ok_claims"] == [] and v["dropped"]


def test_mini_eval_has_no_wrong_and_no_uncited_numbers(conn, cfg, index):
    summary = run_eval(conn, cfg)
    assert summary["tally"]["wrong"] == 0
    assert summary["uncited_numbers_total"] == 0
    assert summary["tally"]["correct"] >= 9


def test_condition_matching_is_word_bounded(conn, cfg, index):
    # 'uti' must not fire inside 'routine', 'ors' not inside 'factors'
    out = answer_question(conn, "What is the routine treatment for malaria?", cfg, index=index)
    assert out["answer_type"] == "abstain" and out["route"] == "abstain_no_corpus"
    out = answer_question(conn, "What are the risk factors for typhoid fever?", cfg, index=index)
    assert out["answer_type"] == "abstain"
    out = answer_question(conn, "ORS volumes for a child with diarrhoea?", cfg, index=index)
    assert out["answer_type"] == "answer" and out["claims"][0]["citations"][0]["document"] == "STW-PED-03"


def test_qa_run_id_is_a_replay_key(conn, cfg, index):
    q = "Which analgesic class must be avoided in suspected dengue, and why?"
    a = answer_question(conn, q, cfg, index=index, as_of="2026-10-14")
    b = answer_question(conn, q, cfg, index=index, as_of="2026-10-14")
    assert a["run_id"] == b["run_id"] and a["run_id"].startswith("qa-")


def test_index_rebuilds_when_a_corpus_file_changes(cfg, tmp_path, monkeypatch):
    import shutil
    from brahmo.rag.index import load_index
    corpus = tmp_path / "corpus"
    shutil.copytree(cfg.path("corpus.dir"), corpus)
    monkeypatch.setenv("BRAHMO_CORPUS__DIR", str(corpus))
    monkeypatch.setenv("BRAHMO_CORPUS__INDEX_PATH", str(tmp_path / "idx.json"))
    from brahmo.config import load_config
    c2 = load_config(fresh=True)
    v1 = load_index(c2).version
    (corpus / "STW_GYN_03_PCOS_Initial.pdf").unlink()          # the corpus changed on disk; nothing else did
    idx2 = load_index(c2)
    assert idx2.version != v1 and not any(c["code"] == "STW-GYN-03" for c in idx2.chunks)
