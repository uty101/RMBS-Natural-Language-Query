"""Markdown to PDF with reportlab Platypus (instruction 07 D). Step 7.2.

`build_pdf` parses a fixed markdown subset (D.1) and anything else raises
`UnsupportedMarkdown(line_number, text)`. `rl_config.invariant = 1` makes 2 builds on 1
machine byte-identical. Every page carries the repo URL and `page N of M`, so the story is
built twice: once to count the pages, then with M known.

`fit_summary` builds the results summary at shrinking image heights until it fits 1 page
(D.3). Images are resolved relative to `cfg.root`, the folder holding `config.toml`, which
is the repo root (C.3).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.fonts import tt2ps
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (HRFlowable, Image, KeepTogether, ListFlowable, ListItem, Paragraph,
                                Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle)

rl_config.invariant = 1

MARGIN = 2 * cm  # D.2
GREY = colors.grey
# palette, shared with rmbsq/deliverable/figures.py
NAVY = colors.HexColor("#1F3A5F")
TEAL = colors.HexColor("#2A9D8F")
INK = colors.HexColor("#1E293B")
MUTED = colors.HexColor("#64748B")
RULE = colors.HexColor("#CBD5E1")
PANEL = colors.HexColor("#F1F5F9")
BAND_PT = 6  # height of the navy band across the top of every page
FOOTNOTE = "All figures are generated from CSV files committed in the repo. The data is synthetic."  # D.2
DESIGN_IMAGE_MAX_CM = 8.0  # D.2
SUMMARY_IMAGE_START_CM, SUMMARY_IMAGE_STEP_CM, SUMMARY_IMAGE_MIN_CM = 5.5, 0.5, 3.5  # D.3

# D.2 sizes in pt: title, heading, body, body leading, code, table
SIZES = {
    "design": {"title": 16, "heading": 12, "body": 10, "leading": 13, "code": 8.5, "table": 9, "row_pad": (2.5, 3)},
    "summary": {"title": 13, "heading": 10, "body": 8.5, "leading": 10.5, "code": 7.5, "table": 8.5,
                "row_pad": (0.8, 1.6)},
}
HEADER_PT, FOOTER_PT, FOOTNOTE_PT = 9, 7.5, 8  # D.2
TABLE_PAD = 4  # pt, left and right padding of a table cell

IMAGE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)$")
TABLE_SEPARATOR = re.compile(r"^\|(\s*:?-+:?\s*\|)+$")
# line starts the subset doesn't have: quotes, deeper headings, other list markers, rules, HTML
UNSUPPORTED_START = re.compile(r"^(>|#{3,}|#[^ #]|[*+] |\d+[.)] |(-{3,}|\*{3,}|_{3,})\s*$|<|~~~)")


class UnsupportedMarkdown(ValueError):
    def __init__(self, line_number: int, text: str):
        super().__init__(f"line {line_number}: unsupported markdown: {text!r}")
        self.line_number = line_number
        self.text = text


@dataclass(frozen=True)
class Block:
    kind: str  # title, heading, para, bullets, table, code, image
    line: int
    content: object


# ---------------------------------------------------------------- parsing (D.1)

def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text: str, line: int, font: str) -> str:
    """Inline markdown to reportlab paragraph markup: **bold**, `code` and [text](url)."""
    parts = re.split(r"(`[^`]*`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            out.append(f'<font face="Courier">{_escape(part[1:-1])}</font>')
            continue
        if "`" in part:
            raise UnsupportedMarkdown(line, text)
        s = _escape(part)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        if "![" in s:
            raise UnsupportedMarkdown(line, text)
        s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
        if re.search(r"(?<![\w])[*_](?=\S)|(?<=\S)[*_](?![\w])", re.sub(r"<[^>]+>", "", s)):
            raise UnsupportedMarkdown(line, text)  # italics, or a stray emphasis marker
        out.append(s)
    return "".join(out)


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip()[1:-1].split("|")]


def parse(markdown_text: str) -> list[Block]:
    lines = markdown_text.split("\n")
    blocks: list[Block] = []
    i = 0
    if not lines or not lines[0].startswith("# "):
        raise UnsupportedMarkdown(1, lines[0] if lines else "")
    blocks.append(Block("title", 1, lines[0][2:].strip()))
    i = 1
    while i < len(lines):
        line, n = lines[i], i + 1
        if line.startswith("    ") or line.startswith("\t"):
            start = n
            code = []
            while i < len(lines) and (lines[i].startswith("    ") or lines[i].startswith("\t")):
                code.append(lines[i][4:] if lines[i].startswith("    ") else lines[i][1:])
                i += 1
            blocks.append(Block("code", start, code))
            continue
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            start = n
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            if i == len(lines):
                raise UnsupportedMarkdown(start, line)  # unterminated fence
            i += 1
            blocks.append(Block("code", start, code))
            continue
        if line.startswith("# "):
            raise UnsupportedMarkdown(n, line)  # the title is the first line only, exactly once
        if line.startswith("## "):
            blocks.append(Block("heading", n, line[3:].strip()))
            i += 1
            continue
        if UNSUPPORTED_START.match(line):
            raise UnsupportedMarkdown(n, line)
        m = IMAGE.match(line.strip())
        if m:
            blocks.append(Block("image", n, (m.group(1), m.group(2))))
            i += 1
            continue
        if line.startswith("|"):
            start = n
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i].rstrip())
                i += 1
            if len(rows) < 2 or not TABLE_SEPARATOR.match(rows[1]):
                raise UnsupportedMarkdown(start, rows[0])
            header, body = _cells(rows[0]), [_cells(r) for r in rows[2:]]
            for k, r in enumerate(body):
                if len(r) != len(header):
                    raise UnsupportedMarkdown(start + 2 + k, rows[2 + k])
            blocks.append(Block("table", start, (header, body)))
            continue
        if line.startswith("- "):
            start = n
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append((i + 1, lines[i][2:].strip()))
                i += 1
            if i < len(lines) and lines[i].strip() and not lines[i].startswith(("    ", "\t")):
                raise UnsupportedMarkdown(i + 1, lines[i])  # a continuation line under a bullet
            blocks.append(Block("bullets", start, items))
            continue
        start = n
        para = []
        while i < len(lines):
            cur = lines[i]
            if (not cur.strip() or cur.startswith(("    ", "\t", "```", "#", "- ", "|"))
                    or IMAGE.match(cur.strip())):
                break
            if UNSUPPORTED_START.match(cur):
                raise UnsupportedMarkdown(i + 1, cur)
            para.append((i + 1, cur.strip()))
            i += 1
        blocks.append(Block("para", start, para))
    return blocks


# ---------------------------------------------------------------- rendering (D.2)

def _styles(font: str, kind: str) -> dict[str, ParagraphStyle]:
    z = SIZES[kind]
    bold = tt2ps(font, 1, 0)
    body_gap = z["body"] * 0.6
    return {
        "title": ParagraphStyle("title", fontName=bold, fontSize=z["title"], leading=z["title"] * 1.25,
                                spaceAfter=2, textColor=NAVY),
        "header": ParagraphStyle("header", fontName=font, fontSize=HEADER_PT, leading=HEADER_PT * 1.3,
                                 textColor=TEAL, spaceAfter=4),
        "heading": ParagraphStyle("heading", fontName=bold, fontSize=z["heading"], leading=z["heading"] * 1.25,
                                  spaceBefore=z["heading"] * 0.8, spaceAfter=z["heading"] * 0.4, keepWithNext=1,
                                  textColor=NAVY),
        "body": ParagraphStyle("body", fontName=font, fontSize=z["body"], leading=z["leading"],
                               spaceAfter=body_gap, textColor=INK),
        "bullet": ParagraphStyle("bullet", fontName=font, fontSize=z["body"], leading=z["leading"], textColor=INK),
        "code": ParagraphStyle("code", fontName="Courier", fontSize=z["code"], leading=z["code"] * 1.35,
                               textColor=NAVY),
        "cell": ParagraphStyle("cell", fontName=font, fontSize=z["table"], leading=z["table"] * 1.25, textColor=INK),
        "cell_head": ParagraphStyle("cell_head", fontName=bold, fontSize=z["table"], leading=z["table"] * 1.25,
                                    textColor=colors.white),
        "footnote": ParagraphStyle("footnote", fontName=font, fontSize=FOOTNOTE_PT, leading=FOOTNOTE_PT * 1.3,
                                   textColor=MUTED, spaceBefore=z["body"]),
    }


def _plain(markup: str) -> str:
    return re.sub(r"<[^>]+>", "", markup).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def _table(header, body, line, st, font, width, row_pad=(2.5, 3)) -> Table:
    bold = tt2ps(font, 1, 0)
    marked = [[inline(c, line, font) for c in header]] + [[inline(c, line + 2 + k, font) for c in r]
                                                         for k, r in enumerate(body)]
    size = st["cell"].fontSize
    natural = [max(stringWidth(_plain(row[j]), bold if r == 0 else font, size) for r, row in enumerate(marked))
               + 2 * (TABLE_PAD + 1) + 2 for j in range(len(header))]
    scale = min(1.0, width / sum(natural))
    widths = [w * scale for w in natural]
    data = [[Paragraph(c, st["cell_head"] if r == 0 else st["cell"]) for c in row] for r, row in enumerate(marked)]
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),  # header row
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PANEL]),  # zebra body rows
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, RULE),  # D.2: 0.25 pt grid, now horizontal rules only
        ("BOX", (0, 0), (-1, -1), 0.25, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), TABLE_PAD + 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), TABLE_PAD + 1),
        ("TOPPADDING", (0, 0), (-1, -1), row_pad[0]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), row_pad[1]),
    ]))
    t.spaceAfter = st["body"].spaceAfter
    # keep each table on 1 page; every table here is short, so it moves whole rather than splitting
    return KeepTogether([t])


def _image(path: Path, kind: str, width: float, image_height_cm: float | None) -> Image:
    iw, ih = ImageReader(str(path)).getSize()
    if kind == "design":
        w = width
        h = w * ih / iw
        if h > DESIGN_IMAGE_MAX_CM * cm:
            h = DESIGN_IMAGE_MAX_CM * cm
            w = h * iw / ih
    else:
        if image_height_cm is None:
            raise ValueError("a summary with an image needs image_height_cm")
        h = image_height_cm * cm
        w = h * iw / ih
        if w > width:
            w, h = width, width * ih / iw
    img = Image(str(path), width=w, height=h)
    img.hAlign = "LEFT"
    return img


def story(blocks: list[Block], cfg, kind: str, image_height_cm: float | None, width: float) -> list:
    font = cfg.deliverable.font
    st = _styles(font, kind)
    out = []
    for b in blocks:
        if b.kind == "title":
            out.append(Paragraph(inline(b.content, b.line, font), st["title"]))
            out.append(Paragraph(_escape(f"{cfg.deliverable.author} · {cfg.deliverable.date_label}"),
                                 st["header"]))
            out.append(HRFlowable(width="100%", thickness=1.2, color=TEAL, spaceBefore=2,
                                  spaceAfter=st["body"].fontSize, hAlign="LEFT"))
        elif b.kind == "heading":
            out.append(Paragraph(inline(b.content, b.line, font), st["heading"]))
        elif b.kind == "para":
            out.append(Paragraph(" ".join(inline(t, n, font) for n, t in b.content), st["body"]))
        elif b.kind == "bullets":
            items = [ListItem(Paragraph(inline(t, n, font), st["bullet"]), leftIndent=st["body"].fontSize * 1.4)
                     for n, t in b.content]
            out.append(ListFlowable(items, bulletType="bullet", start="•", bulletFontName=font,
                                    bulletFontSize=st["body"].fontSize, bulletColor=TEAL,
                                    leftIndent=st["body"].fontSize * 1.4, spaceAfter=st["body"].spaceAfter))
        elif b.kind == "table":
            header, body = b.content
            out.append(_table(header, body, b.line, st, font, width, SIZES[kind]["row_pad"]))
        elif b.kind == "code":
            pre = Preformatted("\n".join(b.content), st["code"])
            panel = Table([[pre]], colWidths=[width], hAlign="LEFT")
            panel.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                ("LINEBEFORE", (0, 0), (0, -1), 2, TEAL),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            panel.spaceAfter = st["body"].spaceAfter
            out.append(panel)
        elif b.kind == "image":
            _alt, rel = b.content
            path = Path(cfg.root) / rel
            out.append(_image(path, kind, width, image_height_cm))
            out.append(Spacer(1, st["body"].spaceAfter))
    if kind == "design":
        out.append(Paragraph(_escape(FOOTNOTE), st["footnote"]))
    return out


def _footer(cfg, total: int):
    def draw(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - BAND_PT, w, BAND_PT, stroke=0, fill=1)  # band across the top
        canvas.setFillColor(TEAL)
        canvas.rect(0, h - BAND_PT - 1.5, w, 1.5, stroke=0, fill=1)  # thin teal line under it
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, MARGIN / 2 + FOOTER_PT + 2, w - MARGIN, MARGIN / 2 + FOOTER_PT + 2)
        canvas.setFont(cfg.deliverable.font, FOOTER_PT)
        canvas.setFillColor(MUTED)
        y = MARGIN / 2
        canvas.drawString(MARGIN, y, cfg.deliverable.repo_url)
        canvas.drawRightString(A4[0] - MARGIN, y, f"page {doc.page} of {total}")
        canvas.restoreState()
    return draw


def _build(blocks, out: Path, cfg, kind, image_height_cm, title: str, total: int) -> int:
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN,
                            bottomMargin=MARGIN, title=title, author=cfg.deliverable.author)
    draw = _footer(cfg, total)
    doc.build(story(blocks, cfg, kind, image_height_cm, doc.width), onFirstPage=draw, onLaterPages=draw)
    return doc.page


def build_pdf(markdown_text: str, out: Path, cfg, kind: Literal["design", "summary"],
              image_height_cm: float | None = None) -> int:
    """Write `out` and return its page count."""
    if kind not in SIZES:
        raise ValueError(f"unknown kind {kind}")
    if cfg.deliverable.page_size != "A4":
        raise ValueError(f"page_size {cfg.deliverable.page_size} is not A4")
    blocks = parse(markdown_text)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    title = blocks[0].content
    pages = _build(blocks, out, cfg, kind, image_height_cm, title, total=0)
    final = _build(blocks, out, cfg, kind, image_height_cm, title, total=pages)
    if final != pages:
        raise RuntimeError(f"page count changed between passes: {pages} then {final}")
    return final


def fit_summary(markdown_text: str, out: Path, cfg) -> tuple[int, float]:
    """D.3: (page count, image height in cm). Above 1 page at 3.5 cm is a stop condition for
    the caller; the last build is left on disk."""
    target = cfg.deliverable.summary_max_pages
    height = SUMMARY_IMAGE_START_CM
    pages = build_pdf(markdown_text, out, cfg, "summary", height)
    while pages > target and height - SUMMARY_IMAGE_STEP_CM >= SUMMARY_IMAGE_MIN_CM - 1e-9:
        height = round(height - SUMMARY_IMAGE_STEP_CM, 2)
        pages = build_pdf(markdown_text, out, cfg, "summary", height)
    return pages, height
