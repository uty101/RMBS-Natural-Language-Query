"""Build the canonical DuckDB file from the raw trustee files (step 2.5).

    python scripts/build_canonical.py --raw data/raw --db data/canonical/rmbs.duckdb

Writes the database, then pool_monthly.csv and canonical_row_counts.csv into --outputs.
--outputs defaults to the repo's outputs/ when --raw is the repo's data/raw/, otherwise to
<--raw>/../outputs (instruction 03 E 3.0). No network code.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rmbsq.canonical.build import build_canonical, pool_monthly, row_counts, write_pool_monthly  # noqa: E402
from rmbsq.config import load_config  # noqa: E402
from rmbsq.db import connect_readonly  # noqa: E402
from rmbsq.synth.truth import write_csv  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--outputs", type=Path, default=None)
    args = ap.parse_args(argv)
    if args.outputs is None:
        repo_raw = args.raw.resolve() == (ROOT / "data" / "raw").resolve()
        args.outputs = ROOT / "outputs" if repo_raw else args.raw.resolve().parent / "outputs"

    t0 = time.perf_counter()
    build_canonical(args.raw, args.db, load_config(ROOT / "config.toml"))
    t_build = time.perf_counter() - t0

    outputs = args.outputs
    outputs.mkdir(parents=True, exist_ok=True)
    con = connect_readonly(args.db)
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
