"""Structured-output wire schemas and their parsing (instruction 08c B, C.3). Step 8c.1.

Structured output accepts a limited JSON Schema (no free maps, no length or range limits),
so the spec call fills `spec_wire_schema(catalog)` and `wire_to_spec` turns it into the
`QuerySpec` dict, which still enforces every limit. `response_json` takes the first text
block of a response, ignoring `thinking` blocks, and raises `InvalidResponse` on a
`max_tokens` or `refusal` stop, a missing text block or text that isn't JSON.
"""

from __future__ import annotations

import json

INVALID_STOPS = ("max_tokens", "refusal")   # C.3

BASELINE_WIRE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["sql"],
                        "properties": {"sql": {"type": "string"}}}   # B.3

MONTH_PATTERN = "^[0-9]{4}-[0-9]{2}$"


class InvalidResponse(Exception):
    pass


def _nullable(schema: dict) -> dict:
    return {"anyOf": [{"type": "null"}, schema]}


def _closed(properties: dict) -> dict:
    """An object with `additionalProperties: false` and every property required."""
    return {"type": "object", "additionalProperties": False, "required": list(properties),
            "properties": properties}


def spec_wire_schema(catalog) -> dict:
    """B.1."""
    metrics = list(catalog.metrics)
    dims = list(catalog.dimensions)
    return _closed({
        "intent": {"type": "string", "enum": ["answer", "clarify", "unsupported"]},
        "metrics": {"type": "array", "items": {"type": "string", "enum": metrics},
                    "description": "1 to 3 metrics for answer; empty otherwise."},
        "group_by": {"type": "array", "items": {"type": "string", "enum": dims},
                     "description": "0 to 2 dimensions."},
        "filters": {"type": "array", "description": "Empty when there are no filters.",
                    "items": _closed({"dimension": {"type": "string", "enum": dims},
                                      "values": {"type": "array", "minItems": 1, "items": {"type": "string"}}})},
        "time": _nullable(_closed({"grain": {"type": "string", "enum": ["month", "quarter", "year"]},
                                   "start": {"type": "string", "pattern": MONTH_PATTERN},
                                   "end": {"type": "string", "pattern": MONTH_PATTERN},
                                   "shape": {"type": "string", "enum": ["series", "point"]}})),
        "order": _nullable(_closed({"metric": {"type": "string", "enum": metrics},
                                    "direction": {"type": "string", "enum": ["desc", "asc"]},
                                    "limit": {"type": "integer", "description": "1 to 20."}})),
        "clarify": _nullable(_closed({"question": {"type": "string"},
                                      "options": {"type": "array", "items": {"type": "string"},
                                                  "description": "2 to 4 options."}})),
        "unsupported_reason": {"anyOf": [{"type": "null"}, {"type": "string"}]},
    })


def output_config(schema: dict) -> dict:
    """C.1."""
    return {"format": {"type": "json_schema", "schema": schema}}


def wire_to_spec(obj: dict) -> dict:
    """B.2: the wire object as a `QuerySpec` dict."""
    spec = dict(obj)
    if isinstance(spec.get("filters"), list):
        filters: dict[str, list] = {}
        for entry in spec["filters"]:
            values = filters.setdefault(entry["dimension"], [])
            values.extend(v for v in entry["values"] if v not in values)
        spec["filters"] = filters
    if "time" in spec and spec["time"] is None:
        del spec["time"]
    if spec.get("intent") in ("clarify", "unsupported"):
        for name in ("metrics", "group_by", "filters", "time", "order"):
            spec.pop(name, None)
    elif spec.get("intent") == "answer":
        for name in ("clarify", "unsupported_reason"):
            if name in spec and spec[name] is None:
                del spec[name]
    return spec


def response_json(response: dict) -> dict:
    """C.3: the first text block parsed as JSON; `thinking` blocks are ignored."""
    stop = response.get("stop_reason")
    if stop in INVALID_STOPS:
        raise InvalidResponse(f"stop_reason {stop}")
    block = next((b for b in response.get("content", []) if b.get("type") == "text"), None)
    if block is None:
        raise InvalidResponse("no text block in the response")
    try:
        obj = json.loads(block["text"])
    except json.JSONDecodeError as err:
        raise InvalidResponse(f"text is not JSON: {err}") from err
    if not isinstance(obj, dict):
        raise InvalidResponse("JSON is not an object")
    return obj
