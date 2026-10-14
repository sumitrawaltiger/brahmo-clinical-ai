"""Pluggable embedders. Default is a deterministic, dependency-free hashed character n-gram + word embedding so the
semantic leg runs offline on a fresh machine. A sentence-transformers backend is available via config when the
optional extra is installed. The provider and model name are recorded in the index version and in every answer.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import List, Sequence

from ..config import Config

_WORD_RE = re.compile(r"[a-z0-9]+")


class LocalHashedEmbedder:
    provider = "local_hashed"

    def __init__(self, dims: int, model: str):
        self.dims = dims
        self.model = model

    def _feats(self, text: str) -> List[str]:
        words = _WORD_RE.findall(text.lower())
        feats: List[str] = []
        for w in words:
            feats.append("w:" + w)
            padded = f"#{w}#"
            for n in (3, 4, 5):
                for i in range(max(0, len(padded) - n + 1)):
                    feats.append(f"c{n}:" + padded[i:i + n])
        for a, b in zip(words, words[1:]):
            feats.append("b:" + a + "_" + b)
        return feats

    def embed_one(self, text: str) -> List[float]:
        v = [0.0] * self.dims
        for f in self._feats(text):
            h = hashlib.blake2b(f.encode("utf-8"), digest_size=8).digest()
            idx = int.from_bytes(h[:4], "little") % self.dims
            sign = 1.0 if (h[4] & 1) else -1.0
            weight = 1.0 if f.startswith("w:") else (0.5 if f.startswith("b:") else 0.35)
            v[idx] += sign * weight
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        return [self.embed_one(t) for t in texts]


class SentenceTransformersEmbedder:
    provider = "sentence_transformers"

    def __init__(self, model: str):
        from sentence_transformers import SentenceTransformer  # optional extra

        self.model = model
        self._m = SentenceTransformer(model)

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        return [list(map(float, v)) for v in self._m.encode(list(texts), normalize_embeddings=True)]

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]


def get_embedder(cfg: Config):
    provider = cfg["retrieval.embedding_provider"]
    model = cfg["retrieval.embedding_model"]
    if provider == "local_hashed":
        return LocalHashedEmbedder(int(cfg["retrieval.embedding_dims"]), model)
    if provider == "sentence_transformers":
        return SentenceTransformersEmbedder(model)
    raise ValueError(f"unknown embedding provider {provider!r}")


def cosine(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
