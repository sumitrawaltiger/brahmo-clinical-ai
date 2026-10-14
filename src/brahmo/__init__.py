"""BRAHMO clinical AI — assessment build.

Package layout:
    config      -> single config loader (settings.json + env overrides); no constants live in code
    db          -> SQLite connection + numbered migration runner
    ingest/     -> loaders for every provided dataset; every row gets a load_batch
    normalize/  -> text normalization, brand resolution, review queue
    regulatory/ -> event-sourced status derivation (no booleans)
    rail/       -> deterministic safety checks with the 8-state contract (no LLM anywhere here)
    rag/        -> STW chunking, hybrid retrieval, grounded answering, mini-eval
    trace/      -> Module C end-to-end trace
"""

__version__ = "0.1.0"
