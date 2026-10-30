# Review: Section 3, semantic layer and compiler

Follows `review/TEMPLATE.md`. Every number below is backed by raw output printed in full.

## 1. Outcome

- Instruction file: `instructions/03_section_3.md`
- Outcome: complete
- Last step reached: 3.6
- Stop reason (if stopped): none. All 15 gold specs equal their hand SQL on both
  profiles (max scaled difference 3.331e-16), with the gold row counts and routes. All 15
  render to Oracle with an empty warning list. 1 point is raised for the reviewer: the
  metric column order of S11 (O-37, step 3.3). The built reading matches the gold file,
  so every test passes.

## 2. Commits

Output of `git log --oneline af1c0b7..HEAD` before the review commit:

```
372082e step 3.6: format_table display strings for pct, AUD millions, counts, years and NULL
ca801b5 step 3.5: all 15 specs render to Oracle with no warning and no DuckDB-only construct
71330e3 step 3.4: auto route matches the gold route for 15 specs, fact and agg routes agree
38397a1 step 3.3: compiler and time aggregation, 15 gold specs equal the hand SQL
b639825 step 3.2: QuerySpec with the kickoff 6.6 rules and the default time
bf8f562 step 3.1: catalogue of 12 metrics and 18 dimensions, allowed values from the database
c4e32ad step 3.0: fixtures, dim_period and an --outputs flag on both data scripts
```

## 3. Steps

### Step 3.0: fixtures and `dim_period`

- Files: `tests/fixtures/compiler_gold.json`, `tests/fixtures/spec_examples.json` (byte
  for byte copies; `cmp` against `instructions/03_*.json` reports no difference),
  `rmbsq/canonical/build.py` (`build_dim_period`, `DIM_PERIOD_SQL`, `dim_period` added to
  `TABLES`), `scripts/generate_data.py` and `scripts/build_canonical.py` (`--outputs`),
  `tests/test_canonical_build.py::test_dim_period`, `tests/test_scripts.py`, `PLAN.md`,
  `outputs/canonical_row_counts.csv`, `docs/CONVENTIONS_RESOLVED.md` (S3 amended for
  O-36 (a)), `decisions/OPEN.md` (O-36 cleared).
- Signatures implemented: `build_dim_period(cfg) -> DataFrame`. Both scripts take
  `--outputs DIR`. It defaults to the repo's `outputs/` for `--profile full` or when
  `--raw` resolves to the repo's `data/raw/`, otherwise to `<--out or --raw>/../outputs`.
- Tests: result passed.

```
tests/test_canonical_build.py::test_dim_period PASSED
tests/test_scripts.py::test_small_run_leaves_repo_outputs_alone PASSED
```

- Outputs: `outputs/canonical_row_counts.csv` (11 rows; new row `dim_period,all,60`).
  `pool_monthly.csv` is unchanged by the rebuild (same SHA-256, section 5).
- Evidence. `outputs/canonical_row_counts.csv` after the full rebuild:

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
dim_period,all,60
```

`dim_period` on the full database, all 60 rows:

```
    period month_label quarter_label year_label
2021-10-01     2021-10       2021-Q4       2021
2021-11-01     2021-11       2021-Q4       2021
2021-12-01     2021-12       2021-Q4       2021
2022-01-01     2022-01       2022-Q1       2022
2022-02-01     2022-02       2022-Q1       2022
2022-03-01     2022-03       2022-Q1       2022
2022-04-01     2022-04       2022-Q2       2022
2022-05-01     2022-05       2022-Q2       2022
2022-06-01     2022-06       2022-Q2       2022
2022-07-01     2022-07       2022-Q3       2022
2022-08-01     2022-08       2022-Q3       2022
2022-09-01     2022-09       2022-Q3       2022
2022-10-01     2022-10       2022-Q4       2022
2022-11-01     2022-11       2022-Q4       2022
2022-12-01     2022-12       2022-Q4       2022
2023-01-01     2023-01       2023-Q1       2023
2023-02-01     2023-02       2023-Q1       2023
2023-03-01     2023-03       2023-Q1       2023
2023-04-01     2023-04       2023-Q2       2023
2023-05-01     2023-05       2023-Q2       2023
2023-06-01     2023-06       2023-Q2       2023
2023-07-01     2023-07       2023-Q3       2023
2023-08-01     2023-08       2023-Q3       2023
2023-09-01     2023-09       2023-Q3       2023
2023-10-01     2023-10       2023-Q4       2023
2023-11-01     2023-11       2023-Q4       2023
2023-12-01     2023-12       2023-Q4       2023
2024-01-01     2024-01       2024-Q1       2024
2024-02-01     2024-02       2024-Q1       2024
2024-03-01     2024-03       2024-Q1       2024
2024-04-01     2024-04       2024-Q2       2024
2024-05-01     2024-05       2024-Q2       2024
2024-06-01     2024-06       2024-Q2       2024
2024-07-01     2024-07       2024-Q3       2024
2024-08-01     2024-08       2024-Q3       2024
2024-09-01     2024-09       2024-Q3       2024
2024-10-01     2024-10       2024-Q4       2024
2024-11-01     2024-11       2024-Q4       2024
2024-12-01     2024-12       2024-Q4       2024
2025-01-01     2025-01       2025-Q1       2025
2025-02-01     2025-02       2025-Q1       2025
2025-03-01     2025-03       2025-Q1       2025
2025-04-01     2025-04       2025-Q2       2025
2025-05-01     2025-05       2025-Q2       2025
2025-06-01     2025-06       2025-Q2       2025
2025-07-01     2025-07       2025-Q3       2025
2025-08-01     2025-08       2025-Q3       2025
2025-09-01     2025-09       2025-Q3       2025
2025-10-01     2025-10       2025-Q4       2025
2025-11-01     2025-11       2025-Q4       2025
2025-12-01     2025-12       2025-Q4       2025
2026-01-01     2026-01       2026-Q1       2026
2026-02-01     2026-02       2026-Q1       2026
2026-03-01     2026-03       2026-Q1       2026
2026-04-01     2026-04       2026-Q2       2026
2026-05-01     2026-05       2026-Q2       2026
2026-06-01     2026-06       2026-Q2       2026
2026-07-01     2026-07       2026-Q3       2026
2026-08-01     2026-08       2026-Q3       2026
2026-09-01     2026-09       2026-Q3       2026
```

A small-profile run of both scripts into the scratch folder `.../scratchpad/small/raw`
wrote `calibration.csv, canonical_row_counts.csv, pool_monthly.csv,
pool_monthly_truth.csv` to `.../scratchpad/small/outputs`, and `git status --short` was
empty afterwards.

- Deviations from PLAN.md or the instruction file: none. O-36 (a), confirmed in
  instruction 03 A, is recorded in `docs/CONVENTIONS_RESOLVED.md` S3 in this commit.

### Step 3.1: catalogue

- Files: `semantic/metrics.yaml`, `semantic/dimensions.yaml`, `rmbsq/semantic/catalog.py`,
  `tests/test_catalog.py`
- Signatures implemented: `load_catalog(metrics_yaml: Path = semantic/metrics.yaml,
  dims_yaml: Path = semantic/dimensions.yaml, db: Path | None = None) -> Catalog`;
  `Catalog.metrics`, `Catalog.dimensions` (dicts in file order), `Catalog.deal_level`,
  `Catalog.allowed_values(name)`.
- Tests: result passed.

```
tests/test_catalog.py::test_twelve_metrics PASSED
tests/test_catalog.py::test_eighteen_dimensions PASSED
tests/test_catalog.py::test_allowed_values_from_db PASSED
```

- Outputs: none
- Evidence. `semantic/metrics.yaml` in full:

```
# The 12 metrics (kickoff 6.3; instruction 03 C.1). numerator and denominator name the
# monthly parts of instruction 03 B.2; they are empty for the flow metrics, which follow
# the compound rule of B.6.

- name: loan_count
  kind: stock
  numerator: "loan_count"
  denominator: ""
  display: count
  definition: "Number of loans with a positive balance at month end."

- name: balance_total
  kind: stock
  numerator: "bal"
  denominator: ""
  display: aud_m
  definition: "Total outstanding balance in AUD at month end."

- name: arrears_30p_bal
  kind: stock
  numerator: "a30_bal"
  denominator: "bal"
  display: pct
  definition: "Share of outstanding balance that is 30 or more days past due, excluding loans in hardship, weighted by balance."

- name: arrears_90p_bal
  kind: stock
  numerator: "a90_bal"
  denominator: "bal"
  display: pct
  definition: "Share of outstanding balance that is 90 or more days past due, excluding loans in hardship, weighted by balance."

- name: arrears_90p_cnt
  kind: stock
  numerator: "a90_cnt"
  denominator: "loan_count"
  display: pct
  definition: "Share of loans by count that are 90 or more days past due, excluding loans in hardship."

- name: hardship_share_bal
  kind: stock
  numerator: "hard_bal"
  denominator: "bal"
  display: pct
  definition: "Share of outstanding balance on a hardship arrangement."

- name: wa_orig_ltv
  kind: stock
  numerator: "orig_ltv_x_bal"
  denominator: "bal"
  display: pct
  definition: "Balance-weighted average loan-to-value ratio at origination."

- name: wa_indexed_ltv
  kind: stock
  numerator: "idx_ltv_x_bal"
  denominator: "bal"
  display: pct
  definition: "Balance-weighted average current loan-to-value ratio, with property values indexed to suburb house prices."

- name: wa_rate
  kind: stock
  numerator: "rate_x_bal"
  denominator: "bal"
  display: pct
  definition: "Balance-weighted average interest rate."

- name: smm_vol
  kind: flow
  numerator: ""
  denominator: ""
  display: pct
  definition: "Monthly voluntary prepayment rate: full prepayments plus partial curtailments over scheduled balance. Excludes repurchases, defaults and clean-up calls."

- name: cpr
  kind: flow
  numerator: ""
  denominator: ""
  display: pct
  definition: "Conditional prepayment rate: smm_vol annualised. Excludes repurchases, defaults and clean-up calls."

- name: cdr
  kind: flow
  numerator: ""
  denominator: ""
  display: pct
  definition: "Conditional default rate: defaulted balance over opening balance each month, annualised."
```

`semantic/dimensions.yaml` in full:

```
# The 18 dimensions (kickoff 6.5; instruction 03 C.2). labels lists the output values
# where they are fixed, and is empty where values come from the database.

- name: deal_id
  column: deal_id
  table: fact_loan_month
  level: deal
  labels: []
  definition: "Deal identifier, for example D004."

- name: deal_name
  column: deal_name
  table: dim_deal
  level: deal
  labels: []
  definition: "Deal name: originator code, issue year and series number, for example HARB 2019-1."

- name: originator
  column: originator
  table: dim_deal
  level: deal
  labels: []
  definition: "Originator code: HARB, KOO, WAT, CST or RED."

- name: trustee_format
  column: trustee_format
  table: dim_deal
  level: deal
  labels: ["A", "B"]
  definition: "Which trustee report format the deal is delivered in."

- name: issue_year
  column: issue_year
  table: dim_deal
  level: deal
  labels: []
  definition: "Year the deal was issued."

- name: vintage_year
  column: vintage_year
  table: dim_loan
  level: loan
  labels: []
  definition: "Year the loan was originated."

- name: city
  column: city
  table: dim_loan
  level: loan
  labels: []
  definition: "Capital city region of the property."

- name: state
  column: state
  table: dim_loan
  level: loan
  labels: ["NSW", "QLD", "SA", "VIC", "WA"]
  definition: "State of the property."

- name: area
  column: area
  table: dim_loan
  level: loan
  labels: []
  definition: "Local area of the property, for example Blacktown."

- name: suburb
  column: suburb
  table: dim_loan
  level: loan
  labels: []
  definition: "Suburb of the property, for example Blacktown North."

- name: rate_type
  column: rate_type
  table: fact_loan_month
  level: loan
  labels: ["fixed", "variable"]
  definition: "Current rate type that month; a fixed loan becomes variable at its fixed rate expiry."

- name: io_flag
  column: io_flag
  table: fact_loan_month
  level: loan
  labels: ["yes", "no"]
  definition: "Whether the loan is interest only that month."

- name: occupancy
  column: occupancy
  table: dim_loan
  level: loan
  labels: ["owner", "investor"]
  definition: "Owner occupied or investment property."

- name: lmi_flag
  column: lmi_flag
  table: dim_loan
  level: loan
  labels: ["yes", "no"]
  definition: "Whether the loan has lenders mortgage insurance (LTV above 80% at origination)."

- name: ltv_bucket_orig
  column: ltv_bucket_orig
  table: dim_loan
  level: loan
  labels: ["<=60", "60-70", "70-80", "80-90", ">90"]
  definition: "Origination LTV band, in percent."

- name: ltv_bucket_indexed
  column: ltv_bucket_indexed
  table: fact_loan_month
  level: loan
  labels: ["<=60", "60-70", "70-80", "80-90", ">90"]
  definition: "Current indexed LTV band, in percent."

- name: seasoning_bucket
  column: seasoning_bucket
  table: fact_loan_month
  level: loan
  labels: ["0-12", "13-24", "25-36", "37-60", ">60"]
  definition: "Months since origination."

- name: dpd_bucket
  column: dpd_bucket
  table: fact_loan_month
  level: loan
  labels: ["current", "1-29", "30-59", "60-89", "90+"]
  definition: "Days past due band. Loans in hardship are current."
```

`allowed_values` for every dimension, on the full database and on the small profile:

```
deal_id: full ['D001', 'D002', 'D003', 'D004', 'D005', 'D006', 'D007', 'D008', 'D009', 'D010', 'D011', 'D012', 'D013', 'D014', 'D015', 'D016', 'D017', 'D018', 'D019', 'D020', 'D021', 'D022', 'D023', 'D024', 'D025', 'D026', 'D027', 'D028', 'D029', 'D030', 'D031', 'D032', 'D033', 'D034', 'D035', 'D036', 'D037', 'D038', 'D039', 'D040', 'D041', 'D042', 'D043', 'D044', 'D045', 'D046', 'D047', 'D048', 'D049', 'D050']
deal_id: small ['D001', 'D002', 'D003', 'D004', 'D005', 'D006', 'D007', 'D008', 'D009', 'D010']
deal_name: full ['CST 2019-1', 'CST 2019-2', 'CST 2020-1', 'CST 2020-2', 'CST 2021-1', 'CST 2021-2', 'CST 2022-1', 'CST 2022-2', 'CST 2023-1', 'CST 2023-2', 'HARB 2019-1', 'HARB 2019-2', 'HARB 2020-1', 'HARB 2020-2', 'HARB 2021-1', 'HARB 2021-2', 'HARB 2022-1', 'HARB 2022-2', 'HARB 2023-1', 'HARB 2023-2', 'KOO 2019-1', 'KOO 2019-2', 'KOO 2020-1', 'KOO 2020-2', 'KOO 2021-1', 'KOO 2021-2', 'KOO 2022-1', 'KOO 2022-2', 'KOO 2023-1', 'KOO 2023-2', 'RED 2019-1', 'RED 2019-2', 'RED 2020-1', 'RED 2020-2', 'RED 2021-1', 'RED 2021-2', 'RED 2022-1', 'RED 2022-2', 'RED 2023-1', 'RED 2023-2', 'WAT 2019-1', 'WAT 2019-2', 'WAT 2020-1', 'WAT 2020-2', 'WAT 2021-1', 'WAT 2021-2', 'WAT 2022-1', 'WAT 2022-2', 'WAT 2023-1', 'WAT 2023-2']
deal_name: small ['CST 2020-1', 'CST 2023-1', 'HARB 2019-1', 'HARB 2021-1', 'KOO 2019-1', 'KOO 2022-1', 'RED 2021-1', 'RED 2023-1', 'WAT 2020-1', 'WAT 2022-1']
originator: full ['CST', 'HARB', 'KOO', 'RED', 'WAT']
originator: small ['CST', 'HARB', 'KOO', 'RED', 'WAT']
trustee_format: full ['A', 'B']
trustee_format: small ['A', 'B']
issue_year: full [2019, 2020, 2021, 2022, 2023]
issue_year: small [2019, 2020, 2021, 2022, 2023]
vintage_year: full [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
vintage_year: small [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
city: full ['Adelaide', 'Brisbane', 'Melbourne', 'Perth', 'Sydney']
city: small ['Adelaide', 'Brisbane', 'Melbourne', 'Perth', 'Sydney']
state: full ['NSW', 'QLD', 'SA', 'VIC', 'WA']
state: small ['NSW', 'QLD', 'SA', 'VIC', 'WA']
area: full ['Blacktown', 'Boroondara', 'Brisbane Inner', 'Casey', 'Charles Sturt', 'Ipswich', 'Joondalup', 'Logan', 'Moreton Bay', 'Onkaparinga', 'Parramatta', 'Penrith', 'Playford', 'Rockingham', 'Salisbury', 'Stirling', 'Sutherland', 'Wanneroo', 'Whittlesea', 'Wyndham']
area: small ['Blacktown', 'Boroondara', 'Brisbane Inner', 'Casey', 'Charles Sturt', 'Ipswich', 'Joondalup', 'Logan', 'Moreton Bay', 'Onkaparinga', 'Parramatta', 'Penrith', 'Playford', 'Rockingham', 'Salisbury', 'Stirling', 'Sutherland', 'Wanneroo', 'Whittlesea', 'Wyndham']
suburb: full ['Blacktown Central', 'Blacktown North', 'Blacktown South', 'Boroondara Central', 'Boroondara North', 'Boroondara South', 'Brisbane Inner Central', 'Brisbane Inner North', 'Brisbane Inner South', 'Casey Central', 'Casey North', 'Casey South', 'Charles Sturt Central', 'Charles Sturt North', 'Charles Sturt South', 'Ipswich Central', 'Ipswich North', 'Ipswich South', 'Joondalup Central', 'Joondalup North', 'Joondalup South', 'Logan Central', 'Logan North', 'Logan South', 'Moreton Bay Central', 'Moreton Bay North', 'Moreton Bay South', 'Onkaparinga Central', 'Onkaparinga North', 'Onkaparinga South', 'Parramatta Central', 'Parramatta North', 'Parramatta South', 'Penrith Central', 'Penrith North', 'Penrith South', 'Playford Central', 'Playford North', 'Playford South', 'Rockingham Central', 'Rockingham North', 'Rockingham South', 'Salisbury Central', 'Salisbury North', 'Salisbury South', 'Stirling Central', 'Stirling North', 'Stirling South', 'Sutherland Central', 'Sutherland North', 'Sutherland South', 'Wanneroo Central', 'Wanneroo North', 'Wanneroo South', 'Whittlesea Central', 'Whittlesea North', 'Whittlesea South', 'Wyndham Central', 'Wyndham North', 'Wyndham South']
suburb: small ['Blacktown Central', 'Blacktown North', 'Blacktown South', 'Boroondara Central', 'Boroondara North', 'Boroondara South', 'Brisbane Inner Central', 'Brisbane Inner North', 'Brisbane Inner South', 'Casey Central', 'Casey North', 'Casey South', 'Charles Sturt North', 'Charles Sturt South', 'Ipswich Central', 'Ipswich North', 'Ipswich South', 'Joondalup Central', 'Joondalup North', 'Joondalup South', 'Logan Central', 'Logan North', 'Logan South', 'Moreton Bay Central', 'Moreton Bay North', 'Moreton Bay South', 'Onkaparinga Central', 'Onkaparinga North', 'Parramatta Central', 'Parramatta North', 'Parramatta South', 'Penrith Central', 'Penrith North', 'Penrith South', 'Playford Central', 'Playford North', 'Playford South', 'Rockingham Central', 'Rockingham North', 'Rockingham South', 'Salisbury Central', 'Salisbury North', 'Salisbury South', 'Stirling Central', 'Stirling North', 'Stirling South', 'Sutherland Central', 'Sutherland North', 'Sutherland South', 'Wanneroo Central', 'Wanneroo North', 'Wanneroo South', 'Whittlesea Central', 'Whittlesea North', 'Whittlesea South', 'Wyndham Central', 'Wyndham North', 'Wyndham South']
rate_type: full ['fixed', 'variable']
rate_type: small ['fixed', 'variable']
io_flag: full ['yes', 'no']
io_flag: small ['yes', 'no']
occupancy: full ['owner', 'investor']
occupancy: small ['owner', 'investor']
lmi_flag: full ['yes', 'no']
lmi_flag: small ['yes', 'no']
ltv_bucket_orig: full ['<=60', '60-70', '70-80', '80-90', '>90']
ltv_bucket_orig: small ['<=60', '60-70', '70-80', '80-90', '>90']
ltv_bucket_indexed: full ['<=60', '60-70', '70-80', '80-90', '>90']
ltv_bucket_indexed: small ['<=60', '60-70', '70-80', '80-90', '>90']
seasoning_bucket: full ['0-12', '13-24', '25-36', '37-60', '>60']
seasoning_bucket: small ['0-12', '13-24', '25-36', '37-60', '>60']
dpd_bucket: full ['current', '1-29', '30-59', '60-89', '90+']
dpd_bucket: small ['current', '1-29', '30-59', '60-89', '90+']
```

- Deviations from PLAN.md or the instruction file:
  - `load_catalog` gains an optional third argument `db`. The kickoff 7 signature takes
    only the 2 YAML paths, but C.2 needs database values from `allowed_values(name)`;
    the 2-argument call still works and reads no database.
  - C.1 says numerator and denominator are "empty for the flow metrics' compound
    rule". Read as: all 3 flow metrics have both empty, and the compiler takes their
    parts from the B.6 rule (`smm_num/smm_den` for smm_vol and cpr, `mdr_num/mdr_den`
    for cdr, `rmbsq/semantic/timeagg.py::FLOW`). loan_count and balance_total have an
    empty denominator.
  - Every YAML string is double-quoted, so `yes`, `no` and `<=60` load as strings.

### Step 3.2: QuerySpec

- Files: `rmbsq/semantic/spec.py`, `tests/test_spec.py`
- Signatures implemented: `QuerySpec`, with `TimeSpec`, `OrderSpec`, `ClarifySpec`.
  `MetricName` and `DimensionName` are `Literal` types built from the catalogue YAML.
  Window bounds and the default month are `[calendar]` `window_start`, `window_end` and
  `latest` from `config.toml`.
- Tests: result passed.

```
tests/test_spec.py::test_valid_examples[V01] PASSED
tests/test_spec.py::test_valid_examples[V02] PASSED
tests/test_spec.py::test_valid_examples[V03] PASSED
tests/test_spec.py::test_valid_examples[V04] PASSED
tests/test_spec.py::test_valid_examples[V05] PASSED
tests/test_spec.py::test_valid_examples[V06] PASSED
tests/test_spec.py::test_valid_examples[V07] PASSED
tests/test_spec.py::test_valid_examples[V08] PASSED
tests/test_spec.py::test_invalid_examples[X01] PASSED
tests/test_spec.py::test_invalid_examples[X02] PASSED
tests/test_spec.py::test_invalid_examples[X03] PASSED
tests/test_spec.py::test_invalid_examples[X04] PASSED
tests/test_spec.py::test_invalid_examples[X05] PASSED
tests/test_spec.py::test_invalid_examples[X06] PASSED
tests/test_spec.py::test_invalid_examples[X07] PASSED
tests/test_spec.py::test_invalid_examples[X08] PASSED
tests/test_spec.py::test_invalid_examples[X09] PASSED
tests/test_spec.py::test_invalid_examples[X10] PASSED
tests/test_spec.py::test_invalid_examples[X11] PASSED
tests/test_spec.py::test_invalid_examples[X12] PASSED
```

- Outputs: none
- Evidence. Each example, with accepted or rejected and the validation message
  (location: message):

```
V01 accepted; time {'grain': 'month', 'start': '2026-09', 'end': '2026-09', 'shape': 'point'}
V02 accepted; time {'grain': 'quarter', 'start': '2024-01', 'end': '2025-12', 'shape': 'series'}
V03 accepted; time {'grain': 'month', 'start': '2026-09', 'end': '2026-09', 'shape': 'point'}
V04 accepted; time {'grain': 'month', 'start': '2021-10', 'end': '2026-09', 'shape': 'point'}
V05 accepted; time None
V06 accepted; time None
V07 accepted; time None
V08 accepted; time {'grain': 'year', 'start': '2022-01', 'end': '2025-12', 'shape': 'series'}
X01 rejected (answer needs at least 1 metric): (spec): Value error, answer needs 1 to 3 metrics
X02 rejected (at most 3 metrics): metrics: List should have at most 3 items after validation, not 4
X03 rejected (unknown metric): metrics.0: Input should be 'loan_count', 'balance_total', 'arrears_30p_bal', 'arrears_90p_bal', 'arrears_90p_cnt', 'hardship_share_bal', 'wa_orig_ltv', 'wa_indexed_ltv', 'wa_rate', 'smm_vol', 'cpr' or 'cdr'
X04 rejected (at most 2 group_by): group_by: List should have at most 2 items after validation, not 3
X05 rejected (unknown dimension in filters): filters.servicer.[key]: Input should be 'deal_id', 'deal_name', 'originator', 'trustee_format', 'issue_year', 'vintage_year', 'city', 'state', 'area', 'suburb', 'rate_type', 'io_flag', 'occupancy', 'lmi_flag', 'ltv_bucket_orig', 'ltv_bucket_indexed', 'seasoning_bucket' or 'dpd_bucket'
X06 rejected (start before window_start): time: Value error, time must satisfy 2021-10 <= start <= end <= 2026-09, got start 2021-09, end 2022-03
X07 rejected (end after window_end): time: Value error, time must satisfy 2021-10 <= start <= end <= 2026-09, got start 2026-01, end 2026-10
X08 rejected (start after end): time: Value error, time must satisfy 2021-10 <= start <= end <= 2026-09, got start 2025-06, end 2025-01
X09 rejected (order limit above 20): order.limit: Input should be less than or equal to 20
X10 rejected (order metric not among the spec's metrics): (spec): Value error, order metric cdr is not among the metrics ['cpr']
X11 rejected (clarify with 1 option): clarify.options: List should have at least 2 items after validation, not 1
X12 rejected (unsupported must not carry metrics): (spec): Value error, unsupported must not carry metrics
```

- Deviations from PLAN.md or the instruction file: none. Filter values are typed
  `list[str | int]`; the compiler turns issue_year and vintage_year values into integer
  literals and every other value into a string literal.

### Step 3.3: compiler and time aggregation

- Files: `rmbsq/semantic/compiler.py`, `rmbsq/semantic/timeagg.py`,
  `tests/test_compiler.py`, `decisions/OPEN.md` (O-37)
- Signatures implemented: `compile(spec, catalog, route="auto") ->
  CompiledQuery(sql_duckdb, sql_oracle, route)`, `execute(compiled, con) -> DataFrame`.
  In `timeagg.py`: `stock_cte`, `flow_cte`, `flow_value` (the B.5 and B.6 steps as sqlglot
  trees) and `aggregate(parts, group_by, metrics)` (the same arithmetic on a pandas frame
  of monthly parts, used by the B.8 test).
- Tests: result passed, default run and `-m full`.

```
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S01] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S02] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S03] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S04] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S05] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S06] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S07] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S08] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S09] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S10] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S11] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S12] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S13] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S14] PASSED
tests/test_compiler.py::test_fifteen_specs_match_hand_sql[S15] PASSED
tests/test_compiler.py::test_quarter_compounding_hand_example PASSED
```

```
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S01] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S02] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S03] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S04] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S05] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S06] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S07] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S08] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S09] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S10] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S11] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S12] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S13] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S14] PASSED
tests/test_compiler.py::test_full_fifteen_specs_match_hand_sql[S15] PASSED
===================== 15 passed, 16 deselected in 24.05s ======================
```

- Outputs: none
- Evidence. Per gold spec: the route chosen, the rows on both profiles beside the gold
  counts, the max scaled difference against the hand SQL (|a − b| / max(1, |b|)), and
  (step 3.4) the max scaled difference between the agg and fact routes for agg specs:

```
 id route_auto route  rows_small  gold_rows_small  diff_small  agg_vs_fact_small  rows_full  gold_rows_full  diff_full  agg_vs_fact_full
S01        agg   agg           1                1   0.000e+00          0.000e+00          1               1  0.000e+00         0.000e+00
S02        agg   agg           4                4   0.000e+00          0.000e+00          5               5  0.000e+00         0.000e+00
S03       fact  fact          30               30   0.000e+00                NaN         30              30  0.000e+00               NaN
S04       fact  fact          20               20   2.220e-16                NaN         20              20  3.331e-16               NaN
S05        agg   agg           4                4   0.000e+00          0.000e+00          4               4  0.000e+00         0.000e+00
S06       fact  fact           5                5   0.000e+00                NaN          7               7  0.000e+00               NaN
S07       fact  fact           4                4   0.000e+00                NaN          4               4  0.000e+00               NaN
S08       fact  fact          12               12   0.000e+00                NaN         12              12  0.000e+00               NaN
S09       fact  fact           2                2   0.000e+00                NaN          2               2  0.000e+00               NaN
S10        agg   agg           5                5   0.000e+00          0.000e+00          5               5  0.000e+00         0.000e+00
S11        agg   agg           1                1   0.000e+00          0.000e+00          1               1  0.000e+00         0.000e+00
S12        agg   agg          10               10   1.110e-16          0.000e+00         10              10  1.110e-16         1.110e-16
S13       fact  fact           2                2   0.000e+00                NaN          2               2  0.000e+00               NaN
S14       fact  fact           3                3   0.000e+00                NaN          3               3  0.000e+00               NaN
S15       fact  fact           3                3   0.000e+00                NaN          3               3  0.000e+00               NaN
```

The compiled result of every gold spec on the full database, in full:

```
S01  spec {"intent": "answer", "metrics": ["arrears_90p_bal"], "group_by": [], "filters": {}, "time": {"grain": "month", "start": "2026-09", "end": "2026-09", "shape": "point"}, "order": null, "clarify": null, "unsupported_reason": null}
period_label  arrears_90p_bal
     2026-09 0.00470555954159

S02  spec {"intent": "answer", "metrics": ["balance_total", "loan_count"], "group_by": ["originator"], "filters": {}, "time": {"grain": "month", "start": "2026-09", "end": "2026-09", "shape": "point"}, "order": null, "clarify": null, "unsupported_reason": null}
originator period_label  balance_total  loan_count
       CST      2026-09   764487387.12        1514
      HARB      2026-09   768870944.95        1466
       KOO      2026-09   662477991.42        1292
       RED      2026-09   711645254.54        1350
       WAT      2026-09   775541878.97        1493

S03  spec {"intent": "answer", "metrics": ["arrears_30p_bal"], "group_by": ["state"], "filters": {}, "time": {"grain": "month", "start": "2024-01", "end": "2024-06", "shape": "series"}, "order": null, "clarify": null, "unsupported_reason": null}
state period_label  arrears_30p_bal
  NSW      2024-01  0.0173914712344
  NSW      2024-02  0.0198350160248
  NSW      2024-03   0.019502046773
  NSW      2024-04  0.0206948082359
  NSW      2024-05   0.022608588005
  NSW      2024-06  0.0244428944393
  QLD      2024-01  0.0147856058223
  QLD      2024-02  0.0171182687509
  QLD      2024-03  0.0189740116553
  QLD      2024-04  0.0199386766478
  QLD      2024-05  0.0192817334606
  QLD      2024-06  0.0212254544999
   SA      2024-01  0.0137084096077
   SA      2024-02  0.0141755562302
   SA      2024-03 0.00957094639643
   SA      2024-04  0.0131784534117
   SA      2024-05  0.0152948326488
   SA      2024-06  0.0161526555868
  VIC      2024-01  0.0209277847341
  VIC      2024-02  0.0198343361528
  VIC      2024-03  0.0225858659477
  VIC      2024-04  0.0232073744995
  VIC      2024-05  0.0216720609044
  VIC      2024-06  0.0206933094275
   WA      2024-01  0.0191913474174
   WA      2024-02  0.0198292142638
   WA      2024-03  0.0184993177594
   WA      2024-04  0.0184886854517
   WA      2024-05  0.0172774105103
   WA      2024-06  0.0173346292442

S04  spec {"intent": "answer", "metrics": ["cpr"], "group_by": ["city"], "filters": {}, "time": {"grain": "quarter", "start": "2025-01", "end": "2025-12", "shape": "series"}, "order": null, "clarify": null, "unsupported_reason": null}
     city period_label            cpr
 Adelaide      2025-Q1 0.163979745736
 Adelaide      2025-Q2 0.171094382806
 Adelaide      2025-Q3  0.20115310482
 Adelaide      2025-Q4 0.178869495614
 Brisbane      2025-Q1 0.205194690222
 Brisbane      2025-Q2 0.186509664218
 Brisbane      2025-Q3 0.211425084444
 Brisbane      2025-Q4 0.195426041745
Melbourne      2025-Q1 0.199202643652
Melbourne      2025-Q2 0.163234046105
Melbourne      2025-Q3 0.167665638148
Melbourne      2025-Q4  0.18412425823
    Perth      2025-Q1 0.177924866648
    Perth      2025-Q2 0.176218707139
    Perth      2025-Q3  0.18631323992
    Perth      2025-Q4 0.188182332677
   Sydney      2025-Q1 0.199444312609
   Sydney      2025-Q2 0.193673567284
   Sydney      2025-Q3 0.169838786859
   Sydney      2025-Q4 0.201832871242

S05  spec {"intent": "answer", "metrics": ["cdr"], "group_by": [], "filters": {}, "time": {"grain": "year", "start": "2022-01", "end": "2025-12", "shape": "series"}, "order": null, "clarify": null, "unsupported_reason": null}
period_label              cdr
        2022 0.00139284990351
        2023 0.00262439696381
        2024  0.0100221041925
        2025  0.0101522112567

S06  spec {"intent": "answer", "metrics": ["wa_indexed_ltv"], "group_by": ["vintage_year"], "filters": {"state": ["NSW"]}, "time": {"grain": "month", "start": "2026-09", "end": "2026-09", "shape": "point"}, "order": null, "clarify": null, "unsupported_reason": null}
 vintage_year period_label  wa_indexed_ltv
         2017      2026-09  0.435393406646
         2018      2026-09  0.402302747358
         2019      2026-09  0.394933784832
         2020      2026-09  0.439412583869
         2021      2026-09  0.513691091978
         2022      2026-09  0.598286090403
         2023      2026-09  0.544132642385

S07  spec {"intent": "answer", "metrics": ["arrears_90p_cnt"], "group_by": ["ltv_bucket_indexed"], "filters": {}, "time": {"grain": "month", "start": "2026-09", "end": "2026-09", "shape": "point"}, "order": null, "clarify": null, "unsupported_reason": null}
ltv_bucket_indexed period_label  arrears_90p_cnt
             60-70      2026-09 0.00407055630936
             70-80      2026-09 0.00374531835206
             80-90      2026-09   0.046511627907
              <=60      2026-09 0.00411997363217

S08  spec {"intent": "answer", "metrics": ["hardship_share_bal"], "group_by": ["occupancy"], "filters": {}, "time": {"grain": "month", "start": "2024-07", "end": "2024-12", "shape": "series"}, "order": null, "clarify": null, "unsupported_reason": null}
occupancy period_label  hardship_share_bal
 investor      2024-07    0.00820062117591
 investor      2024-08    0.00878913658498
 investor      2024-09    0.00923122267164
 investor      2024-10    0.00970192654762
 investor      2024-11    0.00835860832982
 investor      2024-12    0.00780675543014
    owner      2024-07    0.00946138510243
    owner      2024-08    0.00941444742563
    owner      2024-09    0.00888214208228
    owner      2024-10    0.00852091316383
    owner      2024-11    0.00899852182053
    owner      2024-12    0.00840217270654

S09  spec {"intent": "answer", "metrics": ["wa_rate"], "group_by": ["rate_type"], "filters": {}, "time": {"grain": "month", "start": "2023-06", "end": "2023-06", "shape": "point"}, "order": null, "clarify": null, "unsupported_reason": null}
rate_type period_label         wa_rate
    fixed      2023-06 0.0206333867293
 variable      2023-06 0.0687908919681

S10  spec {"intent": "answer", "metrics": ["arrears_90p_bal"], "group_by": ["deal_name"], "filters": {}, "time": {"grain": "month", "start": "2025-06", "end": "2025-06", "shape": "point"}, "order": {"metric": "arrears_90p_bal", "direction": "desc", "limit": 5}, "clarify": null, "unsupported_reason": null}
 deal_name period_label  arrears_90p_bal
RED 2022-1      2025-06  0.0207508139823
RED 2023-1      2025-06  0.0199432572327
KOO 2021-1      2025-06  0.0178633393098
CST 2021-1      2025-06  0.0159009666409
CST 2020-1      2025-06  0.0152159680671

S11  spec {"intent": "answer", "metrics": ["cpr", "balance_total"], "group_by": [], "filters": {"deal_id": ["D004"]}, "time": {"grain": "month", "start": "2025-01", "end": "2025-12", "shape": "point"}, "order": null, "clarify": null, "unsupported_reason": null}
period_label  balance_total            cpr
       range     70128886.3 0.215550815445

S12  spec {"intent": "answer", "metrics": ["smm_vol", "cpr"], "group_by": ["issue_year"], "filters": {}, "time": {"grain": "year", "start": "2023-01", "end": "2024-12", "shape": "series"}, "order": null, "clarify": null, "unsupported_reason": null}
 issue_year period_label         smm_vol            cpr
       2019         2023 0.0156024751824 0.171969838648
       2019         2024 0.0172779145323 0.188724059185
       2020         2023 0.0171152869579 0.187111526099
       2020         2024 0.0166061318468   0.1820439828
       2021         2023 0.0165937225905 0.181920114665
       2021         2024 0.0147491212961 0.163315024406
       2022         2023 0.0159885115963 0.175858039286
       2022         2024    0.0173610281 0.189547038737
       2023         2023 0.0132285411723  0.14768730997
       2023         2024 0.0139875475776 0.155521112233

S13  spec {"intent": "answer", "metrics": ["wa_orig_ltv", "loan_count"], "group_by": ["lmi_flag"], "filters": {}, "time": {"grain": "month", "start": "2026-09", "end": "2026-09", "shape": "point"}, "order": null, "clarify": null, "unsupported_reason": null}
lmi_flag period_label    wa_orig_ltv  loan_count
      no      2026-09 0.683617742028        4852
     yes      2026-09 0.855367867789        2263

S14  spec {"intent": "answer", "metrics": ["arrears_90p_bal"], "group_by": ["seasoning_bucket", "io_flag"], "filters": {}, "time": {"grain": "month", "start": "2026-09", "end": "2026-09", "shape": "point"}, "order": null, "clarify": null, "unsupported_reason": null}
seasoning_bucket io_flag period_label  arrears_90p_bal
           37-60      no      2026-09 0.00314138611305
           37-60     yes      2026-09  0.0299348589245
             >60      no      2026-09 0.00326586690305

S15  spec {"intent": "answer", "metrics": ["balance_total", "loan_count"], "group_by": [], "filters": {"trustee_format": ["A"], "dpd_bucket": ["30-59", "60-89", "90+"]}, "time": {"grain": "month", "start": "2024-04", "end": "2024-06", "shape": "series"}, "order": null, "clarify": null, "unsupported_reason": null}
period_label  balance_total  loan_count
     2024-04    97527946.84         176
     2024-05    101523160.8         180
     2024-06   103361463.77         188
```

The DuckDB SQL for S04 and S11, in full:

```
-- S04
WITH parts AS (
  SELECT
    l.city AS city,
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
        THEN CAST(f.closing_balance AS DOUBLE) * l.orig_ltv
        ELSE 0
      END
    ) AS orig_ltv_x_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0
        THEN CAST(f.closing_balance AS DOUBLE) * f.indexed_ltv
        ELSE 0
      END
    ) AS idx_ltv_x_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0
        THEN CAST(f.closing_balance AS DOUBLE) * f.interest_rate
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
  FROM fact_loan_month AS f
  JOIN dim_loan AS l
    ON l.loan_id = f.loan_id
  JOIN dim_deal AS d
    ON d.deal_id = f.deal_id
  WHERE
    f.period BETWEEN CAST('2025-01-01' AS DATE) AND CAST('2025-12-01' AS DATE)
  GROUP BY
    l.city,
    f.period
), b AS (
  SELECT
    parts.*,
    p.quarter_label AS period_label
  FROM parts
  JOIN dim_period AS p
    ON p.period = parts.period
), keys AS (
  SELECT DISTINCT
    city,
    period_label
  FROM b
), flow AS (
  SELECT
    city,
    period_label,
    CASE
      WHEN SUM(CASE WHEN smm_den > 0 THEN 1 ELSE 0 END) = 0
      THEN NULL
      WHEN MAX(
        CASE
          WHEN smm_den > 0
          THEN CAST(smm_num AS DOUBLE) / CAST(smm_den AS DOUBLE)
          ELSE 0
        END
      ) >= 1
      THEN 1.0
      ELSE 1 - EXP(
        SUM(
          CASE
            WHEN smm_den > 0 AND smm_num < smm_den
            THEN LN(1 - CAST(smm_num AS DOUBLE) / CAST(smm_den AS DOUBLE))
            ELSE 0
          END
        )
      )
    END AS smm_p,
    SUM(CASE WHEN smm_den > 0 THEN 1 ELSE 0 END) AS smm_n
  FROM b
  GROUP BY
    city,
    period_label
)
SELECT
  k.city,
  k.period_label,
  CASE WHEN w.smm_n > 0 THEN 1 - POWER(1 - w.smm_p, 12.0 / w.smm_n) END AS cpr
FROM keys AS k
LEFT JOIN flow AS w
  ON w.city = k.city AND w.period_label = k.period_label
ORDER BY
  k.city,
  k.period_label

-- S11
WITH parts AS (
  SELECT
    a.period,
    SUM(a.loan_count) AS loan_count,
    SUM(a.bal) AS bal,
    SUM(a.a30_bal) AS a30_bal,
    SUM(a.a90_bal) AS a90_bal,
    SUM(a.a90_cnt) AS a90_cnt,
    SUM(a.hard_bal) AS hard_bal,
    SUM(a.orig_ltv_x_bal) AS orig_ltv_x_bal,
    SUM(a.idx_ltv_x_bal) AS idx_ltv_x_bal,
    SUM(a.rate_x_bal) AS rate_x_bal,
    SUM(a.smm_num) AS smm_num,
    SUM(a.smm_den) AS smm_den,
    SUM(a.mdr_num) AS mdr_num,
    SUM(a.mdr_den) AS mdr_den
  FROM agg_deal_month AS a
  JOIN dim_deal AS d
    ON d.deal_id = a.deal_id
  WHERE
    a.period BETWEEN CAST('2025-01-01' AS DATE) AND CAST('2025-12-01' AS DATE)
    AND a.deal_id IN ('D004')
  GROUP BY
    a.period
), b AS (
  SELECT
    parts.*,
    'range' AS period_label
  FROM parts
), keys AS (
  SELECT DISTINCT
    period_label
  FROM b
), stock AS (
  SELECT
    period_label,
    bal AS balance_total
  FROM (
    SELECT
      b.*,
      ROW_NUMBER() OVER (PARTITION BY period_label ORDER BY period DESC) AS rn
    FROM b
    WHERE
      loan_count > 0
  ) AS r
  WHERE
    rn = 1
), flow AS (
  SELECT
    period_label,
    CASE
      WHEN SUM(CASE WHEN smm_den > 0 THEN 1 ELSE 0 END) = 0
      THEN NULL
      WHEN MAX(
        CASE
          WHEN smm_den > 0
          THEN CAST(smm_num AS DOUBLE) / CAST(smm_den AS DOUBLE)
          ELSE 0
        END
      ) >= 1
      THEN 1.0
      ELSE 1 - EXP(
        SUM(
          CASE
            WHEN smm_den > 0 AND smm_num < smm_den
            THEN LN(1 - CAST(smm_num AS DOUBLE) / CAST(smm_den AS DOUBLE))
            ELSE 0
          END
        )
      )
    END AS smm_p,
    SUM(CASE WHEN smm_den > 0 THEN 1 ELSE 0 END) AS smm_n
  FROM b
  GROUP BY
    period_label
)
SELECT
  k.period_label,
  s.balance_total,
  CASE WHEN w.smm_n > 0 THEN 1 - POWER(1 - w.smm_p, 12.0 / w.smm_n) END AS cpr
FROM keys AS k
LEFT JOIN stock AS s
  ON s.period_label = k.period_label
LEFT JOIN flow AS w
  ON w.period_label = k.period_label
ORDER BY
  k.period_label
```

The B.8 hand example, line by line:

```
survival = 0.99 x 0.98 x 0.985 = 0.955647000000
smm_p = 1 - survival = 0.044353000000
cpr = 1 - survival^(12/3) = 1 - 0.955647000000^4 = 0.16595400138
smm_vol = 1 - survival^(1/3) = 0.01500846031
smm_p via 1 - exp(sum ln(1 - m)) = 0.044353000000
aggregate() on the constructed 3-month frame:
period_label           cpr         smm_vol
     2025-Q1 0.16595400138 0.0150084603096
missing month: n = 2, survival = 0.99 x 0.98 = 0.970200000000; cpr = 1 - 0.9702^6 = 0.16599698292
aggregate() with the third month's smm_den = 0:
period_label            cpr         smm_vol
     2025-Q1 0.165996982918 0.0150126904371
targets: 0.16595400138, 0.01500846031, 0.16599698292; diffs 4.77e-13, 4.47e-13, 1.58e-12
```

- Deviations from PLAN.md or the instruction file:
  - **O-37: metric column order.** B.7 says "1 column per metric in spec order". S11's
    metrics are `["cpr", "balance_total"]`, and its hand SQL returns `period_label,
    balance_total, cpr`. The test requires identical columns, so the compiler puts stock
    metrics in spec order, then flow metrics in spec order. S11 is the only gold spec
    where this differs from spec order. Both options are in `decisions/OPEN.md`.
  - Dates in the tree are `exp.DateStrToDate`. DuckDB renders it as `CAST('2025-01-01' AS
    DATE)` and Oracle as `TO_DATE('2025-01-01', 'YYYY-MM-DD')`, so Oracle doesn't depend
    on the session date format.
  - Joins use `ON k.x = s.x` rather than the hand SQL's `USING`, because Oracle forbids
    a table qualifier on a `USING` column and the final select qualifies them (`k.city`).
  - The flow CTE's sum of logs is guarded by `smm_num < smm_den` as well as
    `smm_den > 0`, so `LN` never sees 0. When any month has m ≥ 1 the outer `CASE`
    returns 1 first, as B.6 says.
  - The final select puts `CASE WHEN n > 0 THEN ... END` around `POWER(1 − p, k / n)`, so
    Oracle never divides by n = 0. That gives NULL, as B.6 says.

### Step 3.4: routing

- Files: `rmbsq/semantic/compiler.py` (`choose_route`, the `agg` branch of
  `_parts_cte`), `tests/test_routing.py`
- Signatures implemented: `choose_route(spec, catalog) -> str`. `compile(..., route="agg")`
  raises `ValueError` for a spec with a loan-level dimension.
- Tests: result passed.

```
tests/test_routing.py::test_route_auto_choice[S01] PASSED
tests/test_routing.py::test_route_auto_choice[S02] PASSED
tests/test_routing.py::test_route_auto_choice[S03] PASSED
tests/test_routing.py::test_route_auto_choice[S04] PASSED
tests/test_routing.py::test_route_auto_choice[S05] PASSED
tests/test_routing.py::test_route_auto_choice[S06] PASSED
tests/test_routing.py::test_route_auto_choice[S07] PASSED
tests/test_routing.py::test_route_auto_choice[S08] PASSED
tests/test_routing.py::test_route_auto_choice[S09] PASSED
tests/test_routing.py::test_route_auto_choice[S10] PASSED
tests/test_routing.py::test_route_auto_choice[S11] PASSED
tests/test_routing.py::test_route_auto_choice[S12] PASSED
tests/test_routing.py::test_route_auto_choice[S13] PASSED
tests/test_routing.py::test_route_auto_choice[S14] PASSED
tests/test_routing.py::test_route_auto_choice[S15] PASSED
tests/test_routing.py::test_fact_and_agg_routes_equal[S01] PASSED
tests/test_routing.py::test_fact_and_agg_routes_equal[S02] PASSED
tests/test_routing.py::test_fact_and_agg_routes_equal[S05] PASSED
tests/test_routing.py::test_fact_and_agg_routes_equal[S10] PASSED
tests/test_routing.py::test_fact_and_agg_routes_equal[S11] PASSED
tests/test_routing.py::test_fact_and_agg_routes_equal[S12] PASSED
```

- Outputs: none
- Evidence: the `route`, `route_auto` and `agg_vs_fact_*` columns of the per-spec table
  in step 3.3. Every spec's chosen route equals `route_auto`, and the 6 agg specs differ
  from the fact route by at most 1.110e-16 (S12, full).
- Deviations from PLAN.md or the instruction file: none

### Step 3.5: Oracle rendering

- Files: `rmbsq/semantic/compiler.py` (both renders use `unsupported_level=
  ErrorLevel.RAISE`, so an unsupported construct raises inside `compile`),
  `tests/test_oracle_render.py`
- Signatures implemented: `CompiledQuery.sql_oracle`, `tree.sql(dialect="oracle",
  pretty=True)`.
- Tests: result passed.

```
tests/test_oracle_render.py::test_specs_render_to_oracle[S01] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S02] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S03] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S04] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S05] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S06] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S07] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S08] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S09] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S10] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S11] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S12] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S13] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S14] PASSED
tests/test_oracle_render.py::test_specs_render_to_oracle[S15] PASSED
```

- Outputs: none
- Evidence. The Oracle SQL for S04, S11 and S12, in full:

```
-- S04
WITH parts AS (
  SELECT
    l.city AS city,
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
    f.period BETWEEN TO_DATE('2025-01-01', 'YYYY-MM-DD') AND TO_DATE('2025-12-01', 'YYYY-MM-DD')
  GROUP BY
    l.city,
    f.period
), b AS (
  SELECT
    parts.*,
    p.quarter_label AS period_label
  FROM parts
  JOIN dim_period p
    ON p.period = parts.period
), keys AS (
  SELECT DISTINCT
    city,
    period_label
  FROM b
), flow AS (
  SELECT
    city,
    period_label,
    CASE
      WHEN SUM(CASE WHEN smm_den > 0 THEN 1 ELSE 0 END) = 0
      THEN NULL
      WHEN MAX(
        CASE
          WHEN smm_den > 0
          THEN CAST(smm_num AS DOUBLE PRECISION) / CAST(smm_den AS DOUBLE PRECISION)
          ELSE 0
        END
      ) >= 1
      THEN 1.0
      ELSE 1 - EXP(
        SUM(
          CASE
            WHEN smm_den > 0 AND smm_num < smm_den
            THEN LN(1 - CAST(smm_num AS DOUBLE PRECISION) / CAST(smm_den AS DOUBLE PRECISION))
            ELSE 0
          END
        )
      )
    END AS smm_p,
    SUM(CASE WHEN smm_den > 0 THEN 1 ELSE 0 END) AS smm_n
  FROM b
  GROUP BY
    city,
    period_label
)
SELECT
  k.city,
  k.period_label,
  CASE WHEN w.smm_n > 0 THEN 1 - POWER(1 - w.smm_p, 12.0 / w.smm_n) END AS cpr
FROM keys k
LEFT JOIN flow w
  ON w.city = k.city AND w.period_label = k.period_label
ORDER BY
  k.city,
  k.period_label

-- S11
WITH parts AS (
  SELECT
    a.period,
    SUM(a.loan_count) AS loan_count,
    SUM(a.bal) AS bal,
    SUM(a.a30_bal) AS a30_bal,
    SUM(a.a90_bal) AS a90_bal,
    SUM(a.a90_cnt) AS a90_cnt,
    SUM(a.hard_bal) AS hard_bal,
    SUM(a.orig_ltv_x_bal) AS orig_ltv_x_bal,
    SUM(a.idx_ltv_x_bal) AS idx_ltv_x_bal,
    SUM(a.rate_x_bal) AS rate_x_bal,
    SUM(a.smm_num) AS smm_num,
    SUM(a.smm_den) AS smm_den,
    SUM(a.mdr_num) AS mdr_num,
    SUM(a.mdr_den) AS mdr_den
  FROM agg_deal_month a
  JOIN dim_deal d
    ON d.deal_id = a.deal_id
  WHERE
    a.period BETWEEN TO_DATE('2025-01-01', 'YYYY-MM-DD') AND TO_DATE('2025-12-01', 'YYYY-MM-DD')
    AND a.deal_id IN ('D004')
  GROUP BY
    a.period
), b AS (
  SELECT
    parts.*,
    'range' AS period_label
  FROM parts
), keys AS (
  SELECT DISTINCT
    period_label
  FROM b
), stock AS (
  SELECT
    period_label,
    bal AS balance_total
  FROM (
    SELECT
      b.*,
      ROW_NUMBER() OVER (PARTITION BY period_label ORDER BY period DESC NULLS LAST) AS rn
    FROM b
    WHERE
      loan_count > 0
  ) r
  WHERE
    rn = 1
), flow AS (
  SELECT
    period_label,
    CASE
      WHEN SUM(CASE WHEN smm_den > 0 THEN 1 ELSE 0 END) = 0
      THEN NULL
      WHEN MAX(
        CASE
          WHEN smm_den > 0
          THEN CAST(smm_num AS DOUBLE PRECISION) / CAST(smm_den AS DOUBLE PRECISION)
          ELSE 0
        END
      ) >= 1
      THEN 1.0
      ELSE 1 - EXP(
        SUM(
          CASE
            WHEN smm_den > 0 AND smm_num < smm_den
            THEN LN(1 - CAST(smm_num AS DOUBLE PRECISION) / CAST(smm_den AS DOUBLE PRECISION))
            ELSE 0
          END
        )
      )
    END AS smm_p,
    SUM(CASE WHEN smm_den > 0 THEN 1 ELSE 0 END) AS smm_n
  FROM b
  GROUP BY
    period_label
)
SELECT
  k.period_label,
  s.balance_total,
  CASE WHEN w.smm_n > 0 THEN 1 - POWER(1 - w.smm_p, 12.0 / w.smm_n) END AS cpr
FROM keys k
LEFT JOIN stock s
  ON s.period_label = k.period_label
LEFT JOIN flow w
  ON w.period_label = k.period_label
ORDER BY
  k.period_label

-- S12
WITH parts AS (
  SELECT
    d.issue_year AS issue_year,
    a.period,
    SUM(a.loan_count) AS loan_count,
    SUM(a.bal) AS bal,
    SUM(a.a30_bal) AS a30_bal,
    SUM(a.a90_bal) AS a90_bal,
    SUM(a.a90_cnt) AS a90_cnt,
    SUM(a.hard_bal) AS hard_bal,
    SUM(a.orig_ltv_x_bal) AS orig_ltv_x_bal,
    SUM(a.idx_ltv_x_bal) AS idx_ltv_x_bal,
    SUM(a.rate_x_bal) AS rate_x_bal,
    SUM(a.smm_num) AS smm_num,
    SUM(a.smm_den) AS smm_den,
    SUM(a.mdr_num) AS mdr_num,
    SUM(a.mdr_den) AS mdr_den
  FROM agg_deal_month a
  JOIN dim_deal d
    ON d.deal_id = a.deal_id
  WHERE
    a.period BETWEEN TO_DATE('2023-01-01', 'YYYY-MM-DD') AND TO_DATE('2024-12-01', 'YYYY-MM-DD')
  GROUP BY
    d.issue_year,
    a.period
), b AS (
  SELECT
    parts.*,
    p.year_label AS period_label
  FROM parts
  JOIN dim_period p
    ON p.period = parts.period
), keys AS (
  SELECT DISTINCT
    issue_year,
    period_label
  FROM b
), flow AS (
  SELECT
    issue_year,
    period_label,
    CASE
      WHEN SUM(CASE WHEN smm_den > 0 THEN 1 ELSE 0 END) = 0
      THEN NULL
      WHEN MAX(
        CASE
          WHEN smm_den > 0
          THEN CAST(smm_num AS DOUBLE PRECISION) / CAST(smm_den AS DOUBLE PRECISION)
          ELSE 0
        END
      ) >= 1
      THEN 1.0
      ELSE 1 - EXP(
        SUM(
          CASE
            WHEN smm_den > 0 AND smm_num < smm_den
            THEN LN(1 - CAST(smm_num AS DOUBLE PRECISION) / CAST(smm_den AS DOUBLE PRECISION))
            ELSE 0
          END
        )
      )
    END AS smm_p,
    SUM(CASE WHEN smm_den > 0 THEN 1 ELSE 0 END) AS smm_n
  FROM b
  GROUP BY
    issue_year,
    period_label
)
SELECT
  k.issue_year,
  k.period_label,
  CASE WHEN w.smm_n > 0 THEN 1 - POWER(1 - w.smm_p, 1.0 / w.smm_n) END AS smm_vol,
  CASE WHEN w.smm_n > 0 THEN 1 - POWER(1 - w.smm_p, 12.0 / w.smm_n) END AS cpr
FROM keys k
LEFT JOIN flow w
  ON w.issue_year = k.issue_year AND w.period_label = k.period_label
ORDER BY
  k.issue_year,
  k.period_label
```

The captured `sqlglot` warning list (logger `sqlglot` at WARNING) over all 15 specs:

```
captured sqlglot warnings over all 15 specs: []
```

- Deviations from PLAN.md or the instruction file: the test is named
  `test_specs_render_to_oracle` as instruction 03 E 3.5 names it. PLAN.md had
  `test_specs_render_to_oracle_without_warnings`, and the PLAN.md paragraph is updated.

### Step 3.6: display formatting

- Files: `rmbsq/semantic/format.py`, `tests/test_format_table.py`
- Signatures implemented: `format_table(df, catalog) -> DataFrame`
- Tests: result passed.

```
tests/test_format_table.py::test_display_rules PASSED
```

- Outputs: none
- Evidence. `format_table` on S02 and S12 from the full database, raw beside formatted:

```
-- S02
originator (raw) period_label (raw)  balance_total (raw)  loan_count (raw) originator (shown) period_label (shown) balance_total (shown) loan_count (shown)
             CST            2026-09         764487387.12              1514                CST              2026-09              A$764.5m              1,514
            HARB            2026-09         768870944.95              1466               HARB              2026-09              A$768.9m              1,466
             KOO            2026-09         662477991.42              1292                KOO              2026-09              A$662.5m              1,292
             RED            2026-09         711645254.54              1350                RED              2026-09              A$711.6m              1,350
             WAT            2026-09         775541878.97              1493                WAT              2026-09              A$775.5m              1,493

-- S12
 issue_year (raw) period_label (raw)   smm_vol (raw)      cpr (raw) issue_year (shown) period_label (shown) smm_vol (shown) cpr (shown)
             2019               2023 0.0156024751824 0.171969838648               2019                 2023           1.56%      17.20%
             2019               2024 0.0172779145323 0.188724059185               2019                 2024           1.73%      18.87%
             2020               2023 0.0171152869579 0.187111526099               2020                 2023           1.71%      18.71%
             2020               2024 0.0166061318468   0.1820439828               2020                 2024           1.66%      18.20%
             2021               2023 0.0165937225905 0.181920114665               2021                 2023           1.66%      18.19%
             2021               2024 0.0147491212961 0.163315024406               2021                 2024           1.47%      16.33%
             2022               2023 0.0159885115963 0.175858039286               2022                 2023           1.60%      17.59%
             2022               2024    0.0173610281 0.189547038737               2022                 2024           1.74%      18.95%
             2023               2023 0.0132285411723  0.14768730997               2023                 2023           1.32%      14.77%
             2023               2024 0.0139875475776 0.155521112233               2023                 2024           1.40%      15.55%
```

0.000125, as stored and as formatted:

```
0.000125 as stored: 0.000125000000000000002602085213965210641617886722087860107421875; format(.2%) -> 0.01%
```

The stored double is a little above 0.000125. Python's `%` format multiplies by 100,
giving 0.0125 (as a percent), and rounds that to 2 dp. That is 0.01 under any rounding
mode, because the next digit is 2. So this value is not a tie, and the test records
`0.01%` as Python gives it.

- Deviations from PLAN.md or the instruction file: none

## 4. Full test suite

`.venv/Scripts/python -m pytest -q`, then `.venv/Scripts/python -m pytest -q -m full`, in
the working repo at `372082e`:

```
$ pytest -q
........................................................................ [ 53%]
..............................................................           [100%]
134 passed, 20 deselected in 33.29s
$ pytest -q -m full
....................                                                     [100%]
20 passed, 134 deselected in 39.53s
```

## 5. Determinism

`scripts/build_canonical.py --raw data/raw --db data/canonical/rmbs.duckdb` run twice,
with SHA-256 of every file in `outputs/` after each run:

```
run 1
0dc5cb0ff1f5c5cce1d50f13eed3e0f41fd0ab559088bd7ba68c4de76d0b60f9 *outputs/calibration.csv
c7ef5250f89dc8ada694a5d2896f50ec8fad45e3e78e544d5a5f4cb08d15da22 *outputs/canonical_row_counts.csv
dde99809930d19d094a65f245d19f9052bfc597b4a1d21c0406897dfa814ac63 *outputs/pool_monthly.csv
dc4d912d6c5476a9b4bdc31c56b0210c8801d3745068094aa46deb4e282b6ec9 *outputs/pool_monthly_truth.csv
run 2
0dc5cb0ff1f5c5cce1d50f13eed3e0f41fd0ab559088bd7ba68c4de76d0b60f9 *outputs/calibration.csv
c7ef5250f89dc8ada694a5d2896f50ec8fad45e3e78e544d5a5f4cb08d15da22 *outputs/canonical_row_counts.csv
dde99809930d19d094a65f245d19f9052bfc597b4a1d21c0406897dfa814ac63 *outputs/pool_monthly.csv
dc4d912d6c5476a9b4bdc31c56b0210c8801d3745068094aa46deb4e282b6ec9 *outputs/pool_monthly_truth.csv
```

## 6. Fresh-clone check

```
git clone https://github.com/uty101/RMBS-Natural-Language-Query.git C:/s3fc   # at 372082e
cd C:/s3fc
uv venv --python 3.12 .venv
uv pip sync --python .venv requirements-lock.txt
.venv/Scripts/python --version          # Python 3.12.13
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m pytest -q -m full
```

`pytest -q`:

```
........................................................................ [ 53%]
..............................................................           [100%]
134 passed, 20 deselected in 19.97s
```

`pytest -q -m full`:

```
....................                                                     [100%]
20 passed, 134 deselected in 46.48s
```

## 7. Open questions for the reviewer

1. **O-37 (step 3.3): metric column order when a flow metric comes before a stock
   metric.** B.7 says spec order, but S11's hand SQL (`["cpr", "balance_total"]`)
   returns `balance_total, cpr`, and the test compares column order.
   - (a) Stock metrics in spec order, then flow metrics in spec order, matching the
     gold file. **Built**, and all 15 specs pass.
   - (b) Strict spec order, as B.7 says. S11's hand SQL would then need its final select
     changed to `k.period_label, w.cpr, s.balance_total`.
