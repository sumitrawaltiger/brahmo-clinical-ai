"""Shared fixtures: a throw-away SQLite database built from the real data pack (fast: ~2 s), and the RAG index."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def cfg(tmp_path_factory):
    os.environ["BRAHMO_ROOT"] = str(ROOT)
    tmp = tmp_path_factory.mktemp("brahmo")
    os.environ["BRAHMO_DB__PATH"] = str(tmp / "test.sqlite")
    os.environ["BRAHMO_CORPUS__INDEX_PATH"] = str(tmp / "rag_index.json")
    os.environ["BRAHMO_TRACE__OUTPUT_DIR"] = str(tmp / "outputs")
    from brahmo.config import load_config

    return load_config(fresh=True)


@pytest.fixture(scope="session")
def conn(cfg):
    from brahmo.db import connect, migrate
    from brahmo.ingest.run_all import run_all

    c = connect(cfg)
    migrate(c, cfg)
    run_all(c, cfg)
    return c


@pytest.fixture(scope="session")
def index(cfg):
    from brahmo.rag.index import build_index, load_index

    build_index(cfg)
    return load_index(cfg)
