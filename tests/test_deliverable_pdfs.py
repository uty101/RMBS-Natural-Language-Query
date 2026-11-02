"""Step 7.3: the committed PDFs (instruction 07 F, G 7.3)."""

import re
from pathlib import Path

from pypdf import PdfReader

from rmbsq.config import load_config
from rmbsq.deliverable.claims import build_claims
from rmbsq.deliverable.render import names_used
from rmbsq.deliverable.writeup import PDFS, TEMPLATE_OF, TEMPLATES, eval_recorded

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def pdf_text(path: Path) -> str:
    """Every page's extracted text, with whitespace collapsed."""
    return re.sub(r"\s+", " ", " ".join(p.extract_text() for p in PdfReader(path).pages))


def test_page_counts():
    cfg = load_config(ROOT / "config.toml")
    assert len(PdfReader(ROOT / PDFS["design"][1]).pages) <= cfg.deliverable.design_max_pages
    assert len(PdfReader(ROOT / PDFS["summary"][1]).pages) == cfg.deliverable.summary_max_pages


def test_claims_in_pdf_text():
    recorded = eval_recorded(OUT)
    claims = build_claims(recorded, OUT, out=None)
    display = dict(zip(claims["claim_id"], claims["display"]))
    for kind, (md, pdf) in PDFS.items():
        text = pdf_text(ROOT / pdf)
        used = [n for n in names_used((TEMPLATES / TEMPLATE_OF[md]).read_text(encoding="utf-8"), recorded)
                if n in display]
        assert used, kind
        for name in used:
            assert re.sub(r"\s+", " ", str(display[name])) in text, (kind, name, display[name])
