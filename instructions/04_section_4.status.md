# Status: session 4 (04_section_4)

## Outcome

Complete. Steps 4.0 to 4.7 are built, committed and pushed. Evidence is in
`review/section_4.md`. No live API call was made; every LLM test runs in replay mode
from hand-written fixture responses in a temp cache dir.

- Last step reached: 4.7.
- Stop reason: none.
- The 15 gold specs pass with the corrected S11 gold under strict spec order (O-37 (b)),
  on the small profile and with `-m full`.
- The locked read-only connection refuses CREATE, `COPY … TO`, `read_csv` of a local
  file, `SET threads = 4` and `INSTALL`, and runs `SELECT`.
  - `COPY … TO` fails with `Permission Error: … file system operations are disabled by
    configuration`, and creates no file.
  - A query over `range(10^11)` with a 1 s timeout raised `BaselineError` after 1.028 s
    (1.09 s in the test). The connection still answers `SELECT 1` afterwards.
- All 13 guard cases give exactly their `offending` lists.
- Resolution scores, measured with rapidfuzz 3.14.6 on the small profile:
  - `Blacktwon North` scores 93.33, so it is accepted;
  - `Joondalop` scores 88.89, so it clarifies, with options Joondalup, Boroondara and
    Onkaparinga;
  - `Narnia` scores at most 43.48, so it is unsupported.
- The end-to-end replay test returns the S02 gold table exactly (max scaled difference
  0.0), and the narration passes the guard.
- The same response recorded twice gives byte-identical cache files.

## What was built

- 4.0:
  - `rmbsq/db.py::connect_readonly`, used by every read connection;
  - strict spec order for metric columns in `rmbsq/semantic/compiler.py`;
  - the 3 prompts in `prompts/`, and the gold and guard fixtures in `tests/fixtures/`;
  - `tests/test_db.py`.
- 4.1: `rmbsq/llm/client.py` (`LLMClient`, `request_key`, `CacheMiss`, `MissingApiKey`), `tests/llm_helpers.py`.
- 4.2: `rmbsq/llm/spec_agent.py`.
- 4.3: `rmbsq/llm/resolve.py` (`deal_aliases`, `resolve_entities`).
- 4.4: `rmbsq/llm/guard.py`, `rmbsq/llm/narrate.py`.
- 4.5: `rmbsq/llm/baseline.py`.
- 4.6:
  - `rmbsq/llm/answer.py` and `rmbsq/cli.py`;
  - `[project.scripts] rmbsq = "rmbsq.cli:main"` in `pyproject.toml` (F11).
- 4.7: `PLAN.md` Section 4, `docs/CONVENTIONS_RESOLVED.md` N1 to N5, `decisions/OPEN.md`.
- Tests:
  - `tests/test_llm_client.py`, `tests/test_spec_agent.py`, `tests/test_resolve.py`;
  - `tests/test_guard.py`, `tests/test_baseline.py`, `tests/test_answer.py`;
  - 11 fixture responses in `tests/fixtures/llm_responses/`.

## Deviations (detail in the review, per step)

- **O-38:** `narrate` takes `catalog` as a 6th argument, because the guard needs the
  catalogue's deal names.
- Narration requests:
  - they are keyed with `tools: []` and `tool_choice: null`;
  - in record mode, those 2 keys are not sent to the API.
- Record mode:
  - the SDK client is created with `max_retries=0`, so only the C.4 retries happen;
  - `latency_s` times the attempt that succeeded.
- Clarify text is the question, a newline, then `Options: a; b; c`.
- The empty-table template keeps line 1 above the "No loans match …" line.
- `submit_sql` has no tool description, because G gives none.
- 2 tests were added beyond the named ones: `test_fuzzy_tie_clarifies` and
  `test_non_answer_unchanged`.
- `test_cli_cache_miss_exit_2` runs from a temp working directory, so no test reads the
  repo's `data/llm_cache/`.

## Test results (fresh clone of `4da0a0b`, Windows, Python 3.12.13, from the lock file)

- `pytest -q`: 183 passed, 20 deselected.
- `pytest -q -m full`: 20 passed, 183 deselected.

## Questions for the reviewer

1. **O-38 (step 4.4): `narrate` needs the catalogue for the number guard.** F.1 gives
   `narrate(question, spec, display_table, client, cfg)`. The F.2 guard strips the
   catalogue's deal names, which come from the database.
   - (a) A 6th argument `catalog`, which `answer` already holds. **Built.**
   - (b) Keep F.1's signature, and have `answer` run the guard and swap in the template.
2. **O-39 (step 4.3): "Filters are processed in key order".** This decides which failure
   wins when 2 filters both fail.
   - (a) The spec's own key order, as the model wrote the filters. **Built.**
   - (b) Sorted dimension names.

## Not done, for the user

- The fresh-clone folder `C:\s4fc` (with clone `C:\s4fc\r`) is left on disk. A safety
  check blocked deleting the earlier temp path, so nothing was removed. It is safe to
  delete.

## Last 3 commits on origin (before this file)

```
852fa33 section 4: review file
4da0a0b step 4.7: PLAN.md section 4 and conventions for the locked connection, cache key and guard
4939596 step 4.6: answer pipeline and rmbsq ask CLI, replay by default
```
