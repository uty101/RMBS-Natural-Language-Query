# 00 Kickoff: RMBS Natural Language Query

Session 0 instructions for Claude Code. This file is the spec. It wins over every earlier note or chat answer wherever they differ (`WORKFLOW.md` Part 4 rule 13).

Repo: `https://github.com/uty101/RMBS-Natural-Language-Query`
Package: `rmbsq`
Python: 3.12, venv built with `uv`

---

## 1. How the repo is run

1. Follow `WORKFLOW.md` (already committed in the repo root) exactly. Its Part 4 standing rules are copied into `CLAUDE.md` in session 0, amended by 1.3, 1.4, 1.6, 1.7 and 1.8 below.
2. Session N builds all of Section N and nothing else. Session 0 builds the plan and scaffolding only. There are 7 sections, so 8 sessions in all.
3. **Network rule (replaces Part 4 rule 8).** There is no data pull. Data is generated deterministically by `scripts/generate_data.py`, which has no network code. The only network code in the repo is `rmbsq/llm/client.py` in `record` mode, called only by `scripts/run_eval_live.py` and by `rmbsq ask --live`. Everything else, including the whole test suite, runs in `replay` mode from `data/llm_cache/` with sockets disabled.
4. **Data rule (replaces the raw data half of Part 4 rule 8).** Generated raw files are committed under `data/raw/` with `data/raw/MANIFEST.json` holding SHA-256 hashes. Tests never read the full raw data. They generate the `small` profile in a temp folder (Section 8, `[profiles.small]`).
5. Status files are `instructions/NN_<name>.status.md` as in the workflow. Session 0's is `instructions/00_kickoff.status.md`.
6. Do not stop or wait at any gate this file doesn't name as a stop condition. Build the whole section.
7. The repo and its write-up stay neutral. No mention of any firm, job, application, interview or case study anywhere in the repo, including commit messages.
8. **The project has 2 audiences and 2 outputs.** The repo is the evidence. The send pack in `deliverable/` (Section 7) is what a reader opens first: a written design response as a PDF and a 1 page results summary as a PDF. Every number in either PDF is generated from a committed CSV, never typed by hand. A cover email is drafted by chat Claude outside the repo.

---

## 2. What the project answers

Q1. Can an LLM that only writes a constrained query spec, with all arithmetic done by a compiler over governed metric definitions, answer natural language questions on loan-level RMBS data with numbers that match hand-written SQL?

Q2. How does it compare with a free text-to-SQL baseline that gets the same schema and the same written metric definitions, on the same 40 questions?

Q3. Does it ask for clarification when a question is ambiguous and decline when the data can't answer it, instead of guessing?

Q4. Does query time stay usable at the full production scale of 300 deals × 2,000 loans × 60 months (about 36 million loan-month rows)? Measured by tiling the synthetic fact table 36 times in DuckDB (6.12).

Every result is reported per category with a Wilson 95% interval, because n is small (at most 10 per category).

---

## 3. Corrections to the source notes

The source is the design discussed in chat on 26 and 29 Oct 2026. Fixed decisions:

1. **Oracle is replaced by DuckDB** for execution. The compiler builds a `sqlglot` expression tree, executes it as DuckDB SQL, and also renders Oracle SQL for display. A test renders every gold spec to the `oracle` dialect and fails on any `sqlglot` unsupported warning.
2. **Data is synthetic**, built to carry the Australian features the design depends on (fixed rate expiries, interest only expiries, LMI, hardship, offset accounts are dropped, see 3.6). Every chart and README line says the data is synthetic.
3. **Size.** The notes said 50 deals × 500 loans × 60 months ≈ 1.5 million rows. Loans run off and deals issued before the window are already seasoned, so expect about 1 million loan-month rows. Section 1 tests the count is in [700,000, 1,600,000].
4. **Precompute.** Only 1 aggregate table, `agg_deal_month`. The compiler routes to it when every group_by and filter dimension is deal level. A test proves both routes give the same numbers.
5. **"Every number in the prose appears in the result set"** is defined exactly in 6.9 (the number guard).
6. **Offset and redraw are dropped.** They add schema without adding a test the eval uses.
7. **HPI regression and roll rate tools are out of scope.** `docs/DESIGN_NOTE.md` lists them as phase 2.
8. **Default weighting is balance.** If a question says "arrears" with no day threshold, the system must clarify. If it gives a threshold but not count vs balance, the system uses balance and the answer says so.
9. **The baseline gets the metric definitions in writing,** plus the required output column names for each question. This favours the baseline, and the README says so.
10. **The eval is run once per system,** temperature 0, N = 1 per question. Stability across repeated runs is listed as a limitation.

---

## 4. Universe, data and sample

### 4.1 Calendar

- `period` is a DATE on the first of the month and means the month end status of that month.
- Simulation runs monthly from 2016-01 to 2026-09.
- Observation window (emitted rows): 2021-10 to 2026-09, 60 months.
- A loan-month row is emitted only if `period` is in the window and `period >= deal.issue_month`.
- "Latest" means 2026-09.

### 4.2 Originators and deals

5 fictional originators, each with a trustee format:

| code | name | trustee_format |
|---|---|---|
| HARB | Harbour Home Loans | A |
| KOO | Kookaburra Mutual | A |
| WAT | Wattle Lending | A |
| CST | Coastline Bank | B |
| RED | Redgum Finance | B |

- 50 deals, `deal_id` `D001` to `D050`.
- Deal k (1 based): originator = codes[(k − 1) mod 5], issue_month = 2019-01 + floor((k − 1) × 60 / 50) months.
- `deal_name` = `"{code} {issue_year}-{n}"`, where n counts that originator's deals in that issue year in deal_id order, starting at 1.
- 500 loans per deal at issue. `loan_id` = `"{deal_id}-{nnnn}"`, nnnn from 0001.
- Seasoning at issue: integer uniform on [6, 36] months. orig_month = issue_month − seasoning.
- Each loan is simulated from orig_month, but survival is forced before issue_month (exit draws are made, to keep the RNG stream fixed, and ignored). Arrears and hardship states are reset to current at issue_month. This keeps every deal at exactly 500 loans at issue, as a real pool cut would.
- `issue_balance` = sum of loan balances at issue_month.

### 4.3 Geography

5 cities, 4 areas each, 3 suburbs per area (60 suburbs). Area names are real place names used as labels only. Codes and suburbs are synthetic.

| city | state | weight | areas (beta) |
|---|---|---|---|
| Sydney | NSW | 0.32 | Blacktown 1.2, Parramatta 1.1, Penrith 1.3, Sutherland 0.9 |
| Melbourne | VIC | 0.28 | Casey 1.2, Wyndham 1.3, Whittlesea 1.1, Boroondara 0.8 |
| Brisbane | QLD | 0.20 | Ipswich 1.2, Logan 1.3, Moreton Bay 1.0, Brisbane Inner 0.9 |
| Perth | WA | 0.12 | Wanneroo 1.1, Joondalup 0.9, Rockingham 1.2, Stirling 1.0 |
| Adelaide | SA | 0.08 | Salisbury 1.1, Onkaparinga 1.0, Playford 1.3, Charles Sturt 0.9 |

- Suburbs: `"{area} North"`, `"{area} Central"`, `"{area} South"`.
- Loan city drawn by weight, area uniform within city, suburb uniform within area.

### 4.4 Cash rate (stylised path following RBA target moves)

Rate applies from the given month until the next change: 2016-01 2.00%, 2016-05 1.75%, 2016-08 1.50%, 2019-06 1.25%, 2019-07 1.00%, 2019-10 0.75%, 2020-03 0.25%, 2020-11 0.10%, 2022-05 0.35%, 2022-06 0.85%, 2022-07 1.35%, 2022-08 1.85%, 2022-09 2.35%, 2022-10 2.60%, 2022-11 2.85%, 2022-12 3.10%, 2023-02 3.35%, 2023-03 3.60%, 2023-05 3.85%, 2023-06 4.10%, 2023-11 4.35%, 2025-02 4.10%, 2025-05 3.85%, 2025-08 3.60%, held to 2026-09.

### 4.5 House price index (stylised)

City monthly log drift (%) by regime:

| from | to | Sydney | Melbourne | Brisbane | Perth | Adelaide |
|---|---|---|---|---|---|---|
| 2016-01 | 2017-12 | 0.6 | 0.7 | 0.2 | −0.2 | 0.3 |
| 2018-01 | 2019-06 | −0.8 | −0.8 | 0.0 | −0.6 | 0.0 |
| 2019-07 | 2020-03 | 0.8 | 0.8 | 0.3 | 0.0 | 0.2 |
| 2020-04 | 2020-09 | −0.2 | −0.2 | −0.2 | 0.0 | −0.2 |
| 2020-10 | 2022-03 | 1.6 | 1.0 | 2.0 | 0.8 | 1.7 |
| 2022-04 | 2023-01 | −1.4 | −1.0 | −1.2 | 0.2 | 0.0 |
| 2023-02 | 2024-12 | 0.5 | 0.0 | 1.0 | 1.5 | 1.0 |
| 2025-01 | 2026-09 | 0.4 | 0.3 | 0.6 | 0.7 | 0.6 |

Suburb s in area a, month t:

- noise: e_s,t = 0.8 × e_s,t−1 + 0.004 × z, z ~ N(0,1), e_s,2016-01 = 0
- log return r_s,t = beta_a × drift_city,t / 100 + e_s,t − e_s,t−1
- HPI_s,2016-01 = 100, HPI_s,t = HPI_s,t−1 × exp(r_s,t)

### 4.6 Loan attributes at origination

- orig_balance = clip(exp(ln(520,000 × city_mult) + 0.45 × z), 100,000, 2,500,000), rounded to the dollar. city_mult: Sydney 1.25, Melbourne 1.05, Brisbane 0.95, Perth 0.85, Adelaide 0.85.
- orig_ltv = min(0.35 + 0.6 × Beta(4, 2.2), 0.95). orig_valuation = orig_balance / orig_ltv, rounded to the dollar.
- lmi_flag = orig_ltv > 0.80.
- occupancy = investor with p 0.30, else owner.
- io_flag: p 0.40 investor, 0.15 owner. io_end_month = orig_month + 60.
- rate_type fixed with p 0.15 if orig_month < 2020-01, 0.40 if 2020-01 ≤ orig_month ≤ 2022-03, 0.10 after. fixed_term 24 or 36 months, p 0.5 each. fixed_end_month = orig_month + fixed_term. Variable loans have null fixed_end_month.
- margin ~ N(0.026, 0.004) clipped to [0.018, 0.038]; +0.003 investor; +0.004 io_flag.
- fixed_rate = cash_at_orig + N(0.019, 0.003), clipped to [0.015, 0.06].
- term 360 months.

### 4.7 Monthly simulation (per active loan, per month)

**Rate.** If fixed and period < fixed_end_month: fixed_rate. Otherwise cash_t + margin.

**Payment.** IO and period < io_end_month: balance × rate / 12. Otherwise annuity on remaining term (360 − age, where age = months since orig_month), recomputed every month from the current balance and rate. scheduled_principal = payment − balance × rate / 12 (0 for IO).

**Payment shock.** shock = payment_t / payment_orig − 1, where payment_orig is the payment in orig_month.

**Indexed value and LTV.** indexed_value = orig_valuation × HPI_suburb,t / HPI_suburb,orig_month. indexed_ltv = closing_balance / indexed_value (opening balance for the exit row, see 5.4).

**Draw order.** Each month, for the array of active loans sorted by loan_id, draw 4 uniform arrays in this order: hardship, transition, prepay, repurchase.

**Hardship.** A current loan (dpd 0) not in hardship enters with p 0.002, for a duration uniform on {3, 4, 5, 6} months (drawn from the same hardship uniform: duration = 3 + floor(4 × (u / 0.002)) for u < 0.002). In hardship: dpd frozen, no prepay draw, scheduled principal 0.

**Arrears states.** dpd_bucket 0 current, 1 = 1–29, 2 = 30–59, 3 = 60–89, 4 = 90+.

- From 0 to 1: p = logistic(−5.52 + 3.0 × max(shock, 0) + 4.0 × max(indexed_ltv − 0.8, 0) + 0.3 × investor + 0.5 × io_recent), where io_recent = 1 if io_flag and 0 ≤ period − io_end_month < 12 months.
- From k in {1, 2, 3}: cure to 0 with p_cure_k, roll to k + 1 with p_roll_k × exp(1.5 × max(shock, 0)) capped at 0.95 − p_cure_k, else stay. p_cure = (0.55, 0.30, 0.15), p_roll = (0.25, 0.40, 0.55).
- From 4: cure to 0 with p 0.05, else stay. months_in_90 counts consecutive months at 4.
- Transition outcome: one uniform u; cure if u < p_cure, roll if p_cure ≤ u < p_cure + p_roll, else stay.
- A loan in bucket ≥ 1 pays no principal that month (scheduled_principal 0, balance accrues nothing either: balance unchanged).
- Default: at the end of the month where months_in_90 reaches 6, the loan exits next month with reason defaulted.

**Prepayment (current, not in hardship).**

- base(age) = 0.004 + (0.015 − 0.004) × min(age, 30) / 30
- incentive = 3.0 if fixed and 0 ≤ period − fixed_end_month < 3; else 1 + 8 × max(0, rate − (cash_t + 0.022))
- damp = 0.5 if indexed_ltv > 0.9 else 1
- smm = min(base × incentive × damp, 0.25). Full prepay if u_prepay < smm.
- Curtailment for current, non-hardship, non-exiting loans: 0.001 × balance after scheduled principal.

**Repurchase.** Any active loan not defaulting this month: p 0.0005.

**Default loss.** loss = max(0, opening_balance − 0.80 × indexed_value), rounded to the cent.

**Clean-up call.** At the end of any month t ≥ issue_month where the deal's total closing balance ≤ 0.10 × issue_balance, every active loan exits in month t + 1 with reason called. Exit precedence in a month: called > defaulted > repurchased > prepaid.

**Balances.** Kept to the cent. closing_balance = opening_balance − scheduled_principal − curtailment for survivors, 0 for exits.

**Seed and RNG.** `numpy.random.Generator(PCG64(20261029))`. Draw order: HPI noise for all suburbs over all months (suburb order as in 4.3, months ascending), then static attributes deal by deal in deal_id order, loans in loan_id order, attribute order exactly as listed in 4.6 then seasoning (4.2), then the monthly loop.

### 4.8 Raw trustee files (the data quality traps)

Raw files are loan-month rows with static fields repeated on each row, as trustees send them. One parquet file per deal in `data/raw/trustee_a/` or `data/raw/trustee_b/`.

**Format A** (HARB, KOO, WAT), snake_case columns: `loan_id, deal_id, report_month (YYYY-MM string), submission_seq, opening_balance, scheduled_principal, curtailment, closing_balance, interest_rate, arrears_days, hardship_flag (0/1), exit_code, exit_balance, loss_amount` plus static fields `orig_month, orig_balance, orig_valuation, orig_ltv, rate_type, fixed_end_month, io_flag, io_end_month, occupancy, lmi_flag, city, state, area, suburb`. Balances in dollars, float with 2 dp. exit_code in {null, PIF, REP, DEF, CALL}.

arrears_days: bucket 0 → 0; 1 → uniform integer [1, 29]; 2 → [30, 59]; 3 → [60, 89]; 4 → 90 + 30 × (months_in_90 − 1) + uniform integer [0, 29]. These draws use a second generator `PCG64(20261030)` so they don't shift the simulation stream.

**Format B** (CST, RED), UpperCamel columns (`LoanId, DealId, ReportMonth, SubmissionSeq, OpeningBalanceCents`, and so on, every format A field renamed to UpperCamel, balances as integer cents with suffix `Cents`). Arrears as `MissedPayments` = dpd_bucket (0 to 4). Hardship as `Status` = "H", else "C" current or "A" in arrears. ExitCode in {null, P, R, D}.

Traps the canonical layer must handle:

1. **Arrears units differ** (days in A, missed payments in B).
2. **Hardship coded differently** (flag in A, status letter in B; B reports MissedPayments 0 while in hardship).
3. **Calls reported as repaid in format B.** Format B writes called exits as `P`. Format A writes `CALL`.
4. **Resubmissions.** For deal-months (D004, 2023-06), (D017, 2024-02), (D033, 2025-11) the file holds every row twice: submission_seq 1 with closing_balance and curtailment multiplied by 1.01 (rounded to the cent), and submission_seq 2 with the true values. Keep the highest seq.

---

## 5. Conventions

1. Money is AUD. Stored to the cent as DECIMAL(18,2) in DuckDB, never float.
2. Rates and ratios are stored as decimals (0.0412). Displayed as percent with 2 dp.
3. Balances displayed in AUD millions with 1 dp ("A$412.3m"). Counts displayed as integers with thousands separators.
4. Exit row: a loan's exit month has opening_balance = prior closing, closing_balance 0, exit_reason set, exit_balance = opening_balance − scheduled_principal (scheduled_principal is 0 in the exit month). indexed_ltv on the exit row uses opening_balance.
5. A loan contributes to stock metrics in a month only if closing_balance > 0.
6. Ratios across groups or deals are always ratio of sums, never average of ratios.
7. vintage_year = year of orig_month. issue_year = year of issue_month. seasoning_months = months between orig_month and period.

---

## 6. Methods

### 6.1 Canonical tables (DuckDB file `data/canonical/rmbs.duckdb`, not committed, rebuilt by `scripts/build_canonical.py`)

- `dim_deal(deal_id, deal_name, originator, originator_name, trustee_format, issue_month, issue_year, issue_balance)`
- `dim_loan(loan_id, deal_id, orig_month, vintage_year, orig_balance, orig_valuation, orig_ltv, ltv_bucket_orig, rate_type_orig, fixed_end_month, io_flag_orig, io_end_month, occupancy, lmi_flag, city, state, area, suburb)`
- `fact_loan_month(loan_id, deal_id, period, opening_balance, scheduled_principal, curtailment, closing_balance, interest_rate, dpd_bucket, hardship_flag, exit_reason, exit_balance, loss, indexed_value, indexed_ltv, ltv_bucket_indexed, seasoning_months, seasoning_bucket, rate_type, io_flag)`, where rate_type and io_flag are current status that month.
- `hpi(suburb, period, hpi)` and `cash_rate(period, rate)`, written by the generator to `data/raw/hpi.parquet` and `data/raw/cash_rate.parquet`.
- `agg_deal_month`: deal_id × period with every numerator and denominator column needed by the 12 metrics (6.3), so any deal level metric is a ratio of 2 summed columns.

### 6.2 Canonical rules

- Resubmissions: keep max submission_seq per (loan_id, period).
- dpd_bucket from A: 0 → 0; 1–29 → 1; 30–59 → 2; 60–89 → 3; ≥ 90 → 4. From B: MissedPayments directly, capped at 4.
- hardship_flag: A flag; B Status = "H". Hardship rows get dpd_bucket 0.
- exit_reason: A PIF/REP/DEF/CALL → prepaid/repurchased/defaulted/called. B P/R/D → prepaid/repurchased/defaulted.
- **Call detection (both formats):** for deal d and month t, if loans exiting with reason prepaid in t ≥ 0.95 × loans active at the end of t − 1, every prepaid exit in (d, t) becomes called. Applied to both formats, and a test proves format A's CALL months are unchanged by it.
- Buckets: ltv edges (0, 0.6], (0.6, 0.7], (0.7, 0.8], (0.8, 0.9], (0.9, ∞) labelled `<=60, 60-70, 70-80, 80-90, >90`. seasoning (months) `0-12, 13-24, 25-36, 37-60, >60` with inclusive integer ranges.

### 6.3 Metrics (`semantic/metrics.yaml`), 12 exactly

Stock metrics, per month, over rows with closing_balance > 0:

| name | numerator | denominator | display |
|---|---|---|---|
| loan_count | count(*) | none | count |
| balance_total | sum(closing_balance) | none | AUD m |
| arrears_30p_bal | sum(closing_balance) where dpd_bucket ≥ 2 and hardship_flag = 0 | sum(closing_balance) | % |
| arrears_90p_bal | same with dpd_bucket = 4 | sum(closing_balance) | % |
| arrears_90p_cnt | count where dpd_bucket = 4 and hardship_flag = 0 | count(*) | % |
| hardship_share_bal | sum(closing_balance) where hardship_flag = 1 | sum(closing_balance) | % |
| wa_orig_ltv | sum(closing_balance × orig_ltv) | sum(closing_balance) | % |
| wa_indexed_ltv | sum(closing_balance × indexed_ltv) | sum(closing_balance) | % |
| wa_rate | sum(closing_balance × interest_rate) | sum(closing_balance) | % |

Flow metrics, per month, over all rows with opening_balance > 0:

| name | numerator | denominator | display |
|---|---|---|---|
| smm_vol | sum(curtailment) + sum(exit_balance where prepaid) | sum(opening_balance − scheduled_principal) over rows whose exit_reason is null or prepaid | % |
| cpr | 1 − (1 − smm_vol)^12 | | % |
| cdr | 1 − (1 − mdr)^12, mdr = sum(exit_balance where defaulted) / sum(opening_balance) | | % |

### 6.4 Time aggregation

- `grain` month: 1 value per month.
- grain quarter or year, or shape point over a range: stock metrics take the last month in the bucket that has data. Flow metrics: smm_p = 1 − Π_m (1 − smm_m) over the months in the bucket, then cpr = 1 − (1 − smm_p)^(12 / n_months). cdr the same with mdr.
- Monthly smm and mdr for a group are computed from summed numerators and denominators first (rule 5.6), then compounded.

### 6.5 Dimensions (`semantic/dimensions.yaml`), 18 exactly

deal_id, deal_name, originator, trustee_format, issue_year, vintage_year, city, state, area, suburb, rate_type, io_flag, occupancy, lmi_flag, ltv_bucket_orig, ltv_bucket_indexed, seasoning_bucket, dpd_bucket (labels `current, 1-29, 30-59, 60-89, 90+`).

Deal level dimensions (routable to `agg_deal_month`): deal_id, deal_name, originator, trustee_format, issue_year.

### 6.6 Query spec (pydantic v2 model `QuerySpec`)

```json
{
  "intent": "answer | clarify | unsupported",
  "metrics": ["1 to 3 metric names"],
  "group_by": ["0 to 2 dimension names"],
  "filters": {"<dimension>": ["values"]},
  "time": {"grain": "month | quarter | year", "start": "YYYY-MM", "end": "YYYY-MM", "shape": "series | point"},
  "order": {"metric": "<name>", "direction": "desc | asc", "limit": 1 to 20},
  "clarify": {"question": "...", "options": ["2 to 4 options"]},
  "unsupported_reason": "..."
}
```

Rules: `order`, `clarify` and `unsupported_reason` may be null. `answer` needs metrics and time, and forbids clarify and unsupported_reason. `clarify` needs only clarify. `unsupported` needs only unsupported_reason. Default time when the question gives none: start = end = 2026-09, grain month, shape point. Start must be ≥ 2021-10, end ≤ 2026-09.

### 6.7 Compiler

`compile(spec, route: Literal["auto","fact","agg"]) -> CompiledQuery(sql_duckdb, sql_oracle, route)`. Builds the statement as a `sqlglot` tree (no string pasting of user values; values are literals in the tree). Output columns: the group_by dimensions in order, then `period_label` (YYYY-MM, YYYY-Qn or YYYY; `range` for point shape), then 1 column per metric named after it. Rows sorted by group_by then period_label, unless `order` is set. Results are returned as a pandas DataFrame with decimals converted to float only at the very end.

### 6.8 LLM layer

- Model `claude-sonnet-5-5`, temperature 0, max_tokens 1024, from config.
- Spec call: system prompt `prompts/spec_system.md` rendered with the metric and dimension catalogues (names, definitions, allowed values for every categorical dimension). 1 tool `submit_spec` whose input schema is `QuerySpec.model_json_schema()`, `tool_choice` forced.
- The prompt must say: clarify if "arrears" has no threshold; clarify if a term the catalogue doesn't define carries the meaning ("performance", "risky"); unsupported if the question needs data outside the catalogue (borrower income, LMI claims, servicer names) or asks for a forecast.
- **Entity resolution** after the spec call, on every filter value: exact match on the canonical value or an alias → keep. Else `rapidfuzz.fuzz.token_set_ratio` against all values of that dimension: unique best ≥ 90 → replace; best in [75, 90) or a tie ≥ 75 → turn the spec into `clarify` with the top 3 as options; < 75 → `unsupported` with reason "unknown <dimension> value '<v>'". Deal aliases: `"{originator_name first word} {yy}-{n}"`, `"{code} {yy}-{n}"`, `"{code}{yy}-{n}"` (for example "Harbour 21-1", "HARB 21-1", "HARB21-1").
- **Narration call:** `prompts/narrate_system.md`, inputs: question, spec JSON, result table as formatted strings (5.2, 5.3), at most 50 rows. Output at most 120 words, plain prose.
- **Cache:** key = SHA-256 of the JSON of (model, system prompt, messages, tools, tool_choice, temperature). Stored as `data/llm_cache/<key>.json` holding request and response. Modes: `replay` (default, cache miss raises `CacheMiss`) and `record`.

### 6.9 Number guard

1. Extract every number from the narration with regex `-?\d[\d,]*\.?\d*` together with an immediately following `%` or `m`.
2. Ignore numbers that appear in the question text, 4 digit years 2016 to 2026, and the parts of YYYY-MM or YYYY-Qn labels.
3. Every remaining number, with its unit, must equal a display string in the formatted result table. Commas are ignored when comparing.
4. On any failure, the narration is replaced by the template answer (`rmbsq/llm/narrate.py::template_answer`), and the trip is logged with the offending number.

### 6.10 Baseline

`prompts/baseline_system.md` holds the canonical DDL with a comment on every column, the written metric definitions from 6.3 and 6.4 in prose, and the instruction to return DuckDB SQL whose result columns are named exactly as given. Tool `submit_sql` with `{"sql": string}`. The SQL runs on a read-only DuckDB connection with a 30 second timeout. Errors score as wrong. The baseline cannot clarify or decline, so it scores wrong on those categories unless it returns an empty SQL string, which counts as a decline.

### 6.11 Eval

- `eval/questions.yaml`, 40 items supplied by chat Claude in instruction 05: simple 10, grouped 10, time 6, trap 8, ambiguous 4, unsupported 2.
- Each trap item also carries `trap`: one of `arrears_units, hardship, call_as_prepay, resubmission`, 2 items per trap.
- Each answerable item has `gold_spec`, an independently written `gold_sql`, and `output_columns`. A test asserts compile(gold_spec) equals gold_sql to abs 1e-9 on every value.
- Correct (answer items): same row keys, and every value within abs 1e-6 for ratios and LTVs, rel 1e-6 for balances, exact for counts.
- Correct (ambiguous items): intent clarify. Correct (unsupported items): intent unsupported.
- Report accuracy per category and total, each with a Wilson 95% interval, plus per question latency, input and output tokens, and guard trips.

### 6.12 Scale benchmark

- Build `data/canonical/rmbs_x36.duckdb` (not committed) by copying `fact_loan_month` and `dim_loan` 36 times, with copy c (0 to 35) prefixing every loan_id and deal_id with `C{cc}-` and `dim_deal` copied the same way. `agg_deal_month` is rebuilt from the tiled fact.
- Run every answerable gold spec from the eval through `compile` and `execute` on both the 1x and 36x databases, on route `auto` and route `fact`, 5 timed repeats after 1 untimed warm-up, single thread (`SET threads = 1`) and default threads, wall clock with `time.perf_counter`.
- Report median and max seconds per spec, route and thread setting, plus the row count of each database.
- This measures DuckDB on 1 machine. The write-up states that Oracle timings depend on partitioning and indexes and were not measured.

---

## 7. Signatures and schemas

```python
# rmbsq/config.py
def load_config(path: Path = Path("config.toml")) -> Config

# rmbsq/synth
def build_geography(cfg) -> pd.DataFrame                       # city, state, area, beta, suburb
def build_cash_rate(cfg) -> pd.DataFrame                       # period, rate
def build_hpi(cfg, geo, rng) -> pd.DataFrame                   # suburb, period, hpi
def draw_loans(cfg, geo, cash, rng) -> pd.DataFrame            # static attributes, one row per loan
def simulate(cfg, loans, cash, hpi, rng) -> pd.DataFrame       # true loan-month panel incl. months_in_90
def write_trustee_files(cfg, panel, loans, out_dir: Path, rng_aux) -> dict[str, str]  # path -> sha256
def generate(cfg, profile: str, out_dir: Path) -> None         # runs all of the above

# rmbsq/canonical
def ingest_format_a(path: Path) -> pd.DataFrame
def ingest_format_b(path: Path) -> pd.DataFrame
def dedupe_resubmissions(df) -> pd.DataFrame
def detect_calls(df) -> pd.DataFrame
def enrich(df, hpi, cfg) -> pd.DataFrame
def build_canonical(raw_dir: Path, db_path: Path, cfg) -> None

# rmbsq/semantic
def load_catalog(metrics_yaml: Path, dims_yaml: Path) -> Catalog
class QuerySpec(BaseModel): ...
def compile(spec: QuerySpec, catalog: Catalog, route: str = "auto") -> CompiledQuery
def execute(compiled: CompiledQuery, con: duckdb.DuckDBPyConnection) -> pd.DataFrame
def format_table(df: pd.DataFrame, catalog: Catalog) -> pd.DataFrame   # display strings

# rmbsq/llm
class LLMClient: def __init__(self, cfg, mode: str = "replay"); def call(self, system, messages, tools, tool_choice) -> dict
def resolve_entities(spec, catalog, aliases) -> QuerySpec
def question_to_spec(question: str, client, catalog) -> QuerySpec
def narrate(question, spec, table, client) -> tuple[str, bool]          # text, guard_tripped
def number_guard(text: str, question: str, table) -> list[str]          # offending numbers, empty if pass
def template_answer(spec, table) -> str
def baseline_sql(question: str, output_columns: list[str], client) -> str
def answer(question: str, client, con, catalog) -> Answer               # spec, sql, table, text

# rmbsq/eval
def load_items(path: Path) -> list[EvalItem]
def run_system(items, client, con, catalog) -> pd.DataFrame
def run_baseline(items, client, con) -> pd.DataFrame
def score(results: pd.DataFrame, items) -> pd.DataFrame
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]
def build_tiled_db(src: Path, dst: Path, copies: int) -> None
def run_benchmark(items, src_db: Path, tiled_db: Path, cfg) -> pd.DataFrame

# rmbsq/deliverable
def load_claims(path: Path) -> dict[str, str]                 # claim_id -> display string, every value read from a committed CSV
def render_markdown(template: Path, claims: dict) -> str      # fills {{claim_id}} placeholders; an unknown id raises
def build_pdf(markdown_text: str, figures: list[Path], out: Path) -> None   # reportlab Platypus, A4
def build_onepager(cfg, out: Path) -> None
```

Output tables:

- `outputs/eval_results.csv`: `system, item_id, category, intent, correct, n_values_checked, max_abs_err, latency_s, input_tokens, output_tokens, guard_tripped, error`
- `outputs/eval_summary.csv`: `system, category, n, k, accuracy, wilson_lo, wilson_hi` (category `total` included)
- `outputs/pool_monthly.csv`: `period, arrears_30p_bal, arrears_90p_bal, hardship_share_bal, cpr, cdr, wa_indexed_ltv, balance_total` for the whole pool
- `outputs/figures/`: `eval_accuracy.png`, `arrears_90p_by_vintage.png`, `cpr_by_city.png`
- `outputs/transcripts/`: `01_answer.md`, `02_clarify.md`, `03_unsupported.md`, each with question, spec JSON, Oracle SQL, result table and narration
- `outputs/scale_benchmark.csv`: `item_id, db (1x or 36x), db_rows, route, threads, median_s, max_s`
- `outputs/trap_failures.csv`: `system, item_id, trap (arrears_units, hardship, call_as_prepay, resubmission), expected, got`, 1 row per wrong trap answer, built from the eval results
- `deliverable/claims.csv`: `claim_id, value, source_file, source_row_filter` (every number used in either PDF)
- `deliverable/Design_Response.pdf` and `deliverable/Results_Summary.pdf` (Section 7)

---

## 8. `config.toml`

```toml
[project]
seed = 20261029
seed_aux = 20261030

[calendar]
sim_start = "2016-01"
window_start = "2021-10"
window_end = "2026-09"
latest = "2026-09"

[deals]
n_deals = 50
loans_per_deal = 500
first_issue = "2019-01"
issue_span_months = 60
seasoning_min = 6
seasoning_max = 36
call_threshold = 0.10
call_detect_share = 0.95

[profiles.full]
n_deals = 50
loans_per_deal = 500

[profiles.small]
n_deals = 10
loans_per_deal = 40

[loans]
balance_median = 520000
balance_sigma = 0.45
balance_min = 100000
balance_max = 2500000
ltv_floor = 0.35
ltv_scale = 0.6
ltv_beta_a = 4.0
ltv_beta_b = 2.2
ltv_cap = 0.95
lmi_ltv = 0.80
p_investor = 0.30
p_io_investor = 0.40
p_io_owner = 0.15
io_term = 60
p_fixed_pre2020 = 0.15
p_fixed_2020_2022 = 0.40
p_fixed_post2022 = 0.10
fixed_terms = [24, 36]
margin_mean = 0.026
margin_sd = 0.004
margin_min = 0.018
margin_max = 0.038
margin_investor = 0.003
margin_io = 0.004
fixed_spread_mean = 0.019
fixed_spread_sd = 0.003
fixed_rate_min = 0.015
fixed_rate_max = 0.06
term = 360

[loans.city_mult]
Sydney = 1.25
Melbourne = 1.05
Brisbane = 0.95
Perth = 0.85
Adelaide = 0.85

[hpi]
noise_phi = 0.8
noise_sd = 0.004
base = 100.0

[behaviour]
p_hardship = 0.002
hardship_min = 3
hardship_max = 6
a0 = -5.52
a_shock = 3.0
a_ltv = 4.0
ltv_knot = 0.8
a_investor = 0.3
a_io_recent = 0.5
io_recent_months = 12
p_cure = [0.55, 0.30, 0.15]
p_roll = [0.25, 0.40, 0.55]
roll_shock = 1.5
p_cure_90 = 0.05
default_after_90_months = 6
smm_start = 0.004
smm_flat = 0.015
smm_ramp_months = 30
fixed_cliff_mult = 3.0
fixed_cliff_months = 3
refi_spread = 0.022
refi_slope = 8.0
damp_ltv = 0.9
damp_mult = 0.5
smm_cap = 0.25
curtailment = 0.001
p_repurchase = 0.0005
sale_haircut = 0.80

[calibration]
rows_min = 700000
rows_max = 1600000
arrears_90p_min = 0.002
arrears_90p_max = 0.025
arrears_peak_from = "2023-06"
arrears_peak_to = "2025-06"
cpr12_min = 0.08
cpr12_max = 0.35
fixed_cliff_ratio_min = 2.0
min_deals_called = 3

[resubmissions]
deal_months = [["D004", "2023-06"], ["D017", "2024-02"], ["D033", "2025-11"]]
inflate = 1.01

[resolve]
accept = 90
clarify = 75
top_k = 3

[llm]
model = "claude-sonnet-5-5"
temperature = 0
max_tokens = 1024
narration_max_words = 120
narration_max_rows = 50
baseline_timeout_s = 30

[eval]
tol_ratio_abs = 1e-6
tol_balance_rel = 1e-6
gold_tol_abs = 1e-9
wilson_z = 1.96

[benchmark]
copies = 36
repeats = 5
warmup = 1
thread_settings = [1, 0]   # 0 means DuckDB default

[deliverable]
page_size = "A4"
design_max_pages = 4
summary_max_pages = 1
font = "Helvetica"
```

Cash rate steps, HPI drifts, geography and originators are tables, so they live in `config/` as CSV files committed in session 0, with exactly the values in 4.2 to 4.5: `config/originators.csv`, `config/geography.csv`, `config/cash_rate.csv`, `config/hpi_drift.csv`.

---

## 9. Sections

Each step names its file, tests and outputs. Session N = Section N.

### Section 1: synthetic data generator

- 1.1 `rmbsq/config.py`, `config/*.csv` loaders. Test: config round trip, CSV values equal 4.2 to 4.5.
- 1.2 `rmbsq/synth/geography.py`, `rates.py`, `hpi.py`. Tests: 60 suburbs; cash rate at 2022-05 = 0.0035 and 2026-09 = 0.036; HPI deterministic for a fixed seed; Sydney area log HPI change 2022-04 to 2023-01 within 0.5 pp of beta × sum of drifts when noise is set to 0.
- 1.3 `rmbsq/synth/loans.py`. Tests: 500 loans per deal; LTV in [0.35, 0.95]; lmi_flag iff LTV > 0.80; fixed share by origination era within 3 pp of config on the full profile.
- 1.4 `rmbsq/synth/simulate.py`. Tests on hand-built 1 loan cases: P&I annuity matches `numpy_financial.pmt` to the cent; IO switch at io_end_month; fixed to variable switch; hardship freezes dpd; default after 6 months at 90+; call triggers at ≤ 10%; every deal has exactly 500 loans at issue.
- 1.5 `rmbsq/synth/trustee_formats.py`. Tests: format A arrears_days inside its bucket range; format B cents are integers; called exits written as P in format B and CALL in A; resubmission rows present for exactly the 3 deal-months.
- 1.6 `scripts/generate_data.py --profile full`, writes `data/raw/` and `MANIFEST.json`. Calibration test (reads the full profile once, marked `calibration`, run in this session and in CI): every band in `[calibration]`. If a band fails, stop per rule 4 and report the measured value. Do not tune parameters.
- Outputs: `data/raw/**`, `outputs/pool_monthly_truth.csv` (pool metrics from the true panel, used in Section 2 as a cross check).

### Section 2: canonical layer

- 2.1 `rmbsq/canonical/ingest.py`. Tests: both formats map to the same canonical columns and dtypes.
- 2.2 `dedupe_resubmissions`. Test: the 3 deal-months have 1 row per loan and true values.
- 2.3 `detect_calls`. Tests: format B calls recovered and equal the true panel's called exits; format A unchanged.
- 2.4 `enrich` (indexed value and LTV, buckets, current rate_type and io_flag, seasoning). Test: indexed_ltv recomputed by hand for 5 named rows.
- 2.5 `build_canonical`, `agg_deal_month`. Tests: canonical pool monthly metrics equal `outputs/pool_monthly_truth.csv` to 1e-9; `agg_deal_month` sums equal fact sums.
- Outputs: `outputs/pool_monthly.csv`, `outputs/canonical_row_counts.csv`.

### Section 3: semantic layer and compiler

- 3.1 `semantic/metrics.yaml`, `semantic/dimensions.yaml`, `rmbsq/semantic/catalog.py`. Test: exactly 12 metrics and 18 dimensions; allowed values loaded from the canonical DB.
- 3.2 `rmbsq/semantic/spec.py` (`QuerySpec` with the 6.6 rules). Tests: valid and invalid examples supplied in instruction 03.
- 3.3 `rmbsq/semantic/compiler.py` and `timeagg.py`. Tests: 15 test specs with hand-written SQL supplied in instruction 03, equal to 1e-9; quarter compounding hand example.
- 3.4 Routing. Test: every deal level test spec gives equal results on `fact` and `agg` routes.
- 3.5 Oracle rendering. Test: every test spec renders to Oracle with no `sqlglot` warning.
- 3.6 `format_table`. Test: display rules 5.2 and 5.3.

### Section 4: LLM layer

- 4.1 `rmbsq/llm/client.py` cache. Tests: key stability; replay hit; replay miss raises; sockets disabled in replay.
- 4.2 `prompts/spec_system.md`, `rmbsq/llm/spec_agent.py`. Test: rendered prompt contains every metric and dimension name; fixture cached responses parse into `QuerySpec`.
- 4.3 `rmbsq/llm/resolve.py`. Tests: aliases; score bands; tie handling.
- 4.4 `prompts/narrate_system.md`, `narrate.py`, `guard.py`. Tests: guard cases supplied in instruction 04, including a passing answer and 1 hallucinated figure.
- 4.5 `rmbsq/llm/baseline.py`, `prompts/baseline_system.md`. Test: read-only connection rejects writes; timeout enforced.
- 4.6 `rmbsq/cli.py`: `rmbsq ask "<question>" [--live] [--show-sql]`. Test: replay run of 1 cached question end to end.
- Live calls are not made in this section. Fixture cache files for tests are hand-written JSON in `tests/fixtures/llm_cache/`.

### Section 5: eval

- 5.1 `eval/questions.yaml` exactly as given in instruction 05. Test: 40 items, category counts as 6.11.
- 5.2 Gold check. Test: compile(gold_spec) equals gold_sql to 1e-9 for every answerable item.
- 5.3 `rmbsq/eval/run.py`, `score.py`, `report.py`. Tests: scoring on synthetic result frames; Wilson interval against hand values for (7, 10) and (40, 40).
- 5.4 `scripts/run_eval_live.py` records to `data/llm_cache/` and writes `outputs/eval_results.csv` and `outputs/eval_summary.csv`. If `ANTHROPIC_API_KEY` is missing, this is a stop condition: finish 5.1 to 5.3 and 5.5's code, then stop and report.
- 5.5 Replay test: re-running the eval from the committed cache reproduces both CSVs exactly, comparing every column except `latency_s`, which is wall clock and differs run to run.
- 5.6 `outputs/trap_failures.csv` from the eval results. Test: row count equals the number of wrong trap answers in `eval_results.csv`.
- 5.7 `rmbsq/eval/benchmark.py`, `scripts/run_benchmark.py` (6.12). Test on the small profile: tiled row count = copies × source rows; tiled results for a pool level spec equal the 1x results (ratios unchanged by tiling, totals × copies). Output `outputs/scale_benchmark.csv`, timings excluded from any byte check.

### Section 6: repo write-up

- 6.1 Figures (4) from the CSVs, synthetic data stated on each chart: the 3 listed under "Output tables" in part 7 of this file plus `scale_benchmark.png` (median seconds per spec, 1x vs 36x).
- 6.2 Transcripts (3) from cached runs of the questions named in instruction 06.
- 6.3 `docs/DESIGN_NOTE.md`, at most 1,100 words, structure given in instruction 06. This is the technical note for repo readers.
- 6.4 `README.md`: 1 paragraph summary, mermaid architecture diagram, headline eval table generated from `eval_summary.csv`, the scale result, limitations, how to run. Test: README numbers match the CSVs.
- 6.5 `.github/workflows/ci.yml` running the suite offline on push, plus the calibration test.

### Section 7: send pack (`deliverable/`)

The 2 PDFs a reader opens first. Text and structure are supplied in instruction 07 as templates with `{{claim_id}}` placeholders. Claude Code writes no prose of its own in this section.

- 7.1 `rmbsq/deliverable/claims.py` and `deliverable/claims.csv`: every number either PDF uses, each traced to a source CSV and row filter. Test: every claim recomputes from its source and matches its display string.
- 7.2 `deliverable/design_response.md.tmpl` (from instruction 07) rendered to `deliverable/design_response.md`. This is the written answer to the design question at production scale (300 deals, 2,000 loans each, 5 years, Oracle), with the prototype as evidence. At most 4 A4 pages. Test: no unresolved placeholders; every number in the rendered text appears in `claims.csv` (same guard logic as 6.9, applied to the document).
- 7.3 `deliverable/results_summary.md.tmpl` rendered to `deliverable/results_summary.md`: headline eval table (governed vs baseline, Wilson intervals), `eval_accuracy.png`, the trap failure table, the scale result, and the clarify transcript. Exactly 1 A4 page.
- 7.4 `rmbsq/deliverable/pdf.py` builds both PDFs with reportlab. Tests: page counts within `[deliverable]` limits (read back with pypdf); every embedded figure file exists; the extracted PDF text contains every claim display string; building twice gives identical page text.
- 7.5 Neutrality check. Test: a grep over the whole repo (excluding `instructions/`) for a word list supplied in instruction 07 finds nothing.
- 7.6 Fresh-clone check regenerates both PDFs from committed CSVs with no network and no API key.

---

## 10. What session 0 must produce

1. Read `WORKFLOW.md` from the repo root. Do not edit it.
2. `PLAN.md`: 1 paragraph per step in Section 9 (Sections 1 to 7), with file, signatures, tests by name, outputs and review evidence. No added or removed steps. Anything unspecified marked open and raised in the status file.
3. `CLAUDE.md` with the Part 4 rules, amended by 1.3, 1.4, 1.6, 1.7 and 1.8 of this file.
4. `config.toml` exactly as Section 8, and the 4 CSVs in `config/` exactly as 4.2 to 4.5.
5. `.gitattributes` (`* text=auto eol=lf`), `.gitignore` (venv, `data/canonical/`, caches), `pyproject.toml`, `requirements-lock.txt` with pinned versions of: duckdb, pandas, numpy, pyarrow, pydantic, sqlglot, rapidfuzz, anthropic, pyyaml, matplotlib, numpy-financial, reportlab, pypdf, pytest, pytest-socket. Keep the `.gitattributes` already committed.
6. `review/TEMPLATE.md`, `decisions/OPEN.md` (empty), `docs/CONVENTIONS_RESOLVED.md`.
7. Package skeleton (`rmbsq/` with the subpackages `synth, canonical, semantic, llm, eval, deliverable`, empty modules with docstrings), empty `deliverable/` folder with a `.gitkeep`, `tests/test_placeholder.py`.
8. `instructions/00_kickoff.status.md`, then push.

No real code in session 0.
