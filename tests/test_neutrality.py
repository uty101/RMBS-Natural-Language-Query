"""Step 7.4: neutrality (kickoff 1.7, instruction 07 E).

Every tracked text file outside `instructions/` and `.github/`, and the extracted text of
both PDFs, is searched case-insensitively for the phrases below. The list lives only in
instruction 07 and here (CLAUDE.md rule 16), so this file is not searched.
"""

import subprocess
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SELF = "tests/test_neutrality.py"
EXCLUDED = ("instructions/", ".github/")
PDFS = ["deliverable/RMBS_Query_Design_Note.pdf", "deliverable/RMBS_Query_Results.pdf"]
BANNED = [
    "interview",
    "case study",
    "hiring",
    "recruit",
    "take-home",
    "take home",
    "assessment",
    "applicant",
    "employer",
    "cover letter",
    "vacancy",
    "job description",
    "job application",
]


def _tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def _texts() -> dict[str, str]:
    texts = {}
    for rel in _tracked():
        if rel.startswith(EXCLUDED) or rel == SELF or rel in PDFS:
            continue
        data = (ROOT / rel).read_bytes()
        if b"\0" in data[:8000]:  # binary, by git's own heuristic
            continue
        texts[rel] = data.decode("utf-8", errors="replace")
    for rel in PDFS:
        texts[rel] = " ".join(p.extract_text() for p in PdfReader(ROOT / rel).pages)
    return texts


def test_no_banned_words():
    texts = _texts()
    assert all(rel in texts for rel in PDFS)
    hits = [(rel, phrase) for rel, text in texts.items() for phrase in BANNED if phrase in text.lower()]
    assert hits == []
