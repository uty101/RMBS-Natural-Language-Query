"""Steps 7.0, 7.1 and 7.3: the results summary template, its blocks and the committed render
(instruction 07 C, G)."""

import json
from pathlib import Path

import pandas as pd

from rmbsq.deliverable.claims import build_claims
from rmbsq.deliverable.writeup import (SUMMARY, blocks_for, check_documents, clarify_transcript,
                                       eval_recorded, render_documents, trap_table)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
DOC = "deliverable/results_summary.md"


def test_summary_template_pending():
    claims = build_claims(False, OUT, out=None)
    blocks = blocks_for(OUT, False)
    docs = render_documents(claims, blocks, False, SUMMARY)
    text = docs[DOC]
    assert "{{" not in text
    assert check_documents(docs, claims, blocks, False) == {DOC: []}
    # the {{#eval}} body is absent, the {{^eval}} body present
    assert "Same 40 questions" not in text and "Accuracy by category" not in text
    assert "hasn't been run in this copy" in text
    assert blocks["trap_table"] in text


def test_trap_table():
    table = trap_table(pd.read_csv(OUT / "trap_effects.csv", dtype=str, keep_default_na=False))
    lines = table.splitlines()
    assert lines[0] == "| mistake | question | correct | with the mistake |"
    rows = [[c.strip() for c in line.strip("|").split("|")] for line in lines[2:]]
    assert len(rows) == 6
    by_q = {r[1]: r for r in rows}
    assert by_q["Q29"][2:] == ["21.6%", "100.0%"]
    assert by_q["Q32"][2:] == ["9,975", "10,572"]
    assert by_q["Q29"][0] == "Clean-up calls counted as prepayments"
    assert rows[-1] == ["Monthly CPR averaged, not compounded (dropped)", "Q2 2025 CPR", "18.064%", "18.063%"]


def test_clarify_transcript_recorded(tmp_path):
    rows = [
        {"system": "baseline", "item_id": "Q35", "question": "What are arrears in NSW?", "sql": "select 1"},
        {"system": "system", "item_id": "Q34", "question": "x", "text": "not this one"},
        {"system": "system", "item_id": "Q35", "question": "What are arrears in NSW?",
         "text": "Which arrears threshold do you mean?\nOptions: 30+ days; 90+ days"},
    ]
    path = tmp_path / "eval_detail.jsonl"
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    assert clarify_transcript(path) == ("    Which arrears threshold do you mean?\n"
                                        "    Options: 30+ days; 90+ days")


def test_summary_current():
    """Step 7.3: the committed results_summary.md is the render of the committed state."""
    recorded = eval_recorded(OUT)
    claims = build_claims(recorded, OUT, out=None)
    docs = render_documents(claims, blocks_for(OUT, recorded), recorded, SUMMARY)
    assert (ROOT / DOC).read_bytes() == docs[DOC].encode("utf-8")
