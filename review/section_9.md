# Review: Section 9, Write up the recorded eval as it came out

## 1. Outcome

- Instruction file: `instructions/09_eval_writeup.md`
- Outcome: complete
- Last step reached: 9.3
- Stop reason: none

## 2. Commits

```
3c3bf3e step 9: eval write-up matches the recorded result
```

## 3. Steps

### Step 9.1: Templates and claims

- Files:
  - `templates/DESIGN_RESPONSE.md.tmpl`, `templates/README.md.tmpl` and
    `templates/RESULTS_SUMMARY.md.tmpl`: byte copies of the sources in
    `instructions/06_templates/` and `instructions/07_templates/`.
  - `rmbsq/deliverable/claims.py`: `_eval_result_claims` adds the 7 C claims after the
    existing eval claims, in C order. `build_claims` takes `questions`, which defaults to
    `eval/questions.yaml`.
  - `tests/test_claims.py`: `test_new_eval_claims` and `test_eval_prose_conditions`.
  - `tests/test_documents.py`: `render_recorded` also copies the committed
    `outputs/eval_results.csv` into its constructed folder (see deviations).
- Tests: `tests/test_claims.py::test_new_eval_claims` and
  `tests/test_claims.py::test_eval_prose_conditions`, both passed.
- Evidence (E.4): the 7 C claims, as rows of `deliverable/claims.csv`:

```
claim_id,value,display,source_file,source_rule
answer_n,34,34,eval/questions.yaml,number of items with expected_intent answer
sys_answer_k,31,31,outputs/eval_results.csv,system rows on answer items with correct true
base_answer_k,33,33,outputs/eval_results.csv,baseline rows on answer items with correct true
sys_wrong_numbers,0,0,outputs/eval_results.csv,"system rows on answer items with intent answer, an empty error and correct false"
base_wrong_numbers,0,0,outputs/eval_results.csv,"baseline rows on answer items with intent sql, an empty error and correct false"
base_ambig_declined,4,4,outputs/eval_results.csv,baseline rows in category ambiguous with intent decline
sys_clarified_traps,2,2,outputs/eval_results.csv,system rows in category trap with intent clarify
```

The raw rows behind them. `grep -c 'expected_intent: answer' eval/questions.yaml` gives
`34`. Every row of `outputs/eval_results.csv` with `correct` False:

```
system,item_id,category,intent,correct,n_values_checked,max_abs_err,latency_s,input_tokens,output_tokens,guard_tripped,error
system,Q09,simple,unsupported,False,0,,1.4790000000,5498,87,False,
system,Q27,trap,clarify,False,0,,4.0300000000,5502,451,False,
system,Q28,trap,clarify,False,0,,4.4160000000,5502,539,False,
baseline,Q28,trap,decline,False,0,,3.2690000000,2480,224,,
baseline,Q35,ambiguous,decline,False,0,,3.0730000000,2455,163,,
baseline,Q36,ambiguous,decline,False,0,,1.5900000000,2456,108,,
baseline,Q37,ambiguous,decline,False,0,,1.0960000000,2456,10,,
baseline,Q38,ambiguous,decline,False,0,,2.6230000000,2458,159,,
```

- Q09, Q27 and Q28 are answer items, and Q35 to Q38 are ambiguous. So:
  - the system has 34 - 3 = 31 right on answer items;
  - the baseline has 34 - 1 = 33 (only Q28);
  - no false row on an answer item has intent `answer` (system) or `sql` (baseline), so both
    wrong-number counts are 0.
- The baseline has 4 ambiguous rows with intent `decline` (Q35 to Q38). The system has 2
  trap rows with intent `clarify` (Q27 and Q28).
- What `test_eval_prose_conditions` pins, from `outputs/eval_detail.jsonl`:

```
Q09 system intent: unsupported | unsupported_reason: unknown state value 'Queensland'
```

- Deviations:
  - **`tests/test_documents.py::render_recorded` copies one more committed file.** The
    constructed recorded state, used by `test_recorded_state_renders` and
    `test_recorded_state_pdfs`, held only `eval_summary.csv` and a made-up
    `eval_detail.jsonl`. The C claims read `eval_results.csv`, so both tests failed with
    `FileNotFoundError: ...\outputs\eval_results.csv`. The helper now copies the committed
    `outputs/eval_results.csv` into the folder, as it already does for the 4 summary CSVs.
    No assertion changed.
  - `answer_n` cites `eval/questions.yaml` as its `source_file`, since that file is where
    the count comes from. The other 6 cite `outputs/eval_results.csv`.

### Step 9.2: Rebuild

- Command: `python scripts/build_writeup.py`, in the recorded state:

```
state: recorded
Design_Response.pdf: 3 pages (at most 4)
Results_Summary.pdf: 1 pages (exactly 1), image height 5.5 cm
```

- Evidence E.1: the rendered eval part of `docs/DESIGN_RESPONSE.md`, from the paragraph
  headed "Against plain text-to-SQL" in "What the prototype shows", and the trap section
  after it, in full:

```
**Against plain text-to-SQL.** I ran the same 40 questions through a second setup: a model writing DuckDB SQL directly over the same clean tables, with the same written metric definitions in its prompt. The result is closer than the argument above suggests, so here it is plainly.

On the 34 questions with a numeric answer, plain text-to-SQL got 33 right and the governed system got 31. Neither returned a wrong number: 0 from plain SQL and 0 from the governed system. Every miss on both sides was a refusal.

- The governed system couldn't resolve a state written in full ("Queensland", stored as QLD).
- On the 2 questions phrased in missed payments, it asked which day threshold was meant rather than mapping payments to days.
- On the 4 ambiguous questions, the governed system asked a clarifying question each time. Plain SQL declined all 4 without saying why, which the scoring counts as wrong.

In total, the governed system got 37 of 40 (92.5%, 95% interval 80.1% to 97.4%) and plain SQL 35 of 40 (87.5%, interval 73.9% to 94.5%). The intervals overlap almost entirely.

What I take from it: on clean tables, the metric definitions do most of the work, whether a compiler applies them or a prompt carries them. The plain model did this well only because its prompt held the semantic layer written out as prose, and that copy has to be kept in step with the real definitions by hand. What the governed design adds is what this eval doesn't score: 1 definition per metric used everywhere, a receipt on every answer, a guard on every narrated number, and a question back to the user instead of a silent refusal. The eval didn't test plain SQL against the raw trustee tables, which is where the traps below would bite.

| category | questions | governed system | plain text-to-SQL |
|---|---|---|---|
| simple | 10 | 9 (90%) | 10 (100%) |
| grouped | 10 | 10 (100%) | 10 (100%) |
| time | 6 | 6 (100%) | 6 (100%) |
| trap | 8 | 6 (75%) | 7 (88%) |
| ambiguous | 4 | 4 (100%) | 0 (0%) |
| unsupported | 2 | 2 (100%) | 2 (100%) |
| total | 40 | 37 (92%) | 35 (88%) |

## The traps the eval is built around

The 8 trap questions target mistakes that look fine in SQL and are wrong in credit terms. On this data:

- counting clean-up call exits as prepayments turns CST 2019-1's 2025 CPR from 21.6% into 100.0%;
- counting exit rows as live loans adds 597 phantom loans to the pool in November 2025;
- a simple average instead of balance weighting moves the pool's LVR from 51.96% to 50.92%.

With the definitions written into its prompt, plain text-to-SQL avoided these traps too (7 of 8, against 6 for the governed system). So they measure what a writer without the definitions gets wrong, not what the governed design adds on top.

A fourth candidate, averaging monthly CPR instead of compounding it, was dropped: at the pool's prepayment rate of 18.1%, the 2 methods differ by 1.2e-05, so it couldn't tell a careful system from a careless one.
```

The added line in "What I'd build next, and the limits":

```
The eval set should also grow from real usage: log every question, and add every failure. The first fix it points to is aliases for state names written in full.
```

- Evidence E.2: the rendered eval part of `README.md`, its "Results" section up to the
  cleaning paragraph:

```
## Results

**Governed system against plain text-to-SQL, same 40 questions.** On the 34 questions with a numeric answer, plain text-to-SQL got 33 right and the governed system 31. Neither returned a wrong number (0 and 0), so every miss on both sides was a refusal.

- The governed system couldn't resolve "Queensland", and asked for a day threshold on questions phrased in missed payments.
- Plain SQL declined all 4 ambiguous questions where the governed system asked.

Overall, the governed system got 37 of 40 (92.5%, 95% interval 80.1% to 97.4%) and plain SQL 35 of 40 (87.5%, interval 73.9% to 94.5%). The plain model's prompt held the full written metric definitions and the exact output columns, so this compares 2 ways of delivering the same definitions, not definitions against none. The full reading is in the design response.

| category | questions | governed system | plain text-to-SQL |
|---|---|---|---|
| simple | 10 | 9 (90%) | 10 (100%) |
| grouped | 10 | 10 (100%) | 10 (100%) |
| time | 6 | 6 (100%) | 6 (100%) |
| trap | 8 | 6 (75%) | 7 (88%) |
| ambiguous | 4 | 4 (100%) | 0 (0%) |
| unsupported | 2 | 2 (100%) | 2 (100%) |
| total | 40 | 37 (92%) | 35 (88%) |

![Accuracy by category](outputs/figures/eval_accuracy.png)
```

- Evidence E.3: the text of `deliverable/Results_Summary.pdf` as extracted by `pypdf`:

```
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
The traps in the questions, measured on this data
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
Same 40 questions. The plain model's prompt held the same table definitions and written metric formulas. Neither system
returned a wrong number: every miss on both sides was a refusal. The governed system asked on every ambiguous
question, where plain SQL declined without saying why.
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

Page counts from `pypdf`: `Design_Response.pdf` has 3 pages, and `Results_Summary.pdf` has 1.
The summary image height is 5.5 cm, which is inside instruction 07 D.3's 3.5 to 5.5 cm
range, so the summary still fits on 1 page.

- Deviations: none.

### Step 9.3: Commit

- Committed by explicit path as `3c3bf3e`, then pushed. The commit holds the 3 templates,
  `rmbsq/deliverable/claims.py`, `tests/test_claims.py`, `tests/test_documents.py`,
  `README.md`, `docs/DESIGN_RESPONSE.md`, `deliverable/claims.csv`,
  `deliverable/results_summary.md` and both PDFs.
- `build_writeup.py` changed no other file: `git status --short` showed only these after
  the build.
- Deviations: none.

## 4. Full test suite

In the working checkout, after the rebuild:

```
> .venv/Scripts/python -m pytest -q
246 passed, 58 deselected in 112.60s (0:01:52)
> .venv/Scripts/python -m pytest -q -m full
58 passed, 246 deselected in 84.95s (0:01:24)
```

## 5. Determinism

`build_writeup.py` was rerun in the fresh clone of `3c3bf3e`, and `git status --short` there
was empty afterwards. SHA-256 (first 16 hex digits) of each built document, in the working
checkout and then in the fresh clone:

```
README.md                          8ABF1617A936A3BD 8ABF1617A936A3BD
docs/DESIGN_RESPONSE.md            A60F9A86DAF8083D A60F9A86DAF8083D
deliverable/claims.csv             8355DBEE093E454C 8355DBEE093E454C
deliverable/results_summary.md     9723CCB51EC3C256 9723CCB51EC3C256
deliverable/Design_Response.pdf    A1DC99CC659CC59C A1DC99CC659CC59C
deliverable/Results_Summary.pdf    F71D2DD6A5538E5B F71D2DD6A5538E5B
```

## 6. Fresh-clone check

`ANTHROPIC_API_KEY` was removed from the environment first (E.5). The pytest lines below are
the tail of each run, as captured. The lines before them are progress dots only.

```
> git clone https://github.com/uty101/RMBS-Natural-Language-Query.git C:\s9fc
> git log --oneline -1
3c3bf3e step 9: eval write-up matches the recorded result
> uv venv --python 3.12 .venv
> uv pip sync --python .venv requirements-lock.txt
ANTHROPIC_API_KEY set: False
> .venv/Scripts/python -m pytest -q
........................................................................ [ 87%]
..............................                                           [100%]
246 passed, 58 deselected in 223.73s (0:03:43)
> .venv/Scripts/python -m pytest -q -m full
..........................................................               [100%]
58 passed, 246 deselected in 191.53s (0:03:11)
> .venv/Scripts/python scripts/build_writeup.py
exit 0
> git status --short
(empty)
```

## 7. Open questions for the reviewer

None.
