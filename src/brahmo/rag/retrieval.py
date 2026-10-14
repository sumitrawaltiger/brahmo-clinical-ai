"""Hybrid retrieval with metadata filters: BM25 rank + embedding rank fused by reciprocal rank fusion."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config import Config
from .embeddings import cosine
from .index import RagIndex, tokenize


def retrieve(
    index: RagIndex,
    question: str,
    cfg: Config,
    conditions: Optional[List[str]] = None,
    source_types: Optional[List[str]] = None,
    current_only: Optional[bool] = None,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    current_only = bool(cfg["retrieval.current_only_default"]) if current_only is None else current_only
    top_k = int(top_k or cfg["retrieval.top_k"])
    rrf_k = float(cfg["retrieval.rrf_k"])
    lw, sw = float(cfg["retrieval.lexical_weight"]), float(cfg["retrieval.semantic_weight"])

    idxs = [i for i, c in enumerate(index.chunks)
            if (not conditions or c["condition"] in conditions)
            and (not source_types or c["source_type"] in source_types)
            and (not current_only or c["is_current"])]
    if not idxs:
        return []
    q_tokens = tokenize(question)
    lex = index.bm25.scores(q_tokens)
    qv = index.embedder.embed_one(question)
    sem = [cosine(qv, index.vectors[i]) for i in range(len(index.chunks))]

    lex_rank = {i: r for r, i in enumerate(sorted(idxs, key=lambda i: -lex[i]), start=1)}
    sem_rank = {i: r for r, i in enumerate(sorted(idxs, key=lambda i: -sem[i]), start=1)}
    fused = []
    for i in idxs:
        score = lw / (rrf_k + lex_rank[i]) + sw / (rrf_k + sem_rank[i])
        fused.append((score, i))
    fused.sort(key=lambda t: -t[0])
    out = []
    for score, i in fused[:top_k]:
        c = dict(index.chunks[i])
        c["_scores"] = {"fused": round(score, 5), "bm25": round(lex[i], 4), "cosine": round(sem[i], 4), "lex_rank": lex_rank[i], "sem_rank": sem_rank[i]}
        out.append(c)
    return out
