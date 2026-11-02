# Status: session 8c (08c_structured_output)

## Outcome

Complete. Step 8c.1, the smoke test (8c.2) and instruction 08 B 8.1 to 8.6 are done,
committed and pushed. Evidence is in `review/section_8.md`, which replaces the stopped
version.

- Last step reached: 8.6.
- Stop reason: none.
- Key: present for the live calls.

## Results

- Eval: the system is right on 37/40 and the baseline on 35/40.
  - System misses:
    - Q09: "Queensland" isn't resolved to `QLD`, so the answer is `unsupported`.
    - Q27 and Q28: the `arrears_units` trap is answered with a clarification.
  - Baseline misses:
    - Q28: declined.
    - Q35 to Q38: all 4 ambiguous items.
- Guard trips: none.
- Live API calls: 113 in all.
  - 2 smoke calls (8c.2).
  - 111 in the eval run: 40 spec, 40 baseline and 31 narration.
  - Every response stopped with `end_turn`, and 23 carried a `thinking` block.
- Tokens: 343,610 in and 20,548 out in all. The eval run alone used 337,482 in and
  20,379 out.
- Wall time of the record command: 282.5 s.
- 8.2: `grep -rl "sk-ant" data/llm_cache/ outputs/` found nothing.
- 8.3: state recorded. `Design_Response.pdf` is 3 pages, and `Results_Summary.pdf` is 1
  page at 5.5 cm.
- 8.4: `pytest -q` 244 passed. `pytest -q -m full` 58 passed, with
  `test_eval_replay_reproduces` now running and passing.
- 8.6, fresh clone of `46c8992` with no key set:
  - `pytest -q` 244 passed, and `pytest -q -m full` 58 passed;
  - `build_writeup.py` exit 0 in the recorded state;
  - `git status` clean.

## Deviations (detail in the review)

- **The Q11 baseline smoke call wasn't made before the full run.**
  - The 8c.2 amendment (`7a87921`) landed on origin after this session had pulled 08c, and
    it was only seen when the push was rejected.
  - The full run made the Q11 baseline request live, with a valid reply. The review shows
    it replayed from the cache through `baseline_sql`, with its SQL run by
    `run_baseline_sql`.
- The 3 unpushed local commits were rebased onto `7a87921` before the push. No pushed
  commit was rewritten.
- `test_parse_missing_tool_block` is renamed `test_parse_text_not_json`, with its body
  unchanged.
- An invalid baseline response raises a new `BaselineResponseError`. The eval records it
  as intent `error`.
- The 2 smoke-call cache entries are committed with the rest of `data/llm_cache/`.

## Questions for the reviewer

None.

## Not done, for the user

- The fresh-clone folder `C:\s8fc` is left on disk. It is safe to delete.
- The API key used for this session should be rotated. It was set only in the environment
  of the processes that made live calls, and it is in no file or commit.

## Last 3 commits on origin (before this file)

```
46c8992 writeup: recorded state
6642f76 eval: recorded cache and results
6489ef7 step 8c.1: structured output in place of forced tools (O-47 b)
```
