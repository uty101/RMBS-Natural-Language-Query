"""Step 3.0: the data scripts write their CSVs next to the data they run on (instruction 03 E 3.0)."""

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _hashes(folder: Path) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def test_small_run_leaves_repo_outputs_alone(tmp_path):
    before = _hashes(ROOT / "outputs")
    raw = tmp_path / "raw"
    for cmd in (["scripts/generate_data.py", "--profile", "small", "--out", str(raw)],
                ["scripts/build_canonical.py", "--raw", str(raw), "--db", str(tmp_path / "canonical" / "rmbs.duckdb")]):
        subprocess.run([sys.executable, *cmd], cwd=ROOT, check=True, capture_output=True)
    assert _hashes(ROOT / "outputs") == before
    assert sorted(p.name for p in (tmp_path / "outputs").iterdir()) == [
        "calibration.csv", "canonical_row_counts.csv", "pool_monthly.csv", "pool_monthly_truth.csv"]
