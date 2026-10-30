# 03 Section 3: semantic layer and compiler

Session 3 instructions for Claude Code. Build all of Section 3 (steps 3.0 to 3.6) in this session, without pausing. This file beats `PLAN.md`, which beats the kickoff (rule 13). Status file: `instructions/03_section_3.status.md`.

This session uses 2 data files committed by chat Claude:

- `instructions/03_compiler_gold.json`: the 15 test specs, each with hand SQL, its expected route and expected row counts.
- `instructions/03_spec_examples.json`: 8 valid and 12 invalid QuerySpec examples.

Copy both, byte for byte, to `tests/fixtures/compiler_gold.json` and `tests/fixtures/spec_examples.json` in step 3.0. Never edit them.

---

## A. Approval of Section 2, and O-36

Section 2 is approved. Chat Claude checked it on Linux, installing from the lock file:

- `pytest -q`: 56 passed. `pytest -q -m full`: 5 passed, including `test_full_canonical_equals_truth_panel`.
- `scripts/build_canonical.py` builds the full database on Linux.
- An independent script read the raw format B parquet files directly, with no project code. It applied resubmission dedupe and the C.3 call rule, and recovered the same 7 deals, call months and loan counts.

**O-36: (a) confirmed.** Take the first loan_id per originator among loans that have a row with closing_balance > 0.

---

## B. Query semantics (what every compiled query computes)

Chat Claude wrote the 15 hand SQL statements in `03_compiler_gold.json` from these rules. It also checked them against a separate pandas calculation on both profiles: all 15 agree to within 8e-16, return at least 1 row, and hold no nulls.

**B.1 Rows in scope.** These are the `fact_loan_month` rows with period from time.start to time.end inclusive that pass every filter, joined to `dim_loan` and `dim_deal`. A filter is `dimension IN (values)`, and different filters are ANDed.

**B.2 Monthly parts**, per group and period, over the rows in scope. These are the same 13 parts as the `agg_deal_month` columns (instruction 02 C.5): loan_count, bal, a30_bal, a90_bal, a90_cnt, hard_bal, orig_ltv_x_bal, idx_ltv_x_bal, rate_x_bal, smm_num, smm_den, mdr_num, mdr_den. They use the same row filters (closing_balance > 0 for stock parts; opening_balance > 0 for flow parts), and every sum is 0 rather than NULL when no row qualifies.

**B.3 Period label** per monthly part:

| shape | label |
|---|---|
| series, grain month | `YYYY-MM` |
| series, grain quarter | `YYYY-Qn` |
| series, grain year | `YYYY` |
| point, start = end | the month, `YYYY-MM` (O-16) |
| point, start < end | `range` |

**B.4 Output rows.** There is 1 output row per (group values, period_label) that has at least 1 monthly part. Nothing else is created, so a group with no rows in a bucket has no row there.

**B.5 Stock metrics,** per output row. Take the monthly part at the latest period in the bucket that has loan_count > 0 for that group (O-17). Then:

| metric | value |
|---|---|
| loan_count | loan_count |
| balance_total | bal |
| arrears_30p_bal | a30_bal / bal |
| arrears_90p_bal | a90_bal / bal |
| arrears_90p_cnt | a90_cnt / loan_count |
| hardship_share_bal | hard_bal / bal |
| wa_orig_ltv | orig_ltv_x_bal / bal |
| wa_indexed_ltv | idx_ltv_x_bal / bal |
| wa_rate | rate_x_bal / bal |

If no month in the bucket has loan_count > 0, every stock metric in that row is NULL.

**B.6 Flow metrics,** per output row:

- smm_m = smm_num / smm_den, over the months in the bucket with smm_den > 0. n = the number of such months.
- smm_p = 1 if any smm_m ≥ 1. Otherwise smm_p = 1 − exp(Σ ln(1 − smm_m)).
- smm_vol = 1 − (1 − smm_p)^(1 / n), which is the monthly equivalent.
- cpr = 1 − (1 − smm_p)^(12 / n).
- cdr is the same with mdr_m = mdr_num / mdr_den, over months with mdr_den > 0.
- If n = 0, the metric is NULL.

For grain month, n is 1, so cpr = 1 − (1 − smm)^12, as kickoff 6.3 says.

**B.7 Output columns and order.** The group_by columns in spec order come first, then `period_label`, then 1 column per metric in spec order. Dimension output values are:

- flags: `yes` / `no`;
- dpd_bucket: `current, 1-29, 30-59, 60-89, 90+`;
- issue_year and vintage_year: integers;
- everything else: the stored string.

Rows sort ascending by the group_by columns, then period_label. If `order` is set, rows sort by that metric in its direction with NULLs last, then ascending by group_by and period_label, and the first `limit` rows are kept. Metric columns are float64 in the returned DataFrame, and loan_count is Int64.

**B.8 Hand example** for `test_quarter_compounding_hand_example`. Build it as a constructed 1-group monthly parts frame and run only the time aggregation, not SQL.

- 3 months with smm_m 0.01, 0.02 and 0.015:
  - survival 0.99 × 0.98 × 0.985 = 0.955647;
  - smm_p 0.044353;
  - cpr = 1 − 0.955647^4 = 0.16595400138;
  - smm_vol = 1 − 0.955647^(1/3) = 0.01500846031.
- The same quarter with the third month missing (smm_den = 0):
  - n = 2 and survival 0.9702;
  - cpr = 1 − 0.9702^6 = 0.16599698292.
- Assert all of these to 1e-10.

---

## C. Catalogue files

**C.1 `semantic/metrics.yaml`.** There are 12 entries, with keys `name, kind (stock|flow), numerator, denominator, display (count|aud_m|pct), definition`. numerator and denominator name the B.2 parts, or are empty for the flow metrics' compound rule. The definitions, verbatim:

| name | kind | display | definition |
|---|---|---|---|
| loan_count | stock | count | Number of loans with a positive balance at month end. |
| balance_total | stock | aud_m | Total outstanding balance in AUD at month end. |
| arrears_30p_bal | stock | pct | Share of outstanding balance that is 30 or more days past due, excluding loans in hardship, weighted by balance. |
| arrears_90p_bal | stock | pct | Share of outstanding balance that is 90 or more days past due, excluding loans in hardship, weighted by balance. |
| arrears_90p_cnt | stock | pct | Share of loans by count that are 90 or more days past due, excluding loans in hardship. |
| hardship_share_bal | stock | pct | Share of outstanding balance on a hardship arrangement. |
| wa_orig_ltv | stock | pct | Balance-weighted average loan-to-value ratio at origination. |
| wa_indexed_ltv | stock | pct | Balance-weighted average current loan-to-value ratio, with property values indexed to suburb house prices. |
| wa_rate | stock | pct | Balance-weighted average interest rate. |
| smm_vol | flow | pct | Monthly voluntary prepayment rate: full prepayments plus partial curtailments over scheduled balance. Excludes repurchases, defaults and clean-up calls. |
| cpr | flow | pct | Conditional prepayment rate: smm_vol annualised. Excludes repurchases, defaults and clean-up calls. |
| cdr | flow | pct | Conditional default rate: defaulted balance over opening balance each month, annualised. |

**C.2 `semantic/dimensions.yaml`.** There are 18 entries, with keys `name, column, table, level (deal|loan), labels, definition`. `labels` lists output values where they are fixed, and is empty where values come from the database.

| name | column | table | level | labels | definition |
|---|---|---|---|---|---|
| deal_id | deal_id | fact_loan_month | deal | | Deal identifier, for example D004. |
| deal_name | deal_name | dim_deal | deal | | Deal name: originator code, issue year and series number, for example HARB 2019-1. |
| originator | originator | dim_deal | deal | | Originator code: HARB, KOO, WAT, CST or RED. |
| trustee_format | trustee_format | dim_deal | deal | A, B | Which trustee report format the deal is delivered in. |
| issue_year | issue_year | dim_deal | deal | | Year the deal was issued. |
| vintage_year | vintage_year | dim_loan | loan | | Year the loan was originated. |
| city | city | dim_loan | loan | | Capital city region of the property. |
| state | state | dim_loan | loan | NSW, QLD, SA, VIC, WA | State of the property. |
| area | area | dim_loan | loan | | Local area of the property, for example Blacktown. |
| suburb | suburb | dim_loan | loan | | Suburb of the property, for example Blacktown North. |
| rate_type | rate_type | fact_loan_month | loan | fixed, variable | Current rate type that month; a fixed loan becomes variable at its fixed rate expiry. |
| io_flag | io_flag | fact_loan_month | loan | yes, no | Whether the loan is interest only that month. |
| occupancy | occupancy | dim_loan | loan | owner, investor | Owner occupied or investment property. |
| lmi_flag | lmi_flag | dim_loan | loan | yes, no | Whether the loan has lenders mortgage insurance (LTV above 80% at origination). |
| ltv_bucket_orig | ltv_bucket_orig | dim_loan | loan | <=60, 60-70, 70-80, 80-90, >90 | Origination LTV band, in percent. |
| ltv_bucket_indexed | ltv_bucket_indexed | fact_loan_month | loan | <=60, 60-70, 70-80, 80-90, >90 | Current indexed LTV band, in percent. |
| seasoning_bucket | seasoning_bucket | fact_loan_month | loan | 0-12, 13-24, 25-36, 37-60, >60 | Months since origination. |
| dpd_bucket | dpd_bucket | fact_loan_month | loan | current, 1-29, 30-59, 60-89, 90+ | Days past due band. Loans in hardship are current. |

`Catalog.allowed_values(name)` returns the labels where fixed, otherwise the sorted distinct values from the database.

---

## D. Compiler shape and Oracle rules

**D.1 The statement** is 1 `sqlglot` expression tree with CTEs, in the same shape as the hand SQL:

1. `parts`: B.2, grouped by the group_by columns and period;
2. a labelled `b`: B.3;
3. `keys`: the distinct group values and period_label;
4. `stock`: B.5, by `ROW_NUMBER() OVER (PARTITION BY keys ORDER BY period DESC)` over parts with loan_count > 0;
5. `flow`: B.6;
6. the final select, `keys LEFT JOIN stock LEFT JOIN flow`, with B.7 order.

Leave out the `stock` or `flow` CTE when no metric needs it. Every value from the spec is a literal node in the tree, never pasted into a string.

**D.2 Route `agg`.** `parts` reads `agg_deal_month` joined to `dim_deal`, summing its columns per group and period, instead of reading `fact_loan_month`. Everything after `parts` is identical. Route `auto` picks `agg` when every group_by and filter dimension is deal level (C.2). That includes specs with neither, such as S01 and S05.

**D.3 Oracle-safe constructs.** `sqlglot` writes several DuckDB constructs into Oracle output without any warning, although Oracle can't run them. Chat Claude measured this with the pinned `sqlglot` 30.26.0:

- `COUNT(*) FILTER (WHERE …)` passes through unchanged;
- `year()` and `quarter()` become `YEAR()` and `QUARTER()`, which Oracle doesn't have;
- `CAST(… AS VARCHAR)` becomes `CAST(… AS CLOB)`.

So the compiler uses only these forms:

- **conditional aggregates** as `SUM(CASE WHEN … THEN x ELSE 0 END)` and `SUM(CASE WHEN … THEN 1 ELSE 0 END)`, never FILTER;
- **period labels** from a join to a new table `dim_period` (D.4), never date functions;
- **flag and bucket labels** with `CASE` expressions;
- **math** with `EXP`, `LN`, `POWER` and `ROW_NUMBER`, all of which render to Oracle unchanged.

Booleans are compared as columns (`NOT f.hardship_flag`); the Oracle target is 23ai, which has BOOLEAN. The hand SQL in the gold file is DuckDB flavoured and uses FILTER. That is fine, because the test compares results, not SQL text.

**D.4 `dim_period`** (added in step 3.0). Columns: `period DATE, month_label VARCHAR, quarter_label VARCHAR, year_label VARCHAR`. It has 1 row per month from window_start to window_end, for example `2025-04-01, 2025-04, 2025-Q2, 2025`. `build_canonical` writes it, and `canonical_row_counts.csv` gains its row.

---

## E. Steps, with tests

Commit one per step.

**3.0 Fixtures and `dim_period`.**
- Copy the 2 JSON files (the header of this file).
- Add D.4 to `build_canonical`.
- Rebuild the full database and update `outputs/canonical_row_counts.csv` (the new row is `dim_period, all, 60`).
- Tests: `test_dim_period` (60 rows; spot check 2021-10, 2024-12 and 2026-09). Every Section 2 test still passes.

**3.1 Catalogue** (C.1, C.2, `rmbsq/semantic/catalog.py`). Tests:
- `test_twelve_metrics`: the names and definitions equal C.1 verbatim;
- `test_eighteen_dimensions`: the 5 deal-level names, and every row of C.2;
- `test_allowed_values_from_db`: on `small_db`, states are 5, and originators are those present.

**3.2 QuerySpec** (`rmbsq/semantic/spec.py`). Metric and dimension names are `Literal` types built from the 12 and 18 names, so unknown names fail validation. Rules:
- the kickoff 6.6 intent rules;
- 1 to 3 metrics, and 0 to 2 group_by, without duplicates;
- filter keys from the 18 names, each with 1 to 20 values;
- time months matching `YYYY-MM`, with window_start ≤ start ≤ end ≤ window_end;
- `order.metric` among the spec's metrics, with a limit of 1 to 20;
- 2 to 4 clarify options;
- an answer without time gets the default (2026-09 point month).

Tests: `test_valid_examples` (every valid example parses, and V01 gets its `expect_time`) and `test_invalid_examples` (every invalid example raises `ValidationError`). Window bounds come from config, not literals.

**3.3 Compiler and time aggregation** (`compiler.py`, `timeagg.py`). Tests:
- `test_fifteen_specs_match_hand_sql`: for each gold spec on `small_db`:
  - `execute(compile(spec))` equals the hand SQL's result;
  - the columns and row order are identical;
  - dimension values are equal as strings;
  - metric values are within 1e-9 absolute after scaling by max(1, |value|);
  - the row count equals `rows_small`.
- `test_quarter_compounding_hand_example` (B.8).
- `test_full_fifteen_specs_match_hand_sql` (marked `full`): the same comparison on the full database, with the row counts equal to `rows_full`.

**3.4 Routing.** Tests:
- `test_route_auto_choice`: compile's auto route equals `route_auto` for all 15 specs;
- `test_fact_and_agg_routes_equal`: for the 6 agg specs (S01, S02, S05, S10, S11 and S12), results on route `fact` and route `agg` are equal by the 3.3 rule, on `small_db`.

**3.5 Oracle rendering.** `sql_oracle` is the same tree rendered with `dialect="oracle"` and `pretty=True`. Test `test_specs_render_to_oracle`, for all 15 specs:
- the warning list is empty (capture the `sqlglot` logger at WARNING, with `unsupported_level=ErrorLevel.RAISE`);
- the Oracle text contains none of these case-insensitive substrings: `FILTER(`, `FILTER (`, `YEAR(`, `QUARTER(`, `STRFTIME`, `CLOB`, `LIMIT `, `::`;
- the text parses back with `sqlglot.parse_one(text, read="oracle")`.

**3.6 Display formatting** (`rmbsq/semantic/format.py`). `format_table(df, catalog)` returns all strings:
- pct as `0.00%` (2 dp);
- aud_m as `A$412.3m` (dollars ÷ 1e6, 1 dp);
- count as `12,345`;
- years as plain integers;
- NULL as `n/a`;
- dimensions and period_label unchanged.

Test `test_display_rules` covers each display kind and NULL, plus round-half-even behaviour for 0.000125 → `0.01%` (record what Python's format gives; don't change it).

Update `PLAN.md` for step 3.0 and the D.3 rules, and commit it.

---

## F. Review evidence (`review/section_3.md`)

1. Both YAML files in full.
2. Per gold spec: route chosen, rows on small and full, max scaled difference against the hand SQL on both, and the DuckDB SQL for S04 and S11 in full.
3. The Oracle SQL for S04, S11 and S12 in full, plus the captured warning list.
4. The B.8 arithmetic, line by line, with the computed values.
5. Each valid and invalid example, with accepted or rejected and the message.
6. `format_table` output for S02 and S12 on the full database, beside the raw frame.
7. Both pytest outputs from a fresh clone (default, and `-m full`).

Then write `instructions/03_section_3.status.md` and push.
