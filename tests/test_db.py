"""Step 4.0: the locked read-only connection (instruction 04 B)."""

import duckdb
import pytest

from rmbsq.db import connect_readonly


def test_readonly_blocks(small_db, tmp_path):
    readable = tmp_path / "readable.csv"
    readable.write_text("a\n1\n", encoding="utf-8")
    target = tmp_path / "out.csv"
    before = sorted(tmp_path.iterdir())
    con = connect_readonly(small_db)
    try:
        blocked = [
            "CREATE TABLE t (a INTEGER)",
            f"COPY (SELECT 1 AS a) TO '{target.as_posix()}'",
            f"SELECT * FROM read_csv('{readable.as_posix()}')",
            "SET threads = 4",
        ]
        for sql in blocked:
            with pytest.raises(duckdb.Error):
                con.execute(sql).fetchall()
        assert con.execute("SELECT COUNT(*) FROM dim_deal").fetchone()[0] > 0
    finally:
        con.close()
    assert not target.exists()
    assert sorted(tmp_path.iterdir()) == before
