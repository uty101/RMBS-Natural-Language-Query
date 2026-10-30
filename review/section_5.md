# Review: Section 5, eval and scale benchmark

Follow this template exactly. Every number below must be backed by raw rows or raw
output printed in full in this file (CLAUDE.md rule 10). No paraphrased results.

## 1. Outcome

- Instruction file: `instructions/05_section_5.md`
- Outcome: complete except the live eval run (no API key, by design)
- Last step reached: 5.7
- Stop reason (if stopped): none. Step 5.4 was not run because `ANTHROPIC_API_KEY` is
  not set in the environment, which D.3 says is not a failure. Every other step is built
  in full, including the full benchmark run and `outputs/scale_benchmark.csv`.
  `data/llm_cache/` is left empty and no eval output CSV is written.

## 2. Commits

Output of `git log --oneline` for this section's commits, oldest last, pasted verbatim.

```
9005d56 step 5.7: tiled 36x database and scale benchmark on 1x and 36x, routes auto and fact, 1 and default threads
4e5efe5 step 5.5: replay from the committed cache reproduces the 4 eval outputs, skipped while the cache is empty
135a403 step 5.6: trap failures row count equals the wrong trap answers in eval_results.csv
8062e6b step 5.3: eval runner for both systems, replay and record, with results, summary, trap and detail outputs
7cbcda3 step 5.2: answer, clarify and unsupported scoring for both systems, and the Wilson interval
10c434b step 5.1: C.3 result comparison and the gold spec check on the full profile
1e5f2c1 step 5.0: questions file, load_items and PLAN.md section 5 for the trap set, scoring and eval detail
```

There is no step 5.4 commit: it would hold the cache and the eval outputs, which need
the key. Step 5.6 was committed before 5.5, because its test was split out of the step
5.3 test file.

## 3. Steps

Instruction 05 G evidence items are marked G.1 to G.9. Unless a block says the small
profile, every number comes from the full canonical database
(`data/canonical/rmbs.duckdb`). It was rebuilt this session from the committed
`data/raw/` by `scripts/build_canonical.py`, with no change to the committed outputs.

### Step 5.0: questions file

- Files: `eval/questions.yaml` (byte for byte copy of `instructions/05_questions.yaml`),
  `rmbsq/eval/run.py` (`EvalItem`, `load_items`), `tests/test_eval_items.py`, and
  `PLAN.md` Section 5, rewritten for B.1, C and `outputs/eval_detail.jsonl`.
- Signatures implemented: `load_items(path: Path) -> list[EvalItem]`.
- Tests: `tests/test_eval_items.py::test_questions_file`, result passed.
- Outputs: none.
- Evidence: the copy, then id, category, trap, expected intent and output columns for
  all 40 items:

```
$ cmp instructions/05_questions.yaml eval/questions.yaml   (no output: identical)
$ sha256sum instructions/05_questions.yaml eval/questions.yaml
73ede5625bfa899aee10015bdf4bf59797068879144f8f53af5a2ec77d0536d3 *instructions/05_questions.yaml
73ede5625bfa899aee10015bdf4bf59797068879144f8f53af5a2ec77d0536d3 *eval/questions.yaml
```

```
Q01 simple      -               answer      period_label,arrears_90p_bal
Q02 simple      -               answer      period_label,balance_total
Q03 simple      -               answer      period_label,loan_count
Q04 simple      -               answer      period_label,wa_indexed_ltv
Q05 simple      -               answer      period_label,wa_rate
Q06 simple      -               answer      period_label,hardship_share_bal
Q07 simple      -               answer      period_label,cpr
Q08 simple      -               answer      period_label,arrears_30p_bal
Q09 simple      -               answer      period_label,wa_orig_ltv
Q10 simple      -               answer      period_label,arrears_90p_bal
Q11 grouped     -               answer      state,period_label,arrears_90p_bal
Q12 grouped     -               answer      originator,period_label,balance_total
Q13 grouped     -               answer      ltv_bucket_indexed,period_label,arrears_30p_bal
Q14 grouped     -               answer      rate_type,period_label,wa_rate
Q15 grouped     -               answer      deal_name,period_label,arrears_90p_bal
Q16 grouped     -               answer      io_flag,period_label,arrears_90p_bal
Q17 grouped     -               answer      vintage_year,period_label,loan_count,balance_total
Q18 grouped     -               answer      city,period_label,hardship_share_bal
Q19 grouped     -               answer      occupancy,period_label,arrears_90p_bal
Q20 grouped     -               answer      originator,period_label,cpr
Q21 time        -               answer      period_label,arrears_90p_bal
Q22 time        -               answer      period_label,cdr
Q23 time        -               answer      period_label,arrears_30p_bal
Q24 time        -               answer      rate_type,period_label,cpr
Q25 time        -               answer      period_label,wa_indexed_ltv
Q26 time        -               answer      period_label,cpr
Q27 trap        arrears_units   answer      period_label,arrears_30p_bal
Q28 trap        arrears_units   answer      period_label,arrears_90p_bal
Q29 trap        call_as_prepay  answer      period_label,cpr
Q30 trap        call_as_prepay  answer      period_label,cpr
Q31 trap        exit_rows       answer      period_label,loan_count
Q32 trap        exit_rows       answer      period_label,loan_count
Q33 trap        weighting       answer      period_label,wa_indexed_ltv
Q34 trap        weighting       answer      period_label,wa_rate
Q35 ambiguous   -               clarify     
Q36 ambiguous   -               clarify     
Q37 ambiguous   -               clarify     
Q38 ambiguous   -               clarify     
Q39 unsupported -               unsupported 
Q40 unsupported -               unsupported 
```

- Deviations from PLAN.md or the instruction file: the instruction names only the test,
  so the file name `tests/test_eval_items.py` is mine.

### Step 5.1: gold check

- Files: `rmbsq/eval/score.py` (`Check`, `norm_key`, `compare_result`, the C.3 rule),
  `tests/test_eval_gold.py`.
- Signatures implemented: `compare_result(result, gold, spec, output_columns) -> Check`.
- Tests: `tests/test_eval_gold.py::test_gold_spec_equals_gold_sql[Q01..Q34]` (marked
  `full`), result 34 passed.
- Outputs: none.
- Evidence: for each item, the gold row count, then the C.3 check (`n_values_checked`
  and `max_abs_err`). The largest error is 1.609823385706477e-15 (Q25):

```
Q01 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q02 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q03 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q04 1 Check(correct=True, n_values_checked=1, max_abs_err=2.220446049250313e-16, reason='')
.Q05 1 Check(correct=True, n_values_checked=1, max_abs_err=6.938893903907228e-17, reason='')
.Q06 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q07 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q08 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q09 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q10 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q11 5 Check(correct=True, n_values_checked=5, max_abs_err=0.0, reason='')
.Q12 5 Check(correct=True, n_values_checked=5, max_abs_err=0.0, reason='')
.Q13 4 Check(correct=True, n_values_checked=4, max_abs_err=0.0, reason='')
.Q14 2 Check(correct=True, n_values_checked=2, max_abs_err=0.0, reason='')
.Q15 5 Check(correct=True, n_values_checked=5, max_abs_err=0.0, reason='')
.Q16 2 Check(correct=True, n_values_checked=2, max_abs_err=0.0, reason='')
.Q17 7 Check(correct=True, n_values_checked=14, max_abs_err=0.0, reason='')
.Q18 5 Check(correct=True, n_values_checked=5, max_abs_err=0.0, reason='')
.Q19 2 Check(correct=True, n_values_checked=2, max_abs_err=0.0, reason='')
.Q20 5 Check(correct=True, n_values_checked=5, max_abs_err=0.0, reason='')
.Q21 12 Check(correct=True, n_values_checked=12, max_abs_err=0.0, reason='')
.Q22 4 Check(correct=True, n_values_checked=4, max_abs_err=0.0, reason='')
.Q23 6 Check(correct=True, n_values_checked=6, max_abs_err=0.0, reason='')
.Q24 8 Check(correct=True, n_values_checked=8, max_abs_err=0.0, reason='')
.Q25 4 Check(correct=True, n_values_checked=4, max_abs_err=1.609823385706477e-15, reason='')
.Q26 12 Check(correct=True, n_values_checked=12, max_abs_err=0.0, reason='')
.Q27 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q28 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q29 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q30 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q31 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q32 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.Q33 1 Check(correct=True, n_values_checked=1, max_abs_err=1.1102230246251565e-15, reason='')
.Q34 1 Check(correct=True, n_values_checked=1, max_abs_err=0.0, reason='')
.
34 passed in 22.54s
```

- Deviations from PLAN.md or the instruction file: besides the C.3 rule, the test also
  asserts `max_abs_err <= gold_tol_abs` (1e-9, kickoff 6.11). That is stricter than
  C.3, not looser, and all 34 items pass it.

### Step 5.2: scoring

- Files: `rmbsq/eval/score.py` (`score_row`, `score`, `wilson`), `tests/test_eval_score.py`.
- Signatures implemented: `score(results: DataFrame, items) -> DataFrame`,
  `wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]`.
- Tests: the 27 cases below, result passed.
- Outputs: none.
- Evidence: the Wilson hand values, worked in exact decimal arithmetic (z = 1.96, z² = 3.8416):

```
(7, 10):  k + z²/2 = 8.9208     n + z² = 13.8416   k(n-k)/n + z²/4 = 2.1 + 0.9604 = 3.0604
          sqrt(3.0604) = 1.749399897108
          centre = 8.9208 / 13.8416 = 0.644491966247
          half   = 1.96 x 1.749399897108 / 13.8416 = 0.247718746267
          lo = 0.396773219980 -> 0.396773     hi = 0.892210712514 -> 0.892211
(40, 40): k + z²/2 = 41.9208    n + z² = 43.8416   k(n-k)/n + z²/4 = 0 + 0.9604 = 0.9604
          sqrt(0.9604) = 0.98
          centre = 41.9208 / 43.8416 = 0.956187730375
          half   = 1.96 x 0.98 / 43.8416 = 0.043812269625
          lo = 0.912375460750 -> 0.912375     hi = 1.000000000000 -> 1.000000
```

  The scoring cases and their verdicts. Each test id names its case, and every expected
  verdict is in `tests/test_eval_score.py`:

```
tests/test_eval_score.py::test_key_order_without_order_is_a_multiset PASSED [  3%]
tests/test_eval_score.py::test_key_order_with_order_must_match PASSED    [  7%]
tests/test_eval_score.py::test_pct_absolute_tolerance[9e-07-True] PASSED [ 10%]
tests/test_eval_score.py::test_pct_absolute_tolerance[-9e-07-True] PASSED [ 14%]
tests/test_eval_score.py::test_pct_absolute_tolerance[1.1e-06-False] PASSED [ 17%]
tests/test_eval_score.py::test_pct_absolute_tolerance[-1.1e-06-False] PASSED [ 21%]
tests/test_eval_score.py::test_aud_m_relative_tolerance[900.0-True] PASSED [ 25%]
tests/test_eval_score.py::test_aud_m_relative_tolerance[-900.0-True] PASSED [ 28%]
tests/test_eval_score.py::test_aud_m_relative_tolerance[1100.0-False] PASSED [ 32%]
tests/test_eval_score.py::test_aud_m_relative_tolerance[-1100.0-False] PASSED [ 35%]
tests/test_eval_score.py::test_count_exact[1234-True] PASSED             [ 39%]
tests/test_eval_score.py::test_count_exact[1234.0-True] PASSED           [ 42%]
tests/test_eval_score.py::test_count_exact[1234.0000000005-True] PASSED  [ 46%]
tests/test_eval_score.py::test_count_exact[1233.9999999995-True] PASSED  [ 50%]
tests/test_eval_score.py::test_count_exact[1234.000000002-False] PASSED  [ 53%]
tests/test_eval_score.py::test_count_exact[1234.4-False] PASSED          [ 57%]
tests/test_eval_score.py::test_count_exact[1235-False] PASSED            [ 60%]
tests/test_eval_score.py::test_extra_columns_ignored PASSED              [ 64%]
tests/test_eval_score.py::test_missing_column_is_wrong PASSED            [ 67%]
tests/test_eval_score.py::test_null_is_wrong[None] PASSED                [ 71%]
tests/test_eval_score.py::test_null_is_wrong[nan] PASSED                 [ 75%]
tests/test_eval_score.py::test_null_is_wrong[null2] PASSED               [ 78%]
tests/test_eval_score.py::test_non_numeric_value_is_wrong PASSED         [ 82%]
tests/test_eval_score.py::test_bool_and_float_keys_normalise PASSED      [ 85%]
tests/test_eval_score.py::test_answer_rules_both_systems PASSED          [ 89%]
tests/test_eval_score.py::test_clarify_and_unsupported_rules_both_systems PASSED [ 92%]
tests/test_eval_score.py::test_wilson_hand_values PASSED                 [ 96%]
tests/test_eval_items.py::test_questions_file PASSED                     [100%]
============================= 28 passed in 0.85s ==============================
```

- Deviations from PLAN.md or the instruction file:
  - `wilson` is in `rmbsq/eval/score.py`, where instruction 05 C puts it. The old
    PLAN.md paragraph had `report.py`.
  - The count rule's 1e-9 is a literal (`COUNT_INT_TOL`) citing C.3, under rule 6's
    exception for constants written in an instruction file. `pct` and `aud_m` read
    `tol_ratio_abs` and `tol_balance_rel` from `config.toml`.
  - A non-numeric result cell scores as wrong. This is an added case,
    `test_non_numeric_value_is_wrong`.

### Step 5.3: runner

- Files: `rmbsq/eval/run.py` (`run_system`, `run_baseline`, `gold_result`, `run_eval`),
  `rmbsq/eval/report.py` (`summarise`, `build_trap_failures`, `detail_lines`,
  `write_table`, `write_outputs`), `scripts/run_eval.py`, `tests/test_eval_run.py`.
- Signatures implemented: `run_system(items, client, con, catalog) -> DataFrame` and
  `run_baseline(items, client, con) -> DataFrame`, as in kickoff part 7, with cfg read
  from `client.cfg`; `run_eval(items, db, cache_dir, out_dir, cfg, mode="replay") -> DataFrame`.
- Tests: `test_runner_three_items`, `test_runner_formats`,
  `test_record_with_full_cache_matches_replay`, result passed.
- Outputs: none in `outputs/`, because there is no key. The fixture run (small profile,
  Q02, Q35, Q39) writes into a temp dir.
- Evidence: the tests, then the files the fixture run writes (small profile). The
  fixture responses:
  - system: Q02's spec is its gold spec, with a narration quoting the table's value;
    Q35 is a clarify; Q39 is an unsupported;
  - baseline: Q02 is its gold SQL, Q35 queries a missing table, and Q39 is the empty
    string.

```
tests/test_eval_run.py::test_runner_three_items PASSED                   [ 25%]
tests/test_eval_run.py::test_runner_formats PASSED                       [ 50%]
tests/test_eval_run.py::test_record_with_full_cache_matches_replay PASSED [ 75%]
tests/test_eval_trap_failures.py::test_trap_failures_row_count PASSED    [100%]
============================= 4 passed in 20.07s ==============================
```

```
eval_results.csv:
system,item_id,category,intent,correct,n_values_checked,max_abs_err,latency_s,input_tokens,output_tokens,guard_tripped,error
system,Q02,simple,answer,True,1,0.0000000000,1.7500000000,3800,130,False,
system,Q35,ambiguous,clarify,True,0,,1.2500000000,3000,100,False,
system,Q39,unsupported,unsupported,True,0,,1.0000000000,3000,100,False,
baseline,Q02,simple,sql,True,1,0.0000000000,2.0000000000,2000,50,,
baseline,Q35,ambiguous,error,False,0,,2.5000000000,2000,50,,"Catalog Error: Table with name no_such_table does not exist!
Did you mean ""cash_rate""?

LINE 1: SELECT * FROM no_such_table
                      ^^^^^^^^^^^^^"
baseline,Q39,unsupported,decline,True,0,,0.5000000000,2000,50,,

eval_summary.csv:
system,category,n,k,accuracy,wilson_lo,wilson_hi
system,simple,1,1,1.0000000000,0.2065432915,1.0000000000
system,ambiguous,1,1,1.0000000000,0.2065432915,1.0000000000
system,unsupported,1,1,1.0000000000,0.2065432915,1.0000000000
system,total,3,3,1.0000000000,0.4384939196,1.0000000000
baseline,simple,1,1,1.0000000000,0.2065432915,1.0000000000
baseline,ambiguous,1,0,0.0000000000,0.0000000000,0.7934567085
baseline,unsupported,1,1,1.0000000000,0.2065432915,1.0000000000
baseline,total,3,2,0.6666666667,0.2076549551,0.9385096847

trap_failures.csv:
system,item_id,trap,expected,got

eval_detail.jsonl, line 1 (system Q02) and line 4 (baseline Q02), sql shortened here to its first 60 characters:
{"columns": ["period_label", "balance_total"], "correct": true, "error": "", "intent": "answer", "item_id": "Q02", "offending": [], "question": "What is the total outstanding balance of the pool at the latest month?", "rows": [["2026-09", "A$58.3m"]], "spec": {"clarify": null, "filters": {}, "group_by": [], "intent": "answer", "metrics": ["balance_total"], "order": null, "time": {"end": "2026-09", "grain": "month", "shape": "point", "start": "2026-09"}, "unsupported_reason": null}, "sql_duckdb": "WITH parts AS (\n  SELECT\n    a.period,\n    SUM(a.loan_count)...", "system": "system", "text": "The pool's outstanding balance at 2026-09 was A$58.3m."}
{"columns": ["period_label", "balance_total"], "correct": true, "error": "", "intent": "sql", "item_id": "Q02", "question": "What is the total outstanding balance of the pool at the latest month?", "rows": [["2026-09", "A$58.3m"]], "sql": "WITH parts AS (\n  SELECT f.period,\n    COUNT(*) FILTER (WHER...", "system": "baseline"}
eval_detail.jsonl lines 2, 3, 5, 6 in full:
{"columns": [], "correct": true, "error": "", "intent": "clarify", "item_id": "Q35", "offending": [], "question": "What are arrears in NSW?", "rows": [], "spec": {"clarify": {"options": ["30+ days", "90+ days"], "question": "Which arrears threshold do you mean?"}, "filters": {}, "group_by": [], "intent": "clarify", "metrics": [], "order": null, "time": null, "unsupported_reason": null}, "sql_duckdb": "", "system": "system", "text": "Which arrears threshold do you mean?\nOptions: 30+ days; 90+ days"}
{"columns": [], "correct": true, "error": "", "intent": "unsupported", "item_id": "Q39", "offending": [], "question": "What is the average borrower income for loans in Perth?", "rows": [], "spec": {"clarify": null, "filters": {}, "group_by": [], "intent": "unsupported", "metrics": [], "order": null, "time": null, "unsupported_reason": "Borrower income is not in the data."}, "sql_duckdb": "", "system": "system", "text": "Borrower income is not in the data."}
{"columns": [], "correct": false, "error": "Catalog Error: Table with name no_such_table does not exist!\nDid you mean \"cash_rate\"?\n\nLINE 1: SELECT * FROM no_such_table\n                      ^^^^^^^^^^^^^", "intent": "error", "item_id": "Q35", "question": "What are arrears in NSW?", "rows": [], "sql": "SELECT * FROM no_such_table", "system": "baseline"}
{"columns": [], "correct": true, "error": "", "intent": "decline", "item_id": "Q39", "question": "What is the average borrower income for loans in Perth?", "rows": [], "sql": "", "system": "baseline"}
```

  The script without a key, in both modes. No file is written, and `data/llm_cache/` is
  not created:

```
$ python scripts/run_eval.py --mode replay   (last 2 lines)
    raise CacheMiss(key)
rmbsq.llm.client.CacheMiss: f7e7196c8da2f187d4f05a976c7497e7510519cbd04de774e0052a7d1137d040
$ python scripts/run_eval.py --mode record   (last line)
rmbsq.llm.client.MissingApiKey: ANTHROPIC_API_KEY is not set; record mode needs it on a cache miss
$ ls data
canonical
raw
```

- Deviations from PLAN.md or the instruction file:
  - The script is `scripts/run_eval.py` (D.2), not `scripts/run_eval_live.py`.
  - `eval_detail.jsonl` adds 4 keys to the D.2 list:
    - `system` and `item_id`, to say which line is which;
    - `columns`, the header of `rows`;
    - `offending` (system only), the guard's offending tokens, for G.6.
  - `guard_tripped` is blank for the baseline, which has no narration.
  - A system item whose compile or execute fails records intent `error` (O-42).
  - The CSVs quote any cell that holds a comma, quote or line break, as DuckDB error
    text does. `rmbsq/eval/report.py` therefore has its own writer built on the `csv`
    module. It keeps the cell rules of `rmbsq/synth/truth.py::write_csv`: `%.10f`
    floats, `True`/`False`, and an empty cell for a null.
  - Added test `test_record_with_full_cache_matches_replay`: record mode on a full cache
    makes no call (sockets are disabled) and writes the same bytes as replay.

### Step 5.4: live run

- Files: none.
- Not run, because `ANTHROPIC_API_KEY` is not set (D.3, by design). G.1 to G.7 depend on
  the live run:
  - G.1 `eval_summary.csv`: not available. The live run (step 5.4) was not made, because `ANTHROPIC_API_KEY` is not set (D.3, by design); `data/llm_cache/` is empty and no eval output CSV exists.
  - G.2 per item intent and correct: not available, as above.
  - G.3 detail lines of wrong items: not available, as above.
  - G.4 `trap_failures.csv`: not available, as above.
  - G.5 complete answers for Q11, Q35 and Q39: not available, as above.
  - G.6 guard trips: not available, as above.
  - G.7 API calls, tokens and live wall time: no calls were made.
- To finish it later, in PowerShell from the repo root:

```
$env:ANTHROPIC_API_KEY = "<key>"
python scripts/run_eval.py --mode record
```

  Then commit `data/llm_cache/*.json` with the 4 eval outputs, and run `pytest -m full`.
  `test_eval_replay_reproduces` then runs instead of skipping.

### Step 5.5: replay reproduces

- Files: `tests/test_eval_replay.py`.
- Tests: `tests/test_eval_replay.py::test_eval_replay_reproduces` (marked `full`). It
  skipped through its check, with the reason "no recorded eval cache", the one permitted
  skip (D.3).
- Outputs: none.
- Evidence: section 4 below, `SKIPPED [1] tests\test_eval_replay.py:23: no recorded eval cache`.
  The same byte-for-byte replay is shown on the fixture cache, by
  `test_record_with_full_cache_matches_replay` and in section 5.
- Deviations from PLAN.md or the instruction file: none.

### Step 5.6: trap failures

- Files: `rmbsq/eval/report.py::build_trap_failures` (built in 5.3),
  `tests/test_eval_trap_failures.py`.
- Tests: `tests/test_eval_trap_failures.py::test_trap_failures_row_count`, result passed.
- Outputs: none, because there is no key.
- Evidence: the test builds results for the 8 trap items under both systems, with 4
  wrong rows: a clarify, a wrong ratio, an error and a wrong count. It writes them with
  `write_outputs` and reads `eval_results.csv` back, finding 4 wrong trap rows and 4
  `trap_failures.csv` rows. The rows:

```
system,item_id,trap,expected,got
system,Q28,arrears_units,20.00%,clarify
baseline,Q29,call_as_prepay,20.00%,100.00%
baseline,Q30,call_as_prepay,20.00%,Binder Error: no column x
baseline,Q31,exit_rows,"1,000","1,036"
```

- Deviations from PLAN.md or the instruction file: none.

### Step 5.7: scale benchmark

- Files: `rmbsq/db.py` (`connect_readonly(path, threads=1)`), `rmbsq/eval/benchmark.py`,
  `scripts/run_benchmark.py`, `tests/test_benchmark.py`, `outputs/scale_benchmark.csv`.
- Signatures implemented: `build_tiled_db(src: Path, dst: Path, copies: int) -> None`,
  `run_benchmark(items, src_db: Path, tiled_db: Path, cfg) -> DataFrame`,
  `connect_readonly(path: Path, threads: int = 1)`.
- Tests: the 7 below, result passed (small profile, copies = 3).
- Outputs: `outputs/scale_benchmark.csv`, 272 rows (34 items x 2 databases x 2 routes x
  2 thread settings).
- Evidence: the tests, with the small profile's table counts, 1x then 3x:

```
{'fact_loan_month': 12734, 'dim_loan': 349, 'dim_deal': 10, 'dim_period': 60, 'hpi': 7740, 'cash_rate': 129, 'agg_deal_month': 507} {'fact_loan_month': 38202, 'dim_loan': 1047, 'dim_deal': 30, 'dim_period': 60, 'hpi': 7740, 'cash_rate': 129, 'agg_deal_month': 1521}
tests/test_benchmark.py::test_tiled_row_count PASSED
tests/test_benchmark.py::test_tiled_specs_match_1x[S01-auto] PASSED
tests/test_benchmark.py::test_tiled_specs_match_1x[S01-fact] PASSED
tests/test_benchmark.py::test_tiled_specs_match_1x[S12-auto] PASSED
tests/test_benchmark.py::test_tiled_specs_match_1x[S12-fact] PASSED
tests/test_benchmark.py::test_tiled_spec_rewrites_deal_filters PASSED
tests/test_benchmark.py::test_connect_readonly_threads PASSED
============================== 7 passed in 8.43s ==============================
```

  G.8: the full run (`python scripts/run_benchmark.py`, copies = 36), as the script
  printed it. Machine: Windows 11, 16 logical CPUs, DuckDB 2.0.0. `threads = 0` gives
  DuckDB's default, which is 16 here.

```
built C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\data\canonical\rmbs_x36.duckdb in 82.7 s
rmbs.duckdb: 33828864 bytes
rmbs_x36.duckdb: 1162358784 bytes
benchmark in 302.3 s
                            count    median       max
db  db_rows  route threads                           
1x  773336   auto  1           34  0.021388  0.099349
                   0           34  0.029452  0.153713
             fact  1           34  0.034106  0.170863
                   0           34  0.040371  0.106259
36x 27840096 auto  1           34  0.031282  2.380612
                   0           34  0.053231  0.745008
             fact  1           34  0.322532  3.338742
                   0           34  0.206435  0.684952
exit=0
```

  Per (db, route, threads), the median and max of median_s over the 34 items,
  recomputed from the committed CSV:

```
 db  db_rows route  threads  n  median_of_median_s  max_of_median_s
 1x   773336  auto        1 34            0.021388         0.099349
 1x   773336  auto        0 34            0.029452         0.153714
 1x   773336  fact        1 34            0.034106         0.170863
 1x   773336  fact        0 34            0.040371         0.106259
36x 27840096  auto        1 34            0.031282         2.380612
36x 27840096  auto        0 34            0.053231         0.745008
36x 27840096  fact        1 34            0.322532         3.338742
36x 27840096  fact        0 34            0.206435         0.684952
```

  - Tiled build time: 82.7 s in the committed run (78.0 s in the first run).
  - Database sizes: `rmbs.duckdb` is 33,828,864 bytes; `rmbs_x36.duckdb` is
    1,162,358,784 bytes.
  - Fact rows: 773,336 on 1x and 27,840,096 on 36x (36 x 773,336).

  The benchmark was run twice. The first run overlapped a test run on the same machine,
  so its timings are not clean. The committed CSV is from the second run, made with
  nothing else running. The first run's summary:

```
built C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\data\canonical\rmbs_x36.duckdb in 78.0 s
rmbs.duckdb: 33828864 bytes
rmbs_x36.duckdb: 1162358784 bytes
benchmark in 275.6 s
                            count    median       max
db  db_rows  route threads                           
1x  773336   auto  1           34  0.019429  0.112773
                   0           34  0.020452  0.095013
             fact  1           34  0.030540  0.117785
                   0           34  0.033772  0.109515
36x 27840096 auto  1           34  0.034548  3.242777
                   0           34  0.047844  0.882104
             fact  1           34  0.267489  3.528063
                   0           34  0.150586  0.658212
exit=0
```

  `outputs/scale_benchmark.csv` in full:

```
item_id,db,db_rows,route,threads,median_s,max_s
Q01,1x,773336,auto,1,0.0170972000,0.0178200000
Q01,1x,773336,auto,0,0.0180969000,0.0182151000
Q01,1x,773336,fact,1,0.0298480000,0.0348247000
Q01,1x,773336,fact,0,0.0321083000,0.0447615000
Q01,36x,27840096,auto,1,0.0290444000,0.0411112000
Q01,36x,27840096,auto,0,0.0265023000,0.0324670000
Q01,36x,27840096,fact,1,0.2420464000,0.2672689000
Q01,36x,27840096,fact,0,0.2260154000,0.2510259000
Q02,1x,773336,auto,1,0.0210498000,0.0370081000
Q02,1x,773336,auto,0,0.0229174000,0.0289555000
Q02,1x,773336,fact,1,0.0269315000,0.0383949000
Q02,1x,773336,fact,0,0.0268693000,0.0272810000
Q02,36x,27840096,auto,1,0.0230709000,0.0273821000
Q02,36x,27840096,auto,0,0.0189819000,0.0200591000
Q02,36x,27840096,fact,1,0.2403748000,0.2792931000
Q02,36x,27840096,fact,0,0.2083844000,0.2300624000
Q03,1x,773336,auto,1,0.0178585000,0.0180837000
Q03,1x,773336,auto,0,0.0219415000,0.0247498000
Q03,1x,773336,fact,1,0.0269901000,0.0328877000
Q03,1x,773336,fact,0,0.0257062000,0.0265889000
Q03,36x,27840096,auto,1,0.0160863000,0.0177626000
Q03,36x,27840096,auto,0,0.0150383000,0.0157804000
Q03,36x,27840096,fact,1,0.2348422000,0.3023519000
Q03,36x,27840096,fact,0,0.2044852000,0.2260421000
Q04,1x,773336,auto,1,0.0217252000,0.0218860000
Q04,1x,773336,auto,0,0.0235333000,0.0265312000
Q04,1x,773336,fact,1,0.0265673000,0.0290211000
Q04,1x,773336,fact,0,0.0273275000,0.0321255000
Q04,36x,27840096,auto,1,0.0273979000,0.0342479000
Q04,36x,27840096,auto,0,0.0214041000,0.0230228000
Q04,36x,27840096,fact,1,0.2758759000,0.3623672000
Q04,36x,27840096,fact,0,0.2251824000,0.2440319000
Q05,1x,773336,auto,1,0.0171246000,0.0176997000
Q05,1x,773336,auto,0,0.0200074000,0.0209201000
Q05,1x,773336,fact,1,0.0350864000,0.0832888000
Q05,1x,773336,fact,0,0.0547757000,0.0786274000
Q05,36x,27840096,auto,1,0.0227737000,0.0234985000
Q05,36x,27840096,auto,0,0.0204863000,0.0225847000
Q05,36x,27840096,fact,1,0.4149565001,0.4898160000
Q05,36x,27840096,fact,0,0.2479950000,0.2757989000
Q06,1x,773336,auto,1,0.0255685000,0.0280173000
Q06,1x,773336,auto,0,0.0208716000,0.0246230000
Q06,1x,773336,fact,1,0.0315586000,0.0321067999
Q06,1x,773336,fact,0,0.0458307000,0.0574686000
Q06,36x,27840096,auto,1,0.0423071000,0.0767654000
Q06,36x,27840096,auto,0,0.0242122000,0.0248104000
Q06,36x,27840096,fact,1,0.3603612000,0.3975227000
Q06,36x,27840096,fact,0,0.2379913000,0.2531688000
Q07,1x,773336,auto,1,0.0219475000,0.0307314000
Q07,1x,773336,auto,0,0.0340798000,0.0532350000
Q07,1x,773336,fact,1,0.0385726000,0.0420017000
Q07,1x,773336,fact,0,0.0444128000,0.0450641000
Q07,36x,27840096,auto,1,0.0421403000,0.0488085000
Q07,36x,27840096,auto,0,0.0230693000,0.0245765000
Q07,36x,27840096,fact,1,0.3548445000,0.4825593000
Q07,36x,27840096,fact,0,0.2705855000,0.2872333000
Q08,1x,773336,auto,1,0.0327073000,0.0346965000
Q08,1x,773336,auto,0,0.0331833000,0.0403612000
Q08,1x,773336,fact,1,0.0281919000,0.0306511000
Q08,1x,773336,fact,0,0.0280741000,0.0297878000
Q08,36x,27840096,auto,1,0.1550505000,0.2310033000
Q08,36x,27840096,auto,0,0.0634732000,0.0685231001
Q08,36x,27840096,fact,1,0.1099185000,0.1124850000
Q08,36x,27840096,fact,0,0.1457758000,0.1651843000
Q09,1x,773336,auto,1,0.0285477000,0.0306683000
Q09,1x,773336,auto,0,0.0314757000,0.0402450000
Q09,1x,773336,fact,1,0.0259489000,0.0266343000
Q09,1x,773336,fact,0,0.0262025000,0.0270582000
Q09,36x,27840096,auto,1,0.1303782000,0.1483035000
Q09,36x,27840096,auto,0,0.0635383000,0.0705249000
Q09,36x,27840096,fact,1,0.0841953000,0.0865771000
Q09,36x,27840096,fact,0,0.1224438000,0.1595328000
Q10,1x,773336,auto,1,0.0158922001,0.0167110000
Q10,1x,773336,auto,0,0.0179677000,0.0191133000
Q10,1x,773336,fact,1,0.0274953000,0.0305018000
Q10,1x,773336,fact,0,0.0270198000,0.0319181000
Q10,36x,27840096,auto,1,0.0172304000,0.0178446000
Q10,36x,27840096,auto,0,0.0191996000,0.0196172000
Q10,36x,27840096,fact,1,0.0194966000,0.0214791000
Q10,36x,27840096,fact,0,0.0579574000,0.0636000000
Q11,1x,773336,auto,1,0.0406139000,0.0639910000
Q11,1x,773336,auto,0,0.0420007000,0.0429997000
Q11,1x,773336,fact,1,0.0321683000,0.0395855000
Q11,1x,773336,fact,0,0.0400178000,0.0420160000
Q11,36x,27840096,auto,1,0.2937410000,0.3682510000
Q11,36x,27840096,auto,0,0.1193683000,0.1269380000
Q11,36x,27840096,fact,1,0.2069137000,0.2131765000
Q11,36x,27840096,fact,0,0.2867152000,0.3676775000
Q12,1x,773336,auto,1,0.0193719000,0.0222402000
Q12,1x,773336,auto,0,0.0310090000,0.0413544000
Q12,1x,773336,fact,1,0.0298992000,0.0309276000
Q12,1x,773336,fact,0,0.0355013000,0.0482238000
Q12,36x,27840096,auto,1,0.0297462000,0.0369387000
Q12,36x,27840096,auto,0,0.0325501000,0.0349490000
Q12,36x,27840096,fact,1,0.2017214000,0.2246986000
Q12,36x,27840096,fact,0,0.3638248000,0.3791128000
Q13,1x,773336,auto,1,0.0363541000,0.0428185000
Q13,1x,773336,auto,0,0.0478822000,0.0556074000
Q13,1x,773336,fact,1,0.0291089001,0.0302746000
Q13,1x,773336,fact,0,0.0457857000,0.0543376000
Q13,36x,27840096,auto,1,0.3005528000,0.4163924000
Q13,36x,27840096,auto,0,0.1554151000,0.1634235000
Q13,36x,27840096,fact,1,0.2266391000,0.2433272000
Q13,36x,27840096,fact,0,0.2948763000,0.3616496000
Q14,1x,773336,auto,1,0.0377327000,0.0388628000
Q14,1x,773336,auto,0,0.0435846000,0.0484927000
Q14,1x,773336,fact,1,0.0445298000,0.0932898000
Q14,1x,773336,fact,0,0.0420721000,0.0459479000
Q14,36x,27840096,auto,1,0.4097931000,0.6348008000
Q14,36x,27840096,auto,0,0.1814999999,0.1870814000
Q14,36x,27840096,fact,1,0.4061733000,0.4479370000
Q14,36x,27840096,fact,0,0.2536423000,0.2769825000
Q15,1x,773336,auto,1,0.0171272000,0.0179351000
Q15,1x,773336,auto,0,0.0386244000,0.0570758000
Q15,1x,773336,fact,1,0.0384371000,0.0387327000
Q15,1x,773336,fact,0,0.0578672001,0.0667553000
Q15,36x,27840096,auto,1,0.0316044000,0.0329060000
Q15,36x,27840096,auto,0,0.1025395000,0.1112065000
Q15,36x,27840096,fact,1,0.3289349000,0.3529959000
Q15,36x,27840096,fact,0,0.3148507000,0.3968988000
Q16,1x,773336,auto,1,0.0357694000,0.0622493000
Q16,1x,773336,auto,0,0.0433640000,0.0542102000
Q16,1x,773336,fact,1,0.0374374000,0.0466612000
Q16,1x,773336,fact,0,0.0366501000,0.0395454000
Q16,36x,27840096,auto,1,0.2829500000,0.4083899000
Q16,36x,27840096,auto,0,0.1610554000,0.1666696000
Q16,36x,27840096,fact,1,0.2545694000,0.2870951000
Q16,36x,27840096,fact,0,0.1619664000,0.1706667000
Q17,1x,773336,auto,1,0.0317751000,0.0364806000
Q17,1x,773336,auto,0,0.0351366000,0.0802132000
Q17,1x,773336,fact,1,0.0334892000,0.0345007000
Q17,1x,773336,fact,0,0.0332231000,0.0360480000
Q17,36x,27840096,auto,1,0.2364114000,0.2855140000
Q17,36x,27840096,auto,0,0.1328078000,0.1505534000
Q17,36x,27840096,fact,1,0.2611384000,0.3629817000
Q17,36x,27840096,fact,0,0.1675477000,0.1740479000
Q18,1x,773336,auto,1,0.0331892000,0.0350412000
Q18,1x,773336,auto,0,0.0495417000,0.0536585000
Q18,1x,773336,fact,1,0.0401071000,0.0759845000
Q18,1x,773336,fact,0,0.0500005000,0.0737967000
Q18,36x,27840096,auto,1,0.2329446001,0.3420103000
Q18,36x,27840096,auto,0,0.1479522000,0.1598390000
Q18,36x,27840096,fact,1,0.4291127000,0.4620038000
Q18,36x,27840096,fact,0,0.1639682000,0.1831122000
Q19,1x,773336,auto,1,0.0309084000,0.0319737000
Q19,1x,773336,auto,0,0.0409769000,0.0460715000
Q19,1x,773336,fact,1,0.0307285000,0.0331325000
Q19,1x,773336,fact,0,0.0386452000,0.0439377000
Q19,36x,27840096,auto,1,0.1623289000,0.3717426000
Q19,36x,27840096,auto,0,0.1113205000,0.1203904000
Q19,36x,27840096,fact,1,0.3161298000,0.3378041000
Q19,36x,27840096,fact,0,0.1124153000,0.1268012000
Q20,1x,773336,auto,1,0.0194850000,0.0206330000
Q20,1x,773336,auto,0,0.0341601000,0.0364762000
Q20,1x,773336,fact,1,0.0846158000,0.0909905000
Q20,1x,773336,fact,0,0.0821895000,0.0901285000
Q20,36x,27840096,auto,1,0.0338925000,0.0371400000
Q20,36x,27840096,auto,0,0.0539974000,0.0701827000
Q20,36x,27840096,fact,1,2.7568250000,4.4043291000
Q20,36x,27840096,fact,0,0.5154800000,0.5904345000
Q21,1x,773336,auto,1,0.0177956000,0.0388355000
Q21,1x,773336,auto,0,0.0252217000,0.0268740000
Q21,1x,773336,fact,1,0.0980661000,0.1031889000
Q21,1x,773336,fact,0,0.0536125000,0.0576221000
Q21,36x,27840096,auto,1,0.0333819000,0.0337218000
Q21,36x,27840096,auto,0,0.0387689000,0.0415516000
Q21,36x,27840096,fact,1,3.0101528000,3.3917488000
Q21,36x,27840096,fact,0,0.5063378000,0.5872748000
Q22,1x,773336,auto,1,0.0219461000,0.0242806000
Q22,1x,773336,auto,0,0.0260768000,0.0298176000
Q22,1x,773336,fact,1,0.0972205000,0.1007070000
Q22,1x,773336,fact,0,0.0499258000,0.0592645000
Q22,36x,27840096,auto,1,0.0309588000,0.0382249000
Q22,36x,27840096,auto,0,0.0372885000,0.0384479000
Q22,36x,27840096,fact,1,3.0875664000,3.2936779000
Q22,36x,27840096,fact,0,0.5795687000,0.5885371999
Q23,1x,773336,auto,1,0.0339376000,0.0426240000
Q23,1x,773336,auto,0,0.0422690000,0.0615853000
Q23,1x,773336,fact,1,0.0540136000,0.0643906000
Q23,1x,773336,fact,0,0.0543199000,0.0989217000
Q23,36x,27840096,auto,1,0.3954478000,0.4249814000
Q23,36x,27840096,auto,0,0.1348278000,0.1525195000
Q23,36x,27840096,fact,1,0.3937568000,0.4253939000
Q23,36x,27840096,fact,0,0.1308332000,0.1358824000
Q24,1x,773336,auto,1,0.0993493000,0.1099450000
Q24,1x,773336,auto,0,0.1537135000,0.1706971000
Q24,1x,773336,fact,1,0.1365500000,0.1785102000
Q24,1x,773336,fact,0,0.1062594000,0.1068190000
Q24,36x,27840096,auto,1,2.3806122000,2.4219544000
Q24,36x,27840096,auto,0,0.7450080000,0.7494520000
Q24,36x,27840096,fact,1,2.3612266000,2.4556452000
Q24,36x,27840096,fact,0,0.5444149000,0.5913065000
Q25,1x,773336,auto,1,0.0241223000,0.0441658000
Q25,1x,773336,auto,0,0.0202162000,0.0214931000
Q25,1x,773336,fact,1,0.1708632000,0.1841936000
Q25,1x,773336,fact,0,0.0582874000,0.0645221000
Q25,36x,27840096,auto,1,0.0277798000,0.0282400000
Q25,36x,27840096,auto,0,0.0412550000,0.0461380000
Q25,36x,27840096,fact,1,3.3387419001,3.8091003000
Q25,36x,27840096,fact,0,0.6849516000,0.7718218000
Q26,1x,773336,auto,1,0.0192017000,0.0198733000
Q26,1x,773336,auto,0,0.0278949000,0.0347659001
Q26,1x,773336,fact,1,0.0883935000,0.0952166000
Q26,1x,773336,fact,0,0.0662172000,0.1027001000
Q26,36x,27840096,auto,1,0.0288083000,0.0305100000
Q26,36x,27840096,auto,0,0.0564857000,0.0627330000
Q26,36x,27840096,fact,1,1.7772725000,1.8138564000
Q26,36x,27840096,fact,0,0.3174353000,0.3496464000
Q27,1x,773336,auto,1,0.0158493000,0.0193220000
Q27,1x,773336,auto,0,0.0183526000,0.0260341000
Q27,1x,773336,fact,1,0.0299794000,0.0306606000
Q27,1x,773336,fact,0,0.0337142000,0.0497558000
Q27,36x,27840096,auto,1,0.0266267000,0.0434354000
Q27,36x,27840096,auto,0,0.0570219000,0.0589776000
Q27,36x,27840096,fact,1,0.2785417000,0.4056233000
Q27,36x,27840096,fact,0,0.1372025000,0.1498854000
Q28,1x,773336,auto,1,0.0172678000,0.0190405000
Q28,1x,773336,auto,0,0.0181715000,0.0190598000
Q28,1x,773336,fact,1,0.0347219000,0.0417265000
Q28,1x,773336,fact,0,0.0407243000,0.0431189000
Q28,36x,27840096,auto,1,0.0253068000,0.0267695000
Q28,36x,27840096,auto,0,0.0524653000,0.0538217000
Q28,36x,27840096,fact,1,0.4291930000,0.5321355000
Q28,36x,27840096,fact,0,0.1790606000,0.2239072000
Q29,1x,773336,auto,1,0.0186315000,0.0215803000
Q29,1x,773336,auto,0,0.0203645000,0.0241567000
Q29,1x,773336,fact,1,0.0433087000,0.0947684000
Q29,1x,773336,fact,0,0.0461211000,0.0498143000
Q29,36x,27840096,auto,1,0.0165637000,0.0207683000
Q29,36x,27840096,auto,0,0.0448784000,0.0533172000
Q29,36x,27840096,fact,1,0.0543154000,0.0646741000
Q29,36x,27840096,fact,0,0.0466375000,0.0555741000
Q30,1x,773336,auto,1,0.0178160000,0.0185426000
Q30,1x,773336,auto,0,0.0190727000,0.0195979000
Q30,1x,773336,fact,1,0.0443820000,0.0492796000
Q30,1x,773336,fact,0,0.0393000000,0.0458226000
Q30,36x,27840096,auto,1,0.0255023000,0.0279939000
Q30,36x,27840096,auto,0,0.0612778000,0.0631011000
Q30,36x,27840096,fact,1,0.4738964000,0.5380838000
Q30,36x,27840096,fact,0,0.1586968000,0.2132519000
Q31,1x,773336,auto,1,0.0131918000,0.0201555000
Q31,1x,773336,auto,0,0.0143254000,0.0171129000
Q31,1x,773336,fact,1,0.0258553000,0.0273857000
Q31,1x,773336,fact,0,0.0236330000,0.0255011000
Q31,36x,27840096,auto,1,0.0275169000,0.0583001000
Q31,36x,27840096,auto,0,0.0256215000,0.0281942000
Q31,36x,27840096,fact,1,0.0465484000,0.0557139000
Q31,36x,27840096,fact,0,0.0349689000,0.0352288000
Q32,1x,773336,auto,1,0.0136622000,0.0152880001
Q32,1x,773336,auto,0,0.0140022000,0.0164675000
Q32,1x,773336,fact,1,0.0355375000,0.0371024000
Q32,1x,773336,fact,0,0.0342464000,0.0538629000
Q32,36x,27840096,auto,1,0.0178430000,0.0206644000
Q32,36x,27840096,auto,0,0.0260037000,0.0317358000
Q32,36x,27840096,fact,1,0.3693039000,0.4408478000
Q32,36x,27840096,fact,0,0.1538183000,0.1576077000
Q33,1x,773336,auto,1,0.0160437000,0.0165503000
Q33,1x,773336,auto,0,0.0325060000,0.0453857000
Q33,1x,773336,fact,1,0.0324223000,0.0333109000
Q33,1x,773336,fact,0,0.0517472000,0.0577035000
Q33,36x,27840096,auto,1,0.0216530000,0.0220241000
Q33,36x,27840096,auto,0,0.0497488000,0.0535891000
Q33,36x,27840096,fact,1,0.4383913000,0.4938327000
Q33,36x,27840096,fact,0,0.1845672000,0.2011308000
Q34,1x,773336,auto,1,0.0411500000,0.0551240000
Q34,1x,773336,auto,0,0.0332372000,0.0344638000
Q34,1x,773336,fact,1,0.0328190000,0.0372061000
Q34,1x,773336,fact,0,0.0323117000,0.0372368000
Q34,36x,27840096,auto,1,0.2332410000,0.2818735000
Q34,36x,27840096,auto,0,0.1236557000,0.1350739000
Q34,36x,27840096,fact,1,0.2476204000,0.2627528000
Q34,36x,27840096,fact,0,0.1367397000,0.1707574000
```

- Deviations from PLAN.md or the instruction file:
  - O-40: S01 and S12 hold no balance_total or loan_count. Each spec runs as written for
    the ratio check, then with metrics `[balance_total, loan_count]` for the 3 x check,
    on routes auto and fact.
  - O-41: `db_rows` is the `fact_loan_month` row count.
  - The `route` column holds the requested route (`auto` or `fact`), not the route that
    auto resolved to.
  - Only `execute` is timed. `compile` runs once, before the warm-up.
  - The tiled build runs on 1 thread, as `build_canonical` does (rule 9).
  - `scripts/run_benchmark.py --copies N` labels the tiled database `Nx`. The default
    is `copies = 36`, from config.
  - Added tests: `test_tiled_spec_rewrites_deal_filters` and `test_connect_readonly_threads`.

## 4. Full test suite

Command and its complete output (offline, `--disable-socket`).

```
$ .venv/Scripts/python -m pytest -q
........................................................................ [ 64%]
........................................................................ [ 97%]
......                                                                   [100%]
222 passed, 55 deselected in 51.24s
$ .venv/Scripts/python -m pytest -q -m full -rs
....................................................s..                  [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_eval_replay.py:23: no recorded eval cache
54 passed, 1 skipped, 222 deselected in 73.42s (0:01:13)
```

## 5. Determinism

The outputs regenerated twice and compared byte for byte (SHA-256 of each file, both
runs). There is no eval output in `outputs/` (no key), so the 4 eval files are compared
from 2 runs of the step 5.3 fixture eval (small profile, Q02, Q35, Q39):

```
run 1  481b8a51dda8b4e5e580846c719c2b4e29d0360e6f07b851dcc1c5e220bd4a7f *eval_results.csv
run 1  4eaa6c74cd2fcc8415dbb6c215bf37648ed375f16cb8c88804b50f052f2a36eb *eval_summary.csv
run 1  d265c41b10331b28e82059b507aee3f93944f1dca0a130eb231817d1822fc1e2 *trap_failures.csv
run 1  7691d201eb0ea61e138a99ac92d34806d2e799aa172cd8b90dc41a3c48ff4045 *eval_detail.jsonl
run 2  481b8a51dda8b4e5e580846c719c2b4e29d0360e6f07b851dcc1c5e220bd4a7f *eval_results.csv
run 2  4eaa6c74cd2fcc8415dbb6c215bf37648ed375f16cb8c88804b50f052f2a36eb *eval_summary.csv
run 2  d265c41b10331b28e82059b507aee3f93944f1dca0a130eb231817d1822fc1e2 *trap_failures.csv
run 2  7691d201eb0ea61e138a99ac92d34806d2e799aa172cd8b90dc41a3c48ff4045 *eval_detail.jsonl
```

The non-timing columns of `outputs/scale_benchmark.csv` (`item_id, db, db_rows, route,
threads`), from the 2 full benchmark runs:

```
$ cut -d, -f1-5 <run 1 csv> | sha256sum
0c317401337c82e191566515c7514379129f368c7ae5ce77ada093cb4872f81f *-
$ cut -d, -f1-5 outputs/scale_benchmark.csv | sha256sum
0c317401337c82e191566515c7514379129f368c7ae5ce77ada093cb4872f81f *-
```

The canonical rebuild at the start of the session left `outputs/pool_monthly.csv` and
`outputs/canonical_row_counts.csv` unchanged: `git status --short` printed nothing.

## 6. Fresh-clone check

Clone into a short temp path, `uv venv --python 3.12`, `uv pip sync requirements-lock.txt`,
run the suite. Paste the commands and the complete output. This is G.9; the clone is in
`C:\s5fc\r`.

```
$ git clone https://github.com/uty101/RMBS-Natural-Language-Query.git r
$ git log --oneline -1
9005d56 step 5.7: tiled 36x database and scale benchmark on 1x and 36x, routes auto and fact, 1 and default threads
$ uv venv --python 3.12 .venv
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
$ uv pip sync --python .venv requirements-lock.txt
 + typing-extensions==4.16.0
 + typing-inspection==0.4.4
 + tzdata==2026.6
$ .venv/Scripts/python -m pytest -q
........................................................................ [ 64%]
........................................................................ [ 97%]
......                                                                   [100%]
222 passed, 55 deselected in 126.31s (0:02:06)
$ .venv/Scripts/python -m pytest -q -m full -rs
....................................................s..                  [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_eval_replay.py:23: no recorded eval cache
54 passed, 1 skipped, 222 deselected in 75.32s (0:01:15)
```

## 7. Open questions for the reviewer

1. **O-40 (step 5.7): S01 and S12 carry no balance_total or loan_count.**
   - (a) Run each spec as written for the ratios, then the same spec with metrics
     `[balance_total, loan_count]` for the 3 x check. **Built.**
   - (b) Check the totals only where they fit: S01 with both added, and S12 with 1
     total replacing `smm_vol`.
2. **O-41 (step 5.7): what `db_rows` counts.**
   - (a) `fact_loan_month` rows: 773,336 and 27,840,096. **Built.**
   - (b) The total over all 7 canonical tables.
3. **O-42 (step 5.3): the system's intent when its compile or execute fails.**
   - (a) Intent `error`, with the exception text in `error`, scored wrong. **Built.**
   - (b) The spec's own intent (`answer`), which needs `answer` to return the spec with
     the exception.
