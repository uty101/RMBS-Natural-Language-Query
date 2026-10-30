# Conventions, resolved

Every convention the code follows, with its source. Kickoff section numbers refer to
`instructions/00_kickoff.md`. A convention marked **open (O-n)** waits for a decision
in an instruction file; the O-numbers match `PLAN.md` and
`instructions/00_kickoff.status.md`.

## Calendar and time

| # | Convention | Source |
|---|---|---|
| T1 | `period` is a DATE on the first of the month and means the month end status of that month. | 4.1 |
| T2 | Simulation runs monthly 2016-01 to 2026-09 (129 months). Emitted rows: 2021-10 to 2026-09 (60 months), and only where period ≥ the deal's issue_month. | 4.1 |
| T3 | "Latest" is 2026-09 (`[calendar] latest`). | 4.1 |
| T4 | Month arithmetic uses calendar-month periods, never day offsets. | WORKFLOW Part 6 |
| T5 | Default query time when a question gives none: start = end = 2026-09, grain month, shape point. Start ≥ 2021-10, end ≤ 2026-09. | 6.6 |
| T6 | vintage_year = year of orig_month; issue_year = year of issue_month; seasoning_months = months between orig_month and period. | 5.7 |
| T7 | Quarter and year buckets: stock metrics take the last month in the bucket that has data; flow metrics compound monthly smm or mdr, then annualise with exponent 12 / n_months. n_months and the scope of "has data" are open (O-17). | 6.4 |
| T8 | period_label is YYYY-MM, YYYY-Qn or YYYY, and `range` for point shape. The label for a point whose start equals its end is open (O-16). | 6.7 |

## Units and storage

| # | Convention | Source |
|---|---|---|
| U1 | Money is AUD, stored to the cent as DECIMAL(18,2) in DuckDB, never float. The pandas dtype before storage is open (O-27). | 5.1 |
| U2 | Rates and ratios are stored as decimals (0.0412) and displayed as percent with 2 dp. | 5.2 |
| U3 | Balances display in AUD millions with 1 dp (`A$412.3m`); counts display as integers with thousands separators. | 5.3 |
| U4 | Decimals become float only at the very end of `execute`. | 6.7 |
| U5 | Simulation balances are kept to the cent; default loss is rounded to the cent. | 4.7 |

## Loan states and exits

| # | Convention | Source |
|---|---|---|
| L1 | Exit row: opening_balance = prior closing, closing_balance 0, exit_reason set, scheduled_principal 0, exit_balance = opening_balance. indexed_ltv uses opening_balance. | 5.4 |
| L2 | A loan counts in stock metrics in a month only if closing_balance > 0. Flow metrics use rows with opening_balance > 0. | 5.5, 6.3 |
| L3 | Exit precedence in a month: called > defaulted > repurchased > prepaid. | 4.7 |
| L4 | dpd_bucket 0 current, 1 = 1–29, 2 = 30–59, 3 = 60–89, 4 = 90+; labels `current, 1-29, 30-59, 60-89, 90+`. Hardship rows have dpd_bucket 0. | 4.7, 6.2, 6.5 |
| L5 | Resubmissions: keep the max submission_seq per (loan_id, period). | 6.2 |
| L6 | Call detection applies to both formats, with share `call_detect_share` of loans active at the end of t − 1. | 6.2 |
| L7 | ltv buckets `<=60, 60-70, 70-80, 80-90, >90` on edges (0, 0.6], (0.6, 0.7], (0.7, 0.8], (0.8, 0.9], (0.9, ∞); seasoning buckets `0-12, 13-24, 25-36, 37-60, >60`, inclusive integer ranges. | 6.2 |
| L8 | The current rate_type and io_flag on `fact_loan_month` are the status that month. Which one the query dimensions read is open (O-18). | 6.1 |

## Aggregation

| # | Convention | Source |
|---|---|---|
| A1 | Ratios across groups or deals are always ratio of sums, never average of ratios. | 5.6 |
| A2 | Monthly smm and mdr for a group come from summed numerators and denominators, then compound. | 6.4 |
| A3 | Default weighting is balance. "Arrears" with no day threshold must clarify; a threshold without count vs balance uses balance and says so. | 3.8 |
| A4 | Route `agg` only when every group_by and filter dimension is deal level (deal_id, deal_name, originator, trustee_format, issue_year). | 3.4, 6.5 |

## Files and repo mechanics (resolved in session 0)

| # | Convention | Source |
|---|---|---|
| F1 | Line endings LF everywhere via `.gitattributes` (`* text=auto eol=lf`); parquet, png, pdf and xlsx binary; `data/raw/**` and `tests/fixtures/**` stored as-is. | 10.5, committed `.gitattributes` |
| F2 | `config/cash_rate.csv` stores `period` as YYYY-MM (the month each step starts) and `rate` as a decimal (0.0035), following U2, so the 1.2 test values (0.0035, 0.036) read directly. Session 0 choice, flagged for confirmation. | 4.4, 5.2 |
| F3 | `config/hpi_drift.csv` stores regimes wide (`from, to, Sydney, Melbourne, Brisbane, Perth, Adelaide`) with drift in percent as printed in 4.5, because the 4.5 formula divides by 100. Session 0 choice, flagged for confirmation. | 4.5 |
| F4 | `config/geography.csv` holds 1 row per area (`city, state, weight, area, beta`), 20 rows; suburbs are derived, not stored. Session 0 choice, flagged for confirmation. | 4.3 |
| F5 | `config/originators.csv` holds `code, name, trustee_format`, 5 rows. | 4.2 |
| F6 | Dependencies are pinned in `requirements-lock.txt` by `uv pip compile pyproject.toml --extra test --universal --python-version 3.12 --no-header`, so the same lock installs on Windows and Linux. | 10.5, WORKFLOW Part 6 |
| F7 | pytest runs with `--disable-socket` and `pythonpath = ["."]`; the `calibration` marker is registered. Whether default runs exclude it is open (O-5). | 1.3, 9 step 1.6 |
| F8 | `data/canonical/` is git-ignored and rebuilt; `data/llm_cache/` is committed and must never be ignored. | 6.1, 1.3 |

## Open conventions

O-6 (static draw order), O-7 (HPI 2016-01 draw), O-9 (within-month order), O-12
(trustee field formats), O-16, O-17, O-18, O-19 (guard and hyphenated labels), O-20
(resolution case and scope), O-27. The full list is in the status file.
