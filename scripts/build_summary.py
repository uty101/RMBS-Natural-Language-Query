"""Summary outputs for the write-up (step 6.1; instruction 06 C).

    python scripts/build_summary.py

Run after build_canonical.py. Reads the canonical database, the raw trustee files and
`outputs/pool_monthly.csv`, regenerates the full profile's true panel in memory, and
writes `outputs/data_summary.csv`, `outputs/compiler_check.csv` and
`outputs/trap_effects.csv`. No network code.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rmbsq.config import load_config  # noqa: E402
from rmbsq.db import connect_readonly  # noqa: E402
from rmbsq.eval.report import write_table  # noqa: E402
from rmbsq.eval.run import load_items  # noqa: E402
from rmbsq.eval.summary import compiler_check, data_summary  # noqa: E402
from rmbsq.eval.traps import trap_effects  # noqa: E402
from rmbsq.semantic.catalog import load_catalog  # noqa: E402
from rmbsq.synth.generate import run_profile  # noqa: E402

GOLD = ROOT / "tests" / "fixtures" / "compiler_gold.json"


def main(argv=None) -> list[Path]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=ROOT / "data" / "canonical" / "rmbs.duckdb")
    ap.add_argument("--raw", type=Path, default=ROOT / "data" / "raw")
    ap.add_argument("--outputs", type=Path, default=ROOT / "outputs")
    args = ap.parse_args(argv)
    cfg = load_config(ROOT / "config.toml")
    catalog = load_catalog()
    args.outputs.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    panel = run_profile(cfg, "full")["panel"]
    summary = data_summary(args.db, args.raw, args.outputs / "pool_monthly.csv", panel, cfg)
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    check = compiler_check(args.db, gold, load_items(ROOT / "eval" / "questions.yaml"), catalog)
    con = connect_readonly(args.db)
    try:
        traps = trap_effects(con, catalog)
    finally:
        con.close()

    written = []
    for name, df in [("data_summary.csv", summary), ("compiler_check.csv", check), ("trap_effects.csv", traps)]:
        write_table(df, args.outputs / name)
        written.append(args.outputs / name)
    print(f"summary outputs in {time.perf_counter() - t0:.1f} s")
    return written


if __name__ == "__main__":
    for path in main():
        print(path)
