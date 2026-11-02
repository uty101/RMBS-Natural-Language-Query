# Review: Section 8, Record the eval

## 1. Outcome

- Instruction files:
  - `instructions/08c_structured_output.md`, which carries out
    `instructions/08_record_eval.md` B from 8.1 to 8.6;
  - earlier in session 8, `instructions/08b_drop_temperature.md`, whose step 8b.1 is
    committed as `5f309fd`.
- Outcome: complete
- Last step reached: 8.6
- Stop reason: none

## 2. Commits

```
46c8992 writeup: recorded state
6642f76 eval: recorded cache and results
6489ef7 step 8c.1: structured output in place of forced tools (O-47 b)
5f309fd step 8b.1: drop temperature from the LLM request (O-46 b)
```

## 3. Steps

### Step 8c.1: Structured output

- Files:
  - New: `rmbsq/llm/wire.py`, with `spec_wire_schema`, `wire_to_spec`,
    `BASELINE_WIRE_SCHEMA`, `output_config`, `response_json` and `InvalidResponse`.
  - Changed:
    - `rmbsq/llm/client.py`: the request is
      `{model, max_tokens, system, messages, output_config}`, and a null `output_config`
      isn't sent.
    - `rmbsq/llm/spec_agent.py` and `rmbsq/llm/baseline.py`: both parse structured
      output.
    - `rmbsq/llm/narrate.py`: the call signature only. It already joined only `text`
      blocks, so `thinking` blocks are ignored (C.4).
    - `rmbsq/eval/run.py`: an invalid baseline response is intent `error`.
    - `config.toml`: `max_tokens = 4096` (C.2).
    - `prompts/spec_system.md` and `prompts/baseline_system.md`: byte copies of
      `instructions/08c_prompts/`.
    - `PLAN.md` 4.1, 4.2 and 4.5, `docs/CONVENTIONS_RESOLVED.md` N2 and
      `decisions/OPEN.md` (O-47 decided (b)).
  - Removed: `spec_input_schema`, `spec_tool`, the `submit_sql` tool with both
    `TOOL_CHOICE`s, and `test_tool_schema_inlined`, which only checked them.
- Fixtures: 6 converted from `tool_use` to a `text` block holding the same JSON, with
  `stop_reason` `end_turn`:
  - `baseline_empty`, `baseline_sql`;
  - `spec_answer`, `spec_clarify`, `spec_four_metrics`, `spec_unsupported`.

  3 added: `spec_thinking`, `refusal` and `truncated`.
- Tests:
  - `tests/test_wire.py`: `test_wire_schema_supported`, `test_wire_to_spec`,
    `test_parse_thinking_then_text`, `test_parse_refusal`, `test_parse_truncated`.
  - Call sites were updated in `test_llm_client`, `test_spec_agent`, `test_baseline`,
    `test_answer`, `test_guard` and `test_eval_run`.
  - Result:
    - `pytest -q`: 244 passed. That is 240 - 1 removed + 5 new.
    - `pytest -q -m full`: 57 passed, 1 skipped (before recording).
- `build_writeup.py`: exit 0, state pending. No document changed.
- Deviations:
  - `test_parse_missing_tool_block` is renamed `test_parse_text_not_json`. There is no
    tool block any more, and its body and fixture are unchanged.
  - The baseline signals an invalid response with a new `BaselineResponseError`.
    `run_baseline` records it as intent `error`, `sql` "" and the reason as error text
    (C.3), not as a decline.
  - `response_json` also rejects JSON that isn't an object, through the same invalid path.
  - Fixture JSON content was kept as it was, so `spec_answer` and its siblings hold partial
    objects, and `test_eval_run` seeds Q02's gold spec dump with dict `filters`.
    - `wire_to_spec` converts `filters` only when it is a list, and treats missing keys as
      absent.

### Step 8c.2: Smoke test

- Call 1: `rmbsq ask "What is the 90+ arrears rate by balance for each state now?" --live
  --show-sql`.
  - 2 live calls (spec and narration). Exit 0, 19.1 s, and the key check printed
    `key len=106 prefix=sk-ant-`.
  - Its output, reproduced byte for byte by the same command in replay:

```
For 2026-09, the 90+ arrears rate by balance is highest in WA at 0.91%, followed by NSW at 0.55%. VIC is at 0.35%, QLD at 0.34%, and SA is lowest at 0.19%. These figures are weighted by balance, as you asked.

state period_label arrears_90p_bal
  NSW      2026-09           0.55%
  QLD      2026-09           0.34%
   SA      2026-09           0.19%
  VIC      2026-09           0.35%
   WA      2026-09           0.91%

WITH parts AS (
  SELECT
    l.state AS state,
    f.period,
    SUM(CASE WHEN f.closing_balance > 0 THEN 1 ELSE 0 END) AS loan_count,
    SUM(CASE WHEN f.closing_balance > 0 THEN f.closing_balance ELSE 0 END) AS bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0 AND f.dpd_bucket >= 2 AND NOT f.hardship_flag
        THEN f.closing_balance
        ELSE 0
      END
    ) AS a30_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0 AND f.dpd_bucket = 4 AND NOT f.hardship_flag
        THEN f.closing_balance
        ELSE 0
      END
    ) AS a90_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0 AND f.dpd_bucket = 4 AND NOT f.hardship_flag
        THEN 1
        ELSE 0
      END
    ) AS a90_cnt,
    SUM(
      CASE
        WHEN f.closing_balance > 0 AND f.hardship_flag
        THEN f.closing_balance
        ELSE 0
      END
    ) AS hard_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0
        THEN CAST(f.closing_balance AS DOUBLE PRECISION) * l.orig_ltv
        ELSE 0
      END
    ) AS orig_ltv_x_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0
        THEN CAST(f.closing_balance AS DOUBLE PRECISION) * f.indexed_ltv
        ELSE 0
      END
    ) AS idx_ltv_x_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0
        THEN CAST(f.closing_balance AS DOUBLE PRECISION) * f.interest_rate
        ELSE 0
      END
    ) AS rate_x_bal,
    SUM(CASE WHEN f.opening_balance > 0 THEN f.curtailment ELSE 0 END) + SUM(
      CASE
        WHEN f.opening_balance > 0 AND f.exit_reason = 'prepaid'
        THEN f.exit_balance
        ELSE 0
      END
    ) AS smm_num,
    SUM(
      CASE
        WHEN f.opening_balance > 0
        AND (
          f.exit_reason IS NULL OR f.exit_reason = 'prepaid'
        )
        THEN f.opening_balance - f.scheduled_principal
        ELSE 0
      END
    ) AS smm_den,
    SUM(
      CASE
        WHEN f.opening_balance > 0 AND f.exit_reason = 'defaulted'
        THEN f.exit_balance
        ELSE 0
      END
    ) AS mdr_num,
    SUM(CASE WHEN f.opening_balance > 0 THEN f.opening_balance ELSE 0 END) AS mdr_den
  FROM fact_loan_month f
  JOIN dim_loan l
    ON l.loan_id = f.loan_id
  JOIN dim_deal d
    ON d.deal_id = f.deal_id
  WHERE
    f.period BETWEEN TO_DATE('2026-09-01', 'YYYY-MM-DD') AND TO_DATE('2026-09-01', 'YYYY-MM-DD')
  GROUP BY
    l.state,
    f.period
), b AS (
  SELECT
    parts.*,
    '2026-09' AS period_label
  FROM parts
), keys AS (
  SELECT DISTINCT
    state,
    period_label
  FROM b
), stock AS (
  SELECT
    state,
    period_label,
    CAST(a90_bal AS DOUBLE PRECISION) / CAST(bal AS DOUBLE PRECISION) AS arrears_90p_bal
  FROM (
    SELECT
      b.*,
      ROW_NUMBER() OVER (PARTITION BY state, period_label ORDER BY period DESC NULLS LAST) AS rn
    FROM b
    WHERE
      loan_count > 0
  ) r
  WHERE
    rn = 1
)
SELECT
  k.state,
  k.period_label,
  s.arrears_90p_bal
FROM keys k
LEFT JOIN stock s
  ON s.state = k.state AND s.period_label = k.period_label
ORDER BY
  k.state,
  k.period_label
```

- Baseline request for Q11: **deviation.**
  - Instruction 08c was amended on origin (`7a87921`, "smoke test covers the baseline
    request too") after this session had pulled it.
  - The amendment wasn't pulled until the push in 8.5 was rejected, so the Q11 baseline
    call was not made before the full run.
  - The full run made that request live, with a valid reply. Below is that recorded call,
    replayed through `baseline_sql` with Q11's `output_columns` (a cache hit, no new API
    call), and its SQL run with `run_baseline_sql`:

```
Q11: Show the 90+ arrears rate by balance for each state at the latest month.
output_columns: ['state', 'period_label', 'arrears_90p_bal']
calls: [{'key': '8f58878245633b34b260fb8ee7ea03740eb31202379c30af24663b966d8fb4a8', 'hit': True, 'latency_s': 3.565, 'input_tokens': 2481, 'output_tokens': 414}]
--- sql
SELECT l.state AS state, '2026-09' AS period_label, SUM(CASE WHEN f.dpd_bucket = 4 AND NOT f.hardship_flag THEN f.closing_balance ELSE 0 END) / SUM(f.closing_balance) AS arrears_90p_bal FROM fact_loan_month f JOIN dim_loan l ON f.loan_id = l.loan_id WHERE f.period = DATE '2026-09-01' AND f.closing_balance > 0 GROUP BY l.state ORDER BY l.state
--- result
state period_label  arrears_90p_bal
  NSW      2026-09         0.005532
  QLD      2026-09         0.003389
   SA      2026-09         0.001937
  VIC      2026-09         0.003487
   WA      2026-09         0.009111
```

### Step 8.1: Record

- Command: `python scripts/run_eval.py --mode record`, with the key set in the environment
  of that one process only.
- Its complete output, with the key redaction filter applied (nothing matched):

```
key len=106 prefix=sk-ant-
cache before: 2
system: 37/40 correct
baseline: 35/40 correct
record run in 265.8 s; outputs in C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\outputs
exit=0 wall_s=282.5
cache after: 113
```

- **C.6: calls, tokens and wall time**, summed from the cache files. There is 1 file per
  live call, and `usage` is from each response.

```
smoke (8c.2): calls 2, input_tokens 6128, output_tokens 169, summed latency_s 5.404
eval run (8.1): calls 111, input_tokens 337482, output_tokens 20379, summed latency_s 247.497
all: calls 113, input_tokens 343610, output_tokens 20548, summed latency_s 252.901
eval calls by type: {'spec': 40, 'baseline': 40, 'narration': 31}
stop_reason over all 113: {'end_turn': 113}
content shapes over all 113: {('text',): 90, ('thinking', 'text'): 23}
```

- Live wall time: 282.5 s for the whole command, 265.8 s as `run_eval.py` reports it
  (record pass plus replay pass).
- The 2 smoke entries match no eval request, and they are committed with the rest of
  `data/llm_cache/` (8.5 says every file).

### Step 8.2: Key check (C.7)

```
$ grep -rl "sk-ant" data/llm_cache/ outputs/
(exit 1)
```

No output: no file holds the substring.

### Step 8.3: Regenerate (C.8)

```
summary outputs in 14.9 s
state: recorded
Design_Response.pdf: 3 pages (at most 4)
Results_Summary.pdf: 1 pages (exactly 1), image height 5.5 cm
outputs/data_summary.csv
outputs/compiler_check.csv
outputs/trap_effects.csv
outputs/arrears_90p_by_vintage.csv
outputs/figures/arrears_90p_by_vintage.png
outputs/figures/scale_benchmark.png
outputs/figures/eval_accuracy.png
outputs/worked_example.md
outputs/transcripts/01_answer.md
outputs/transcripts/02_clarify.md
outputs/transcripts/03_unsupported.md
deliverable/claims.csv
README.md
docs/DESIGN_RESPONSE.md
deliverable/results_summary.md
deliverable/Design_Response.pdf
deliverable/Results_Summary.pdf
```

- Summary: 1 page, image height 5.5 cm.
- The extracted text of `deliverable/Results_Summary.pdf` (pypdf):

```
pages 1
https://github.com/uty101/RMBS-Natural-Language-Query
page 1 of 1
Asking RMBS loan data questions in plain English: results
Utkarsh Malhotra · November 2026
A language model turns each question into a small query spec, and a compiler turns the spec into SQL over governed metric
definitions, so the model never does the arithmetic. These results are from a working prototype on synthetic data: 50
Australian RMBS deals, 21,945 loans and 773,336 loan-months in 2 trustee formats.
What is proved
 check
result
Cleaning: canonical table against simulated truth
0 mismatches over 773,336 loan-months
Cleaning: resubmitted duplicates removed
721 of 774,057 raw rows
Cleaning: clean-up calls coded as repayments, recovered
7 deals
Compiler: output against hand-written SQL
49 of 49 match, worst difference 1.6e-15
Compiler: queries that render to Oracle
49 of 49
Scale: slowest question at 27,840,096 loan-months
under 0.75 s with default threads
The traps a plain SQL writer falls into
 trap
question
correct
naive mistake gives
Arrears units
Q27
0.66%
0.59%
Calls as prepayments
Q29
21.6%
100.0%
Calls as prepayments
Q30
18.3%
49.0%
Exit rows as live loans
Q32
9,975
10,572
Unweighted average
Q33
51.96%
50.92%
Averaging CPR (dropped, gap too small)
Q2 2025 CPR
18.064%
18.063%
Governed system against plain text-to-SQL
Same 40 questions. The plain model was given the same table definitions, the same written metric formulas and the exact
output columns.
 category
questions
governed system
plain text-to-SQL
simple
10
9 (90%)
10 (100%)
grouped
10
10 (100%)
10 (100%)
time
6
6 (100%)
6 (100%)
trap
8
6 (75%)
7 (88%)
ambiguous
4
4 (100%)
0 (0%)
unsupported
2
2 (100%)
2 (100%)
total
40
37 (92%)
35 (88%)
Asked "What are arrears in NSW?", the governed system replied:
 Which arrears measure do you want for NSW?
Options: 30+ days past due; 90+ days past due
```

### Step 8.4: Tests

- `pytest -q`: 244 passed, 58 deselected.
- `pytest -q -m full -rA`: 58 passed, 244 deselected, including
  `PASSED tests/test_eval_replay.py::test_eval_replay_reproduces`. It now runs and passes,
  no longer skipped.

### Step 8.5: Commit

- `6642f76 eval: recorded cache and results`: 117 files, being 113 cache files and the 4
  eval outputs.
- `46c8992 writeup: recorded state`: `README.md`, `docs/DESIGN_RESPONSE.md`,
  `deliverable/claims.csv`, `deliverable/results_summary.md`, both PDFs,
  `outputs/figures/eval_accuracy.png` and the 3 files under `outputs/transcripts/`.
  `build_writeup.py` changed no other file.
- Deviation: the first push was rejected because of `7a87921` on origin. The 3 local,
  unpushed commits were rebased onto it, which changed their hashes, and then pushed. No
  pushed commit was rewritten.

## 4. Full test suite

See 8.4, and the fresh clone in section 6.

## 5. Determinism

The fresh clone rebuilt every output, including both PDFs, from the committed cache with no
key. `git status --short` stayed empty, so every regenerated file is byte-identical to the
commit.

## 6. Fresh-clone check (C.9)

Clone of `46c8992` into `C:\s8fc\r`, in a shell with `ANTHROPIC_API_KEY` unset:

```
ANTHROPIC_API_KEY set: False
> git log --oneline -1
46c8992 writeup: recorded state
> uv venv --python 3.12 .venv
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
> uv pip sync --python .venv requirements-lock.txt
 + typing-inspection==0.4.4
 + tzdata==2026.6
> python --version
Python 3.12.13
> pytest -q
........................................................................ [ 29%]
........................................................................ [ 59%]
........................................................................ [ 88%]
............................                                             [100%]
244 passed, 58 deselected in 135.73s (0:02:15)
> pytest -q -m full
..........................................................               [100%]
58 passed, 244 deselected in 110.11s (0:01:50)
> python scripts/build_writeup.py
built C:\s8fc\r\data\canonical\rmbs.duckdb in 12.0 s, 33828864 bytes
          table trustee_format   rows
       dim_deal            all     50
       dim_loan            all  21945
       dim_loan              A  13076
       dim_loan              B   8869
fact_loan_month            all 773336
fact_loan_month              A 464452
fact_loan_month              B 308884
            hpi            all   7740
      cash_rate            all    129
 agg_deal_month            all   2567
     dim_period            all     60
summary outputs in 9.4 s
state: recorded
Design_Response.pdf: 3 pages (at most 4)
Results_Summary.pdf: 1 pages (exactly 1), image height 5.5 cm
data/canonical/rmbs.duckdb
outputs/pool_monthly.csv
outputs/canonical_row_counts.csv
outputs/data_summary.csv
outputs/compiler_check.csv
outputs/trap_effects.csv
outputs/arrears_90p_by_vintage.csv
outputs/figures/arrears_90p_by_vintage.png
outputs/figures/scale_benchmark.png
outputs/figures/eval_accuracy.png
outputs/worked_example.md
outputs/transcripts/01_answer.md
outputs/transcripts/02_clarify.md
outputs/transcripts/03_unsupported.md
deliverable/claims.csv
README.md
docs/DESIGN_RESPONSE.md
deliverable/results_summary.md
deliverable/Design_Response.pdf
deliverable/Results_Summary.pdf
exit=0
> git status --short
(end of git status)
```

## C. Review evidence

### C.1 `outputs/eval_summary.csv`

```
system,category,n,k,accuracy,wilson_lo,wilson_hi
system,simple,10,9,0.9000000000,0.5958436145,0.9821242505
system,grouped,10,10,1.0000000000,0.7224598312,1.0000000000
system,time,6,6,1.0000000000,0.6096569663,1.0000000000
system,trap,8,6,0.7500000000,0.4092698791,0.9285223111
system,ambiguous,4,4,1.0000000000,0.5100999796,1.0000000000
system,unsupported,2,2,1.0000000000,0.3423719529,1.0000000000
system,total,40,37,0.9250000000,0.8013546984,0.9741644432
baseline,simple,10,10,1.0000000000,0.7224598312,1.0000000000
baseline,grouped,10,10,1.0000000000,0.7224598312,1.0000000000
baseline,time,6,6,1.0000000000,0.6096569663,1.0000000000
baseline,trap,8,7,0.8750000000,0.5291051942,0.9775830911
baseline,ambiguous,4,0,0.0000000000,0.0000000000,0.4899000204
baseline,unsupported,2,2,1.0000000000,0.3423719529,1.0000000000
baseline,total,40,35,0.8750000000,0.7388757933,0.9454058023
```

### C.2 Every item

| id | category | system intent | system correct | baseline intent | baseline correct |
|---|---|---|---|---|---|
| Q01 | simple | answer | True | sql | True |
| Q02 | simple | answer | True | sql | True |
| Q03 | simple | answer | True | sql | True |
| Q04 | simple | answer | True | sql | True |
| Q05 | simple | answer | True | sql | True |
| Q06 | simple | answer | True | sql | True |
| Q07 | simple | answer | True | sql | True |
| Q08 | simple | answer | True | sql | True |
| Q09 | simple | unsupported | False | sql | True |
| Q10 | simple | answer | True | sql | True |
| Q11 | grouped | answer | True | sql | True |
| Q12 | grouped | answer | True | sql | True |
| Q13 | grouped | answer | True | sql | True |
| Q14 | grouped | answer | True | sql | True |
| Q15 | grouped | answer | True | sql | True |
| Q16 | grouped | answer | True | sql | True |
| Q17 | grouped | answer | True | sql | True |
| Q18 | grouped | answer | True | sql | True |
| Q19 | grouped | answer | True | sql | True |
| Q20 | grouped | answer | True | sql | True |
| Q21 | time | answer | True | sql | True |
| Q22 | time | answer | True | sql | True |
| Q23 | time | answer | True | sql | True |
| Q24 | time | answer | True | sql | True |
| Q25 | time | answer | True | sql | True |
| Q26 | time | answer | True | sql | True |
| Q27 | trap | clarify | False | sql | True |
| Q28 | trap | clarify | False | decline | False |
| Q29 | trap | answer | True | sql | True |
| Q30 | trap | answer | True | sql | True |
| Q31 | trap | answer | True | sql | True |
| Q32 | trap | answer | True | sql | True |
| Q33 | trap | answer | True | sql | True |
| Q34 | trap | answer | True | sql | True |
| Q35 | ambiguous | clarify | True | decline | False |
| Q36 | ambiguous | clarify | True | decline | False |
| Q37 | ambiguous | clarify | True | decline | False |
| Q38 | ambiguous | clarify | True | decline | False |
| Q39 | unsupported | unsupported | True | decline | True |
| Q40 | unsupported | unsupported | True | decline | True |

### C.3 Every wrong answer, with its full `eval_detail.jsonl` line

8 wrong answers: system Q09, system Q27, system Q28, baseline Q28, baseline Q35, baseline Q36, baseline Q37, baseline Q38.

- System Q09 answered `unsupported`, with the reason "unknown state value 'Queensland'".
  The resolver doesn't map the full state name to `QLD`.
- System Q27 and Q28 (trap `arrears_units`) asked to clarify instead of mapping missed
  payments to an arrears bucket.

**system Q09**

```json
{"columns": [], "correct": false, "error": "", "intent": "unsupported", "item_id": "Q09", "offending": [], "question": "What is the weighted average original LVR of loans in Queensland now?", "rows": [], "spec": {"clarify": null, "filters": {}, "group_by": [], "intent": "unsupported", "metrics": [], "order": null, "time": null, "unsupported_reason": "unknown state value 'Queensland'"}, "sql_duckdb": "", "system": "system", "text": "unknown state value 'Queensland'"}
```

**system Q27**

```json
{"columns": [], "correct": false, "error": "", "intent": "clarify", "item_id": "Q27", "offending": [], "question": "What share of the pool's balance had missed 2 or more payments at the latest month?", "rows": [], "spec": {"clarify": {"options": ["30+ days past due", "90+ days past due"], "question": "Missing 2 or more payments isn't a defined measure, and we have no 60+ day arrears metric. Which arrears threshold should I use (as a share of balance, latest month)?"}, "filters": {}, "group_by": [], "intent": "clarify", "metrics": [], "order": null, "time": null, "unsupported_reason": null}, "sql_duckdb": "", "system": "system", "text": "Missing 2 or more payments isn't a defined measure, and we have no 60+ day arrears metric. Which arrears threshold should I use (as a share of balance, latest month)?\nOptions: 30+ days past due; 90+ days past due"}
```

**system Q28**

```json
{"columns": [], "correct": false, "error": "", "intent": "clarify", "item_id": "Q28", "offending": [], "question": "What share of the pool's balance had missed 4 or more payments in December 2024?", "rows": [], "spec": {"clarify": {"options": ["30+ days past due (share of balance)", "90+ days past due (share of balance)", "90+ days past due (share of loans by count)"], "question": "The data doesn't have a measure for 4 or more missed payments. Arrears are only available at 30+ and 90+ days past due, and 90+ days is the closest to 4 missed payments. Which would you like for December 2024?"}, "filters": {}, "group_by": [], "intent": "clarify", "metrics": [], "order": null, "time": null, "unsupported_reason": null}, "sql_duckdb": "", "system": "system", "text": "The data doesn't have a measure for 4 or more missed payments. Arrears are only available at 30+ and 90+ days past due, and 90+ days is the closest to 4 missed payments. Which would you like for December 2024?\nOptions: 30+ days past due (share of balance); 90+ days past due (share of balance); 90+ days past due (share of loans by count)"}
```

**baseline Q28**

```json
{"columns": [], "correct": false, "error": "", "intent": "decline", "item_id": "Q28", "question": "What share of the pool's balance had missed 4 or more payments in December 2024?", "rows": [], "sql": "", "system": "baseline"}
```

**baseline Q35**

```json
{"columns": [], "correct": false, "error": "", "intent": "decline", "item_id": "Q35", "question": "What are arrears in NSW?", "rows": [], "sql": "", "system": "baseline"}
```

**baseline Q36**

```json
{"columns": [], "correct": false, "error": "", "intent": "decline", "item_id": "Q36", "question": "How is the Harbour book performing?", "rows": [], "sql": "", "system": "baseline"}
```

**baseline Q37**

```json
{"columns": [], "correct": false, "error": "", "intent": "decline", "item_id": "Q37", "question": "Which deals are the riskiest?", "rows": [], "sql": "", "system": "baseline"}
```

**baseline Q38**

```json
{"columns": [], "correct": false, "error": "", "intent": "decline", "item_id": "Q38", "question": "Show me arrears for Blacktown.", "rows": [], "sql": "", "system": "baseline"}
```

### C.4 `outputs/trap_failures.csv`

```
system,item_id,trap,expected,got
system,Q27,arrears_units,0.66%,clarify
system,Q28,arrears_units,1.35%,clarify
baseline,Q28,arrears_units,1.35%,decline
```

### C.5 Guard trips

None. The distinct `(system, guard_tripped)` values over all 80 rows of
`eval_results.csv`:

```
[('baseline', ''), ('system', 'False')]
```

### C.6 to C.9

- C.6: step 8.1.
- C.7: step 8.2.
- C.8: step 8.3.
- C.9: section 6.

## 7. Open questions for the reviewer

None. O-46 and O-47 are decided. The findings in C.3 (Q09's state name, and the
`arrears_units` traps answered with a clarification) are results, not open decisions.
