"""Step 6.4: the committed documents are current, every number in them is explained, and
the recorded state renders (instruction 06 H, J 6.4). Step 7.3: the recorded state also
builds both PDFs (instruction 07 G 7.3)."""

import dataclasses
import json
import re
import shutil
from collections import Counter
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from rmbsq.config import load_config
from rmbsq.deliverable.claims import build_claims
from rmbsq.deliverable.figures import eval_figure
from rmbsq.deliverable.writeup import (DOCUMENTS, SUMMARY, blocks_for, check_documents, eval_recorded,
                                       render_documents, write_pdfs)
from rmbsq.eval.report import SUMMARY_COLUMNS, write_table
from rmbsq.eval.run import load_items
from rmbsq.eval.score import wilson

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SUMMARY_SOURCES = ["data_summary.csv", "compiler_check.csv", "scale_benchmark.csv", "trap_effects.csv"]
# made-up k per category, for (system, baseline): not results
MADE_UP_K = {"simple": (9, 7), "grouped": (8, 5), "time": (5, 3), "trap": (7, 2), "ambiguous": (3, 0),
             "unsupported": (2, 1)}
# made-up system text for Q35, for the clarify_transcript block (instruction 07 C.2): not a result
MADE_UP_CLARIFY = "Which arrears threshold do you mean?\nOptions: 30+ days; 90+ days"


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


def made_up_eval_detail(path: Path) -> None:
    """An eval_detail.jsonl holding only the system's Q35 row, with made-up text."""
    row = {"system": "system", "item_id": "Q35", "question": "What are arrears in NSW?", "intent": "clarify",
           "columns": [], "rows": [], "text": MADE_UP_CLARIFY, "correct": True, "error": ""}
    path.write_bytes((json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))


def render_recorded(folder: Path) -> tuple[dict, pd.DataFrame, dict]:
    folder.mkdir(parents=True, exist_ok=True)
    for name in SUMMARY_SOURCES:
        shutil.copy(OUT / name, folder / name)
    # the committed results, which the instruction 09 C claims count
    shutil.copy(OUT / "eval_results.csv", folder / "eval_results.csv")
    made_up_eval_summary(folder / "eval_summary.csv")
    made_up_eval_detail(folder / "eval_detail.jsonl")
    assert eval_recorded(folder)
    claims = build_claims(True, folder, out=None)
    blocks = blocks_for(folder, True)
    return render_documents(claims, blocks, True), claims, blocks


def test_recorded_state_renders(tmp_path):
    docs, claims, blocks = render_recorded(tmp_path / "outputs")
    table = blocks["eval_table"]
    assert table.splitlines()[0] == "| category | questions | compiled approach | direct SQL |"
    assert table.splitlines()[2] == "| simple | 10 | 9 (90%) | 7 (70%) |"
    assert table.splitlines()[-1] == "| total | 40 | 34 (85%) | 18 (45%) |"
    for doc, text in docs.items():
        assert "{{" not in text, doc
        assert table in text, doc
        assert "in this copy" not in text, doc
    assert "34 of 40 (85.0%" in docs["README.md"]
    assert check_documents(docs, claims, blocks, True) == {doc: [] for doc in DOCUMENTS}


def build_recorded_pdfs(root: Path) -> tuple[dict, dict, dict]:
    """The constructed recorded state under `root`: rendered documents, blocks and the PDF build."""
    docs, claims, blocks = render_recorded(root / "outputs")
    summary = render_documents(claims, blocks, True, SUMMARY)
    assert check_documents(summary, claims, blocks, True) == {doc: [] for doc in SUMMARY}
    eval_figure(root / "outputs")
    cfg = dataclasses.replace(load_config(ROOT / "config.toml"), root=root)
    return docs | summary, blocks, write_pdfs(docs | summary, cfg, root)


def test_recorded_state_pdfs(tmp_path):
    docs, blocks, pdfs = build_recorded_pdfs(tmp_path)
    cfg = load_config(ROOT / "config.toml")
    assert "{{" not in docs["deliverable/results_summary.md"]
    assert pdfs["design_pages"] <= cfg.deliverable.design_max_pages
    assert pdfs["summary_pages"] == cfg.deliverable.summary_max_pages
    assert 3.5 <= pdfs["summary_image_height_cm"] <= 5.5
    design, summary = pdfs["paths"]
    assert len(PdfReader(design).pages) == pdfs["design_pages"]
    assert len(PdfReader(summary).pages) == 1
    text = re.sub(r"\s+", " ", " ".join(p.extract_text() for p in PdfReader(summary).pages))
    for line in blocks["eval_table"].splitlines()[2:]:
        for cell in line.strip("|").split("|"):
            assert cell.strip() in text, cell
    for line in blocks["clarify_transcript"].splitlines():
        assert line.strip() in text, line
