# Status: session 2 (02_section_2)

## Outcome

Complete. Steps 2.1 to 2.6 are built, committed and pushed. Evidence is in
`review/section_2.md`.

- Last step reached: 2.6.
- Stop reason: none. Every expected value in instruction 02 matched exactly:
  - fact_loan_month 773,336 rows, from 774,057 raw rows less 721 resubmission duplicates;
  - dim_loan 21,945 loans; dim_deal 50 deals;
  - exits: called 2,542, prepaid 11,566, repurchased 376, defaulted 346;
  - the 7 format B called deals (D004, D005, D009, D010, D014, D015, D020), with every
    call month and called-loan count as listed in D 2.3.
- `fact_loan_month` equals the true panel row for row, on the small profile and on the
  full profile (step 2.6).
- `outputs/pool_monthly.csv` matches `outputs/pool_monthly_truth.csv` with a max absolute
  difference of 0 on every ratio column at 10 dp. balance_total differs by at most
  1.9e-6, which is float noise in the truth file.
- `scripts/build_canonical.py` takes about 11 to 14 s on the full profile. The DuckDB file
  is 33,566,720 bytes and is not committed.
- The outputs are byte-identical across 2 builds.

## What was built

- 2.1: `rmbsq/canonical/ingest.py`, both formats to the C.1 frame (money in `Int64` cents).
- 2.2 to 2.5: `rmbsq/canonical/build.py` holds `dedupe_resubmissions`, `detect_calls`,
  `enrich` and `build_canonical`, plus `scripts/build_canonical.py`.
- 2.5 outputs: `outputs/pool_monthly.csv` and `outputs/canonical_row_counts.csv`.
- 2.6: `tests/test_canonical_truth.py`, plus the step 2.6 paragraph in `PLAN.md`.
- `tests/conftest.py` gains the fixtures `small_rows`, `small_db` and `full_db`.

## Deviations (detail in the review, per step)

- **O-29 reading (step 2.4), raised as O-36.** RED's first loan, D005-0001, has no row in
  the small panel. The test uses the first RED loan that has a row, D005-0002.
- `detect_calls(df)` reads `call_detect_share` from `config.toml` itself, because its
  kickoff 7 signature takes no config.
- `agg_deal_month` sums are `DECIMAL(38,2)`, the type DuckDB gives a sum, and its counts
  are `BIGINT`.
- The build runs DuckDB on 1 thread, so DOUBLE sums are deterministic (rule 9).

## Test results (fresh clone of `ab84488`, Windows, Python 3.12.13, from the lock file)

- `pytest -q`: 56 passed, 5 deselected.
- `pytest -q -m full`: 5 passed, 56 deselected.

## Questions for the reviewer

1. **O-36 (step 2.4).** O-29's literal rule gives 4 rows, because D005-0001 has no row in
   the window. Option (a) is built: take the first loan_id per originator among loans
   that have a row with closing_balance > 0, which makes RED's row D005-0002 at 2026-09.
   Option (b): a later instruction names the 5 (loan_id, period) pairs. Confirm (a) or
   give (b).

## Last 3 commits on origin (before this file)

```
4882d12 section 2: review file and open decision O-36
ab84488 step 2.6: fact_loan_month equals the true panel row for row
fd55a18 step 2.5: build_canonical writes the DuckDB tables, pool_monthly.csv and row counts
```
