"""Step 7.2: the markdown to PDF builder (instruction 07 D, G)."""

import dataclasses
import re
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

from rmbsq.config import load_config
from rmbsq.deliverable.pdf import UnsupportedMarkdown, build_pdf, parse

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "docs" / "DESIGN_RESPONSE.md"

SUBSET = """# Subset title

## A heading

A paragraph with **bold words**, `inline code` and a [link text](https://example.org),
joined across 2 lines.

- first bullet
- second bullet

| col a | col b |
|---|---|
| **cell bold** | `cell code` |

    indented code line 1
    indented code line 2

```
fenced code line
```

![a figure](fig/box.png)
"""


@pytest.fixture(scope="module")
def cfg():
    return load_config(ROOT / "config.toml")


def _text(path: Path) -> list[str]:
    return [page.extract_text() for page in PdfReader(path).pages]


def _collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def test_markdown_subset(cfg, tmp_path):
    (tmp_path / "fig").mkdir()
    Image.new("RGB", (200, 100), "white").save(tmp_path / "fig" / "box.png")
    local = dataclasses.replace(cfg, root=tmp_path)

    kinds = [b.kind for b in parse(SUBSET)]
    assert kinds == ["title", "heading", "para", "bullets", "table", "code", "code", "image"]

    for kind in ["design", "summary"]:
        out = tmp_path / f"{kind}.pdf"
        pages = build_pdf(SUBSET, out, local, kind, image_height_cm=4.0)
        assert pages == 1
        text = _collapse(" ".join(_text(out)))
        for s in ["Subset title", "A heading", "A paragraph with bold words, inline code and a link text, joined "
                  "across 2 lines.", "first bullet", "second bullet", "col a", "col b", "cell bold", "cell code",
                  "indented code line 1", "indented code line 2", "fenced code line"]:
            assert s in text, (kind, s)
        assert PdfReader(out).pages[0].images, kind
    reader = PdfReader(tmp_path / "design.pdf")
    links = [a.get_object()["/A"]["/URI"] for a in reader.pages[0]["/Annots"]]
    assert links == ["https://example.org"]

    with pytest.raises(UnsupportedMarkdown) as e:
        build_pdf("# T\n\n> quote\n", tmp_path / "bad.pdf", local, "design")
    assert e.value.line_number == 3 and e.value.text == "> quote"


def test_pdf_deterministic(cfg, tmp_path):
    md = DESIGN.read_text(encoding="utf-8")
    build_pdf(md, tmp_path / "a.pdf", cfg, "design")
    build_pdf(md, tmp_path / "b.pdf", cfg, "design")
    assert (tmp_path / "a.pdf").read_bytes() == (tmp_path / "b.pdf").read_bytes()


def test_footer_and_header(cfg, tmp_path):
    out = tmp_path / "d.pdf"
    pages = build_pdf(DESIGN.read_text(encoding="utf-8"), out, cfg, "design")
    first = _text(out)[0]
    assert cfg.deliverable.author in first
    assert cfg.deliverable.date_label in first
    assert "page 1 of" in first
    assert f"page 1 of {pages}" in first
    assert cfg.deliverable.repo_url in first
