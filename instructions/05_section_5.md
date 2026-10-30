# 05 Section 5: eval and scale benchmark

Session 5 instructions for Claude Code. Build all of Section 5 (steps 5.0 to 5.7) in this session, without pausing. This is the only session that calls the API. This file beats `PLAN.md`, which beats the kickoff (rule 13). Status file: `instructions/05_section_5.status.md`.

The file committed by chat Claude for this session (copy byte for byte; never edit):

| source | destination |
|---|---|
| `instructions/05_questions.yaml` | `eval/questions.yaml` |

---

## A. Approval of Section 4, and O-38, O-39

Section 4 is approved. Chat Claude checked it on Linux, installing from the lock file:

- `pytest -q`: 183 passed. `pytest -q -m full`: 20 passed.
- All 5 supplied files (3 prompts, the gold file and the guard cases) are byte-identical to the instruction copies.
- The spec prompt rendered from the full database is 8,270 characters, about 2,100 tokens, with every deal name, suburb and value listed.
- Before writing the guard cases, chat Claude implemented F.2 independently, and all 13 cases came out as specified.

**O-38: (a) confirmed.** **O-39: (a) confirmed.**

---

## B. The 40 questions

`eval/questions.yaml` holds 40 items:

| category | n |
|---|---|
| simple | 10 |
| grouped | 10 |
| time | 6 |
| trap | 8 |
| ambiguous | 4 |
| unsupported | 2 |

Each item has `id, category, question, expected_intent`, and `trap` for trap items. The 34 answer items also have `gold_spec`, `output_columns` and `gold_sql`.

Chat Claude checked every answer item 3 ways on the full database: the gold SQL, an independent pandas calculation, and this repo's compiler on the gold spec. All 34 agree to within 1.7e-15, return at least 1 row, and hold no nulls.

**B.1 The trap set changes from the kickoff (amends kickoff 6.11 and part 7).** The kickoff named the traps `arrears_units, hardship, call_as_prepay, resubmission`. Two of those can't be tested by a question. Resubmission duplicates and hardship coding are undone in the canonical layer that both systems read, and Section 2 already proved that, row for row against the true panel.

The eval's traps are definition traps instead: places where a SQL writer working on clean data plausibly goes wrong. Chat Claude measured each naive answer against gold on the full database:

| trap | items | the naive mistake | gold | naive |
|---|---|---|---|---|
| arrears_units | Q27, Q28 | reading "2 or more missed payments" as 60+ days | 0.663% | 0.586% |
| call_as_prepay | Q29, Q30 | counting clean-up call exits as prepayments | Q29 CPR 21.6%; Q30 CPR 18.3% | 100.0%; 49.0% |
| exit_rows | Q31, Q32 | counting exit rows as live loans | 150; 9,975 | 154; 10,572 |
| weighting | Q33, Q34 | a simple mean where the metric is balance-weighted | 51.96% LVR; 6.683% rate | 50.92%; 6.709% |

A fifth candidate, compounding CPR over a quarter instead of averaging monthly CPR, was dropped. At prepayment rates near 18%, the 2 methods differ by 1.2e-5, and one naive variant lands inside the 1e-6 scoring tolerance. That trap couldn't tell a careful system from a careless one.

`outputs/trap_failures.csv` uses these 4 trap names.

---

## C. Scoring (`rmbsq/eval/score.py`)

**C.1 Answer items** (expected_intent answer). The system is correct only if all of these hold:

- its spec intent is answer and spec_valid is true;
- the query ran;
- the result satisfies C.3.

The baseline is correct only if its SQL ran and the result satisfies C.3.

**C.2 Other items:**

- **Ambiguous:** the system is correct if its intent is clarify. The baseline is never correct, because it has no way to ask (O-21 (b)); score it wrong and record its intent.
- **Unsupported:** the system is correct if its intent is unsupported. The baseline is correct if its SQL is the empty string.

**C.3 Result comparison** against the gold result (`gold_sql` executed on the same connection):

1. **Columns.** Every name in `output_columns` must be a column of the result. Extra columns are ignored.
2. **Keys.** The key columns are the gold dimension columns plus `period_label`. Each key cell is normalised to a string:
   - a bool becomes `yes` or `no`;
   - a whole-number int or float becomes `str(int(v))`;
   - anything else becomes `str(v).strip()`.

   The result's key rows must equal gold's as a multiset. If the gold spec has `order`, they must be equal in order (O-22 (a)).
3. **Values,** matched by key, for each metric column. The tolerance depends on the metric's display:
   - `pct`: absolute 1e-6;
   - `aud_m`: relative 1e-6;
   - `count`: equal after rounding, and within 1e-9 of an integer.

   A null where gold is not null is wrong.
4. **Bookkeeping.** `n_values_checked` counts the compared cells. `max_abs_err` is the largest absolute difference, blank when nothing was compared.

**C.4 Wilson interval.** `wilson(k, n, z)` uses the standard score interval:

centre = (k + z²/2) / (n + z²), half width = z × √(k(n − k)/n + z²/4) / (n + z²).

Tests check (7, 10) and (40, 40) against hand values printed in the test with 6 dp. Measure them with your own arithmetic and write them as literals.

---

## D. Runs (`rmbsq/eval/run.py`, `scripts/run_eval.py`)

**D.1 Per item.** The system runs `answer(question, …)`. For answer, clarify and unsupported items alike, that is 1 spec call, plus 1 narration call when its intent ends as answer. The baseline makes 1 `baseline_sql` call with the item's `output_columns`. For non-answer items it uses `["period_label"]`, since it gets no gold columns there.

**D.2 `scripts/run_eval.py --mode {record,replay}`.**

- Record mode makes any missing API calls and writes them to `data/llm_cache/`, then runs again in replay mode.
- The outputs always come from the replay pass, so record and replay produce identical files.
- The database is `data/canonical/rmbs.duckdb`, through `connect_readonly`.

Outputs, written with LF and floats `%.10f`:

- `outputs/eval_results.csv`, with the kickoff part 7 columns. intent for the baseline is `sql`, `decline` (empty SQL) or `error`. latency_s and the token columns are summed over the item's calls, from the cache.
- `outputs/eval_summary.csv`, with the kickoff part 7 columns, by system × (each category + `total`).
- `outputs/trap_failures.csv`: `system, item_id, trap, expected, got`. 1 row per wrong trap answer. `expected` is the gold first metric's first value formatted by `format_table`. `got` is the same for the result, or the intent or error text when there is no value.
- `outputs/eval_detail.jsonl`, 1 JSON object per (system, item) with sorted keys:
  - question, intent, spec (system only), sql_duckdb or baseline sql;
  - result rows as display strings (at most 20);
  - text (system only), correct, error.

**D.3 The live run.**

- `ANTHROPIC_API_KEY` must be set in the environment. Never write the key to any file, log or commit.
- If it isn't set, this is a stop condition: finish every other step (5.0 to 5.3, and the code and tests of 5.5 to 5.7), then stop and report.
- The cost is about 40 spec calls, 34 narration calls and 40 baseline calls.
- Commit every file in `data/llm_cache/` together with the outputs.

---

## E. Scale benchmark (6.12, with O-23 (a))

**E.1 Tiled database** (`rmbsq/eval/benchmark.py::build_tiled_db(src, dst, copies)`). Build `data/canonical/rmbs_x36.duckdb` (git-ignored) from the canonical database. For c from 0 to copies − 1:

- `fact_loan_month` and `dim_loan`: every row is copied with loan_id and deal_id prefixed `C{c:02d}-`.
- `dim_deal`: every row is copied with deal_id and deal_name prefixed the same way.
- `dim_period`, `hpi` and `cash_rate` are copied once.
- `agg_deal_month` is rebuilt from the tiled fact with the Section 2 statement.

**E.2 Benchmark** (`run_benchmark`). It runs all 34 answer items' gold specs through `compile` and `execute`:

- on the 1x and 36x databases;
- on route auto and route fact;
- with threads 1 and with DuckDB's default (`threads = 0` in config).

For the 36x database, deal_name and deal_id filter values are rewritten to copy `C00-`. Each run gets 1 untimed warm-up, then 5 timed repeats with `time.perf_counter`.

- `connect_readonly` gains a `threads: int = 1` argument, where 0 means DuckDB's default.
- The default connection stays 1 thread.

Output: `outputs/scale_benchmark.csv`, with columns `item_id, db, db_rows, route, threads, median_s, max_s`. Timings are excluded from every byte check.

---

## F. Steps, with tests

**5.0 Questions file.** Copy it, and update `PLAN.md` for B.1, C and the new `outputs/eval_detail.jsonl`. Test `test_questions_file`:
- 40 items with the B category counts;
- 2 items per trap name;
- every answer item has gold_spec, output_columns and gold_sql;
- every gold_spec validates as `QuerySpec`.

**5.1 Gold check** (marked `full`). `test_gold_spec_equals_gold_sql`: for every answer item on the full database, `execute(compile(gold_spec))` equals `gold_sql`'s result by the C.3 rule.

**5.2 Scoring** (C). Tests on constructed frames:
- key order (with and without `order`);
- each tolerance kind on both sides of its bound;
- extra columns ignored;
- a missing column is wrong;
- a null is wrong;
- bool and float keys normalise;
- the C.2 rules for both systems;
- `wilson`.

**5.3 Runner** (D.1, D.2). Tests in replay against fixture caches for 3 items (Q02, Q35 and Q39), written into a temp cache dir as in Section 4, using a temp outputs dir. Assert the 3 result rows for each system, and that the CSV formats match D.2.

**5.4 Live run** (D.3). Run `scripts/run_eval.py --mode record` and commit the cache and outputs.

**5.5 Replay reproduces** (marked `full`). `test_eval_replay_reproduces`: running in replay from the committed cache into a temp dir reproduces `eval_results.csv`, `eval_summary.csv`, `trap_failures.csv` and `eval_detail.jsonl` byte for byte. latency comes from the cache, so it matches too.

**5.6 Trap failures.** Built in D.2. Test: the row count equals the number of wrong trap answers in `eval_results.csv`.

**5.7 Benchmark** (E). Tests on the small profile with copies = 3:
- the tiled row count is 3 × the source;
- for S01 and S12, ratio metrics on the tiled database equal the 1x values to 1e-9, and balance_total and loan_count are 3 × to 1e-9 relative.

Run the full benchmark (copies = 36) and commit `outputs/scale_benchmark.csv`. Record the tiled build time and database size in the review.

---

## G. Review evidence (`review/section_5.md`)

1. `outputs/eval_summary.csv` in full.
2. For every item: id, category, system intent and correct, baseline intent and correct.
3. For every item either system got wrong, the full `eval_detail.jsonl` lines for both systems.
4. `outputs/trap_failures.csv` in full.
5. 3 complete system answers (Q11, Q35, Q39): question, spec, Oracle SQL, display table, text.
6. Guard trips: the count, and every tripped narration with its offending tokens.
7. API calls made, total input and output tokens, and the total live wall time.
8. `outputs/scale_benchmark.csv`: per (db, route, threads), the median and max of median_s over the 34 items; the tiled build time; and both database sizes.
9. Both pytest outputs from a fresh clone (default, and `-m full`).

Then write `instructions/05_section_5.status.md` and push.
