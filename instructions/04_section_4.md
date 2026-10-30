# 04 Section 4: LLM layer

Session 4 instructions for Claude Code. Build all of Section 4 (steps 4.0 to 4.7) in this session, without pausing. No live API call is made in this section; every test runs in replay mode. This file beats `PLAN.md`, which beats the kickoff (rule 13). Status file: `instructions/04_section_4.status.md`.

Files committed by chat Claude for this session (copy byte for byte; never edit):

| source | destination |
|---|---|
| `instructions/04_compiler_gold.json` | `tests/fixtures/compiler_gold.json` (replaces the Section 3 copy) |
| `instructions/04_prompts/spec_system.md` | `prompts/spec_system.md` |
| `instructions/04_prompts/narrate_system.md` | `prompts/narrate_system.md` |
| `instructions/04_prompts/baseline_system.md` | `prompts/baseline_system.md` |
| `instructions/04_guard_cases.json` | `tests/fixtures/guard_cases.json` |

---

## A. Approval of Section 3, and O-37

Section 3 is approved. Chat Claude checked it on Linux, installing from the lock file:

- `pytest -q`: 134 passed. `pytest -q -m full`: 20 passed.
- A full rebuild leaves every committed output unchanged, so the `--outputs` fix holds.
- Independently, every gold spec was compiled on every route it supports and executed on the full database, then compared with chat Claude's own pandas calculation, not with the hand SQL. The worst scaled difference is 7.8e-16.
- The Oracle SQL for S11 reads cleanly: `CASE` aggregates, `TO_DATE` literals and plain `ON` joins.

**O-37: (b).** The bug was in chat Claude's gold file: its hand SQL put stock metrics before flow metrics. Metric columns follow strict spec order. A user who asks for "CPR and balance" should see them in that order, and Section 5 compares output columns in spec order. `instructions/04_compiler_gold.json` corrects S11's hand SQL to select `period_label, cpr, balance_total`. No other spec, row count or route changes; chat Claude rechecked all 15 against pandas on both profiles.

---

## B. Locked database connection (step 4.0)

Chat Claude tested DuckDB 2.0.0 with a read-only connection. Read-only alone still let SQL write a file with `COPY … TO` and read any local file with `read_csv('/etc/hostname')`. The baseline runs SQL written by a model, so that is not acceptable.

With these settings, every one of those, `INSTALL` and any `SET`, was blocked, while `SELECT` worked:

```python
duckdb.connect(path, read_only=True,
               config={"enable_external_access": False, "lock_configuration": True, "threads": 1})
```

`con.interrupt()` from a `threading.Timer` stopped a long query after 1.00 s, and the connection stayed usable afterwards.

DuckDB refuses a second connection to the same file in one process with a different configuration. So every read connection in the project uses exactly this one, through a new function `rmbsq/db.py::connect_readonly(path: Path) -> DuckDBPyConnection`. That covers the catalogue, the compiler, `answer`, the baseline, the eval and the tests. `build_canonical` keeps its own write connection. `threads: 1` keeps DOUBLE sums deterministic (rule 9).

---

## C. LLM client and cache (`rmbsq/llm/client.py`)

**C.1 Request.** `LLMClient(cfg, mode="replay", cache_dir=Path("data/llm_cache"))`. `call(system, messages, tools, tool_choice) -> dict` builds:

```python
request = {"model": cfg.llm.model, "max_tokens": cfg.llm.max_tokens, "temperature": cfg.llm.temperature,
           "system": system, "messages": messages, "tools": tools, "tool_choice": tool_choice}
```

**C.2 Key.** The key is the SHA-256 hex of `json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` encoded in UTF-8.

**C.3 Cache file** `cache_dir/<key>.json`:

```json
{"key": "...", "request": {...}, "response": {...}, "latency_s": 1.234}
```

- `response` is `message.model_dump(mode="json")` from the Anthropic SDK.
- `latency_s` is the wall-clock seconds of the live call, rounded to 3 dp.
- The file is written with `json.dumps(…, sort_keys=True, indent=1, ensure_ascii=False)` and a trailing LF.
- There is no timestamp, so re-recording an identical response gives an identical file.

**C.4 Modes:**

- `replay`: a hit returns the stored response. A miss raises `CacheMiss(key)`.
- `record`: a hit returns the stored response without calling the API. A miss calls the API.
  - It retries on HTTP 429, 529 and 5xx, up to 3 times, after 2, 4 and 8 seconds.
  - A missing `ANTHROPIC_API_KEY` raises `MissingApiKey` before any network use.
  - The `anthropic.Anthropic` client is created only on the first record-mode miss, so replay never touches the network or the SDK client.

`call` returns the response dict. The client keeps a list `calls` of `{key, hit, latency_s, input_tokens, output_tokens}`, with tokens from `response["usage"]`.

---

## D. Question to spec (`rmbsq/llm/spec_agent.py`)

**D.1 Prompt rendering.** `render_spec_prompt(catalog, cfg) -> str` fills `prompts/spec_system.md`:

- `{{n_deals}}`: the number of rows in `dim_deal`.
- `{{window_start}}`, `{{window_end}}` and `{{latest}}`: from config.
- `{{metrics_table}}`: a markdown table `| name | kind | definition |` in metrics.yaml order.
- `{{dimensions_table}}`: a markdown table `| name | level | definition |` in dimensions.yaml order.
- `{{allowed_values}}`: 1 line per dimension in dimensions.yaml order, `- name: v1, v2, …`, with the values from `Catalog.allowed_values` comma-separated. The one exception: `deal_name` lists all names, then adds `(aliases such as "Harbour 19-1" or "HARB19-1" are also accepted)`.

A placeholder left unfilled raises an error.

**D.2 Tool.** `submit_spec`, with description "Submit the query spec for the question.". Its `input_schema` is `QuerySpec.model_json_schema()` with every `$ref` inlined from `$defs`, `$defs` removed and every `title` key removed. A test asserts the result has no `$ref`. The call uses `tool_choice={"type": "tool", "name": "submit_spec"}`, and `messages=[{"role": "user", "content": question}]`.

**D.3 Parsing.** `question_to_spec(question, client, catalog) -> tuple[QuerySpec, bool]`. It takes the first `tool_use` block named `submit_spec` and validates its `input`. If the block is missing or validation fails, it returns `QuerySpec(intent="unsupported", unsupported_reason="invalid spec from model: <first error, at most 200 chars>")` with the flag False. Otherwise it returns the spec with the flag True.

---

## E. Entity resolution (`rmbsq/llm/resolve.py`), for intent answer only

`resolve_entities(spec, catalog, aliases) -> QuerySpec`. Every filter value is resolved in this order:

1. **Exact, case-insensitive,** against the dimension's allowed values. The stored casing is kept.
2. **Deal aliases.** For `deal_name`, and for `deal_id` values that are not deal ids, the alias table is checked case-insensitively. For each deal, the aliases of `"HARB 2019-1"` are `"Harbour 19-1"` (first word of originator_name), `"HARB 19-1"` and `"HARB19-1"`. 2-digit years are zero padded. A deal_id filter value that matches a deal_name or an alias moves to a `deal_name` filter.
3. **Flags** accept `yes, no, true, false, y, n` (case-insensitive) and map to `yes` or `no`. **Years** must be integers that are allowed values. **dpd_bucket** must match a label exactly. Anything else becomes `unsupported`, with reason `unknown <dimension> value '<v>'`.
4. **Fuzzy,** for the text dimensions only: deal_name (values plus aliases), originator, trustee_format, city, state, area, suburb, rate_type and occupancy.
   - The score is `rapidfuzz.fuzz.token_set_ratio(value.lower(), candidate.lower())` against every candidate. An alias candidate maps to its deal_name.
   - A unique best score ≥ `resolve.accept` (90) replaces the value.
   - A best in [`resolve.clarify`, `resolve.accept`), or a tie for best at ≥ `resolve.clarify`, turns the whole spec into `clarify`. The question is `Which <dimension> did you mean by '<v>'?`. The options are the top `resolve.top_k` distinct canonical values by score descending, then name ascending, at least 2.
   - A best < 75 becomes `unsupported`, with reason `unknown <dimension> value '<v>'`.

The first value that becomes clarify or unsupported decides the result. Filters are processed in key order, and values in list order.

---

## F. Narration and the number guard

**F.1 Narration** (`rmbsq/llm/narrate.py`). `narrate(question, spec, display_table, client, cfg) -> tuple[str, bool, list[str]]` returns the text, guard_tripped and the offending tokens.

- System: `prompts/narrate_system.md` with `{{max_words}}` from config.
- User message: `json.dumps({"question": …, "spec": spec.model_dump(mode="json"), "table": {"columns": […], "rows": [[…], …]}, "truncated": bool}, ensure_ascii=False, sort_keys=True)`. The table holds at most `narration_max_rows` rows of display strings.
- There are no tools. The text is the concatenation of the response's text blocks, stripped.
- If the guard trips, the returned text is `template_answer(spec, display_table)`.

**F.2 Guard** (`rmbsq/llm/guard.py`). `number_guard(text, question, display_table, catalog) -> list[str]` works in this order:

1. **Strip** from the text, in this order:
   - every `\d{4}-\d{2}` and `\d{4}-Q[1-4]` token;
   - every deal_name in the catalogue;
   - every fixed dimension label in the catalogue, longest first.

   Strings are replaced by a space. A label is stripped only where it is not touching a letter, a digit or `.` on either side.
2. **Extract** with `re.finditer(r"-?\d[\d,]*\.?\d*(%|m\b)?", text)`. The token is the number with commas removed and a trailing `.` dropped, followed by its unit (`%`, `m` or nothing).
3. **Ignore:**
   - a token whose number appears as a number in the question (extract from the question with the same regex, units ignored);
   - a bare token (no unit) that is a whole year from 2016 to 2026.
4. **Allowed tokens** are made by applying step 2's extraction and normalisation to every display cell in the table (`A$412.3m` gives `412.3m`; `12,345` gives `12345`).
5. **Return** the remaining tokens that are not allowed, in text order, without duplicates.

**F.3 Template answer.** `template_answer(spec, display_table) -> str`:

- line 1: `Result computed from the data (narration withheld because it cited a number not in the table):`;
- 1 line per row for up to 10 rows, `- <dimension values joined by ' / ', then period_label>: <metric> <value>; <metric> <value>`;
- if there are more rows: `- … and N more rows.`;
- for an empty table: `No loans match the filters and dates in the query.`.

---

## G. Baseline (`rmbsq/llm/baseline.py`)

`baseline_sql(question, output_columns, client, cfg) -> str` uses `prompts/baseline_system.md`, with `{{window_start}}`, `{{window_end}}` and `{{latest}}` filled.

- User message: `question + "\n\nOutput columns, in order: " + ", ".join(output_columns)`.
- Tool `submit_sql`, input schema `{"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}`, forced with `tool_choice`. It returns the `sql` string, or "" if the block is missing.

`run_baseline_sql(sql, con, cfg) -> pd.DataFrame | None` runs the SQL on the B connection with a `threading.Timer(cfg.llm.baseline_timeout_s, con.interrupt)`. It returns None for an empty string, and raises `BaselineError(message)` on any database error or interrupt.

---

## H. The pipeline and CLI

`rmbsq/llm/answer.py::answer(question, client, con, catalog, cfg) -> Answer`. `Answer` is a dataclass with these fields:

- question;
- spec_raw, spec_valid, spec (after resolution);
- route, sql_duckdb, sql_oracle;
- table (raw DataFrame or None), display (formatted DataFrame or None);
- text, guard_tripped, offending;
- calls (the client's call log for this answer).

The steps:

1. `question_to_spec`.
2. If the intent is answer, `resolve_entities`.
3. If the intent is still answer, compile and execute it, `format_table` the result, then narrate.
4. For clarify, text = `clarify.question` plus `Options: a; b; c`. For unsupported, text = the reason.

`rmbsq/cli.py`: `rmbsq ask "<question>" [--live] [--show-sql] [--db PATH]`. `--live` uses record mode, and the default is replay. It prints the text, then the display table as aligned text, then with `--show-sql` the Oracle SQL. The default db is `data/canonical/rmbs.duckdb`. A `CacheMiss` in replay prints `not in the cache; run with --live` and exits with code 2.

---

## I. Steps, with tests

Hand-written fixture responses live in `tests/fixtures/llm_responses/<name>.json`, each a full Messages API response dict (`id, type, role, model, content, stop_reason, stop_sequence, usage`). Tests build the request exactly as the code would, compute its key with the client's key function, and write `{key, request, response, latency_s}` into a temp cache dir. No test reads `data/llm_cache/`.

**4.0 Fixtures, prompts, locked connection.**
- Copy the files in the header.
- Change the compiler to strict spec order for metric columns (A).
- Add `rmbsq/db.py::connect_readonly` (B) and switch every read connection to it.
- Tests: `test_fifteen_specs_match_hand_sql` passes with the new fixture. `test_readonly_blocks`: on `small_db`, CREATE, `COPY … TO` a temp file, `read_csv` of a temp file and `SET threads=4` all raise, `SELECT` works, and no file is created.

**4.1 Client** (C). Tests:
- `test_key_stable`: the same request in a different dict order gives the same key;
- `test_replay_hit`;
- `test_replay_miss_raises`;
- `test_record_hit_does_not_call_api` (monkeypatch the SDK constructor to raise if called);
- `test_missing_key_raises` (record mode with the env var removed, on a miss);
- `test_cache_file_format` (keys, sort order, trailing LF).

**4.2 Spec agent** (D). Tests:
- `test_prompt_has_every_name`: all 12 metric and 18 dimension names appear, and no `{{` remains;
- `test_tool_schema_inlined`: no `$ref` and no `title`;
- `test_parse_fixture_answer`, `test_parse_fixture_clarify` and `test_parse_fixture_unsupported`: 3 fixture responses with valid `submit_spec` inputs;
- `test_parse_invalid_spec`: a fixture whose input has 4 metrics returns unsupported and False;
- `test_parse_missing_tool_block`: a text-only response returns unsupported and False.

**4.3 Resolution** (E). Tests on `small_db`:
- `test_exact_case_insensitive` ("nsw" becomes NSW);
- `test_aliases` (all 3 alias forms of D001's name, plus "d001" as a deal_id);
- `test_deal_id_to_deal_name` ("HARB 2019-1" given under deal_id moves to deal_name);
- `test_fuzzy_accept` ("Blacktwon North" becomes Blacktown North);
- `test_fuzzy_clarify` (a value between 75 and 90, with its options);
- `test_unknown_unsupported` ("Narnia" as a suburb);
- `test_flags_and_years` ("Y" becomes yes; 2031 as vintage_year is unsupported);
- `test_first_failure_decides`.

Record the scores that `rapidfuzz` actually gives for each fuzzy test value in the review. Choose the clarify-band test value by measuring, and print its score.

**4.4 Narration and guard** (F). Tests:
- `test_guard_cases`: every case in `guard_cases.json` gives exactly its `offending` list;
- `test_narrate_passes`: a fixture narration that passes is returned unchanged;
- `test_narrate_trips_to_template`: a fixture narration with 1 invented figure returns the F.3 template and that token;
- `test_template_formats`: 3 rows, 12 rows and 0 rows;
- `test_truncation_flag`: a 60-row table sends 50 rows with `truncated: true`.

**4.5 Baseline** (G). Tests:
- `test_baseline_parse` (fixture with SQL), and an empty-SQL fixture returning "";
- `test_baseline_timeout` (timeout set to 1 s through a config copy, on a query over `range(10^11)`, raises `BaselineError` within 3 s);
- `test_baseline_cannot_write`: `COPY … TO` raises `BaselineError` and creates no file;
- `test_baseline_runs_select` on `small_db`.

**4.6 Pipeline and CLI** (H). Tests:
- `test_answer_end_to_end_replay`: fixtures for a spec call (S02's spec) and a narration call. The result's table equals the S02 gold, and the text equals the narration;
- `test_answer_clarify` and `test_answer_unsupported`;
- `test_cli_cache_miss_exit_2`.

**4.7 Docs.** Update `PLAN.md` steps 4.0 to 4.7, and `docs/CONVENTIONS_RESOLVED.md` for B, C.2 and F.2. Commit `PLAN.md`.

---

## J. Review evidence (`review/section_4.md`)

1. The rendered spec prompt in full (from `small_db`), and its length in characters.
2. The inlined tool schema in full.
3. A table of every resolution test: input, rapidfuzz scores for the top 3 candidates, and outcome.
4. Every guard case: text, expected offending list, actual offending list.
5. The 3 template outputs.
6. The baseline timeout test's measured seconds, and the exception message from `COPY … TO`.
7. 1 fixture cache file in full.
8. Both pytest outputs from a fresh clone (default, and `-m full`).

Then write `instructions/04_section_4.status.md` and push.
