# 02 Section 2: canonical layer

Session 2 instructions for Claude Code. Build all of Section 2 (steps 2.1 to 2.6) in this session, without pausing. This file beats `PLAN.md`, which beats the kickoff (rule 13). Status file: `instructions/02_section_2.status.md`.

---

## A. Approval of Section 1

Section 1 is approved, including the 01b completion. Chat Claude checked it on Linux, installing from the lock file:

- `pytest -q`: 39 passed, 2 deselected.
- `pytest -q -m full`: 2 passed. This includes `test_full_regenerates_identically`, so the generator now reproduces the Windows-built `MANIFEST.json` byte for byte on Linux, and the HPI rounding fix works.
- `outputs/calibration.csv`: every band passes, and every value equals chat Claude's prototype exactly.

The hardship test frame moved from D001 to D050 (status file, "Deviation"). That is accepted. A spell already running when the window opens can't start on an entry row, and D050's issue reset falls inside the window.

---

## B. What this section must prove

The canonical layer has 1 job: undo the 4 trustee traps so that the database equals the true panel.

The test of that is direct. `fact_loan_month`, built from the raw trustee files, must equal the true panel from `simulate` row for row, on every column they share (2.6). That holds on the small profile in every default run, and on the full profile under `-m full`. Once it passes, every later number in the project rests on data whose cleaning has been proved, not assumed.

---

## C. Fixed details for every step

**C.1 Canonical row frame** (output of both ingest functions, then of dedupe, calls and enrich). The columns, in this order:

| column | pandas dtype | from A | from B |
|---|---|---|---|
| loan_id, deal_id | string | as is | LoanId, DealId |
| period | datetime64[ns], first of month | report_month | ReportMonth |
| submission_seq | int64 | as is | SubmissionSeq |
| opening_balance_c, scheduled_principal_c, curtailment_c, closing_balance_c, exit_balance_c, loss_c | Int64 cents | round(dollars × 100) | the `…Cents` columns |
| interest_rate | float64 | as is | InterestRate |
| dpd_bucket | int8 | from arrears_days (C.2) | MissedPayments, capped at 4 |
| hardship_flag | bool | hardship_flag == 1 | Status == "H" |
| exit_reason | string, nullable | PIF prepaid, REP repurchased, DEF defaulted, CALL called | P prepaid, R repurchased, D defaulted |
| orig_month, fixed_end_month, io_end_month | datetime64[ns], nullable | as is | as is |
| orig_balance_c, orig_valuation_c | Int64 cents | | |
| orig_ltv | float64 | | |
| rate_type_orig | string | rate_type | RateType |
| io_flag_orig, lmi_flag | bool | | |
| occupancy, city, state, area, suburb | string | | |
| trustee_format | string | "A" | "B" |

Money stays in integer cents from ingest to the database insert (O-27). Column names carry a `_c` suffix while in cents. Inside DuckDB the suffix goes: the columns are DECIMAL(18,2) dollars, named as in kickoff 6.1.

**C.2 Arrears days to bucket (format A).** 0 → 0; 1 to 29 → 1; 30 to 59 → 2; 60 to 89 → 3; 90 and above → 4. Hardship rows get dpd_bucket 0 in both formats. Format B already reports 0 there; set it anyway, as a rule.

**C.3 Call detection.** For each deal d and month t, let active(d, t − 1) = the number of rows of deal d in month t − 1 with closing_balance_c > 0. If the number of rows in (d, t) with exit_reason prepaid is at least call_detect_share × active(d, t − 1), and active(d, t − 1) > 0, then every prepaid exit in (d, t) becomes called. This applies to both formats, after dedupe.

**C.4 Enrich.** HPI comes from `data/raw/hpi.parquet` (already rounded to 6 dp).

- indexed_value = orig_valuation × hpi(suburb, period) / hpi(suburb, orig_month), as float64 dollars.
- indexed_ltv = closing_balance / indexed_value, or opening_balance / indexed_value on exit rows (exit_reason not null).
- ltv_bucket_orig on orig_ltv and ltv_bucket_indexed on indexed_ltv, with the 6.2 edges. Labels are `<=60, 60-70, 70-80, 80-90, >90`; values exactly on an edge go to the lower bucket.
- seasoning_months = months from orig_month to period. seasoning_bucket is `0-12, 13-24, 25-36, 37-60, >60`.
- rate_type (current) = `fixed` if rate_type_orig is fixed and period < fixed_end_month, else `variable`.
- io_flag (current) = io_flag_orig and period < io_end_month.
- vintage_year = year of orig_month.

**C.5 Database** (`data/canonical/rmbs.duckdb`). Tables and DuckDB types:

- `dim_deal(deal_id VARCHAR, deal_name VARCHAR, originator VARCHAR, originator_name VARCHAR, trustee_format VARCHAR, issue_month DATE, issue_year INTEGER, issue_balance DECIMAL(18,2))`, from `deals.parquet`.
- `dim_loan(loan_id VARCHAR, deal_id VARCHAR, orig_month DATE, vintage_year INTEGER, orig_balance DECIMAL(18,2), orig_valuation DECIMAL(18,2), orig_ltv DOUBLE, ltv_bucket_orig VARCHAR, rate_type_orig VARCHAR, fixed_end_month DATE, io_flag_orig BOOLEAN, io_end_month DATE, occupancy VARCHAR, lmi_flag BOOLEAN, city VARCHAR, state VARCHAR, area VARCHAR, suburb VARCHAR)`. It has 1 row per loan, taken from that loan's first canonical row. Building it fails with a clear error if any static field differs between a loan's rows.
- `fact_loan_month(loan_id VARCHAR, deal_id VARCHAR, period DATE, opening_balance DECIMAL(18,2), scheduled_principal DECIMAL(18,2), curtailment DECIMAL(18,2), closing_balance DECIMAL(18,2), interest_rate DOUBLE, dpd_bucket TINYINT, hardship_flag BOOLEAN, exit_reason VARCHAR, exit_balance DECIMAL(18,2), loss DECIMAL(18,2), indexed_value DOUBLE, indexed_ltv DOUBLE, ltv_bucket_indexed VARCHAR, seasoning_months INTEGER, seasoning_bucket VARCHAR, rate_type VARCHAR, io_flag BOOLEAN)`. Rows are sorted by period, then loan_id, and loan_id plus period is unique.
- `hpi(suburb VARCHAR, period DATE, hpi DOUBLE)` and `cash_rate(period DATE, rate DOUBLE)`.
- `agg_deal_month`, 1 row per deal_id and period. It is built by 1 SQL statement over `fact_loan_month`, with these columns:

| column | definition |
|---|---|
| deal_id, period | keys |
| loan_count | count of rows with closing_balance > 0 |
| bal | sum(closing_balance) where closing_balance > 0, DECIMAL |
| a30_bal | the same, where dpd_bucket ≥ 2 and not hardship_flag |
| a90_bal | the same, where dpd_bucket = 4 and not hardship_flag |
| a90_cnt | count where closing_balance > 0, dpd_bucket = 4 and not hardship_flag |
| hard_bal | sum(closing_balance) where closing_balance > 0 and hardship_flag |
| orig_ltv_x_bal | sum(closing_balance × orig_ltv) where closing_balance > 0, DOUBLE (join to dim_loan) |
| idx_ltv_x_bal | sum(closing_balance × indexed_ltv), the same filter, DOUBLE |
| rate_x_bal | sum(closing_balance × interest_rate), the same filter, DOUBLE |
| smm_num | sum(curtailment) + sum(exit_balance where prepaid), over rows with opening_balance > 0, DECIMAL |
| smm_den | sum(opening_balance − scheduled_principal) over rows with opening_balance > 0 and exit_reason null or prepaid, DECIMAL |
| mdr_num | sum(exit_balance where defaulted), over rows with opening_balance > 0, DECIMAL |
| mdr_den | sum(opening_balance) over rows with opening_balance > 0, DECIMAL |

A deal-month with no qualifying rows for a sum gets 0, never NULL (COALESCE).

**C.6 Pool output.** `outputs/pool_monthly.csv` is computed by SQL over `agg_deal_month` (sum the columns over deals per period, then take ratios). It has the `pool_monthly_truth.csv` columns. Ratios are written `%.10f`, and balance_total with exactly 2 decimals.

`outputs/canonical_row_counts.csv` has columns `table, trustee_format, rows`. It holds 1 row per table with trustee_format `all`, plus `fact_loan_month` and `dim_loan` split into A and B.

---

## D. Steps, with tests

Commit one per step. Small profile fixtures are generated once per session. The `small_db` fixture runs `build_canonical` on them.

**2.1 Ingestion.** `rmbsq/canonical/ingest.py`. Tests:
- `test_formats_same_columns_and_dtypes`: both formats give exactly the C.1 columns and dtypes;
- `test_arrears_days_map`: every boundary of C.2 (0, 1, 29, 30, 59, 60, 89, 90, 400);
- `test_hardship_rows_bucket_zero`: in both formats, every hardship row has dpd_bucket 0;
- `test_cents_exact`: format A dollars become the same cents as the true panel's balances × 100, for every row of 1 file.

**2.2 Resubmissions.** `dedupe_resubmissions` keeps the max submission_seq per (loan_id, period). Tests:
- `test_resubmission_months_one_row_true_values`: D004 2023-06 in the small profile has 1 row per loan, with closing_balance and curtailment equal to the true panel;
- `test_no_duplicates_after_dedupe`: loan_id plus period is unique after dedupe.

**2.3 Call detection** (C.3, with 01b B.3). Tests:
- `test_detect_calls_constructed`: a hand-built 1-deal frame of 10 loans in which 10 prepay in month t gets 10 called. A second frame in which 9 of 10 prepay (below 0.95) gets 0 called;
- `test_format_b_calls_recovered`: on the small profile, the set of (deal_id, period, loan_id) called in canonical equals the true panel's called exits for format B deals, where empty on both sides is allowed;
- `test_format_a_calls_unchanged`: format A rows read as CALL equal the called rows after detection, and detection changes no format A row;
- `test_full_format_b_calls_recovered` (marked `full`): the 7 format B called deals come back with exactly these call months and called loan counts.

| deal | call month | called loans |
|---|---|---|
| D004 | 2025-11 | 146 |
| D005 | 2025-04 | 150 |
| D009 | 2026-03 | 154 |
| D010 | 2025-12 | 151 |
| D014 | 2026-02 | 147 |
| D015 | 2026-06 | 148 |
| D020 | 2026-04 | 158 |

**2.4 Enrichment** (C.4). Tests:
- `test_indexed_ltv_by_hand_five_rows` (O-29 rows): each value is recomputed in the test from the raw HPI parquet and orig_valuation, without calling `enrich`, to 1e-12;
- `test_buckets_edges`: ltv 0.6, 0.7, 0.8 and 0.9 land in the lower bucket, and seasoning 12, 13, 24, 25, 36, 37, 60 and 61 land in the right buckets;
- `test_current_rate_type_and_io`: on 1 fixed loan and 1 IO loan, the switch happens exactly at fixed_end_month and io_end_month.

**2.5 Canonical database** (C.5 and C.6). `build_canonical` and `scripts/build_canonical.py --raw DIR --db PATH`. Tests:
- `test_tables_and_types`: `DESCRIBE` of every table equals C.5;
- `test_agg_sums_equal_fact_sums`: every `agg_deal_month` column summed over the whole table equals the same sum computed directly from `fact_loan_month`, exactly for DECIMAL columns and to 1e-9 relative for DOUBLE columns;
- `test_dim_loan_static_check`: a constructed pair of rows with a changed suburb makes the build raise;
- `test_pool_monthly_matches_truth`: on the small profile, pool metrics from the canonical layer match the true panel's `pool_monthly` to abs 1e-9 for ratio columns and abs 0.01 for balance_total. truth.py sums floats while DuckDB sums exact decimals, so balances differ by float noise only;
- `test_full_pool_monthly_matches_truth` (marked `full`): the same comparison between the committed `outputs/pool_monthly_truth.csv` and the canonical layer built from the committed full `data/raw/`.

Run the script on the full raw data, write `outputs/pool_monthly.csv` and `outputs/canonical_row_counts.csv`, and commit both. Expected full profile counts, which must match exactly:
- fact_loan_month: 773,336 rows (the raw files hold 774,057, of which 721 are resubmission duplicates);
- dim_loan: 21,945 loans;
- dim_deal: 50 deals;
- exits: called 2,542, prepaid 11,566, repurchased 376, defaulted 346.

**2.6 Canonical equals truth.** New test file `tests/test_canonical_truth.py`:
- `test_canonical_equals_truth_panel`: on the small profile, join `fact_loan_month` to the true panel on loan_id and period. Assert:
  - the same row count on both sides, with no unmatched row on either side;
  - every money column equal to the cent;
  - interest_rate, indexed_value and indexed_ltv equal to 1e-9;
  - dpd_bucket, hardship_flag and exit_reason identical.
- `test_full_canonical_equals_truth_panel` (marked `full`): the same comparison on the full profile, against the panel regenerated in memory.

Add one paragraph to `PLAN.md` for step 2.6, and commit `PLAN.md`.

---

## E. Review evidence (`review/section_2.md`, following the template)

1. Column and dtype table after ingest, for each format, and 3 ingested rows from each.
2. The 2 rows (seq 1 and 2) before dedupe and the 1 row after, for the first 2 loans of D004 2023-06.
3. Every called deal: deal_id, trustee_format, call month and called loans, truth beside canonical.
4. The 5 O-29 rows with HPI at orig_month and period, orig_valuation, balance, the hand value and the computed value.
5. `DESCRIBE` of every table, and `outputs/canonical_row_counts.csv` in full.
6. `pool_monthly.csv`: the first 3 and last 3 rows, plus the max absolute difference against truth for each column.
7. Exit counts by reason from `fact_loan_month`, beside the expected values in step 2.5.
8. The full build runtime and the DuckDB file size.
9. Both pytest outputs (default, and `-m full`) from a fresh clone.

Then write `instructions/02_section_2.status.md` and push.
