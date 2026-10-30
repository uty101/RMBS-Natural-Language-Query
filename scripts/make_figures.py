"""Figures for the write-up (step 6.3; instruction 06 F).

    python scripts/make_figures.py

Builds `outputs/arrears_90p_by_vintage.csv` from the canonical database, then draws
`outputs/figures/arrears_90p_by_vintage.png` and `scale_benchmark.png`, and
`eval_accuracy.png` when `outputs/eval_summary.csv` exists (deleted otherwise).
No network code.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rmbsq.deliverable.figures import build_arrears_by_vintage, make_figures  # noqa: E402


def main(argv=None) -> list[Path]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=ROOT / "data" / "canonical" / "rmbs.duckdb")
    ap.add_argument("--outputs", type=Path, default=ROOT / "outputs")
    args = ap.parse_args(argv)
    recorded = (args.outputs / "eval_summary.csv").exists()
    return [build_arrears_by_vintage(args.db, args.outputs), *make_figures(args.outputs, recorded)]


if __name__ == "__main__":
    for path in main():
        print(path)
