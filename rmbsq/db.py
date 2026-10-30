"""The locked read-only DuckDB connection (instruction 04 B, step 4.0).

Read-only alone still lets SQL write a file with `COPY ... TO` or read any local file
with `read_csv`. With external access off and the configuration locked, those, `INSTALL`
and any `SET` are refused while `SELECT` works. DuckDB refuses a second connection to
the same file in 1 process with a different configuration, so every read connection in
the project uses this one. `threads: 1` keeps DOUBLE sums deterministic (rule 9). The scale benchmark alone also
times DuckDB's default thread count (step 5.7).
"""

from __future__ import annotations

from pathlib import Path

import duckdb


def connect_readonly(path: Path, threads: int = 1) -> duckdb.DuckDBPyConnection:
    """`threads` 0 means DuckDB's default (instruction 05 E.2); the default stays 1 thread."""
    config = {"enable_external_access": False, "lock_configuration": True}
    if threads:
        config["threads"] = threads
    return duckdb.connect(str(path), read_only=True, config=config)
