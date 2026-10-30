"""Scale benchmark: tiled database, then timings on 1x and tiled (step 5.7; instruction 05 E).

    python scripts/run_benchmark.py [--copies N]

Builds `data/canonical/rmbs_x36.duckdb` (git-ignored) from `data/canonical/rmbs.duckdb`,
then times every answer item's gold spec and writes `outputs/scale_benchmark.csv`. Prints
the build time, both database sizes and fact row counts, and per (db, route, threads) the
median and max of median_s. No network code.
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rmbsq.config import load_config  # noqa: E402
from rmbsq.eval.benchmark import build_tiled_db, run_benchmark  # noqa: E402
from rmbsq.eval.report import write_table  # noqa: E402
from rmbsq.eval.run import load_items  # noqa: E402


def main(argv=None) -> int:
    cfg = load_config(ROOT / "config.toml")
    ap = argparse.ArgumentParser()
    ap.add_argument("--copies", type=int, default=cfg.benchmark.copies)
    ap.add_argument("--db", type=Path, default=ROOT / "data" / "canonical" / "rmbs.duckdb")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "scale_benchmark.csv")
    args = ap.parse_args(argv)
    # the tiled database's label (36x) follows the copies actually built
    cfg = dataclasses.replace(cfg, benchmark=dataclasses.replace(cfg.benchmark, copies=args.copies))
    tiled = args.db.parent / f"rmbs_x{args.copies}.duckdb"

    t0 = time.perf_counter()
    build_tiled_db(args.db, tiled, args.copies)
    print(f"built {tiled} in {time.perf_counter() - t0:.1f} s")
    for path in (args.db, tiled):
        print(f"{path.name}: {path.stat().st_size} bytes")

    t0 = time.perf_counter()
    bench = run_benchmark(load_items(ROOT / "eval" / "questions.yaml"), args.db, tiled, cfg)
    print(f"benchmark in {time.perf_counter() - t0:.1f} s")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_table(bench, args.out)

    print(bench.groupby(["db", "db_rows", "route", "threads"], sort=False)["median_s"]
          .agg(["count", "median", "max"]).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
