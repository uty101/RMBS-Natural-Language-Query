"""Run the eval: the governed system and the baseline on the 40 items (step 5.3; instruction 05 D).

    python scripts/run_eval.py --mode {record,replay}

Replay reads only `data/llm_cache/`, and a cache miss stops the run. Record makes the
missing API calls into `data/llm_cache/` (it needs ANTHROPIC_API_KEY in the environment),
then runs again in replay. The outputs always come from the replay pass:
`outputs/eval_results.csv`, `eval_summary.csv`, `trap_failures.csv` and `eval_detail.jsonl`.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rmbsq.config import load_config  # noqa: E402
from rmbsq.eval.run import load_items, run_eval  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["record", "replay"], required=True)
    ap.add_argument("--db", type=Path, default=ROOT / "data" / "canonical" / "rmbs.duckdb")
    ap.add_argument("--cache", type=Path, default=ROOT / "data" / "llm_cache")
    ap.add_argument("--outputs", type=Path, default=ROOT / "outputs")
    args = ap.parse_args(argv)

    items = load_items(ROOT / "eval" / "questions.yaml")
    t0 = time.perf_counter()
    scored = run_eval(items, args.db, args.cache, args.outputs, load_config(ROOT / "config.toml"), args.mode)
    wall = time.perf_counter() - t0
    for system in ("system", "baseline"):
        mine = scored[scored["system"] == system]
        print(f"{system}: {int(mine['correct'].sum())}/{len(mine)} correct")
    print(f"{args.mode} run in {wall:.1f} s; outputs in {args.outputs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
