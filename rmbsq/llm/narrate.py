"""Narration call and template answer (kickoff 6.8, 6.9; instruction 04 F.1, F.3). Step 4.4.

The narration sees the question, the spec and at most `narration_max_rows` rows of
display strings. If the number guard finds a figure that is not in the table, the text
is replaced by `template_answer`, built from the display table alone.
"""

from __future__ import annotations

import json

from rmbsq.llm.guard import number_guard
from rmbsq.llm.spec_agent import fill
from rmbsq.semantic.catalog import ROOT

PROMPT = ROOT / "prompts" / "narrate_system.md"
TEMPLATE_HEAD = "Result computed from the data (narration withheld because it cited a number not in the table):"
TEMPLATE_EMPTY = "No loans match the filters and dates in the query."
TEMPLATE_ROWS = 10  # F.3


def narrate_system(cfg) -> str:
    return fill(PROMPT.read_text(encoding="utf-8"), {"max_words": cfg.llm.narration_max_words})


def narrate_message(question: str, spec, display_table, cfg) -> str:
    """F.1: the user message, with at most narration_max_rows rows."""
    n = cfg.llm.narration_max_rows
    rows = [[str(v) for v in row] for row in display_table.head(n).itertuples(index=False)]
    return json.dumps({"question": question, "spec": spec.model_dump(mode="json"),
                       "table": {"columns": [str(c) for c in display_table.columns], "rows": rows},
                       "truncated": len(display_table) > n}, ensure_ascii=False, sort_keys=True)


def narrate(question: str, spec, display_table, client, cfg, catalog) -> tuple[str, bool, list[str]]:
    response = client.call(narrate_system(cfg), [{"role": "user", "content": narrate_message(question, spec,
                                                                                            display_table, cfg)}],
                           [], None)
    text = "".join(b["text"] for b in response.get("content", []) if b.get("type") == "text").strip()
    offending = number_guard(text, question, display_table, catalog)
    if offending:
        return template_answer(spec, display_table), True, offending
    return text, False, []


def template_answer(spec, display_table) -> str:
    lines = [TEMPLATE_HEAD]
    if display_table.empty:
        return "\n".join([*lines, TEMPLATE_EMPTY])
    keys = [*spec.group_by, "period_label"]
    for _, row in display_table.head(TEMPLATE_ROWS).iterrows():
        values = "; ".join(f"{m} {row[m]}" for m in spec.metrics)
        lines.append(f"- {' / '.join(str(row[k]) for k in keys)}: {values}")
    if len(display_table) > TEMPLATE_ROWS:
        lines.append(f"- … and {len(display_table) - TEMPLATE_ROWS} more rows.")
    return "\n".join(lines)
