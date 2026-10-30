"""The README and the design response, rendered from the templates (instruction 06 B, E, H).
Step 6.4.

The eval is recorded when `outputs/eval_summary.csv` exists, and pending otherwise. The
`eval_table` block is built only in the recorded state. Each document is written with LF
and a single trailing newline, then number-checked against the claims it uses and
`templates/fixed_numbers.txt`.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rmbsq.deliverable.numbers import unexplained_numbers
from rmbsq.deliverable.render import names_used, render
from rmbsq.semantic.catalog import ROOT

TEMPLATES = ROOT / "templates"
DOCUMENTS = {"README.md": "README.md.tmpl", "docs/DESIGN_RESPONSE.md": "DESIGN_RESPONSE.md.tmpl"}
FIXED = TEMPLATES / "fixed_numbers.txt"
TABLE_SYSTEMS = [("system", "governed system"), ("baseline", "plain text-to-SQL")]


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


def blocks_for(outputs: Path, recorded: bool) -> dict[str, str]:
    if not recorded:
        return {}
    return {"eval_table": eval_table(pd.read_csv(Path(outputs) / "eval_summary.csv"))}


def render_documents(claims: pd.DataFrame, blocks: dict, recorded: bool) -> dict[str, str]:
    display = dict(zip(claims["claim_id"], claims["display"]))
    docs = {}
    for doc, template in DOCUMENTS.items():
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
        used = names_used((TEMPLATES / DOCUMENTS[doc]).read_text(encoding="utf-8"), recorded)
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
