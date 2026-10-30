"""Build the canonical DuckDB file from the raw trustee files (step 2.5).

    python scripts/build_canonical.py --raw data/raw --db data/canonical/rmbs.duckdb

Writes the database, then outputs/pool_monthly.csv and outputs/canonical_row_counts.csv.
No network code.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import duckdb  # noqa: E402

from rmbsq.canonical.build import build_canonical, pool_monthly, row_counts, write_pool_monthly  # noqa: E402
from rmbsq.config import load_config  # noqa: E402
from rmbsq.synth.truth import write_csv  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--db", type=Path, required=True)
    args = ap.parse_args(argv)

    t0 = time.perf_counter()
    build_canonical(args.raw, args.db, load_config(ROOT / "config.toml"))
    t_build = time.perf_counter() - t0

    outputs = ROOT / "outputs"
    outputs.mkdir(exist_ok=True)
    con = duckdb.connect(str(args.db), read_only=True)
    try:
        write_pool_monthly(pool_monthly(con), outputs / "pool_monthly.csv")
        counts = row_counts(con)
        write_csv(counts, outputs / "canonical_row_counts.csv")
    finally:
        con.close()

    print(f"built {args.db} in {t_build:.1f} s, {args.db.stat().st_size} bytes")
    print(counts.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
