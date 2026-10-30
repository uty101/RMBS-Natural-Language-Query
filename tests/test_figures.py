"""Step 6.3: the figures are deterministic, and the pending state has no eval outputs
(instruction 06 F, G, J 6.3)."""

import shutil
from pathlib import Path

from rmbsq.deliverable.figures import make_figures

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["arrears_90p_by_vintage.csv", "scale_benchmark.csv"]


def _build(folder: Path) -> dict[str, bytes]:
    folder.mkdir()
    for name in SOURCES:
        shutil.copy(ROOT / "outputs" / name, folder / name)
    paths = make_figures(folder, eval_recorded=False)
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in paths}


def test_figures_deterministic(tmp_path):
    first, second = _build(tmp_path / "a"), _build(tmp_path / "b")
    assert sorted(first) == ["figures/arrears_90p_by_vintage.png", "figures/scale_benchmark.png"]
    assert first == second

    # pending state: no eval figure and no transcripts
    if not (ROOT / "outputs" / "eval_summary.csv").exists():
        assert not (ROOT / "outputs" / "figures" / "eval_accuracy.png").exists()
        assert not (ROOT / "outputs" / "transcripts").exists()
