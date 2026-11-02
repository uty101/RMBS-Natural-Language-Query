"""Step 7.0: the results summary template (instruction 07 C, G)."""

from pathlib import Path

from rmbsq.deliverable.claims import build_claims
from rmbsq.deliverable.writeup import SUMMARY, blocks_for, check_documents, render_documents

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
    assert "hasn't been recorded in this copy" in text
    assert blocks["trap_table"] in text

