"""Deterministic text normalization. One function, one key — used everywhere a match happens."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_WS = re.compile(r"\s+")


def norm_key(text: str) -> str:
    """Lower-case, strip accents, fold every non-alphanumeric run to a single space.

    'Telma-H 40' -> 'telma h 40'; 'NIMUPAR-P' -> 'nimupar p'; 'Iron (Ferrous Ascorbate)' -> 'iron ferrous ascorbate'
    """
    if text is None:
        return ""
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    t = _NON_ALNUM.sub(" ", t.lower())
    return _WS.sub(" ", t).strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
