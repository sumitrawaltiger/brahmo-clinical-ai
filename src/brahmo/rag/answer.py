"""Grounded answering.

Two modes, same output contract and same guards:
  extractive (default): decision units are returned verbatim, each with its citation. Zero generation.
  llm: Claude composes a short synthesis from the retrieved units, emitting claims with chunk ids; every claim is
       re-verified (citation exists, every number appears in cited text) before it is shown; failures are dropped
       and the answer abstains if nothing survives.
Rules enforced here: structured facts route to Module A; absent conditions abstain; dose text is quoted, never
computed; local protocol is labelled as the clinic's; superseded editions are shown separately, never merged.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from ..config import Config, load_config
from ..db import utcnow_iso
from ..normalize.text import sha256_text
from .analysis import analyze
from .guard import verify_claims
from .index import RagIndex, load_index, tokenize
from .retrieval import retrieve

ANSWERER_VERSION = "answerer-1.0.0"


def _cite(c: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "chunk_id": c["chunk_id"], "source_type": c["source_type"], "document": c["code"], "title": c["title"], "version": c["version"],
        "effective_date": c["effective_date"], "section": c["section"], "page": c["page"], "anchor": c["anchor"], "file": c["file_name"],
        "file_sha256": c["file_sha256"][:12], "organization": c.get("organization"), "is_current": c["is_current"], "superseded_by": c.get("superseded_by"),
        "label": ("CLINIC PROTOCOL — " + str(c.get("organization")) if c["source_type"] == "local_protocol" else "NATIONAL STW"),
    }


def _label_for(c: Dict[str, Any]) -> str:
    if c["source_type"] == "local_protocol":
        return f"CLINIC PROTOCOL ({c.get('organization')}, {c['code']} v{c['version']}, approved {c['effective_date']}) — organization-level knowledge, not national guidance"
    return f"NATIONAL STW {c['code']} v{c['version']} (effective {c['effective_date']}) — {c['title']}"


def _stem(t: str) -> str:
    """Tiny suffix stemmer for overlap counting only (avoided->avoid, nsaids->nsaid, doses->dose)."""
    if len(t) > 4:
        for suf in ("ing", "ies", "ed", "es", "s"):
            if t.endswith(suf) and not t.endswith("ss"):
                return t[: -len(suf)] + ("y" if suf == "ies" else "")
    return t


def _lexical_overlap(question: str, chunk: Dict[str, Any]) -> int:
    q = {_stem(t) for t in tokenize(question)} - _STOP
    t = {_stem(x) for x in tokenize(f"{chunk['section']} {chunk['text']}")}
    return len(q & t)


_STOP = set("what is the a an of for in and or to at which with that this are does do how after each per when its it as by on from be must should can".split())


def _superseded_editions(index: RagIndex, codes: List[str], question: str) -> List[Dict[str, Any]]:
    out = []
    for c in index.chunks:
        if c["code"] in codes and not c["is_current"] and c["unit_type"] == "recommendation" and _lexical_overlap(question, c) > 0:
            out.append({"text": c["text"], "citation": _cite(c),
                        "note": f"archived edition {c['code']} v{c['version']} (effective {c['effective_date']}), superseded by {c['superseded_by']}; shown for transparency, not merged into the answer"})
    return out


def answer_question(conn: Optional[sqlite3.Connection], question: str, cfg: Optional[Config] = None, mode: Optional[str] = None,
                    index: Optional[RagIndex] = None, as_of: Optional[str] = None) -> Dict[str, Any]:
    cfg = cfg or load_config()
    mode = mode or cfg["answering.mode"]
    index = index or load_index(cfg)
    analysis = analyze(question, cfg)
    # replay key: same question + index + mode + as-of => same run_id (audit rows carry their own uuid)
    run_id = "qa-" + sha256_text(json.dumps({"q": question, "index": index.version, "mode": mode, "as_of": as_of}, sort_keys=True))[:16]
    base: Dict[str, Any] = {
        "run_id": run_id, "question": question, "as_of": as_of, "analysis": analysis, "mode": mode,
        "versions": {"index_version": index.version, "answerer_version": ANSWERER_VERSION, "embedding_model": index.meta["embedding_model"],
                     "prompt_version": None, "model": None},
    }

    # 1. structured facts -> Module A (never retrieval)
    if analysis["route"] == "module_a_structured":
        from .structured import answer_structured

        out = dict(base, route="module_a_structured", **answer_structured(conn, question, cfg, as_of))
        _audit(conn, out)
        return out

    # 2. condition the corpus does not cover -> clean abstention before retrieval
    if analysis["route"] == "abstain_no_corpus":
        covered = sorted({c["condition"] for c in index.chunks if c["is_current"]})
        out = dict(base, route="abstain_no_corpus", answer_type="abstain", claims=[],
                   abstention={"reason": f"the provided corpus has no workflow for {', '.join(analysis['conditions_absent_from_corpus'])}",
                               "missing": f"a national STW page or clinic protocol covering {', '.join(analysis['conditions_absent_from_corpus'])}",
                               "corpus_covers": covered},
                   retrieval={"considered": []})
        _audit(conn, out)
        return out

    # 3. retrieval with metadata filters
    conds = analysis["conditions_in_corpus"] or None
    wants_local = analysis["markers"]["local_protocol"]
    # Answers always come from CURRENT editions. Superseded editions are surfaced separately (never merged) whenever
    # a cited document has an archived edition in the corpus — asking about "editions" does not change what is current.
    current_only = True
    candidates = retrieve(index, question, cfg, conditions=conds, current_only=current_only)
    considered = [dict(_cite(c), scores=c["_scores"], text=c["text"]) for c in candidates]

    # units that actually address the question: lexical overlap with the question beyond stop words, ordered by
    # overlap then fused rank; the top semantic unit is kept as a safety net when wording differs entirely
    scored = [(_lexical_overlap(question, c), c) for c in candidates]
    supporting = [c for ov, c in sorted(scored, key=lambda t: (-t[0], -t[1]["_scores"]["fused"])) if ov >= 1]
    for ov, c in scored:
        if ov == 0 and c["_scores"]["sem_rank"] <= 1 and c not in supporting:
            supporting.append(c)
    if analysis["markers"]["dose"]:
        dose_units = [c for c in supporting if any(u in c["text"].lower() for u in ("mg", "ml", "mcg", "dose"))]
        supporting = dose_units or supporting
    supporting = supporting[: int(cfg["answering.max_claims"])]

    national = [c for c in supporting if c["source_type"] == "national_stw"]
    local = [c for c in supporting if c["source_type"] == "local_protocol"]
    notes: List[str] = []
    if analysis["markers"]["dose"] or analysis["markers"]["patient_specific"]:
        notes.append("Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted.")
    if analysis["markers"]["pregnancy"] and not any(c["population"] == "pregnancy" for c in supporting):
        notes.append("The question mentions pregnancy but no pregnancy-specific unit was retrieved; verify population applicability.")

    # 4. national-vs-local comparison when the clinic protocol is in play
    comparison = None
    if local or wants_local:
        nat_cands = retrieve(index, question, cfg, conditions=conds, source_types=["national_stw"], current_only=True)
        nat_support = [c for c in nat_cands if c["condition"] in (conds or []) and _lexical_overlap(question, c) >= 1]
        if nat_support:
            comparison = {"national_units": [{"text": c["text"], "citation": _cite(c)} for c in nat_support[:4]],
                          "statement": "The national workflow pack contains units on this condition; they are shown alongside the clinic protocol. Where they differ, both are shown and neither is merged."}
        else:
            nearest = retrieve(index, question, cfg, source_types=["national_stw"], current_only=True, top_k=3)
            comparison = {"national_units": [],
                          "statement": ("The provided national STW pack contains no workflow for "
                                        f"{', '.join((conds or ['this condition'])).replace('_', ' ')}. It therefore neither confirms nor contradicts the clinic protocol; "
                                        "the clinic protocol stands as organization-level guidance only."),
                          "nearest_national_pages": sorted({f"{c['code']} v{c['version']} ({c['title']}) — different condition, not applicable" for c in nearest})}

    if not supporting:
        out = dict(base, route="retrieval", answer_type="abstain", claims=[], notes=notes,
                   abstention={"reason": "no decision unit in the corpus addresses the question's terms",
                               "missing": f"a unit about: {question}", "conditions_searched": conds or "all"},
                   retrieval={"considered": considered}, comparison=comparison)
        _audit(conn, out)
        return out

    # 5. compose
    if mode == "llm":
        composed = _compose_llm(question, supporting, cfg)
        base["versions"]["prompt_version"] = composed["prompt_version"]
        base["versions"]["model"] = composed["model"]
        chunks_by_id = {c["chunk_id"]: c for c in supporting}
        verified = verify_claims(composed["claims"], chunks_by_id)
        claims = [{"text": c["text"], "citations": [_cite(chunks_by_id[i]) for i in c["citations"]], "label": _label_for(chunks_by_id[c["citations"][0]]), "verbatim": False}
                  for c in verified["ok_claims"]]
        if composed.get("error"):
            notes.append(f"LLM composition unavailable ({composed['error']}); fell back to extractive units")
        if not claims:
            # the model produced nothing verifiable: show verbatim units instead of guessing
            claims = _extractive_claims(supporting)
            notes.append("LLM claims failed verification; verbatim units shown instead")
        guard_report = {"dropped": verified["dropped"], "model_abstained": composed.get("abstain_reason")}
    else:
        claims = _extractive_claims(supporting)
        guard_report = {"dropped": [], "model_abstained": None}

    labels = sorted({c["label"] for c in claims})
    out = dict(base, route="retrieval", answer_type="answer", claims=claims, labels=labels, notes=notes,
               superseded_editions=_superseded_editions(index, sorted({c["code"] for c in national}), question),
               comparison=comparison, guard=guard_report, retrieval={"considered": considered, "filters": {"conditions": conds, "current_only": current_only}})
    _audit(conn, out)
    return out


def _extractive_claims(supporting: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"text": c["text"], "citations": [_cite(c)], "label": _label_for(c), "verbatim": True} for c in supporting]


def _compose_llm(question: str, units: List[Dict[str, Any]], cfg: Config) -> Dict[str, Any]:
    prompt_path = cfg.path("answering.prompt_path")
    template = prompt_path.read_text(encoding="utf-8")
    prompt_version = sha256_text(template)[:12]
    model = str(cfg["answering.llm_model"])
    units_block = "\n".join(f"[{c['chunk_id']}] ({c['code']} v{c['version']}, {c['section']}, {'CLINIC PROTOCOL' if c['source_type']=='local_protocol' else 'NATIONAL STW'}) {c['text']}" for c in units)
    prompt = template.replace("{{QUESTION}}", question).replace("{{UNITS}}", units_block)
    try:
        import anthropic  # optional dependency

        client = anthropic.Anthropic()
        msg = client.messages.create(model=model, max_tokens=int(cfg["answering.llm_max_tokens"]), messages=[{"role": "user", "content": prompt}])
        text = "".join(getattr(b, "text", "") for b in msg.content)
        start, end = text.find("{"), text.rfind("}")
        data = json.loads(text[start:end + 1])
        claims = [{"text": c.get("text", ""), "citations": list(c.get("chunk_ids", []))} for c in data.get("claims", [])]
        return {"claims": claims, "abstain_reason": data.get("abstain_reason"), "prompt_version": prompt_version, "model": model}
    except Exception as e:  # no key, no package, bad JSON: visible fallback, never a silent one
        return {"claims": [], "abstain_reason": None, "prompt_version": prompt_version, "model": model, "error": f"{type(e).__name__}: {e}"[:200]}


def _audit(conn: Optional[sqlite3.Connection], out: Dict[str, Any]) -> None:
    """Write the audit row. A failure raises (law 11): an answer whose audit record could not be written must not
    look like a normal answer. conn=None means the caller explicitly runs without a database (e.g. corpus-only tools)."""
    if conn is None:
        return
    conn.execute(
        "INSERT INTO qa_run(audit_id, run_id, question, as_of, index_version, prompt_version, model, mode, output_json, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), out["run_id"], out["question"], out.get("as_of"), out["versions"]["index_version"], out["versions"].get("prompt_version"),
         out["versions"].get("model"), out["mode"], json.dumps(out, ensure_ascii=False, default=str), utcnow_iso()),
    )
    conn.commit()
