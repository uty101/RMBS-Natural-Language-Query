# 08c Structured output instead of forced tools, then record the eval

Session 8c instructions for Claude Code. Replace the 2 forced tool calls with structured output, then carry out instruction 08 from step 8.1 to the end. This file beats `PLAN.md`, `08_record_eval.md`, `08b_drop_temperature.md` and the kickoff (rule 13). Status file: `instructions/08c_structured_output.status.md`.

`ANTHROPIC_API_KEY` must be set in the environment, under the same rules as instruction 08 A.

Files committed by chat Claude for this session (copy byte for byte over the current copies; never edit):

| source | destination |
|---|---|
| `instructions/08c_prompts/spec_system.md` | `prompts/spec_system.md` |
| `instructions/08c_prompts/baseline_system.md` | `prompts/baseline_system.md` |

---

## A. O-47: (b)

The tool use docs list Claude Sonnet 5.5 among the models that "reject forced tool use regardless of thinking settings". They recommend `auto` with strict tools, or structured outputs "when you need a response in a fixed JSON shape".

Option (a), `auto` with a prompt telling the model to use the tool, would let the model sometimes answer in text instead. That would bias the eval:

- a missing tool block scores as `unsupported` for the system, which could be counted right on the 2 unsupported items by accident;
- it scores as an empty SQL "decline" for the baseline.

Structured output removes that failure mode: every response is JSON in 1 fixed shape. The pinned SDK 2.3.0 has `output_config` on `Messages.create`, and chat Claude checked this in the installed package.

The 2 prompts change in only the lines that mentioned tools, filters and `time`. Diff `instructions/04_prompts/` against `instructions/08c_prompts/` to see every change.

---

## B. Wire schemas (`rmbsq/llm/wire.py`)

Structured output accepts a limited JSON Schema:

- `additionalProperties` must be `false` on every object, which rules out a free map such as the current `filters`;
- arrays allow only `minItems` 0 or 1, and no `maxItems`;
- strings allow no `minLength` or `maxLength`, and numbers no `minimum` or `maximum`.

So the model fills a **wire schema**, and `wire_to_spec` turns it into the `QuerySpec` dict. `QuerySpec` still enforces every limit (1 to 3 metrics, limit 1 to 20 and the rest). A wire object that fails `QuerySpec` validation follows the existing D.3 rule: unsupported, with flag False.

**B.1 `spec_wire_schema(catalog) -> dict`.** Every object has `additionalProperties: false`, and every one of its properties is listed in `required`.

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["intent", "metrics", "group_by", "filters", "time", "order", "clarify", "unsupported_reason"],
  "properties": {
    "intent": {"type": "string", "enum": ["answer", "clarify", "unsupported"]},
    "metrics": {"type": "array", "items": {"type": "string", "enum": METRIC_NAMES},
                "description": "1 to 3 metrics for answer; empty otherwise."},
    "group_by": {"type": "array", "items": {"type": "string", "enum": DIMENSION_NAMES},
                 "description": "0 to 2 dimensions."},
    "filters": {"type": "array", "description": "Empty when there are no filters.",
                "items": {"type": "object", "additionalProperties": false, "required": ["dimension", "values"],
                          "properties": {"dimension": {"type": "string", "enum": DIMENSION_NAMES},
                                         "values": {"type": "array", "minItems": 1, "items": {"type": "string"}}}}},
    "time": {"anyOf": [{"type": "null"},
                       {"type": "object", "additionalProperties": false, "required": ["grain", "start", "end", "shape"],
                        "properties": {"grain": {"type": "string", "enum": ["month", "quarter", "year"]},
                                       "start": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}$"},
                                       "end": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}$"},
                                       "shape": {"type": "string", "enum": ["series", "point"]}}}]},
    "order": {"anyOf": [{"type": "null"},
                        {"type": "object", "additionalProperties": false, "required": ["metric", "direction", "limit"],
                         "properties": {"metric": {"type": "string", "enum": METRIC_NAMES},
                                        "direction": {"type": "string", "enum": ["desc", "asc"]},
                                        "limit": {"type": "integer", "description": "1 to 20."}}}]},
    "clarify": {"anyOf": [{"type": "null"},
                          {"type": "object", "additionalProperties": false, "required": ["question", "options"],
                           "properties": {"question": {"type": "string"},
                                          "options": {"type": "array", "items": {"type": "string"},
                                                      "description": "2 to 4 options."}}}]},
    "unsupported_reason": {"anyOf": [{"type": "null"}, {"type": "string"}]}
  }
}
```

`METRIC_NAMES` and `DIMENSION_NAMES` are the 12 and 18 catalogue names, in YAML order.

**B.2 `wire_to_spec(obj: dict) -> dict`:**

- `filters`: the list becomes a dict `{dimension: values}`. A repeated dimension appends its values, deduplicated, keeping first-seen order. The dict keeps the order of first appearance (O-39 (a)).
- `time: null` drops the key, so `QuerySpec` applies its default.
- For intent `clarify` or `unsupported`, drop metrics, group_by, filters, time and order before validation.
- For intent `answer`, drop clarify and unsupported_reason when they are null.

**B.3 `BASELINE_WIRE_SCHEMA`:** `{"type": "object", "additionalProperties": false, "required": ["sql"], "properties": {"sql": {"type": "string"}}}`.

---

## C. Requests and parsing

**C.1 The request dict and cache key** (amends instruction 04 C.1 and 08b). The keys are now:

`{model, max_tokens, system, messages, output_config}`

- for the spec call, `output_config = {"format": {"type": "json_schema", "schema": spec_wire_schema(catalog)}}`;
- for the baseline call, the same with `BASELINE_WIRE_SCHEMA`;
- for narration, `output_config` is null and isn't sent.

`tools` and `tool_choice` leave the request and the key entirely. `_record` sends every key except a null `output_config`.

**C.2 `max_tokens`** becomes 4096 in `config.toml`. Sonnet 5.5 may think before answering, and its thinking tokens count against `max_tokens`. At 1024, a long think could truncate the JSON.

**C.3 Parsing** (amends instruction 04 D.3 and G):

- Take the first `text` content block, ignoring any `thinking` blocks.
- A `stop_reason` of `max_tokens` or `refusal`, a missing text block, or text that fails `json.loads`, all count as invalid:
  - for the spec agent, that is unsupported with the D.3 reason format and flag False;
  - for the baseline, that is `sql = ""` with intent `error` and the reason as error text. It is not a decline.
- Otherwise, the spec agent validates `QuerySpec(**wire_to_spec(obj))`, and the baseline returns `obj["sql"]`.

**C.4 Narration** is unchanged, apart from also ignoring `thinking` blocks when joining text.

---

## D. Steps

**8c.1 Structured output.**

- Copy the 2 prompts.
- Build `rmbsq/llm/wire.py`, and change `client.py`, `spec_agent.py` and `baseline.py`, with C.2 in `config.toml`.
- Remove `spec_tool`, `spec_input_schema` and the `submit_sql` tool, and any test that only checked them.
- Convert the hand-written fixture responses in `tests/fixtures/llm_responses/` from `tool_use` blocks to `text` blocks holding the JSON. Fixture content otherwise stays the same.

Tests:

- `test_wire_schema_supported`: walk both schemas and assert that:
  - every object has `additionalProperties: false`, with every property in `required`;
  - no `maxItems`, `minLength`, `maxLength`, `minimum`, `maximum` or `$ref` appears;
  - no `minItems` above 1 appears.
- `test_wire_to_spec`:
  - the filters list with a repeated dimension;
  - `time: null`;
  - a clarify object carrying stray empty lists;
  - an answer object with 4 metrics, which comes back unsupported with flag False.
- `test_parse_thinking_then_text`: a fixture with a `thinking` block before the `text` block parses.
- `test_parse_refusal` and `test_parse_truncated`: both are invalid, for both agents.
- Every Section 4 and 5 test passes, after the fixture conversion.

Run `build_writeup.py` (still pending; nothing in the documents changes) and both pytest commands. Update `PLAN.md` steps 4.1, 4.2, 4.5 and `docs/CONVENTIONS_RESOLVED.md` N2, and mark O-47 decided (b). Commit as `step 8c.1: structured output in place of forced tools (O-47 b)`, with `PLAN.md` included.

**8c.2 Smoke test all 3 request types first.** With the key set, make exactly 3 live calls before the full run:

1. `rmbsq ask "What is the 90+ arrears rate by balance for each state now?" --live --show-sql`. This covers the spec request and the narration request.
2. 1 baseline request in record mode, for eval item Q11, through `baseline_sql` with Q11's `output_columns`. Then run the returned SQL with `run_baseline_sql`.

- If any of the 3 fails at the API, or returns a reply that fails C.3 parsing, stop. Report the full error or reply, with the key redacted, before spending on the full run.
- If all 3 succeed, put their outputs in the review.
- The calls they record land in `data/llm_cache/` and are reused by the eval run if they match.

**8c.3 Record.** Carry out instruction 08 B, from 8.1 to 8.6, exactly as written. Write the review as `review/section_8.md`, replacing the stopped version, and end with this status file.
