"""Question to QuerySpec call (kickoff 6.8; instruction 04 D). Step 4.2.

`render_spec_prompt` fills `prompts/spec_system.md` from the catalogue and config (D.1).
The single tool `submit_spec` takes `QuerySpec.model_json_schema()` with every `$ref`
inlined and every `title` removed (D.2). `question_to_spec` validates the tool input and
turns a missing block or an invalid spec into `unsupported` (D.3).
"""

from __future__ import annotations

import copy
import re

from pydantic import ValidationError

from rmbsq.db import connect_readonly
from rmbsq.semantic.catalog import ROOT
from rmbsq.semantic.spec import QuerySpec

PROMPT = ROOT / "prompts" / "spec_system.md"
TOOL_NAME = "submit_spec"
TOOL_CHOICE = {"type": "tool", "name": TOOL_NAME}
DEAL_ALIAS_NOTE = '(aliases such as "Harbour 19-1" or "HARB19-1" are also accepted)'  # D.1


def fill(template: str, values: dict) -> str:
    """Replaces every `{{name}}`; a placeholder left unfilled raises."""
    for name, value in values.items():
        template = template.replace("{{" + name + "}}", str(value))
    left = re.findall(r"\{\{[^}]*\}\}", template)
    if left:
        raise ValueError(f"unfilled placeholders: {sorted(set(left))}")
    return template


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join([*lines, *("| " + " | ".join(r) + " |" for r in rows)])


def render_spec_prompt(catalog, cfg) -> str:
    con = connect_readonly(catalog.db)
    try:
        n_deals = con.execute("SELECT COUNT(*) FROM dim_deal").fetchone()[0]
    finally:
        con.close()
    allowed = []
    for name in catalog.dimensions:
        line = f"- {name}: " + ", ".join(str(v) for v in catalog.allowed_values(name))
        allowed.append(f"{line} {DEAL_ALIAS_NOTE}" if name == "deal_name" else line)
    cal = cfg.calendar
    return fill(PROMPT.read_text(encoding="utf-8"), {
        "n_deals": n_deals,
        "window_start": cal.window_start,
        "window_end": cal.window_end,
        "latest": cal.latest,
        "metrics_table": _table(["name", "kind", "definition"],
                                [[m.name, m.kind, m.definition] for m in catalog.metrics.values()]),
        "dimensions_table": _table(["name", "level", "definition"],
                                   [[d.name, d.level, d.definition] for d in catalog.dimensions.values()]),
        "allowed_values": "\n".join(allowed),
    })


def _inline(node, defs: dict):
    if isinstance(node, dict):
        if "$ref" in node:
            target = defs[node["$ref"].removeprefix("#/$defs/")]
            return _inline({**copy.deepcopy(target), **{k: v for k, v in node.items() if k != "$ref"}}, defs)
        return {k: _inline(v, defs) for k, v in node.items() if k not in ("title", "$defs")}
    if isinstance(node, list):
        return [_inline(v, defs) for v in node]
    return node


def spec_input_schema() -> dict:
    """D.2: QuerySpec's JSON schema with `$ref` inlined, `$defs` and every `title` removed."""
    schema = QuerySpec.model_json_schema()
    return _inline(schema, schema.get("$defs", {}))


def spec_tool() -> dict:
    return {"name": TOOL_NAME, "description": "Submit the query spec for the question.",
            "input_schema": spec_input_schema()}


def _invalid(reason: str) -> QuerySpec:
    """D.3: the first error, at most 200 characters."""
    return QuerySpec(intent="unsupported", unsupported_reason=f"invalid spec from model: {reason[:200]}")


def question_to_spec(question: str, client, catalog) -> tuple[QuerySpec, bool]:
    response = client.call(render_spec_prompt(catalog, client.cfg), [{"role": "user", "content": question}],
                           [spec_tool()], TOOL_CHOICE)
    block = next((b for b in response.get("content", [])
                  if b.get("type") == "tool_use" and b.get("name") == TOOL_NAME), None)
    if block is None:
        return _invalid(f"no {TOOL_NAME} tool call in the response"), False
    try:
        return QuerySpec.model_validate(block["input"]), True
    except ValidationError as err:
        first = err.errors()[0]
        loc = ".".join(str(p) for p in first["loc"])
        return _invalid(f"{loc}: {first['msg']}" if loc else first["msg"]), False
