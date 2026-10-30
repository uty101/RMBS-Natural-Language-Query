# 01 Section 1: synthetic data generator

Session 1 instructions for Claude Code. Build all of Section 1 (steps 1.1 to 1.6) in this session, without pausing. This file beats `PLAN.md`, which beats the kickoff (rule 13). Status file: `instructions/01_section_1.status.md`.

---

## A. Approval of session 0

Session 0 is approved. Chat Claude checked it independently:

- `config.toml` is byte-identical to kickoff part 8 (extracted from the kickoff and compared in Python).
- The 4 `config/*.csv` tables hold exactly the values in kickoff 4.2 to 4.5, all 24 cash rate steps and all 8 HPI regimes included.
- `requirements-lock.txt` installs on Linux with Python 3.12 through `uv pip sync`. The suite gives 7 passed with sockets disabled.
- All 49 tracked text files are LF.

The 3 table layouts (F2, F3, F4 in `docs/CONVENTIONS_RESOLVED.md`) are confirmed as built.

---

## B. Decisions on the open questions

Every O-item from `instructions/00_kickoff.status.md` is decided here, including the ones for later sections, so `PLAN.md` and `docs/CONVENTIONS_RESOLVED.md` can be updated once (step 1.0 below).

**Process**

- **O-1: (a).** Commit `CLAUDE.md` and `PLAN.md` in step 1.0. From now on, both are committed whenever an instruction changes them. If Claude Code's own safety check refuses to edit `CLAUDE.md`, commit `PLAN.md` alone and say so in the status file. The user then commits `CLAUDE.md`.
- **O-2: (b).** The 7.5 neutrality grep excludes `instructions/` and `.github/`. Instruction 07 also keeps workflow keywords out of its word list.
- **O-3: (b), extended.** Module homes:
  - `build_deals(cfg, n_deals) -> pd.DataFrame` in `rmbsq/synth/deals.py`;
  - `generate` in `rmbsq/synth/generate.py`;
  - `dedupe_resubmissions`, `detect_calls`, `enrich`, `build_canonical` in `rmbsq/canonical/build.py`;
  - `CompiledQuery` and `execute` in `rmbsq/semantic/compiler.py`;
  - `Catalog` in `rmbsq/semantic/catalog.py`;
  - `format_table` in `rmbsq/semantic/format.py`;
  - `answer` and `Answer` in `rmbsq/llm/answer.py`;
  - `load_items` and `EvalItem` in `rmbsq/eval/run.py`;
  - `build_trap_failures` in `rmbsq/eval/report.py`;
  - `render_markdown` in `rmbsq/deliverable/render.py`;
  - figures in `scripts/make_figures.py`;
  - config table loaders in `rmbsq/config.py`: `load_originators`, `load_geography`, `load_cash_steps`, `load_hpi_drift`, each `(path: Path) -> pd.DataFrame`.
- **O-4: (a).** `[project.scripts] rmbsq = "rmbsq.cli:main"`, installed with `uv pip install -e . --no-deps`.
- **O-5: (a), with a renamed marker.** Replace the `calibration` marker with `full`. It covers every test that reads or regenerates the full profile: the calibration test and the full regeneration test (step 1.6), plus the gold check (5.2) and the replay test (5.5) later. `addopts` gains `-m "not full"`. The review and CI run `pytest -m full` as a second command.
- **O-33: (a).** Neither `scripts/run_all.py` nor `docs/METHODS.md` is built. Section 7 has its own regeneration check.

**Section 1**

- **O-6: (a).** Part D gives the exact sequence of `rng` calls.
- **O-7: (b).** 128 noise draws per suburb, for months 2016-02 to 2026-09. e for 2016-01 is 0 and HPI for 2016-01 is 100.
- **O-8: (a).** The change runs from log HPI(2022-03) to log HPI(2023-01), which is 10 months of drift.
- **O-9: (a).** Part E gives the month loop as ordered pseudo-code.
- **O-10: (a).** The issue formula uses each profile's own n_deals. Resubmissions apply only to listed deal-months whose deal exists and whose month is in the emitted rows (D004 2023-06 in the small profile).
- **O-11: (a).** Part F gives every calibration statistic as a formula.
- **O-12: (a).** Part G gives both trustee schemas in full.

**Section 2**

- **O-13: (a).** `pool_monthly_truth.csv` has the columns of `pool_monthly.csv`. Test 2.5 compares truth and canonical on the small profile in a temp folder. A second test, marked `full`, compares the committed full truth CSV with the canonical layer built from the committed full raw data.
- **O-14: (b).** Columns are `table, trustee_format, rows`, with trustee_format `all` for tables that are not split by format.
- **O-27: (a).** Integer cents (`Int64`), cast to DECIMAL(18,2) on insert.
- **O-28: (b) plus a property check.** Test 2.3 uses a constructed frame with a known call month. It also asserts on the small profile that the recovered format B calls equal the true panel's called exits. The small profile has at least 1 called format B deal in the reference run; if it has none, the second assertion fails loudly rather than passing vacuously.
- **O-29: (b).** The 5 rows are the first loan_id of each originator, at the latest period where that loan has a row with closing_balance > 0, in the small profile.

**Section 3**

- **O-15: (a).** Use the Section 7 signature, `compile(spec, catalog, route="auto")`.
- **O-16: (b).** When start equals end, the label is that month (`2026-09`). Otherwise point shape uses `range`.
- **O-17: (a).** n_months is the months with data for that group, and "last month with data" is per group.
- **O-18: (a).** `rate_type` and `io_flag` are the current status that month, read from `fact_loan_month`.
- **O-30: (b).** Metric keys are `name, kind, numerator, denominator, display, definition`. Dimension keys are `name, column, table, level, labels, definition`.

**Section 4**

- **O-19: (a), done by stripping first.** Before extracting numbers, the guard removes:
  - every dimension label in the catalogue (`30-59`, `60-70`, `<=60`, `>90`, `0-12`, `>60` and the rest);
  - every YYYY-MM and YYYY-Qn token;
  - every deal_name.

  It does this longest match first, then runs the 6.9 regex on what is left.
- **O-20: (a).**
  - Exact matching is case-insensitive.
  - Fuzzy matching applies to the text dimensions only: deal_name, originator, trustee_format, city, state, area, suburb, rate_type, occupancy.
  - Numeric and flag dimensions match exactly or go to `unsupported`.
  - An alias resolves to its deal_name. If a deal_id filter value is not a deal_id but matches a deal_name or an alias, the filter key is rewritten to deal_name.
- **O-26: (a).** Tests pass a modified copy of `Config` built with `dataclasses.replace` or the model's copy method. Where a path can't be forced to certainty, the test checks a property of every realised path instead (part H, step 1.4).

**Section 5**

- **O-21: (b).** An empty baseline SQL string counts as correct only on unsupported items.
- **O-22: (a).** Order must match for items with `order` set. Otherwise row keys are compared as a set.
- **O-23: (a).** Prefix deal_name too (`C07-HARB 2021-1`). Deal-filtered specs are rewritten to copy `C00-` on the 36x database.
- **O-31: (a).** Both are marked `full`.

**Section 6**

- **O-24: (a), plus a regeneration check.** CI reads the committed `data/raw/`. The `full` regeneration test (step 1.6) also proves the generator reproduces `MANIFEST.json`.
- **O-25: (a).** Review evidence only, except 6.5, where the evidence is the link to the green Actions run.
- **O-32: (a).** Add `outputs/arrears_90p_by_vintage.csv` and `outputs/cpr_by_city.csv`, built through `compile` from governed specs.

---

## C. Config amendments (step 1.0)

Chat Claude ran an independent implementation of parts D and E on the full profile before writing this file. With the kickoff's own parameters, step 1.6 would have stopped on 3 problems:

1. **No deal was ever called,** against a band of at least 3. The oldest deals still had a pool factor of about 0.29 at 2026-09.
2. **90+ arrears never peaked.** They kept rising to 2.96%, because the payment shock was measured against the origination payment and rates never returned to their 2021 level.
3. **CDR averaged about 3% a year,** roughly 10 times a realistic level for Australian prime.

Make exactly these changes to `config.toml`:

```toml
[deals]
call_threshold = 0.25          # was 0.10

[behaviour]
a0 = -6.0                      # was -5.52
p_cure_90 = 0.10               # was 0.05
default_after_90_months = 9    # was 6
shock_lookback_months = 12     # new key, after roll_shock

[calibration]
arrears_90p_min = 0.001        # was 0.002
min_b_deals_called = 3         # new key, after min_deals_called
```

Add a comment above `call_threshold`: `# stylised clean-up call at 25% of issue balance (instruction 01 C)`.

The payment shock now uses the 12-month lookback in part E.3.

The measured result, with these values and parts D to G followed exactly:

| statistic (part F) | chat Claude's value | band |
|---|---|---|
| emitted rows | 781,909 | [700,000, 1,600,000] |
| arrears_90p_bal, min and max over the window | 0.197% and 1.757% | [0.1%, 2.5%] |
| arrears peak month | 2024-06 | [2023-06, 2025-06] |
| cpr12, min and max | 16.25% and 17.57% | [8%, 35%] |
| fixed cliff ratio | 2.52 | ≥ 2.0 |
| deals called | 16 | ≥ 3 |
| format B deals called | 6 (D004, D005, D009, D010, D015, D020) | ≥ 3 |
| exits by reason | prepaid 11,217, called 2,429, defaulted 457, repurchased 369 | none |
| small profile rows and called deals | 12,570 and 3 | none |

These are reference values, not targets. Put your own values next to them in the review. Never tune a parameter toward them. Small differences can come from float order; anything beyond about 1% on a count, or a different list of called deals, needs a sentence in the review explaining which rule you think differs.

---

## D. Static draws (`rmbsq/synth/hpi.py`, `rmbsq/synth/loans.py`)

One generator, `rng = numpy.random.Generator(numpy.random.PCG64(cfg.project.seed))`, is used in exactly this order and for nothing else.

**D.1 HPI noise (once).** `z = rng.standard_normal((60, 128))`. Rows are suburbs in geography order (city order of 4.3, areas in listed order, then North, Central, South). Columns are months 2016-02 to 2026-09.

- e[s, 2016-01] = 0
- e[s, t] = noise_phi × e[s, t − 1] + noise_sd × z[s, t − 1]
- r[s, t] = beta_area × drift_city,t / 100 + e[s, t] − e[s, t − 1] for t ≥ 2016-02
- HPI[s, 2016-01] = 100 and HPI[s, t] = HPI[s, t − 1] × exp(r[s, t])

The drift for month t is the regime row with from ≤ t ≤ to.

**D.2 Deals (no draws).** `build_deals`:

- issue_month(k) = first_issue + floor((k − 1) × issue_span_months / n_deals);
- originator = codes[(k − 1) mod 5];
- deal_name = `"{code} {issue_year}-{n}"`, with n counting that originator's deals in that issue year in deal_id order, from 1.

**D.3 Loans, deal by deal in deal_id order.** Each draw is 1 array of length n = loans_per_deal, in exactly this order:

1. `seasoning = rng.integers(seasoning_min, seasoning_max + 1, n)`
2. `u_city = rng.random(n)`. city index = `min(searchsorted(cumsum(city weights), u_city, side="right"), 4)`, with weights in city order.
3. `area = rng.integers(0, 4, n)`
4. `suburb = rng.integers(0, 3, n)` (0 North, 1 Central, 2 South)
5. `z_bal = rng.standard_normal(n)`
6. `b_ltv = rng.beta(ltv_beta_a, ltv_beta_b, n)`
7. `u_inv = rng.random(n)`. investor if `u_inv < p_investor`.
8. `u_io = rng.random(n)`. io_flag if `u_io < (p_io_investor if investor else p_io_owner)`.
9. `u_fix = rng.random(n)`. fixed if `u_fix < p_fixed(era of orig_month)`. Eras: before 2020-01; 2020-01 to 2022-03 inclusive; after.
10. `u_term = rng.random(n)`. fixed_term = 24 if `u_term < 0.5` else 36.
11. `z_margin = rng.standard_normal(n)`
12. `z_fixed = rng.standard_normal(n)`

Every array is drawn for every loan, and then masked. Derived fields:

- orig_month = issue_month − seasoning;
- orig_balance = round(clip(exp(ln(balance_median × city_mult) + balance_sigma × z_bal), balance_min, balance_max)) to the whole dollar;
- orig_ltv = min(ltv_floor + ltv_scale × b_ltv, ltv_cap), kept at full float precision;
- orig_valuation = round(orig_balance / orig_ltv) to the whole dollar;
- lmi_flag = orig_ltv > lmi_ltv;
- io_end_month = orig_month + io_term for IO loans, null otherwise;
- fixed_end_month = orig_month + fixed_term for fixed loans, null otherwise;
- margin = clip(margin_mean + margin_sd × z_margin, margin_min, margin_max) + margin_investor × investor + margin_io × io_flag;
- fixed_rate = clip(cash(orig_month) + fixed_spread_mean + fixed_spread_sd × z_fixed, fixed_rate_min, fixed_rate_max) for fixed loans, null otherwise;
- loan_id = `"{deal_id}-{nnnn}"`.

The global loan order is deal_id, then loan number. That equals sorting by loan_id, and every monthly array in part E uses it.

---

## E. The month loop (`rmbsq/synth/simulate.py`)

Months run from 2016-02 to 2026-09. A loan is **live** in month t if orig_month < t and it hasn't exited before t. In orig_month itself it exists with closing_balance = orig_balance, state current, and gets no draws and no row.

State per loan:

- closing_balance;
- bucket (0 to 4);
- months_in_90;
- hardship_remaining;
- default_flag;
- payment history (the payment computed each live month).

State per deal: call_flag and issue_balance.

**E.1 Origination payment.** payment_orig is the payment at orig_month on orig_balance, at the loan's rate in orig_month, with age 1. It is interest only if the loan is IO. It is stored as the payment history entry for orig_month.

**Payment function.** For a balance B, rate r, age a and month t:

- interest only if io_flag and t < io_end_month: B × r / 12;
- otherwise the annuity B × i / (1 − (1 + i)^(−n)), with i = r / 12 and n = term − a + 1.

**Rate.** If fixed and t < fixed_end_month, the rate is fixed_rate. Otherwise it is cash(t) + margin.

For each month t, in this order:

1. **Live set.** live = loans with orig_month < t that haven't exited. Order them by loan_id.
2. **Issue reset.** For live loans whose deal has issue_month = t, set:
   - bucket 0;
   - months_in_90 0;
   - hardship_remaining 0;
   - default_flag false.
3. **Draws.** In this order, each of length len(live): `u_h = rng.random(n)`, `u_t = rng.random(n)`, `u_p = rng.random(n)`, `u_r = rng.random(n)`. These are drawn for every live loan, including loans before their deal's issue month and loans already flagged to exit.
4. **Month quantities**, from opening_balance = the previous closing_balance:
   - age = t − orig_month
   - rate = rate(t)
   - payment = payment(opening_balance, rate, age, t), stored in the payment history
   - lookback month m = t − shock_lookback_months. reference payment = payment_orig if m ≤ orig_month, else the stored payment for month m
   - shock = max(payment / reference − 1, 0)
   - indexed_value = orig_valuation × HPI(suburb, t) / HPI(suburb, orig_month)
   - ltv_open = opening_balance / indexed_value
   - scheduled = 0 if interest only this month, else min(payment − opening_balance × rate / 12, opening_balance)
5. **Hardship entry.** A live loan with bucket 0 and hardship_remaining 0 enters if u_h < p_hardship. It then gets hardship_remaining = hardship_min + floor((hardship_max − hardship_min + 1) × u_h / p_hardship). in_hardship = hardship_remaining > 0. This includes loans that entered this month.
6. **Transitions,** for live loans not in hardship. Use u_t and the bucket at the start of the month:
   - from 0: to 1 if u_t < logistic(a0 + a_shock × shock + a_ltv × max(ltv_open − ltv_knot, 0) + a_investor × investor + a_io_recent × io_recent), where io_recent = io_flag and 0 ≤ t − io_end_month < io_recent_months;
   - from k in 1 to 3: p_roll_eff = min(p_roll[k] × exp(roll_shock × shock), 0.95 − p_cure[k]). To 0 if u_t < p_cure[k]. To k + 1 if p_cure[k] ≤ u_t < p_cure[k] + p_roll_eff. Else stay;
   - from 4: to 0 if u_t < p_cure_90. Else stay.

   Loans in hardship keep their bucket. Then months_in_90 = months_in_90 + 1 if the new bucket is 4, else 0.
7. **Exits.** Let pre = t < issue_month of the loan's deal. Exits are suppressed when pre is true. Otherwise, in precedence order:
   - **called:** the deal's call_flag is true;
   - **defaulted:** default_flag is true;
   - **repurchased:** u_r < p_repurchase;
   - **prepaid:** the loan is not in hardship, its new bucket is 0, and u_p < smm. Here:
     - smm = min(base × incentive × damp, smm_cap);
     - base = smm_start + (smm_flat − smm_start) × min(age, smm_ramp_months) / smm_ramp_months;
     - incentive = fixed_cliff_mult if fixed and 0 ≤ t − fixed_end_month < fixed_cliff_months, else 1 + refi_slope × max(0, rate − (cash(t) + refi_spread));
     - damp = damp_mult if ltv_open > damp_ltv, else 1.

   A loan takes the first reason that applies.
8. **Cash flows,** all rounded to the cent with Python's round-half-even through `numpy.round(x, 2)`:
   - payer = live, not exiting, not in hardship, new bucket 0;
   - scheduled_principal = round(scheduled, 2) for payers, else 0;
   - curtailment = round(curtailment × (opening_balance − scheduled_principal), 2) for payers, else 0;
   - closing_balance = round(opening_balance − scheduled_principal − curtailment, 2) for live loans that don't exit. It is unchanged for loans in arrears or hardship, because nothing accrues. It is 0 for exits;
   - exit_balance = opening_balance on the exit row (scheduled_principal is 0 there);
   - loss = round(max(0, opening_balance − sale_haircut × indexed_value), 2) for defaulted exits, else 0.
9. **End-of-month flags:**
   - default_flag = not exiting and months_in_90 ≥ default_after_90_months;
   - hardship_remaining decreases by 1 for loans that were in hardship this month.
10. **Issue balance.** In a deal's issue month, issue_balance = the sum of opening_balance over its live loans, which is exactly 500 loans on the full profile.
11. **Call trigger.** If t ≥ issue_month and the deal's summed closing_balance ≤ call_threshold × issue_balance, set call_flag. Every remaining live loan in that deal exits as called in month t + 1.
12. **Rows.** Emit a row for every live loan with t in the window and t ≥ its deal's issue_month, exit rows included.
    - dpd_bucket is 0 for loans in hardship, else the new bucket. hardship_flag = in_hardship. interest_rate = rate.
    - indexed_ltv = closing_balance / indexed_value, or opening_balance / indexed_value on exit rows.
    - The panel also carries months_in_90 and indexed_value.

`simulate` returns the true panel with these columns:

```
loan_id, deal_id, period, opening_balance, scheduled_principal, curtailment, closing_balance,
interest_rate, dpd_bucket, hardship_flag, months_in_90, exit_reason, exit_balance, loss,
indexed_value, indexed_ltv
```

It also returns the deals frame with issue_balance filled in. exit_reason is null or one of prepaid, repurchased, defaulted, called. period is a `datetime64` first-of-month.

---

## F. Calibration statistics (step 1.6, from the true full panel)

Every statistic is computed from the true panel using the 6.3 metric definitions. Each is written to `outputs/calibration.csv` with columns `stat, value, band_lo, band_hi, pass`. Floats are written with `%.10f`.

| stat | definition |
|---|---|
| rows | emitted rows |
| arrears_90p_min, arrears_90p_max | min and max of pool arrears_90p_bal over every month 2021-10 to 2026-09; each within [arrears_90p_min, arrears_90p_max] |
| arrears_peak_month | the argmax month of pool arrears_90p_bal (first on ties), within [arrears_peak_from, arrears_peak_to] |
| cpr12_min, cpr12_max | cpr12(m) = 1 − Π (1 − smm_vol) over the 12 months ending m, for m from 2022-09 to 2026-09 (6.4 with n = 12) |
| fixed_cliff_ratio | pooled smm_vol over fixed-origination loans' rows with 0 ≤ t − fixed_end_month ≤ fixed_cliff_months − 1, divided by pooled smm_vol over the same loans' rows with −6 ≤ t − fixed_end_month ≤ −1. Pooled means summed numerators over summed denominators |
| deals_called | distinct deals with a called exit in the window |
| b_deals_called | the same for format B deals, against min_b_deals_called |

For arrears_peak_month, `value` holds the YYYY-MM string and `band_lo` and `band_hi` hold the 2 months as strings.

If any band fails, finish the rest of Section 1, write the review and status files, and stop (rule 4). Report the measured value. Do not change any parameter.

---

## G. Trustee files (`rmbsq/synth/trustee_formats.py`)

One parquet file per deal: `data/raw/trustee_a/{deal_id}.parquet` or `data/raw/trustee_b/{deal_id}.parquet`.

- Rows are sorted by report month, then loan_id. Write with `pyarrow.parquet.write_table(table, path, compression="snappy")` and no pandas index.
- Months are `"YYYY-MM"` strings.
- Static fields are repeated on every row.
- A second generator `rng_aux = Generator(PCG64(cfg.project.seed_aux))` is used only for the arrears days in G.1.

**G.1 Format A** (trustee_format A). Columns in this order and type:

| column | type | rule |
|---|---|---|
| loan_id, deal_id | string | |
| report_month | string | YYYY-MM |
| submission_seq | int64 | 1, or 1 and 2 on resubmitted deal-months |
| opening_balance, scheduled_principal, curtailment, closing_balance | float64 | dollars, 2 dp |
| interest_rate | float64 | decimal |
| arrears_days | int64 | see below |
| hardship_flag | int8 | 0/1 |
| exit_code | string, nullable | PIF, REP, DEF, CALL |
| exit_balance, loss_amount | float64 | 0.0 when not an exit or not a default |
| orig_month | string | YYYY-MM |
| orig_balance, orig_valuation | float64 | whole dollars |
| orig_ltv | float64 | full precision |
| rate_type | string | `fixed` or `variable`, at origination |
| fixed_end_month | string, nullable | |
| io_flag | int8 | |
| io_end_month | string, nullable | |
| occupancy | string | `owner` or `investor` |
| lmi_flag | int8 | |
| city, state, area, suburb | string | |

**Arrears days.** For each format A deal in deal_id order, draw `u = rng_aux.random(n_rows)` over that file's rows in file order, before resubmission rows are added. Then by dpd_bucket:

- 0 (including every hardship row): 0;
- 1: 1 + floor(29u);
- 2: 30 + floor(30u);
- 3: 60 + floor(30u);
- 4: 90 + 30 × (months_in_90 − 1) + floor(30u).

**G.2 Format B** (trustee_format B). Every format A column (G.1) is renamed to UpperCamel with acronyms written as words:

`LoanId, DealId, ReportMonth, SubmissionSeq, OpeningBalanceCents, ScheduledPrincipalCents, CurtailmentCents, ClosingBalanceCents, InterestRate, MissedPayments, Status, ExitCode, ExitBalanceCents, LossAmountCents, OrigMonth, OrigBalanceCents, OrigValuationCents, OrigLtv, RateType, FixedEndMonth, IoFlag, IoEndMonth, Occupancy, LmiFlag, City, State, Area, Suburb`

- Every money field is int64 cents = round(dollars × 100).
- MissedPayments = dpd_bucket, which is 0 for hardship rows. It replaces arrears_days.
- Status = `H` if hardship, else `A` if dpd_bucket ≥ 1, else `C`. It replaces hardship_flag.
- ExitCode: prepaid and called become `P`, repurchased `R`, defaulted `D`.
- Flags are int8 and the other types are as in G.1.

**G.3 Resubmissions.** For each `[resubmissions] deal_months` pair that exists in the profile, every row of that deal-month appears twice:

- submission_seq 1, with closing_balance and curtailment multiplied by `inflate` and rounded to the cent (or to the integer cent in B);
- submission_seq 2, with the true values.

The seq 1 row comes first.

**G.4 Other raw files:**

- `data/raw/deals.parquet`: deal_id, deal_name, originator, originator_name, trustee_format, issue_month (YYYY-MM), issue_balance (float64, 2 dp).
- `data/raw/hpi.parquet`: suburb, period (YYYY-MM), hpi (float64), every suburb and month 2016-01 to 2026-09.
- `data/raw/cash_rate.parquet`: period, rate, monthly 2016-01 to 2026-09.
- `data/raw/MANIFEST.json`: `{"files": {relative POSIX path: sha256}}` with sorted keys, indent 2, LF line ending, covering every file under `data/raw/` except itself.

---

## H. Steps, with tests

Commit one per step as `step 1.N: …`. Tests use the small profile generated once per session into `tmp_path_factory`, unless marked `full`.

**1.0 Plan and config updates.** Apply part C to `config.toml`. Update `PLAN.md` paragraphs and `docs/CONVENTIONS_RESOLVED.md` with every part B decision, removing each "open" mark. Add rule 17 to `CLAUDE.md`: "Tests marked `full` read or regenerate the full profile. Run `pytest -m full` in every review and fresh-clone check." Swap the `calibration` marker for `full` in `pyproject.toml`. Commit `CLAUDE.md` and `PLAN.md` (O-1).

**1.1 Config loaders.** `rmbsq/config.py`: `load_config` returns a frozen dataclass tree (or pydantic model) mirroring `config.toml`, plus the 4 table loaders. Tests:
- every config key round trips;
- the CSV loaders return the kickoff 4.2 to 4.5 values. Spot check 5 cash steps, 3 drift cells, 4 betas and all 5 originators against literals in the test.

**1.2 Geography, rates, HPI.** Tests:
- 60 suburbs in D.1 order;
- monthly cash rate at 2022-05 = 0.0035, 2023-11 = 0.0435 and 2026-09 = 0.036;
- HPI is identical across 2 runs with the same seed;
- with noise_sd = 0, log HPI(2023-01) − log HPI(2022-03) for Blacktown North equals 1.2 × 10 × (−1.4) / 100 = −0.168 within 0.005 (it is exact up to float);
- the HPI frame has 60 × 129 rows.

**1.3 Loans.** Tests:
- each deal has loans_per_deal loans and loan_ids are unique;
- orig_ltv is in [0.35, 0.95] and lmi_flag holds iff orig_ltv > 0.80;
- on the full profile (the loan draw only, which is fast), the fixed share by era is within 3 pp of 0.15, 0.40 and 0.10;
- fixed_end_month is null iff variable, and io_end_month is null iff not IO;
- deal_name for D001 is `HARB 2019-1`, and D006 is `HARB 2019-2`.

**1.4 Simulation.** Tests on constructed loan frames, using the O-26 decision:
- annuity: a 1-loan P&I frame where scheduled_principal plus interest matches `numpy_financial.pmt(rate / 12, term − age + 1, −opening_balance)` to the cent in a month chosen in the test;
- IO switch: scheduled_principal is 0 before io_end_month and positive from io_end_month;
- fixed to variable: interest_rate equals fixed_rate before fixed_end_month and cash + margin from it;
- hardship property (p_hardship = 1): every hardship spell lasts 3 to 6 consecutive rows, with dpd_bucket 0, scheduled_principal 0 and an unchanged closing_balance on every hardship row;
- default property (a0 = 50, a 200-loan frame): every loan whose months_in_90 reaches 9 at month t exits as defaulted at t + 1, and no defaulted exit happens otherwise;
- call property (small profile): for each called deal, the first month where summed closing ≤ 0.25 × issue_balance is the month before the call month, and every row in the call month is a called exit;
- issue: every small profile deal has exactly loans_per_deal rows in its issue month, if that month is in the window;
- determinism: 2 runs give identical panels.

**1.5 Trustee files.** Tests on the small profile:
- every format A arrears_days lies inside its bucket range, and is 0 on hardship rows;
- every format B Cents column is int64;
- every called exit is `CALL` in A and `P` in B;
- resubmission rows exist for exactly D004 2023-06, with seq 1 inflated and seq 2 true;
- the format A and format B column lists equal part G exactly;
- MANIFEST hashes match the files.

**1.6 Full profile.** `scripts/generate_data.py --profile {full,small} --out DIR` writes the raw files, then:
- `outputs/pool_monthly_truth.csv`, with the `pool_monthly.csv` columns and 1 row per window month, floats `%.10f`;
- `outputs/calibration.csv`.

Run it for the full profile into `data/raw/` and commit. Tests marked `full`:
- `test_calibration_bands`: every row of `calibration.csv` passes;
- `test_full_regenerates_identically`: regenerating into a temp folder reproduces every MANIFEST hash.

Record the runtime of the full generation.

---

## I. Review evidence (`review/section_1.md`, following the template)

Print each of these in full with `to_string()`:

1. `outputs/calibration.csv`, with chat Claude's part C values beside it.
2. `pool_monthly_truth.csv` rows for 2021-10, 2022-10, 2023-10, 2024-06, 2025-10 and 2026-09.
3. Called deals: deal_id, originator, trustee_format, call month.
4. Exit counts by reason, and row counts by dpd_bucket and hardship_flag.
5. The first 12 rows of `deals.parquet`.
6. 3 raw rows from a format A file and 3 from a format B file: 1 called exit, 1 hardship row and 1 row at 90+ in each.
7. Both submission_seq rows for the first 3 loans of D004 2023-06.
8. MANIFEST file count, the total size of `data/raw/` in MB, and the full generation runtime.
9. Both pytest outputs (default, and `-m full`) from the fresh clone.

Then `instructions/01_section_1.status.md`, then push.
