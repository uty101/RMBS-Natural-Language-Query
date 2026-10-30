"""Runs the governed system and the baseline over the eval items (kickoff 6.11; instruction
05 D). Step 5.0 (items), step 5.3 (runs).

`eval/questions.yaml` is copied byte for byte from instruction 05. Each item has `id`,
`category`, `question` and `expected_intent`, plus `trap` on trap items; the answer
items also carry `gold_spec`, `output_columns` and `gold_sql`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from rmbsq.semantic.spec import QuerySpec


@dataclass(frozen=True)
class EvalItem:
    id: str
    category: str
    question: str
    expected_intent: str
    trap: str | None = None
    gold_spec: QuerySpec | None = None
    output_columns: tuple[str, ...] | None = None
    gold_sql: str | None = None


def load_items(path: Path) -> list[EvalItem]:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)["items"]
    items = []
    for r in raw:
        spec = r.get("gold_spec")
        cols = r.get("output_columns")
        items.append(EvalItem(id=r["id"], category=r["category"], question=r["question"],
                              expected_intent=r["expected_intent"], trap=r.get("trap"),
                              gold_spec=None if spec is None else QuerySpec.model_validate(spec),
                              output_columns=None if cols is None else tuple(cols), gold_sql=r.get("gold_sql")))
    return items
