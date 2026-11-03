"""The README and the design response, rendered from the templates (instruction 06 B, E, H).
Step 6.4. The results summary (instruction 07 C), steps 7.0 and 7.1, and both PDFs
(instruction 07 F), step 7.3.

The eval is recorded when `outputs/eval_summary.csv` exists, and pending otherwise. The
`eval_table` and `clarify_transcript` blocks are built only in the recorded state, and
`trap_table` in both. Each document is written with LF
and a single trailing newline, then number-checked against the claims it uses and
`templates/fixed_numbers.txt`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from rmbsq.deliverable.claims import FORMATS
from rmbsq.deliverable.numbers import unexplained_numbers
from rmbsq.deliverable.pdf import build_pdf, fit_summary
from rmbsq.deliverable.render import names_used, render
from rmbsq.semantic.catalog import ROOT

TEMPLATES = ROOT / "templates"
DOCUMENTS = {"README.md": "README.md.tmpl", "docs/DESIGN_RESPONSE.md": "DESIGN_RESPONSE.md.tmpl"}
SUMMARY = {"deliverable/results_summary.md": "RESULTS_SUMMARY.md.tmpl"}
PDFS = {"design": ("docs/DESIGN_RESPONSE.md", "deliverable/RMBS_Query_Design_Note.pdf"),
        "summary": ("deliverable/results_summary.md", "deliverable/RMBS_Query_Results.pdf")}
TEMPLATE_OF = DOCUMENTS | SUMMARY
FIXED = TEMPLATES / "fixed_numbers.txt"
TABLE_SYSTEMS = [("system", "compiled approach"), ("baseline", "direct SQL")]
# instruction 07 C.1: trap -> (label, value format); pct3 is x 100, 3 dp and %
TRAP_ROWS = {
    "arrears_units": ("2 missed payments read as 60+ days", "pct2"),
    "call_as_prepay": ("Clean-up calls counted as prepayments", "pct1"),
    "exit_rows": ("Exit month counted as a live loan", "int"),
    "weighting": ("Simple average, not balance-weighted", "pct2"),
    "compounding": ("Monthly CPR averaged, not compounded (dropped)", "pct3"),
}
TRAP_FORMATS = FORMATS | {"pct3": lambda v: f"{float(v) * 100:.3f}%"}
TRAP_QUESTION = {"Q2_2025": "Q2 2025 CPR"}
CLARIFY_ITEM = "Q35"


def eval_recorded(outputs: Path) -> bool:
    return (Path(outputs) / "eval_summary.csv").exists()


def eval_table(summary: pd.DataFrame) -> str:
    """E: 1 row per category in the summary's order, then total; k (k / n as 0 dp %)."""
    rows = {(s, c): r for s, c, r in zip(summary["system"], summary["category"], summary.to_dict("records"))}
    categories = [c for c in dict.fromkeys(summary["category"]) if c != "total"] + ["total"]
    lines = ["| category | questions | " + " | ".join(label for _, label in TABLE_SYSTEMS) + " |",
             "|---|---|" + "---|" * len(TABLE_SYSTEMS)]
    for c in categories:
        n = int(rows[(TABLE_SYSTEMS[0][0], c)]["n"])
        cells = []
        for system, _ in TABLE_SYSTEMS:
            r = rows[(system, c)]
            k, n_s = int(r["k"]), int(r["n"])
            cells.append(f"{k} ({100 * k / n_s:.0f}%)")
        lines.append(f"| {c} | {n} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def trap_table(traps: pd.DataFrame) -> str:
    """C.1: 1 row per trap_effects.csv row, in CSV order."""
    lines = ["| mistake | question | correct | with the mistake |", "|---|---|---|---|"]
    for r in traps.itertuples(index=False):
        label, fmt = TRAP_ROWS[r.trap]
        show = TRAP_FORMATS[fmt]
        lines.append(f"| {label} | {TRAP_QUESTION.get(r.item_id, r.item_id)} | {show(r.gold)} | {show(r.naive)} |")
    return "\n".join(lines)


def clarify_transcript(detail_path: Path) -> str:
    """C.2: the system's text for Q35, as an indented code block, 1 line per line of text."""
    for line in Path(detail_path).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["system"] == "system" and row["item_id"] == CLARIFY_ITEM:
            return "\n".join("    " + text for text in row["text"].split("\n"))
    raise KeyError(f"no system row for {CLARIFY_ITEM} in {detail_path}")


def blocks_for(outputs: Path, recorded: bool) -> dict[str, str]:
    outputs = Path(outputs)
    blocks = {"trap_table": trap_table(pd.read_csv(outputs / "trap_effects.csv", dtype=str, keep_default_na=False))}
    if recorded:
        blocks["eval_table"] = eval_table(pd.read_csv(outputs / "eval_summary.csv"))
        blocks["clarify_transcript"] = clarify_transcript(outputs / "eval_detail.jsonl")
    return blocks


def render_documents(claims: pd.DataFrame, blocks: dict, recorded: bool,
                     documents: dict[str, str] = DOCUMENTS) -> dict[str, str]:
    display = dict(zip(claims["claim_id"], claims["display"]))
    docs = {}
    for doc, template in documents.items():
        text = render((TEMPLATES / template).read_text(encoding="utf-8"), display, blocks, recorded)
        docs[doc] = text.rstrip("\n") + "\n"
    return docs


def fixed_numbers() -> list[str]:
    return [line for line in FIXED.read_text(encoding="utf-8").splitlines() if line.strip()]


def check_documents(docs: dict[str, str], claims: pd.DataFrame, blocks: dict, recorded: bool) -> dict[str, list[str]]:
    """The unexplained numbers per document, each checked against the claims its template uses."""
    display = dict(zip(claims["claim_id"], claims["display"]))
    out = {}
    for doc, text in docs.items():
        used = names_used((TEMPLATES / TEMPLATE_OF[doc]).read_text(encoding="utf-8"), recorded)
        out[doc] = unexplained_numbers(text, {n: display[n] for n in used if n in display}, blocks,
                                       fixed_numbers())
    return out


def write_documents(docs: dict[str, str], root: Path = ROOT) -> list[Path]:
    written = []
    for doc, text in docs.items():
        path = Path(root) / doc
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        written.append(path)
    return written


def write_pdfs(docs: dict[str, str], cfg, root: Path = ROOT) -> dict:
    """Both PDFs from the rendered markdown in `docs` (keyed as in PDFS), written under `root`.
    Returns the page counts, the summary image height and the paths."""
    design_md, design_pdf = PDFS["design"]
    summary_md, summary_pdf = PDFS["summary"]
    design_pages = build_pdf(docs[design_md], Path(root) / design_pdf, cfg, "design")
    summary_pages, height = fit_summary(docs[summary_md], Path(root) / summary_pdf, cfg)
    return {"design_pages": design_pages, "summary_pages": summary_pages, "summary_image_height_cm": height,
            "paths": [Path(root) / design_pdf, Path(root) / summary_pdf]}
