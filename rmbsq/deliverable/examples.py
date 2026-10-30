"""Worked example and transcripts (instruction 06 G). Step 6.3.

`worked_example` runs eval item Q11's gold spec through the compiler, without the LLM.
`transcripts` replays `answer()` from `data/llm_cache/` for Q11, Q35 and Q39; it is built
only in the recorded state, and in the pending state the folder is removed.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

from rmbsq.db import connect_readonly
from rmbsq.llm.answer import answer
from rmbsq.llm.client import LLMClient
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.compiler import compile, execute
from rmbsq.semantic.format import format_table

WORKED_ITEM = "Q11"
TRANSCRIPTS = [("01_answer.md", "Q11"), ("02_clarify.md", "Q35"), ("03_unsupported.md", "Q39")]


def markdown_table(df: pd.DataFrame) -> str:
    lines = ["| " + " | ".join(str(c) for c in df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def _spec_json(spec) -> str:
    return json.dumps(spec.model_dump(mode="json"), indent=2)


def _write(path: Path, parts: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("\n\n".join(parts) + "\n").encode("utf-8"))
    return path


def worked_example(items, db: Path, outputs: Path) -> Path:
    item = {i.id: i for i in items}[WORKED_ITEM]
    catalog = load_catalog()
    compiled = compile(item.gold_spec, catalog)
    con = connect_readonly(db)
    try:
        display = format_table(execute(compiled, con), catalog)
    finally:
        con.close()
    return _write(Path(outputs) / "worked_example.md", [
        "# Worked example: the compiler path (spec written by hand)",
        "## Question", item.question,
        "## Spec", f"```json\n{_spec_json(item.gold_spec)}\n```",
        "## Oracle SQL", f"```sql\n{compiled.sql_oracle}\n```",
        "## Result", markdown_table(display),
    ])


def transcripts(items, db: Path, outputs: Path, cache_dir: Path, cfg, eval_recorded: bool) -> list[Path]:
    folder = Path(outputs) / "transcripts"
    if not eval_recorded:
        if folder.exists():
            shutil.rmtree(folder)
        return []
    by_id = {i.id: i for i in items}
    catalog = load_catalog(db=db)
    client = LLMClient(cfg, mode="replay", cache_dir=cache_dir)
    con = connect_readonly(db)
    written = []
    try:
        for name, item_id in TRANSCRIPTS:
            ans = answer(by_id[item_id].question, client, con, catalog, cfg)
            parts = [f"# Transcript {item_id}", "## Question", ans.question,
                     "## Spec", f"```json\n{_spec_json(ans.spec_raw)}\n```"]
            if name == "01_answer.md":
                parts += ["## Oracle SQL", f"```sql\n{ans.sql_oracle}\n```",
                          "## Result", markdown_table(ans.display)]
            parts += ["## Text", ans.text]
            written.append(_write(folder / name, parts))
    finally:
        con.close()
    return written
