"""Step 1.6: full profile tests, marked `full` (instruction 01 H 1.6, O-5).

These are the only Section 1 tests that read or regenerate the full profile. Run them
with `pytest -m full`.
"""

import csv
import json
from pathlib import Path

import pytest

from rmbsq.synth.generate import generate
from rmbsq.synth.trustee_formats import sha256

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.full


def test_calibration_bands():
    with open(ROOT / "outputs" / "calibration.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 9
    failed = [r for r in rows if r["pass"] != "True"]
    assert not failed, failed


def test_full_regenerates_identically(cfg, tmp_path):
    manifest = json.loads((ROOT / "data" / "raw" / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    generate(cfg, "full", tmp_path)
    regenerated = json.loads((tmp_path / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    assert regenerated == manifest
    assert all(sha256(tmp_path / rel) == digest for rel, digest in manifest.items())
    assert (tmp_path / "MANIFEST.json").read_bytes() == (ROOT / "data" / "raw" / "MANIFEST.json").read_bytes()
