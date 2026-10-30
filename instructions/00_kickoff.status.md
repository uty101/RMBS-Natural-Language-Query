# Status: session 0 (00_kickoff)

## Outcome

Complete. Session 0 built the plan and scaffolding only, with no real code.

- Last step reached: kickoff Section 10, item 8 (this file).
- Stop reason: none.

## What was produced (kickoff Section 10)

| item | file(s) | committed |
|---|---|---|
| 1 | `WORKFLOW.md` read, not edited | already in repo |
| 2 | `PLAN.md`: 41 paragraphs, steps 1.1 to 7.6, none added or removed | **no** (rule 14, see O-1) |
| 3 | `CLAUDE.md`: Part 4 rules amended by kickoff 1.3, 1.4, 1.6, 1.7, 1.8 | **no** (rule 14, see O-1) |
| 4 | `config.toml` (byte-identical to kickoff Section 8, checked with `diff`), `config/originators.csv`, `config/geography.csv`, `config/cash_rate.csv`, `config/hpi_drift.csv` | yes |
| 5 | `.gitattributes` (kept as committed), `.gitignore`, `pyproject.toml`, `requirements-lock.txt` | yes |
| 6 | `review/TEMPLATE.md`, `decisions/OPEN.md` (empty, 0 bytes), `docs/CONVENTIONS_RESOLVED.md` | yes |
| 7 | `rmbsq/` skeleton with `synth, canonical, semantic, llm, eval, deliverable` (docstring-only modules, only those the kickoff names), `deliverable/.gitkeep`, `tests/test_placeholder.py` | yes |
| 8 | this file | yes |

Pinned top-level versions in `requirements-lock.txt` (Python 3.12, `uv pip compile --universal`):
anthropic 2.3.0, duckdb 2.0.0, matplotlib 3.11.2, numpy 2.5.4, numpy-financial 1.0.0,
pandas 3.1.0, pyarrow 26.0.0, pydantic 2.14.2, pypdf 6.21.4, pytest 9.2.0,
pytest-socket 0.8.1, pyyaml 6.0.3, rapidfuzz 3.14.6, reportlab 5.1.0, sqlglot 30.26.0.

### Notes on how session 0 was run

- Session 0 has no numbered steps, so commits use `session 0: <one line>` instead of `step X.Y: …`.
- In `CLAUDE.md` rule 4, the stop condition "a data pull fails" reads "a data generation run fails", because kickoff 1.3 says there is no data pull.
- `CLAUDE.md` rule 16 states the neutrality rule by reference to kickoff 1.7 and does not repeat its word list, so the file cannot trip the step 7.5 grep.
- 3 table layouts were chosen in session 0 and need confirming (`docs/CONVENTIONS_RESOLVED.md` F2 to F4):
  - `cash_rate.csv` stores rates as decimals (0.0035);
  - `hpi_drift.csv` is wide, with drift in percent as printed;
  - `geography.csv` has 1 row per area, and suburbs are derived from it.

## Fresh-clone check

Cloned the local `main` (6e054d5, same as pushed) to `%LOCALAPPDATA%\Temp\rq0`:

```
$ git log --oneline -1
6e054d5 session 0: review template, open decisions file and resolved conventions
$ uv venv --python 3.12 .venv
$ uv pip sync --python .venv requirements-lock.txt
$ .venv/Scripts/python -m pytest -q
.......                                                                  [100%]
7 passed in 0.15s
```

The suite runs with `--disable-socket` (from `pyproject.toml`). Every tracked text file is LF (`git ls-files --eol`).

## Questions for the reviewer

Each question has 2 options. "(a)" is listed first, with no preference implied unless stated.

### Process

- **O-1. `CLAUDE.md` and `PLAN.md` are not on GitHub.** WORKFLOW rule 14 says not to stage them unless an instruction file says to, and the kickoff asks for them to be produced but not committed. Both exist in the working tree only, so the reviewer can't read `PLAN.md` from a clone.
  - (a) Instruction 01 tells Claude Code to commit both.
  - (b) The user commits them by hand.
- **O-2. The neutrality grep (7.5) covers `.github/`.** A GitHub Actions workflow file needs the key `jobs:`, and 7.5 greps every path except `instructions/`.
  - (a) Instruction 07's word list leaves out that word.
  - (b) 7.5 also excludes `.github/workflows/`.
- **O-3. Module homes the kickoff doesn't name:**
  - `generate` and the deal-table builder (deal_name, issue_balance);
  - `dedupe_resubmissions`, `detect_calls`, `enrich`, `build_canonical`;
  - `execute`, `format_table`, `CompiledQuery`, `Catalog`;
  - `answer`;
  - `load_items`, the trap-failures builder;
  - `render_markdown`;
  - the figures script;
  - the names of the `config/*.csv` loaders.

  Options:
  - (a) Instruction 01 to 07 name each one.
  - (b) A default rule: canonical functions go in `rmbsq/canonical/build.py`; `execute` goes in `compiler.py`; `format_table` in `semantic/format.py`; `generate` in `synth/generate.py`; `answer` in `llm/answer.py`; `load_items` in `eval/run.py`; `render_markdown` in `deliverable/render.py`.
- **O-4. Console entry point for `rmbsq ask` (step 4.6).**
  - (a) `[project.scripts] rmbsq = "rmbsq.cli:main"`, run after `uv pip install -e . --no-deps`.
  - (b) Invoked only as `python -m rmbsq.cli`.
- **O-5. Default pytest selection for the `calibration` test.**
  - (a) `addopts` adds `-m "not calibration"`, and the review and CI run it explicitly.
  - (b) It runs in every default `pytest` invocation.
- **O-33. `WORKFLOW.md` Part 5 lists `scripts/run_all.py` and `docs/METHODS.md`, but the kickoff has no step for either.**
  - (a) Neither is built.
  - (b) An instruction file adds them to a section.

### Section 1

- **O-6. Static draw order (4.2, 4.6, 4.7 "Seed and RNG").** Several things are unspecified:
  - whether draws within a deal go loan by loan or attribute by attribute;
  - where the city, area and suburb draws sit (orig_balance needs the city);
  - whether conditional attributes draw for every loan (io_flag's p depends on occupancy; fixed_term and fixed_rate apply only to fixed loans);
  - how seasoning, drawn last, feeds rate_type and fixed_rate, which need orig_month.

  Options:
  - (a) Instruction 01 gives the exact draw sequence as a numbered list of `rng` calls.
  - (b) A vectorised rule: per deal, 1 array of length `loans_per_deal` per attribute, in the order seasoning, city, area, suburb, then 4.6. Every attribute draws for every loan and the result is masked.
- **O-7. HPI noise draws.**
  - (a) 129 draws per suburb (2016-01 drawn and discarded).
  - (b) 128 draws (2016-02 onward).
- **O-8. HPI zero-noise test window (1.2), "change 2022-04 to 2023-01".** With beta × drift ≈ 1.8 pp a month, the choice moves the result by more than the 0.5 pp tolerance.
  - (a) log HPI(2023-01) − log HPI(2022-03), 10 months of drift.
  - (b) log HPI(2023-01) − log HPI(2022-04), 9 months.
- **O-9. Order within a month (4.7).** Unspecified:
  - whether a loan amortises in orig_month (age 0);
  - whether "bucket ≥ 1 pays no principal" and "current" for prepayment use the bucket before or after this month's transition;
  - whether the hardship duration counts the entry month;
  - whether the 4 uniform arrays run over all active loans across all deals sorted by loan_id (one global array) or deal by deal.

  Options:
  - (a) Instruction 01 gives an ordered pseudo-code month loop.
  - (b) Default: there is no payment in orig_month; the payment and eligibility rules use the start-of-month bucket; the duration includes the entry month; the arrays are global.
- **O-10. Small profile.** 4.2's issue formula hard-codes 50 deals over 60 months, and D017 and D033 don't exist with 10 deals.
  - (a) The small profile uses `floor((k − 1) × issue_span_months / n_deals)` with its own n_deals, and resubmissions apply only to deal-months that exist (D004 only).
  - (b) The small profile keeps the 50-deal spacing (deals 2019-01 to 2019-11) and also D004 only.
- **O-11. Calibration statistics (1.6).** The kickoff gives the bands but not the statistics:
  - arrears_90p: which metric (bal or cnt), measured in every month or at the peak;
  - arrears peak: the argmax month of the pool series?
  - cpr12: the trailing 12-month CPR, over which months;
  - fixed cliff ratio: SMM in the `fixed_cliff_months` after expiry divided by what baseline;
  - deals called: within the window.

  Options:
  - (a) Instruction 01 defines each one as a formula.
  - (b) This repo proposes the definitions in instruction 01's status file for approval before step 1.6 runs. That would add a stop, so (a) is the one that keeps the section unblocked.
- **O-12. Trustee field details (4.8).** Unspecified:
  - which format B fields carry `Cents` (orig_balance, orig_valuation, scheduled_principal, curtailment, exit_balance, loss_amount?);
  - the encoding of orig_month, fixed_end_month and io_end_month (YYYY-MM string, or date);
  - flags as 0/1 integers or booleans;
  - UpperCamel acronyms (`OrigLtv` or `OrigLTV`, `IoFlag` or `IOFlag`).

  Options:
  - (a) Instruction 01 lists both column schemas in full.
  - (b) Default: every money field in cents; months as YYYY-MM strings; flags 0/1; acronyms as words (`OrigLtv`, `IoFlag`).

### Section 2

- **O-13. `pool_monthly_truth.csv` columns, and the profile for test 2.5.** Kickoff 1.4 says tests never read the full raw data, but the truth CSV is from the full profile.
  - (a) The truth CSV has the same columns as `pool_monthly.csv`, and test 2.5 recomputes truth vs canonical on the small profile in a temp folder.
  - (b) Test 2.5 is marked `calibration` and reads the full profile.
- **O-14. `outputs/canonical_row_counts.csv` columns.**
  - (a) `table, rows`.
  - (b) `table, trustee_format, rows`.
- **O-27. pandas dtype of money before DuckDB.**
  - (a) Integer cents (`Int64`) cast to DECIMAL(18,2) on insert.
  - (b) Python `Decimal` objects.
- **O-28. Call detection test (2.3) on the small profile.** Its deals may never reach 10% of issue balance, which would make `test_format_b_calls_recovered` vacuous.
  - (a) The test asserts that at least 1 called format B deal exists in the fixture and fails otherwise.
  - (b) It uses a constructed frame with a known call month.
- **O-29. The "5 named rows" of test 2.4 are not named.**
  - (a) Instruction 02 names them (loan_id, period).
  - (b) The test selects them by a fixed rule, such as the first row of each originator in loan_id order.

### Section 3

- **O-15. `compile` signature.** 6.7 has `compile(spec, route)`, and Section 7 has `compile(spec, catalog, route="auto")`.
  - (a) Use the Section 7 signature.
  - (b) Use the 6.7 signature, with the catalogue bound at module level.
- **O-16. `period_label` for shape point with start = end** (for example the default 2026-09).
  - (a) `range`.
  - (b) The single period's label, `2026-09`.
- **O-17. Time buckets (6.4).** Is n_months the calendar months in the bucket, or the months with data for that group? Is "last month in the bucket that has data" per group or pool-wide?
  - (a) n_months is the months with data, and the last month is per group.
  - (b) n_months is the calendar months, and the last month is pool-wide.
- **O-18. The `rate_type` and `io_flag` dimensions.**
  - (a) The current status from `fact_loan_month`.
  - (b) The origination value from `dim_loan` (`rate_type_orig`, `io_flag_orig`).
- **O-30. YAML structure of `semantic/metrics.yaml` and `dimensions.yaml`.**
  - (a) Instruction 03 gives the schema.
  - (b) Default keys: metric `name, kind (stock|flow), numerator, denominator, display, definition`; dimension `name, column, table, level (deal|loan), labels, definition`.

### Section 4

- **O-19. Number guard and hyphenated labels (6.9).** The regex turns `30-59` into `30` and `-59`, and `60-70` into `60` and `-70`. Those are dimension labels, not display strings.
  - (a) Dimension label cells count as display strings, and their hyphen-split parts are ignored like YYYY-MM parts.
  - (b) The regex requires no digit immediately before `-`, so `-59` becomes `59`, and label parts must match a label cell.
- **O-20. Entity resolution (6.8).** Unspecified:
  - whether exact matching is case-sensitive;
  - which dimensions are fuzzy-matched (issue_year, vintage_year, io_flag, lmi_flag?);
  - whether a deal alias resolves to the deal_name or the deal_id value.

  Options:
  - (a) Case-insensitive; fuzzy on text dimensions only; aliases resolve within whichever of deal_name or deal_id is filtered.
  - (b) Case-sensitive; fuzzy on all 18; aliases resolve to deal_name only.
- **O-26. How tests force paths.** This covers noise = 0 (1.2), hand-built hardship, default and call cases (1.4), and a timeout shorter than 30 s (4.5).
  - (a) Tests pass a modified copy of `Config` (for example p_hardship = 1, noise_sd = 0, baseline_timeout_s = 1).
  - (b) Functions accept injected uniform arrays or a scripted `rng`.

### Section 5

- **O-21. An empty baseline SQL string on an ambiguous item.**
  - (a) It counts as correct, as on unsupported items.
  - (b) It counts only on unsupported items.
- **O-22. Row order in scoring for items with `order`.**
  - (a) Order must match.
  - (b) The keys are compared as a set.
- **O-23. Tiling (6.12).** Only deal_id and loan_id get the `C{cc}-` prefix, so deal_name stays shared across copies. Gold specs that filter on a deal_id match no rows in the 36x DB.
  - (a) Prefix deal_name too, and run deal_id-filtered specs on 36x with the filter rewritten to copy `C00-`.
  - (b) Leave deal_name unprefixed, and mark deal-filtered specs `n/a` on 36x.
- **O-31. Database for the gold check (5.2) and the replay test (5.5).** Both need the full canonical DB, but kickoff 1.4 says tests never read the full raw data.
  - (a) Mark both tests `calibration`-style (full data, run in review and CI).
  - (b) Build them against the small profile, with gold results recomputed on it.

### Section 6

- **O-24. How CI gets the full profile for the calibration test.**
  - (a) It reads the committed `data/raw/`.
  - (b) It regenerates with `scripts/generate_data.py --profile full` and checks the result against `MANIFEST.json`.
- **O-25. Steps with no named test:** 5.4, 6.1, 6.2, 6.3, 6.5, 7.3 (its page check is in 7.4) and 7.6.
  - (a) Review evidence only.
  - (b) Instruction files add a test each.
- **O-32. The source data for `arrears_90p_by_vintage.png` and `cpr_by_city.png`.** `pool_monthly.csv` is pool level only.
  - (a) Add CSVs `outputs/arrears_90p_by_vintage.csv` and `outputs/cpr_by_city.csv`, built through `compile` from governed specs.
  - (b) Draw them directly from the canonical DB.

## Last 3 commits on origin (before this file)

```
6e054d5 session 0: review template, open decisions file and resolved conventions
1800249 session 0: package skeleton and placeholder test
a5590f9 session 0: config.toml and config tables
```
