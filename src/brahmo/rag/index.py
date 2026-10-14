"""Hybrid index: BM25 (lexical) + embeddings (semantic) over decision units, persisted with a version fingerprint."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ..config import Config, load_config
from .chunker import CHUNKER_VERSION, Chunk, chunk_corpus, corpus_fingerprint
from .embeddings import get_embedder

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")
INDEX_FORMAT = "rag-index-1.0"


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


def unit_index_text(c: Dict[str, Any]) -> str:
    """What gets indexed for a unit: section + text + title + condition words, so a question phrased by section
    ('red flags', 'first-line') or by condition reaches the right unit."""
    return f"{c['section']}: {c['text']} [{c['title']}; {c['condition'].replace('_', ' ')}]"


class BM25:
    def __init__(self, docs: Sequence[List[str]], k1: float, b: float):
        self.k1, self.b = k1, b
        self.docs = [Counter(d) for d in docs]
        self.lens = [len(d) for d in docs]
        self.avgdl = (sum(self.lens) / len(self.lens)) if self.lens else 0.0
        df: Counter = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def score(self, query: List[str], i: int) -> float:
        d, dl = self.docs[i], self.lens[i]
        s = 0.0
        for t in query:
            if t not in d:
                continue
            tf = d[t]
            s += self.idf.get(t, 0.0) * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1)))
        return s

    def scores(self, query: List[str]) -> List[float]:
        return [self.score(query, i) for i in range(len(self.docs))]


class RagIndex:
    def __init__(self, data: Dict[str, Any], cfg: Config):
        self.cfg = cfg
        self.meta = data["meta"]
        self.chunks: List[Dict[str, Any]] = data["chunks"]
        self.vectors: List[List[float]] = data["vectors"]
        self.embedder = get_embedder(cfg)
        self.bm25 = BM25([tokenize(unit_index_text(c)) for c in self.chunks], float(cfg["retrieval.bm25_k1"]), float(cfg["retrieval.bm25_b"]))

    @property
    def version(self) -> str:
        return self.meta["index_version"]

    def by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        return next((c for c in self.chunks if c["chunk_id"] == chunk_id), None)


def build_index(cfg: Optional[Config] = None) -> Dict[str, Any]:
    cfg = cfg or load_config()
    chunks = chunk_corpus(cfg)
    emb = get_embedder(cfg)
    dicts = [c.to_dict() for c in chunks]
    vectors = emb.embed([unit_index_text(c) for c in dicts])
    fp = corpus_fingerprint(chunks)
    meta = {
        "format": INDEX_FORMAT,
        "chunker_version": CHUNKER_VERSION,
        "embedding_provider": emb.provider,
        "embedding_model": emb.model,
        "corpus_fingerprint": fp,
        "corpus_files": corpus_file_shas(cfg),
        "index_version": f"{INDEX_FORMAT}:{CHUNKER_VERSION}:{emb.model}:{fp}",
        "chunk_count": len(chunks),
        "documents": sorted({f"{c.code} v{c.version} ({'current' if c.is_current else 'superseded by ' + str(c.superseded_by)})" for c in chunks}),
    }
    out = cfg.path("corpus.index_path")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"meta": meta, "chunks": dicts, "vectors": vectors}, ensure_ascii=False), encoding="utf-8")
    return dict(meta, path=str(out))


def load_index(cfg: Optional[Config] = None, build_if_missing: bool = True) -> RagIndex:
    cfg = cfg or load_config()
    path = cfg.path("corpus.index_path")
    if not path.exists():
        if not build_if_missing:
            raise FileNotFoundError(path)
        build_index(cfg)
    data = json.loads(path.read_text(encoding="utf-8"))
    # no silent upgrades: an index built with a different chunker/embedder OR from different corpus files is rebuilt,
    # and the resulting index version is visible in every answer
    emb = get_embedder(cfg)
    stale = (data["meta"].get("chunker_version") != CHUNKER_VERSION
             or data["meta"].get("embedding_model") != emb.model
             or data["meta"].get("corpus_files") != corpus_file_shas(cfg))
    if stale:
        build_index(cfg)
        data = json.loads(path.read_text(encoding="utf-8"))
    return RagIndex(data, cfg)


def corpus_file_shas(cfg: Config) -> Dict[str, str]:
    from ..normalize.text import sha256_file

    files = sorted(cfg.path("corpus.dir").glob(cfg["corpus.stw_glob"])) + [cfg.resolve_path(p) for p in cfg["corpus.local_protocols"]]
    return {p.name: sha256_file(p) for p in files if p.exists()}
