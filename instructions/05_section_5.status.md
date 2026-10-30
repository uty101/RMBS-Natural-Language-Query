# Status: session 5 (05_section_5)

## Outcome

Complete except the live eval run (no API key, by design). Steps 5.0 to 5.3 and 5.5 to
5.7 are built, committed and pushed. Evidence is in `review/section_5.md`.

- Last step reached: 5.7.
- Stop reason: none. Step 5.4, the live run, was not made, because `ANTHROPIC_API_KEY`
  is not set in the environment. D.3 says this is not a failure.
  - `data/llm_cache/` is empty, and no eval output CSV is written.
  - No API call was made in this session.
- The gold check holds on all 34 answer items on the full profile, by the C.3 rule and
  also within `gold_tol_abs`. The largest error is 1.61e-15 (Q25).
- The full benchmark ran (copies = 36), and `outputs/scale_benchmark.csv` is committed
  with 272 rows.
  - The tiled build took 82.7 s.
  - `rmbs.duckdb` is 33,828,864 bytes; `rmbs_x36.duckdb` is 1,162,358,784 bytes.
  - Fact rows: 773,336 on 1x and 27,840,096 on 36x.
  - Median of median_s over the 34 items, threads 1: 1x auto 0.0214 s, 36x auto 0.0313 s,
    1x fact 0.0341 s, 36x fact 0.3225 s.
- `test_eval_replay_reproduces` skips with "no recorded eval cache", the one permitted
  skip. It runs unchanged once the cache exists.

## To finish the live eval later

In PowerShell, from the repo root:

```powershell
$env:ANTHROPIC_API_KEY = "<key>"
python scripts/run_eval.py --mode record
```

Then commit every file in `data/llm_cache/` with `outputs/eval_results.csv`,
`outputs/eval_summary.csv`, `outputs/trap_failures.csv` and `outputs/eval_detail.jsonl`.
Run `pytest -q -m full`, where `test_eval_replay_reproduces` will then run instead of
skipping. Review items G.1 to G.7 come from that run. The cost is about 40 spec calls,
34 narration calls and 40 baseline calls.

## What was built

- 5.0:
  - `eval/questions.yaml`, a byte for byte copy;
  - `load_items` and `EvalItem` in `rmbsq/eval/run.py`;
  - `PLAN.md` Section 5;
  - `tests/test_eval_items.py`.
- 5.1: `compare_result` (C.3) in `rmbsq/eval/score.py`; `tests/test_eval_gold.py` (full).
- 5.2: `score_row`, `score` and `wilson` in `rmbsq/eval/score.py`; `tests/test_eval_score.py`.
- 5.3:
  - `run_system`, `run_baseline` and `run_eval` in `rmbsq/eval/run.py`;
  - `rmbsq/eval/report.py`;
  - `scripts/run_eval.py --mode {record,replay}`;
  - `tests/test_eval_run.py`.
- 5.5: `tests/test_eval_replay.py` (full).
- 5.6: `build_trap_failures` (in 5.3); `tests/test_eval_trap_failures.py`.
- 5.7:
  - `connect_readonly(path, threads=1)`;
  - `rmbsq/eval/benchmark.py` and `scripts/run_benchmark.py`;
  - `tests/test_benchmark.py`;
  - `outputs/scale_benchmark.csv`.

## Deviations (detail in the review, per step)

- `eval_detail.jsonl` adds 4 keys to the D.2 list: `system`, `item_id`, `columns` and,
  for the system, `offending`.
- `guard_tripped` is blank for the baseline.
- The CSVs quote any cell holding a comma, quote or line break, because DuckDB error
  text holds all 3.
- The 5.1 test also asserts `max_abs_err <= gold_tol_abs`. This is stricter than C.3,
  not looser.
- In `scale_benchmark.csv`, `route` is the requested route, and only `execute` is timed.
- The benchmark was run twice. The committed CSV is the second run, made with nothing
  else running. Its non-timing columns are identical to the first run's.
- 5 tests were added beyond the named ones:
  - `test_non_numeric_value_is_wrong`;
  - `test_record_with_full_cache_matches_replay`;
  - `test_tiled_spec_rewrites_deal_filters`;
  - `test_connect_readonly_threads`;
  - `test_runner_formats`, which is named here because F 5.3 asks for the D.2 format
    checks without naming the test.
- Step 5.6 was committed before 5.5. There is no 5.4 commit.

## Test results (fresh clone of `9005d56`, Windows, Python 3.12.13, from the lock file)

- `pytest -q`: 222 passed, 55 deselected.
- `pytest -q -m full`: 54 passed, 1 skipped (no recorded eval cache), 222 deselected.

## Questions for the reviewer

1. **O-40 (step 5.7): S01 and S12 carry no balance_total or loan_count.**
   - (a) Run each spec as written for the ratios, then the same spec with metrics
     `[balance_total, loan_count]` for the 3 × check. **Built.**
   - (b) Check the totals only where they fit: S01 with both added, and S12 with 1 total
     replacing `smm_vol`.
2. **O-41 (step 5.7): what `db_rows` counts.**
   - (a) `fact_loan_month` rows. **Built.**
   - (b) The total over all 7 canonical tables.
3. **O-42 (step 5.3): the system's intent when its compile or execute fails.**
   - (a) Intent `error`, with the exception text, scored wrong. **Built.**
   - (b) The spec's own intent (`answer`), which needs `answer` to return the spec with
     the exception.

## Not done, for the user

- The fresh-clone folder `C:\s5fc` (with clone `C:\s5fc\r`) is left on disk. It is safe
  to delete, as are the earlier `C:\s3fc` and `C:\s4fc`.
- `data/canonical/rmbs_x36.duckdb` (1.16 GB, git-ignored) is left on disk. It can be
  rebuilt with `python scripts/run_benchmark.py`.

## Last 3 commits on origin (before this file)

```
e32d99a section 5: review file
9005d56 step 5.7: tiled 36x database and scale benchmark on 1x and 36x, routes auto and fact, 1 and default threads
4e5efe5 step 5.5: replay from the committed cache reproduces the 4 eval outputs, skipped while the cache is empty
```
