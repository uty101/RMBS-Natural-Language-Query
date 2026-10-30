# Review: Section 2, canonical layer

Follow this template exactly. Every number below must be backed by raw rows or raw
output printed in full in this file (CLAUDE.md rule 10). No paraphrased results.

## 1. Outcome

- Instruction file: `instructions/02_section_2.md`
- Outcome: complete
- Last step reached: 2.6
- Stop reason (if stopped): none. Every expected value in instruction 02 matched exactly:
  - fact_loan_month 773,336 rows (774,057 raw rows, 721 resubmission duplicates removed);
  - dim_loan 21,945 loans; dim_deal 50 deals;
  - exits: called 2,542, prepaid 11,566, repurchased 376, defaulted 346;
  - the 7 format B called deals, with every call month and loan count as listed.

  `fact_loan_month` equals the true panel row for row on the small profile and on the full
  profile (step 2.6). 1 reading of O-29 had to be made for step 2.4. It is the only
  reading that gives 5 rows, and it is raised as O-36 (section 7).

## 2. Commits

Output of `git log --oneline` for this section's commits, oldest last, pasted verbatim.

```
ab84488 step 2.6: fact_loan_month equals the true panel row for row
fd55a18 step 2.5: build_canonical writes the DuckDB tables, pool_monthly.csv and row counts
d2ee8ee step 2.4: enrich adds indexed value and LTV, buckets, seasoning and current status
f23a7d6 step 2.3: detect_calls turns deal-wide prepaid exits into calls in both formats
b50d529 step 2.2: dedupe_resubmissions keeps the max submission_seq per loan-month
86e6971 step 2.1: format A and B ingestion to the canonical row frame
```

The review file, `decisions/OPEN.md` and the status file are committed after these.

## 3. Steps

### Step 2.1: ingestion

- Files: `rmbsq/canonical/ingest.py`, `tests/test_canonical_ingest.py`
- Signatures implemented: `ingest_format_a(path: Path) -> DataFrame`,
  `ingest_format_b(path: Path) -> DataFrame`. Helper `arrears_days_to_bucket(days)` (C.2).
- Tests: `test_formats_same_columns_and_dtypes`, `test_arrears_days_map`,
  `test_hardship_rows_bucket_zero`, `test_cents_exact`, result passed
- Outputs: none
- Evidence (E1). Column and dtype table after ingest, from the full profile files
  `trustee_a/D001.parquet` and `trustee_b/D004.parquet`:

```
               column format A dtype format B dtype
              loan_id         string         string
              deal_id         string         string
               period datetime64[ns] datetime64[ns]
       submission_seq          int64          int64
    opening_balance_c          Int64          Int64
scheduled_principal_c          Int64          Int64
        curtailment_c          Int64          Int64
    closing_balance_c          Int64          Int64
       exit_balance_c          Int64          Int64
               loss_c          Int64          Int64
        interest_rate        float64        float64
           dpd_bucket           int8           int8
        hardship_flag           bool           bool
          exit_reason         string         string
           orig_month datetime64[ns] datetime64[ns]
      fixed_end_month datetime64[ns] datetime64[ns]
         io_end_month datetime64[ns] datetime64[ns]
       orig_balance_c          Int64          Int64
     orig_valuation_c          Int64          Int64
             orig_ltv        float64        float64
       rate_type_orig         string         string
         io_flag_orig           bool           bool
             lmi_flag           bool           bool
            occupancy         string         string
                 city         string         string
                state         string         string
                 area         string         string
               suburb         string         string
       trustee_format         string         string
```

3 ingested rows, format A (D001):

```
                                           0                    1                    2
loan_id                            D001-0002            D001-0004            D001-0005
deal_id                                 D001                 D001                 D001
period                   2021-10-01 00:00:00  2021-10-01 00:00:00  2021-10-01 00:00:00
submission_seq                             1                    1                    1
opening_balance_c                   72498753             28843531             71352404
scheduled_principal_c                 159517                69122               167534
curtailment_c                          72339                28774                71185
closing_balance_c                   72266897             28745635             71113685
exit_balance_c                             0                    0                    0
loss_c                                     0                    0                    0
interest_rate                       0.026516             0.021758             0.022604
dpd_bucket                                 0                    0                    0
hardship_flag                          False                False                False
exit_reason                             <NA>                 <NA>                 <NA>
orig_month               2017-12-01 00:00:00  2017-08-01 00:00:00  2017-10-01 00:00:00
fixed_end_month                          NaT  2020-08-01 00:00:00  2019-10-01 00:00:00
io_end_month                             NaT                  NaT                  NaT
orig_balance_c                      82212700             33261300             81627200
orig_valuation_c                   124344800             41635600            117308700
orig_ltv                            0.661167             0.798867             0.695832
rate_type_orig                      variable                fixed                fixed
io_flag_orig                           False                False                False
lmi_flag                               False                False                False
occupancy                              owner                owner                owner
city                                Adelaide             Adelaide               Sydney
state                                     SA                   SA                  NSW
area                           Charles Sturt          Onkaparinga           Sutherland
suburb                 Charles Sturt Central    Onkaparinga North     Sutherland South
trustee_format                             A                    A                    A
```

3 ingested rows, format B (D004):

```
                                         0                    1                    2
loan_id                          D004-0001            D004-0002            D004-0004
deal_id                               D004                 D004                 D004
period                 2021-10-01 00:00:00  2021-10-01 00:00:00  2021-10-01 00:00:00
submission_seq                           1                    1                    1
opening_balance_c                 47947630             13808463             60276093
scheduled_principal_c               114136                    0                    0
curtailment_c                        47833                    0                60276
closing_balance_c                 47785661                    0             60215817
exit_balance_c                           0             13808463                    0
loss_c                                   0                    0                    0
interest_rate                     0.023451             0.023976             0.034425
dpd_bucket                               0                    0                    0
hardship_flag                        False                False                False
exit_reason                           <NA>              prepaid                 <NA>
orig_month             2017-04-01 00:00:00  2018-09-01 00:00:00  2017-07-01 00:00:00
fixed_end_month                        NaT                  NaT                  NaT
io_end_month                           NaT                  NaT  2022-07-01 00:00:00
orig_balance_c                    55586400             15317000             63368100
orig_valuation_c                  75180200             24717600             71762700
orig_ltv                          0.739375             0.619679             0.883023
rate_type_orig                    variable             variable             variable
io_flag_orig                         False                False                 True
lmi_flag                             False                False                 True
occupancy                            owner                owner             investor
city                                 Perth             Brisbane                Perth
state                                   WA                  QLD                   WA
area                              Stirling                Logan           Rockingham
suburb                    Stirling Central          Logan South     Rockingham South
trustee_format                           B                    B                    B
```

- Deviations from PLAN.md or the instruction file: none. The C.2 day edges and the
  MissedPayments cap of 4 are literals in `ingest.py`, with comments citing instruction
  02 C.2 and kickoff 6.2 (rule 6 exception).

### Step 2.2: resubmissions

- Files: `rmbsq/canonical/build.py` (new), `tests/test_canonical_dedupe.py`
- Signatures implemented: `dedupe_resubmissions(df) -> DataFrame`. Helper
  `ingest_raw(raw_dir)`: every format A file, then every format B file, ingested and
  concatenated.
- Tests: `test_resubmission_months_one_row_true_values`, `test_no_duplicates_after_dedupe`,
  result passed
- Outputs: none
- Evidence (E2), full profile. `ingest_raw(data/raw)` returns 774,057 rows. The first 2
  loans of D004 2023-06 before dedupe:

```
  loan_id deal_id     period  submission_seq  opening_balance_c  curtailment_c  closing_balance_c
D004-0001    D004 2023-06-01               1           45131487          45515           45469255
D004-0001    D004 2023-06-01               2           45131487          45064           45019064
D004-0004    D004 2023-06-01               1           58152989          58662           58603115
D004-0004    D004 2023-06-01               2           58152989          58081           58022886
rows after dedupe: 773336 removed: 721
```

After dedupe:

```
  loan_id deal_id     period  submission_seq  opening_balance_c  curtailment_c  closing_balance_c
D004-0001    D004 2023-06-01               2           45131487          45064           45019064
D004-0004    D004 2023-06-01               2           58152989          58081           58022886
```

(D004-0003 has no row in 2023-06, so the first 2 loans are 0001 and 0004. The seq 1
values are the seq 2 values × 1.01, rounded to the cent: 45019064 × 1.01 = 45469254.64 →
45469255.)

- Deviations from PLAN.md or the instruction file: none

### Step 2.3: call detection

- Files: `rmbsq/canonical/build.py`, `tests/test_canonical_calls.py`
- Signatures implemented: `detect_calls(df) -> DataFrame`
- Tests: `test_detect_calls_constructed`, `test_format_b_calls_recovered`,
  `test_format_a_calls_unchanged`, `test_full_format_b_calls_recovered` (marked `full`),
  result passed
- Outputs: none
- Evidence (E3). Every called deal of the full profile, truth (`simulate`, regenerated in
  memory) beside canonical (`fact_loan_month` in the full database):

```
deal_id trustee_format call_month  truth_called  canonical_called
   D001              A    2025-11           142               142
   D002              A    2025-03           148               148
   D003              A    2025-07           150               150
   D004              B    2025-11           146               146
   D005              B    2025-04           150               150
   D006              A    2025-04           163               163
   D007              A    2025-11           144               144
   D008              A    2026-02           142               142
   D009              B    2026-03           154               154
   D010              B    2025-12           151               151
   D011              A    2026-09           142               142
   D012              A    2026-06           147               147
   D013              A    2025-12           154               154
   D014              B    2026-02           147               147
   D015              B    2026-06           148               148
   D017              A    2026-02           156               156
   D020              B    2026-04           158               158
format A CALL rows before detection: 1488  after: 1488  identical frames: True
format B rows read as prepaid before detection: 5685  after: 4631
```

The format B drop, 5,685 − 4,631 = 1,054, equals the 7 format B call counts summed
(146 + 150 + 154 + 151 + 147 + 148 + 158 = 1,054). The small profile has no called format B
deal; `test_format_b_calls_recovered` asserts the empty set on both sides, as 01b B.3
allows.

- Deviations from PLAN.md or the instruction file: the kickoff 7 signature is
  `detect_calls(df)` with no config argument, so the function reads `call_detect_share`
  from the repo's `config.toml` itself.

### Step 2.4: enrichment

- Files: `rmbsq/canonical/build.py`, `tests/conftest.py` (fixture `small_rows`),
  `tests/test_canonical_enrich.py`
- Signatures implemented: `enrich(df, hpi, cfg) -> DataFrame`. Helpers `ltv_bucket`,
  `seasoning_bucket`, and `canonical_rows(raw_dir, cfg)` (ingest, dedupe, detect calls,
  enrich). `cfg` is accepted and not used, because C.4 needs no config value.
- Tests: `test_indexed_ltv_by_hand_five_rows`, `test_buckets_edges`,
  `test_current_rate_type_and_io`, result passed
- Outputs: none
- Evidence (E4). The 5 O-29 rows (small profile). The hand value is
  orig_valuation × hpi_period / hpi_orig, read from the raw `hpi.parquet`, and the hand
  LTV is closing_balance / hand value:

```
                                               0                               1                               2                                3                               4
originator                                   CST                            HARB                             KOO                              RED                             WAT
loan_id                                D004-0001                       D001-0001                       D002-0001                        D005-0002                       D003-0001
period                                   2026-09                         2024-09                         2025-05                          2026-09                         2023-07
orig_month                               2018-07                         2017-11                         2017-10                          2018-01                         2017-09
suburb                       Charles Sturt South                     Logan North              Sutherland Central                 Sutherland North                Whittlesea North
hpi_orig                              105.886133                      105.959956                      111.600915                        111.69843                      117.209558
hpi_period                            194.792696                      191.149489                      135.788648                       141.980878                      119.166304
orig_valuation                         728643.00                       324208.00                       934038.00                        796428.00                       992831.00
closing_balance                        543946.43                       175884.96                       635599.48                        385901.84                       541405.55
hand_value                    1340443.0813572917               584864.2814622535               1136475.961694615               1012346.7868239866              1009405.7411821653
computed_value    np.float64(1340443.0813572917)   np.float64(584864.2814622535)   np.float64(1136475.961694615)   np.float64(1012346.7868239866)  np.float64(1009405.7411821653)
hand_ltv                     0.40579599206048833              0.3007278193844556              0.5592722604112531              0.38119530285731573              0.5363606802611733
computed_ltv     np.float64(0.40579599206048833)  np.float64(0.3007278193844556)  np.float64(0.5592722604112531)  np.float64(0.38119530285731573)  np.float64(0.5363606802611733)
first loan of each originator in loan_id order: {'CST': 'D004-0001', 'HARB': 'D001-0001', 'KOO': 'D002-0001', 'RED': 'D005-0001', 'WAT': 'D003-0001'}
rows of D005-0001 in the small panel: 0
```

Every hand value equals the computed value exactly (difference 0, under the 1e-12
tolerance).

- Deviations from PLAN.md or the instruction file: **O-29 reading (O-36).** RED's first
  loan, D005-0001, has 0 rows in the small panel (it exits before 2021-10), so read
  literally the rule gives 4 rows. The test takes the first loan_id of each originator
  among loans that have a row with closing_balance > 0, so RED's row is D005-0002. The
  other 4 rows are the ones the literal rule gives. This is raised in section 7. The
  bucket edges are literals with a comment citing kickoff 6.2 and instruction 02 C.4.

### Step 2.5: canonical database

- Files: `rmbsq/canonical/build.py`, `scripts/build_canonical.py`, `tests/conftest.py`
  (fixtures `small_db`, `full_db`), `tests/test_canonical_build.py`,
  `outputs/pool_monthly.csv`, `outputs/canonical_row_counts.csv`
- Signatures implemented: `build_canonical(raw_dir: Path, db_path: Path, cfg) -> None`;
  script `scripts/build_canonical.py --raw DIR --db PATH`. Helpers `build_dim_loan(rows)`
  (raises `ValueError` if a static field differs between a loan's rows),
  `pool_monthly(con)`, `write_pool_monthly(df, path)` and `row_counts(con)`.
- Tests: `test_tables_and_types`, `test_agg_sums_equal_fact_sums`,
  `test_dim_loan_static_check`, `test_pool_monthly_matches_truth`,
  `test_full_pool_monthly_matches_truth` (marked `full`), result passed
- Outputs: `outputs/pool_monthly.csv` (60 rows), `outputs/canonical_row_counts.csv`
  (10 rows)
- Evidence (E5). `DESCRIBE` of every table, full database:

```
-- dim_deal
    column_name   column_type null
        deal_id       VARCHAR  YES
      deal_name       VARCHAR  YES
     originator       VARCHAR  YES
originator_name       VARCHAR  YES
 trustee_format       VARCHAR  YES
    issue_month          DATE  YES
     issue_year       INTEGER  YES
  issue_balance DECIMAL(18,2)  YES
-- dim_loan
    column_name   column_type null
        loan_id       VARCHAR  YES
        deal_id       VARCHAR  YES
     orig_month          DATE  YES
   vintage_year       INTEGER  YES
   orig_balance DECIMAL(18,2)  YES
 orig_valuation DECIMAL(18,2)  YES
       orig_ltv        DOUBLE  YES
ltv_bucket_orig       VARCHAR  YES
 rate_type_orig       VARCHAR  YES
fixed_end_month          DATE  YES
   io_flag_orig       BOOLEAN  YES
   io_end_month          DATE  YES
      occupancy       VARCHAR  YES
       lmi_flag       BOOLEAN  YES
           city       VARCHAR  YES
          state       VARCHAR  YES
           area       VARCHAR  YES
         suburb       VARCHAR  YES
-- fact_loan_month
        column_name   column_type null
            loan_id       VARCHAR  YES
            deal_id       VARCHAR  YES
             period          DATE  YES
    opening_balance DECIMAL(18,2)  YES
scheduled_principal DECIMAL(18,2)  YES
        curtailment DECIMAL(18,2)  YES
    closing_balance DECIMAL(18,2)  YES
      interest_rate        DOUBLE  YES
         dpd_bucket       TINYINT  YES
      hardship_flag       BOOLEAN  YES
        exit_reason       VARCHAR  YES
       exit_balance DECIMAL(18,2)  YES
               loss DECIMAL(18,2)  YES
      indexed_value        DOUBLE  YES
        indexed_ltv        DOUBLE  YES
 ltv_bucket_indexed       VARCHAR  YES
   seasoning_months       INTEGER  YES
   seasoning_bucket       VARCHAR  YES
          rate_type       VARCHAR  YES
            io_flag       BOOLEAN  YES
-- hpi
column_name column_type null
     suburb     VARCHAR  YES
     period        DATE  YES
        hpi      DOUBLE  YES
-- cash_rate
column_name column_type null
     period        DATE  YES
       rate      DOUBLE  YES
-- agg_deal_month
   column_name   column_type null
       deal_id       VARCHAR  YES
        period          DATE  YES
    loan_count        BIGINT  YES
           bal DECIMAL(38,2)  YES
       a30_bal DECIMAL(38,2)  YES
       a90_bal DECIMAL(38,2)  YES
       a90_cnt        BIGINT  YES
      hard_bal DECIMAL(38,2)  YES
orig_ltv_x_bal        DOUBLE  YES
 idx_ltv_x_bal        DOUBLE  YES
    rate_x_bal        DOUBLE  YES
       smm_num DECIMAL(38,2)  YES
       smm_den DECIMAL(38,2)  YES
       mdr_num DECIMAL(38,2)  YES
       mdr_den DECIMAL(38,2)  YES
```

`outputs/canonical_row_counts.csv` in full:

```
table,trustee_format,rows
dim_deal,all,50
dim_loan,all,21945
dim_loan,A,13076
dim_loan,B,8869
fact_loan_month,all,773336
fact_loan_month,A,464452
fact_loan_month,B,308884
hpi,all,7740
cash_rate,all,129
agg_deal_month,all,2567
```

Evidence (E6). `outputs/pool_monthly.csv`, first 3 and last 3 rows:

```
period,arrears_30p_bal,arrears_90p_bal,hardship_share_bal,cpr,cdr,wa_indexed_ltv,balance_total
2021-10,0.0036242084,0.0018019773,0.0087918290,0.1881004253,0.0000000000,0.5592228180,6239242545.92
2021-11,0.0029533948,0.0016137690,0.0082821421,0.1731157987,0.0006635597,0.5499630500,6416115254.83
2021-12,0.0029447042,0.0016841426,0.0090595164,0.1703665567,0.0000000000,0.5402992200,6301936887.75
2026-07,0.0080536365,0.0056145266,0.0072783020,0.1519943686,0.0021937132,0.4696790014,3893422726.92
2026-08,0.0073318387,0.0047945144,0.0079443610,0.1728171535,0.0040476044,0.4666260437,3825122676.49
2026-09,0.0066313916,0.0047055595,0.0088981668,0.1900242660,0.0003573804,0.4647222207,3683023457.00
```

The same rows of `outputs/pool_monthly_truth.csv`, for comparison:

```
period,arrears_30p_bal,arrears_90p_bal,hardship_share_bal,cpr,cdr,wa_indexed_ltv,balance_total
2021-10,0.0036242084,0.0018019773,0.0087918290,0.1881004253,0.0000000000,0.5592228180,6239242545.9200010300
2021-11,0.0029533948,0.0016137690,0.0082821421,0.1731157987,0.0006635597,0.5499630500,6416115254.8299999237
2021-12,0.0029447042,0.0016841426,0.0090595164,0.1703665567,0.0000000000,0.5402992200,6301936887.7500000000
2026-07,0.0080536365,0.0056145266,0.0072783020,0.1519943686,0.0021937132,0.4696790014,3893422726.9200000763
2026-08,0.0073318387,0.0047945144,0.0079443610,0.1728171535,0.0040476044,0.4666260437,3825122676.4899992943
2026-09,0.0066313916,0.0047055595,0.0088981668,0.1900242660,0.0003573804,0.4647222207,3683023457.0000000000
```

Max absolute difference per column, `pool_monthly.csv` against `pool_monthly_truth.csv`,
over all 60 periods (2021-10 to 2026-09):

```
arrears_30p_bal      0.000e+00
arrears_90p_bal      0.000e+00
hardship_share_bal   0.000e+00
cpr                  0.000e+00
cdr                  0.000e+00
wa_indexed_ltv       0.000e+00
balance_total        1.907e-06
```

The balance_total difference is float noise in the truth file, which sums floats
(`6239242545.9200010300`). The canonical value is an exact DECIMAL sum.

Evidence (E7). Exit counts by reason from `fact_loan_month`, beside the step 2.5
expected values:

```
exit_reason     n
     called  2542
  defaulted   346
    prepaid 11566
repurchased   376
```

Expected (instruction 02, step 2.5): called 2,542, prepaid 11,566, repurchased 376,
defaulted 346. All 4 match.

Evidence (E8). The full build (`scripts/build_canonical.py --raw data/raw --db
data/canonical/rmbs.duckdb`, which ingests, dedupes, detects calls, enriches and writes
every table) on Windows, Python 3.12.13:

```
built data\canonical\rmbs.duckdb in 14.2 s, 33566720 bytes     (first run, step 2.5)
built data\canonical\rmbs.duckdb in 10.8 s, 33566720 bytes     (determinism run 1)
built data\canonical\rmbs.duckdb in 11.0 s, 33566720 bytes     (determinism run 2)
```

The DuckDB file is 33,566,720 bytes (32.0 MiB), and it is not committed (`.gitignore`).

- Deviations from PLAN.md or the instruction file:
  - `agg_deal_month` sums are `DECIMAL(38,2)`, the type DuckDB gives a sum of
    DECIMAL(18,2), and counts are `BIGINT`. C.5 says "DECIMAL" and "count" without a
    width. `test_tables_and_types` checks exact types for the 5 tables C.5 types in full,
    and checks the column kind (count, DECIMAL, DOUBLE) for `agg_deal_month`.
  - `build_canonical` sets DuckDB to 1 thread, so DOUBLE sums add in the same order on
    every run (rule 9). The build takes about 11 s on the full profile anyway.
  - `test_dim_loan_static_check` calls `build_dim_loan`, the function `build_canonical`
    uses for `dim_loan`, on a constructed pair of rows of 1 loan with the second row's
    suburb changed. It asserts a `ValueError` naming `suburb`.
  - `build_canonical` also raises if `fact_loan_month` has a duplicate (loan_id, period),
    and `test_tables_and_types` asserts both keys are unique.

### Step 2.6: canonical equals truth

- Files: `tests/test_canonical_truth.py`, `PLAN.md` (1 paragraph for step 2.6)
- Signatures implemented: none
- Tests: `test_canonical_equals_truth_panel`, `test_full_canonical_equals_truth_panel`
  (marked `full`), result passed
- Outputs: none
- Evidence: the test outputs, from the run in section 4:

```
tests/test_canonical_truth.py::test_canonical_equals_truth_panel PASSED
tests/test_canonical_truth.py::test_full_canonical_equals_truth_panel PASSED
```

  The full test joins 773,336 canonical rows to the 773,336 rows of the full panel
  regenerated in memory with an outer join, and asserts that every row matched, that the 6
  money columns are equal to the cent, that interest_rate, indexed_value and indexed_ltv
  are within 1e-9, and that dpd_bucket, hardship_flag and exit_reason are identical.
- Deviations from PLAN.md or the instruction file: none

## 4. Full test suite

Command and its complete output (offline, `--disable-socket`). Working repo, Windows,
Python 3.12.13. Section 2 tests by id, then both suites:

```
$ .venv/Scripts/python -m pytest -v tests/test_canonical_*.py
tests/test_canonical_ingest.py::test_formats_same_columns_and_dtypes PASSED
tests/test_canonical_ingest.py::test_arrears_days_map PASSED
tests/test_canonical_ingest.py::test_hardship_rows_bucket_zero PASSED
tests/test_canonical_ingest.py::test_cents_exact PASSED
tests/test_canonical_dedupe.py::test_resubmission_months_one_row_true_values PASSED
tests/test_canonical_dedupe.py::test_no_duplicates_after_dedupe PASSED
tests/test_canonical_calls.py::test_detect_calls_constructed PASSED
tests/test_canonical_calls.py::test_format_b_calls_recovered PASSED
tests/test_canonical_calls.py::test_format_a_calls_unchanged PASSED
tests/test_canonical_enrich.py::test_indexed_ltv_by_hand_five_rows PASSED
tests/test_canonical_enrich.py::test_buckets_edges PASSED
tests/test_canonical_enrich.py::test_current_rate_type_and_io PASSED
tests/test_canonical_build.py::test_tables_and_types PASSED
tests/test_canonical_build.py::test_agg_sums_equal_fact_sums PASSED
tests/test_canonical_build.py::test_dim_loan_static_check PASSED
tests/test_canonical_build.py::test_pool_monthly_matches_truth PASSED
tests/test_canonical_truth.py::test_canonical_equals_truth_panel PASSED
====================== 17 passed, 3 deselected in 6.70s =======================
$ .venv/Scripts/python -m pytest -v -m full
tests/test_canonical_build.py::test_full_pool_monthly_matches_truth PASSED
tests/test_canonical_calls.py::test_full_format_b_calls_recovered PASSED
tests/test_canonical_truth.py::test_full_canonical_equals_truth_panel PASSED
tests/test_full_profile.py::test_calibration_bands PASSED
tests/test_full_profile.py::test_full_regenerates_identically PASSED
====================== 5 passed, 56 deselected in 34.79s ======================
$ .venv/Scripts/python -m pytest -q
........................................................
56 passed, 5 deselected in 13.45s
```

## 5. Determinism

The outputs regenerated twice and compared byte for byte (SHA-256 of each file, both runs).

```
$ python scripts/build_canonical.py --raw data/raw --db data/canonical/rmbs.duckdb   (run 1)
built data\canonical\rmbs.duckdb in 10.8 s, 33566720 bytes
$ sha256sum outputs/pool_monthly.csv outputs/canonical_row_counts.csv
dde99809930d19d094a65f245d19f9052bfc597b4a1d21c0406897dfa814ac63 *outputs/pool_monthly.csv
7347407f38c74305a29516fbee3a549d69760e246cfb8b01b1792693727b4065 *outputs/canonical_row_counts.csv
$ python scripts/build_canonical.py --raw data/raw --db data/canonical/rmbs.duckdb   (run 2)
built data\canonical\rmbs.duckdb in 11.0 s, 33566720 bytes
$ sha256sum outputs/pool_monthly.csv outputs/canonical_row_counts.csv
dde99809930d19d094a65f245d19f9052bfc597b4a1d21c0406897dfa814ac63 *outputs/pool_monthly.csv
7347407f38c74305a29516fbee3a549d69760e246cfb8b01b1792693727b4065 *outputs/canonical_row_counts.csv
$ git status --short outputs/
(empty: both runs equal the committed files)
```

## 6. Fresh-clone check

Clone into a short temp path, `uv venv --python 3.12`, `uv pip sync requirements-lock.txt`,
run the suite. Paste the commands and the complete output. (The `+ <package>` install lines
of `uv pip sync` are left out; the lock installs 44 packages. `UV_LINK_MODE=copy` was set
to avoid the hardlink warning.)

```
$ git clone "<repo>" %LOCALAPPDATA%\Temp\rq2 && cd rq2
$ git log --oneline -1
ab84488 step 2.6: fact_loan_month equals the true panel row for row
$ uv venv --python 3.12 .venv
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
$ uv pip sync --python .venv requirements-lock.txt
Resolved 44 packages in 924ms
Installed 44 packages in 30.06s
$ .venv/Scripts/python -m pytest -q
........................................................                 [100%]
56 passed, 5 deselected in 8.55s
$ .venv/Scripts/python -m pytest -q -m full
.....                                                                    [100%]
5 passed, 56 deselected in 34.47s
```

## 7. Open questions for the reviewer

1. **O-36, step 2.4: O-29's first RED loan has no row in the window.** O-29 picks the
   first loan_id of each originator. RED's first loan, D005-0001, exits before 2021-10 and
   has 0 rows in the small panel, so read literally the rule gives 4 rows.
   - (a) Take the first loan_id of each originator among loans that have a row with
     closing_balance > 0, which makes RED's row D005-0002 at 2026-09. **This is what is
     built**, because it is the only reading that gives 5 rows.
   - (b) A later instruction names the 5 (loan_id, period) pairs, and the test uses them
     as given.
