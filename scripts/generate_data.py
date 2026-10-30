"""Generate a profile's raw files, then the truth and calibration CSVs (step 1.6).

    python scripts/generate_data.py --profile full --out data/raw

Writes the raw files into --out, then pool_monthly_truth.csv and calibration.csv into
--outputs. --outputs defaults to the repo's outputs/ for --profile full, otherwise to
<--out>/../outputs, so a small run never overwrites the committed full-profile CSVs
(instruction 03 E 3.0). No network code.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rmbsq.config import load_config  # noqa: E402
from rmbsq.synth.generate import run_profile, write_raw  # noqa: E402
from rmbsq.synth.truth import calibration, pool_monthly, write_csv  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["full", "small"], required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--outputs", type=Path, default=None)
    args = ap.parse_args(argv)
    if args.outputs is None:
        args.outputs = ROOT / "outputs" if args.profile == "full" else args.out.resolve().parent / "outputs"

    t0 = time.perf_counter()
    cfg = load_config(ROOT / "config.toml")
    run = run_profile(cfg, args.profile)
    write_raw(run, args.out)
    t_raw = time.perf_counter() - t0

    outputs = args.outputs
    outputs.mkdir(parents=True, exist_ok=True)
    write_csv(pool_monthly(run["panel"]), outputs / "pool_monthly_truth.csv")
    cal = calibration(run["cfg"], run["panel"], run["loans"], run["deals"])
    write_csv(cal, outputs / "calibration.csv")
    t_all = time.perf_counter() - t0

    print(f"profile {args.profile}: {len(run['panel'])} rows, raw files in {t_raw:.1f} s, total {t_all:.1f} s")
    print(cal.to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
