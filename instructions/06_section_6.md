# 06 Section 6: repo write-up

Session 6 instructions for Claude Code. Build all of Section 6 (steps 6.0 to 6.6) in this session, without pausing. No API call is made. This file beats `PLAN.md`, which beats the kickoff (rule 13). Status file: `instructions/06_section_6.status.md`.

Files committed by chat Claude for this session (copy byte for byte; never edit):

| source | destination |
|---|---|
| `instructions/06_templates/README.md.tmpl` | `templates/README.md.tmpl` |
| `instructions/06_templates/DESIGN_RESPONSE.md.tmpl` | `templates/DESIGN_RESPONSE.md.tmpl` |

Chat Claude wrote all prose in this section. Claude Code writes no prose of its own into the README or the design response: only code, generated tables, figures and the values that fill the placeholders.

---

## A. Approval of Section 5, and O-40 to O-42

Section 5 is approved, complete except the live eval run, which is deliberately left for later. Chat Claude checked it on Linux, installing from the lock file:

- `pytest -q`: 222 passed. `pytest -q -m full`: 54 passed and 1 skipped (the empty-cache skip).
- `eval/questions.yaml` is byte-identical to the instruction copy.
- `outputs/scale_benchmark.csv`, at 36x with default threads, has a max median of 0.745 s over all 34 items and routes. Single-threaded, the slowest is 3.34 s (Q25), as the status file reports.

**O-40 (a), O-41 (a) and O-42 (a)** are all confirmed.

**The eval stays unrecorded.** This section must produce a complete, consistent write-up in both states:

- **pending:** `outputs/eval_summary.csv` doesn't exist. This is the state to commit now;
- **recorded:** it exists.

`scripts/build_writeup.py` regenerates everything for whichever state the repo is in, so a reader who records the eval with their own key gets updated documents from 1 command.

---

## B. Templates

- **Scalars.** `{{name}}` is replaced by a claim's display string (D). An unknown name raises.
- **Blocks.** `{{eval_table}}` is replaced by the generated markdown table in E.
- **Sections.** `{{#eval}}…{{/eval}}` is kept only in the recorded state. `{{^eval}}…{{/eval}}` is kept only in the pending state. The markers and the 1 newline after each marker are removed. Sections don't nest.
- A claim used inside an `{{#eval}}` section is resolved only in the recorded state. In the pending state, the eval claims are never computed and never needed.
- `rmbsq/deliverable/render.py::render(template_text, claims: dict, blocks: dict, eval_recorded: bool) -> str`.

**Rendered outputs:**

- `README.md`, from `templates/README.md.tmpl`;
- `docs/DESIGN_RESPONSE.md`, from `templates/DESIGN_RESPONSE.md.tmpl`.

Both are written with LF and a single trailing newline.

**Number check (also used by Section 7).** `rmbsq/deliverable/numbers.py::unexplained_numbers(rendered, claims, blocks, fixed) -> list[str]` checks a rendered document:

1. Remove every block's rendered text, and fenced code blocks (``` … ```) and indented code lines.
2. Strip `YYYY-MM` and `YYYY-Qn` tokens, and every deal_name.
3. Extract tokens with the Section 4 guard regex and normalisation.
4. Ignore bare years from 2016 to 2026.

Every remaining token must be in the allowed set. That set is the tokens of every claim display string used in the document, plus the tokens of `templates/fixed_numbers.txt`.

**`templates/fixed_numbers.txt`**, created by Claude Code with exactly these lines. These are the design constants written as literals in the templates. Chat Claude extracted them from the templates and checked that none is a measured result.

```
0
1
2
3
4
5
6
8
10
21
-1
30
34
36
40
90
95%
114
300
2000
3.12
```

---

## C. New summary outputs

All 3 are written by a new script, `scripts/build_summary.py`, run after `build_canonical.py`. They are CSVs with LF, and floats are written `%.10f` unless stated otherwise.

**C.1 `outputs/data_summary.csv`**, with columns `stat, value`:

| stat | definition |
|---|---|
| n_deals | rows of `dim_deal` |
| n_loans | rows of `dim_loan` |
| n_loan_months | rows of `fact_loan_month` |
| n_raw_rows | total rows over every file in `data/raw/trustee_a/` and `trustee_b/` |
| n_resubmission_duplicates | n_raw_rows − n_loan_months |
| n_called_deals | distinct deal_id with a called exit |
| n_called_deals_b | the same, for trustee_format B |
| canonical_truth_mismatches | rows where `fact_loan_month` differs from the true panel regenerated in memory, by the step 2.6 rule. Use the comparison from `tests/test_canonical_truth.py`, moved into `rmbsq/canonical/truth_check.py` so both use it |
| arrears_90p_first, arrears_90p_peak, arrears_90p_latest | pool arrears_90p_bal at 2021-10, at its maximum, and at 2026-09, from `outputs/pool_monthly.csv` |
| arrears_90p_peak_month | the YYYY-MM of the maximum (first on ties) |

**C.2 `outputs/compiler_check.csv`**, with columns `id, source, rows, max_scaled_diff, route, oracle_ok`. It has 1 row per compiler gold spec (S01 to S15, source `compiler_gold`) and per eval answer item (Q01 to Q34, source `eval`), run on the full database:

- `rows` is the compiled result's row count;
- `max_scaled_diff` is against that item's hand or gold SQL, by the step 3.3 rule, written `%.3e`;
- `route` is the auto route;
- `oracle_ok` is true when the Oracle text has no banned substring and parses back (step 3.5).

**C.3 `outputs/trap_effects.csv`**, with columns `trap, item_id, gold, naive, naive_rule`. The gold and naive values come from SQL on the full database, written in `rmbsq/eval/traps.py`. The gold values are computed with the compiler.

| trap | item_id | gold | naive | naive_rule |
|---|---|---|---|---|
| arrears_units | Q27 | arrears_30p_bal at 2026-09 | the same ratio with dpd_bucket ≥ 3 | `2 or more missed payments read as 60+ days` |
| call_as_prepay | Q29 | cpr for deal_name CST 2019-1, 2025-01 to 2025-12, point | the B.6 compounding with `called` treated as `prepaid` in both smm_num and smm_den | `clean-up call exits counted as prepayments` |
| call_as_prepay | Q30 | pool cpr at 2025-11 | the same naive rule | as above |
| exit_rows | Q32 | pool loan_count at 2025-11 | COUNT(*) of all fact rows in 2025-11 | `exit rows counted as live loans` |
| weighting | Q33 | pool wa_indexed_ltv at 2024-12 | AVG(indexed_ltv) over rows with closing_balance > 0 at 2024-12 | `simple mean instead of balance weighting` |
| compounding | Q2_2025 | pool cpr, 2025-04 to 2025-06, point | the mean of the 3 monthly cpr values | `monthly CPR averaged instead of compounded` |

The compounding row is the trap that was dropped (instruction 05 B.1). It is kept here as evidence for that decision.

Chat Claude's values on the full database, which must match to 1e-4:

- Q27: 0.006631 and 0.005857;
- Q29: 0.2156 and 1.0000;
- Q30: 0.1832 and 0.4898;
- Q32: 9975 and 10572;
- Q33: 0.519643 and 0.509175;
- Q2_2025: 0.180644 and 0.180632.

---

## D. Claims (`deliverable/claims.csv`)

`rmbsq/deliverable/claims.py::build_claims(eval_recorded: bool) -> pd.DataFrame` writes `deliverable/claims.csv`, with columns `claim_id, value, display, source_file, source_rule`. `value` is the raw number or string, and `display` is the string placed in documents.

**Formats:**

- `int`: thousands separators, `21,945`;
- `pct2`: × 100 with 2 dp and `%`, `1.54%`;
- `pct1`: 1 dp, `21.6%`;
- `pp1`: percentage points with 1 dp;
- `s2`: seconds with 2 dp;
- `sci1`: `1.7e-15`;
- `str`: as is.

| claim_id | source_file | rule | format |
|---|---|---|---|
| n_deals, n_loans, n_loan_months, n_raw_rows, n_resubmission_duplicates, n_called_deals, n_called_deals_b, canonical_truth_mismatches | data_summary.csv | stat of that name | int |
| arrears_90p_first_pct, arrears_90p_peak_pct, arrears_90p_latest_pct | data_summary.csv | arrears_90p_first / peak / latest | pct2 |
| arrears_90p_peak_month | data_summary.csv | arrears_90p_peak_month | str |
| gold_total | compiler_check.csv | row count | int |
| gold_matched | compiler_check.csv | rows with max_scaled_diff ≤ 1e-9 | int |
| gold_worst_diff | compiler_check.csv | max of max_scaled_diff | sci1 |
| oracle_ok | compiler_check.csv | rows with oracle_ok true | int |
| rows_36x | scale_benchmark.csv | db_rows where db = 36x | int |
| x36_max_default_s | scale_benchmark.csv | max median_s where db = 36x and threads = 0, rounded **up** to 2 dp | s2 |
| x36_max_single_s | scale_benchmark.csv | max median_s where db = 36x and threads = 1 | s2 |
| trap_call_deal | trap_effects.csv | the literal `CST 2019-1` (the Q29 filter) | str |
| trap_call_gold_pct, trap_call_naive_pct | trap_effects.csv | Q29 gold, naive | pct1 |
| trap_exit_extra_loans | trap_effects.csv | Q32 naive − gold | int |
| trap_exit_month | trap_effects.csv | the literal `November 2025` | str |
| trap_weight_gold_pct, trap_weight_naive_pct | trap_effects.csv | Q33 gold, naive | pct2 |
| trap_compound_cpr_pct | trap_effects.csv | Q2_2025 gold | pct1 |
| trap_compound_gap | trap_effects.csv | abs(Q2_2025 gold − naive) | sci1 |

Recorded state only (from `eval_summary.csv`, with system `system` for `sys_` and `baseline` for `base_`):

| claim_id | rule | format |
|---|---|---|
| sys_total_k, sys_total_n, base_total_k, base_total_n | k, n of category total | int |
| sys_total_pct, base_total_pct | accuracy of total | pct1 |
| sys_total_lo, sys_total_hi, base_total_lo, base_total_hi | wilson_lo, wilson_hi of total | pct1 |
| sys_trap_k, base_trap_k | k of category trap | int |
| sys_ambig_k | k of category ambiguous, system | int |

`x36_max_default_s` rounds up because it is written as "under X seconds"; rounding down could make the sentence false.

---

## E. The `eval_table` block

This is a markdown table generated from `eval_summary.csv`:

```
| category | questions | governed system | plain text-to-SQL |
|---|---|---|---|
| simple | 10 | 9 (90%) | 7 (70%) |
…
| total | 40 | … | … |
```

- The rows follow the category order of `eval_summary.csv`, then total.
- Percentages are 0 dp, from k / n.
- In the pending state, the block is never rendered.

---

## F. Figures (`scripts/make_figures.py`, matplotlib, 150 dpi, PNG)

Every figure has the footnote "Synthetic data. Source: <csv path>." at the bottom left, in 8 pt grey.

1. **`outputs/figures/arrears_90p_by_vintage.png`.**
   - Data: `outputs/arrears_90p_by_vintage.csv`, built through `compile` and `execute` from the governed spec: arrears_90p_bal, group_by vintage_year, quarterly series from 2021-10 to 2026-09 (O-32 (a)).
   - 1 line per vintage year, y axis in %, x axis quarter labels with every 4th shown.
2. **`outputs/figures/scale_benchmark.png`.**
   - Data: `outputs/scale_benchmark.csv`, rows with route auto and threads 0.
   - 1 dot per item at 1x and at 36x, with items sorted by 36x time and a log y axis in seconds.
   - Title: "Query time per eval question, 1x and 36x data".
3. **`outputs/figures/eval_accuracy.png`**, recorded state only.
   - Grouped bars by category for the 2 systems, with Wilson interval whiskers and the y axis from 0 to 100%.
   - In the pending state, the file must not exist; delete it if present.

The kickoff's `cpr_by_city.png` isn't used by any document, so it is dropped. `make_figures.py` must be deterministic: set `matplotlib.use("Agg")`, fix the figure size, and set `svg.hashsalt` and `savefig` metadata `{"Software": None}`. Two runs give byte-identical PNGs.

---

## G. Worked example and transcripts

- **`outputs/worked_example.md`**, always built, from eval item Q11's gold spec, without the LLM. It holds the question, the spec JSON, the Oracle SQL, and the display table as a markdown table. Its heading is "Worked example: the compiler path (spec written by hand)".
- **`outputs/transcripts/01_answer.md`, `02_clarify.md` and `03_unsupported.md`**, recorded state only, for Q11, Q35 and Q39, from the replayed `answer()`. They hold the question, the model's spec, the Oracle SQL (01 only), the display table (01 only) and the text. In the pending state the folder must not exist.

---

## H. `scripts/build_writeup.py`

In order:

1. If `outputs/eval_summary.csv` exists, the state is recorded; otherwise pending.
2. `build_summary.py`, which needs the canonical database; build it first if missing.
3. Figures, the worked example, and the transcripts if recorded.
4. Claims.
5. README and design response.
6. The number check on both documents, failing loudly on any unexplained number.
7. Print the state and the list of files written.

It has no network code and needs no API key.

---

## I. CI (`.github/workflows/ci.yml`)

- On push and pull request to main, run on `ubuntu-latest` with Python 3.12 through `astral-sh/setup-uv`.
- Steps: `uv venv`, `uv pip sync requirements-lock.txt`, `uv pip install -e . --no-deps`, `pytest -q`, `pytest -q -m full`.
- No secrets are used.

---

## J. Steps, with tests

**6.0 Templates and render.**
- Copy the 2 templates and write `fixed_numbers.txt`.
- Build `render.py` and `numbers.py`.
- Tests:
  - `test_render_sections`: each marker kind in both states, an unknown name raising, and the newline handling;
  - `test_number_check`: a constructed document with 1 unexplained number fails, and passes once that number is a claim.

**6.1 Summary outputs** (C). Run `build_summary.py`, and commit the 3 CSVs. Tests:
- `test_data_summary_values` (`full`): n_loan_months 773,336, n_raw_rows 774,057, duplicates 721, called deals 17 with 7 in format B, and mismatches 0;
- `test_compiler_check` (`full`): 49 rows, all ≤ 1e-9 and all oracle_ok;
- `test_trap_effects` (`full`): the C.3 values to 1e-4.

**6.2 Claims** (D). Test `test_claims_pending`: every scalar placeholder in both templates outside `{{#eval}}` sections has a claim, and every claim value traces to its source_file and rule.

**6.3 Figures and worked example** (F, G). Test `test_figures_deterministic`: build twice into temp dirs and get byte-identical PNGs. In the pending state, `eval_accuracy.png` and `outputs/transcripts/` don't exist.

**6.4 Documents** (H).
- Run `build_writeup.py` and commit `README.md`, `docs/DESIGN_RESPONSE.md`, `deliverable/claims.csv`, the figures and `outputs/worked_example.md`.
- Tests:
  - `test_documents_current`: re-rendering from the committed CSVs equals the committed README and design response byte for byte;
  - `test_documents_numbers_explained`: the number check passes on both;
  - `test_recorded_state_renders` uses a constructed `eval_summary.csv` in a temp dir with made-up k values. It checks the recorded state renders, has no `{{`, includes the eval table, and passes the number check. This proves the recorded path works before a real run exists.

**6.5 CI** (I). Push, then record the Actions run's result in the review. If it fails, fix it, push again, and record both runs. This is a stop condition only if it still fails after a second fix.

**6.6 Plan.** Update `PLAN.md` Section 6 for this file (the pending and recorded states, the dropped `cpr_by_city.png`, the new outputs), and commit it.

---

## K. Review evidence (`review/section_6.md`)

1. The 3 C CSVs in full.
2. `deliverable/claims.csv` in full.
3. The rendered `README.md` and `docs/DESIGN_RESPONSE.md` in full.
4. The rendered recorded state from the `test_recorded_state_renders` fixture, as 1 example, marked as made-up numbers.
5. The 2 figures, as image links.
6. The Actions run URL and result.
7. Both pytest outputs from a fresh clone.

Then write `instructions/06_section_6.status.md` and push.
