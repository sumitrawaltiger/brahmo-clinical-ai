"""G5: every data row traceable to a load batch with file hash + declared version."""


def test_every_dataset_has_a_batch(conn):
    datasets = {r[0] for r in conn.execute("SELECT dataset FROM load_batch")}
    assert {"cdci", "nlem", "jan_aushadhi", "gazette", "interactions", "pharmacy_stock"} <= datasets


def test_batches_carry_hash_and_version(conn):
    for r in conn.execute("SELECT batch_id, file_sha256, source_version, row_count FROM load_batch"):
        assert len(r["file_sha256"]) == 64
        assert r["source_version"]
        assert r["row_count"] > 0


def test_every_product_row_points_at_a_batch(conn):
    orphans = conn.execute(
        "SELECT COUNT(*) FROM product p LEFT JOIN load_batch b ON b.batch_id = p.batch_id WHERE b.batch_id IS NULL"
    ).fetchone()[0]
    assert orphans == 0


def test_fdc_decomposition_rows_have_confidence_and_method(conn):
    bad = conn.execute("SELECT COUNT(*) FROM product_ingredient WHERE confidence IS NULL OR method IS NULL OR method=''").fetchone()[0]
    assert bad == 0
    n_fdc = conn.execute("SELECT COUNT(*) FROM product WHERE is_fdc=1").fetchone()[0]
    assert n_fdc >= 100  # brief A.4


def test_no_boolean_status_column_anywhere(conn):
    cols = [r[1] for t in ("regulatory_event", "regulatory_target", "product") for r in conn.execute(f"PRAGMA table_info({t})")]
    assert not any(c in ("banned", "is_banned", "prohibited", "status") for c in cols)


def test_loader_is_idempotent(conn, cfg):
    from brahmo.ingest import cdci

    before = conn.execute("SELECT COUNT(*) FROM product").fetchone()[0]
    out = cdci.load(conn, cfg)
    assert out.get("skipped") is True
    assert conn.execute("SELECT COUNT(*) FROM product").fetchone()[0] == before
