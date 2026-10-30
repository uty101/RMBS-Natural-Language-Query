"""Step 5.5: replay from the committed cache reproduces the eval outputs byte for byte
(instruction 05 F 5.5).

This test reads the repo's `data/llm_cache/`, which `scripts/run_eval.py --mode record`
fills. While that folder is empty (the live run has not been made, D.3), it skips with
"no recorded eval cache", the one permitted skip; it runs unchanged once the cache exists.
"""

from pathlib import Path

import pytest

from rmbsq.eval.run import load_items, run_eval

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "llm_cache"
OUTPUTS = ["eval_results.csv", "eval_summary.csv", "trap_failures.csv", "eval_detail.jsonl"]


@pytest.mark.full
def test_eval_replay_reproduces(full_db, cfg, tmp_path):
    if not CACHE.is_dir() or not any(CACHE.glob("*.json")):
        pytest.skip("no recorded eval cache")
    run_eval(load_items(ROOT / "eval" / "questions.yaml"), full_db, CACHE, tmp_path, cfg, mode="replay")
    for name in OUTPUTS:
        assert (tmp_path / name).read_bytes() == (ROOT / "outputs" / name).read_bytes(), name
