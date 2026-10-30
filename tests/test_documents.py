"""Step 6.4: the committed documents are current, every number in them is explained, and
the recorded state renders (instruction 06 H, J 6.4)."""

import shutil
from collections import Counter
from pathlib import Path

import pandas as pd

from rmbsq.config import load_config
from rmbsq.deliverable.claims import build_claims
from rmbsq.deliverable.writeup import (DOCUMENTS, blocks_for, check_documents, eval_recorded,
                                       render_documents)
from rmbsq.eval.report import SUMMARY_COLUMNS, write_table
from rmbsq.eval.run import load_items
from rmbsq.eval.score import wilson

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SUMMARY_SOURCES = ["data_summary.csv", "compiler_check.csv", "scale_benchmark.csv", "trap_effects.csv"]
# made-up k per category, for (system, baseline): not results
MADE_UP_K = {"simple": (9, 7), "grouped": (8, 5), "time": (5, 3), "trap": (7, 2), "ambiguous": (3, 0),
             "unsupported": (2, 1)}


def _committed_state():
    recorded = eval_recorded(OUT)
    claims = build_claims(recorded, OUT, out=None)
    blocks = blocks_for(OUT, recorded)
    return recorded, claims, blocks


def test_documents_current():
    recorded, claims, blocks = _committed_state()
    for doc, text in render_documents(claims, blocks, recorded).items():
        assert (ROOT / doc).read_bytes() == text.encode("utf-8"), doc
    committed = pd.read_csv(ROOT / "deliverable" / "claims.csv", dtype=str, keep_default_na=False)
    assert list(committed["claim_id"]) == list(claims["claim_id"])
    assert list(committed["display"]) == list(claims["display"])


def test_documents_numbers_explained():
    recorded, claims, blocks = _committed_state()
    docs = {doc: (ROOT / doc).read_text(encoding="utf-8") for doc in DOCUMENTS}
    assert check_documents(docs, claims, blocks, recorded) == {doc: [] for doc in DOCUMENTS}


def made_up_eval_summary(path: Path) -> None:
    """An eval_summary.csv in the D.2 layout with made-up k values."""
    items = load_items(ROOT / "eval" / "questions.yaml")
    n_by = Counter(i.category for i in items)
    z = load_config(ROOT / "config.toml").eval.wilson_z
    rows = []
    for s, system in enumerate(["system", "baseline"]):
        for category in [*n_by, "total"]:
            n = len(items) if category == "total" else n_by[category]
            k = sum(v[s] for v in MADE_UP_K.values()) if category == "total" else MADE_UP_K[category][s]
            rows.append([system, category, n, k, k / n, *wilson(k, n, z)])
    write_table(pd.DataFrame(rows, columns=SUMMARY_COLUMNS), path)


def render_recorded(folder: Path) -> tuple[dict, pd.DataFrame, dict]:
    folder.mkdir(parents=True, exist_ok=True)
    for name in SUMMARY_SOURCES:
        shutil.copy(OUT / name, folder / name)
    made_up_eval_summary(folder / "eval_summary.csv")
    assert eval_recorded(folder)
    claims = build_claims(True, folder, out=None)
    blocks = blocks_for(folder, True)
    return render_documents(claims, blocks, True), claims, blocks


def test_recorded_state_renders(tmp_path):
    docs, claims, blocks = render_recorded(tmp_path / "outputs")
    table = blocks["eval_table"]
    assert table.splitlines()[0] == "| category | questions | governed system | plain text-to-SQL |"
    assert table.splitlines()[2] == "| simple | 10 | 9 (90%) | 7 (70%) |"
    assert table.splitlines()[-1] == "| total | 40 | 34 (85%) | 18 (45%) |"
    for doc, text in docs.items():
        assert "{{" not in text, doc
        assert table in text, doc
        assert "hasn't been recorded" not in text and "hasn't been run" not in text, doc
    assert "34 of 40 (85.0%" in docs["README.md"]
    assert check_documents(docs, claims, blocks, True) == {doc: [] for doc in DOCUMENTS}
