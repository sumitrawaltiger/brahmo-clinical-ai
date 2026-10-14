"""Dataset loaders. Each loader: registers a load_batch (file sha256 + declared version), inserts rows,
and routes every uncertainty to the review queue. Loaders are idempotent per (dataset, sha256)."""
