# Conventions, resolved

Every convention the code follows, with its source. Kickoff section numbers refer to
`instructions/00_kickoff.md`; "instr 01" is `instructions/01_section_1.md`. Session 0
marked some conventions open (O-n); instruction 01 part B decided every one of them, and
the O-number is kept next to each decision.

## Calendar and time

| # | Convention | Source |
|---|---|---|
| T1 | `period` is a DATE on the first of the month and means the month end status of that month. | 4.1 |
| T2 | Simulation runs monthly 2016-01 to 2026-09 (129 months). Emitted rows: 2021-10 to 2026-09 (60 months), and only where period ≥ the deal's issue_month. | 4.1 |
| T3 | "Latest" is 2026-09 (`[calendar] latest`). | 4.1 |
| T4 | Month arithmetic uses calendar-month periods, never day offsets. | WORKFLOW Part 6 |
| T5 | Default query time when a question gives none: start = end = 2026-09, grain month, shape point. Start ≥ 2021-10, end ≤ 2026-09. | 6.6 |
| T6 | vintage_year = year of orig_month; issue_year = year of issue_month; seasoning_months = months between orig_month and period. | 5.7 |
| T7 | Quarter and year buckets: stock metrics take the last month in the bucket that has data; flow metrics compound monthly smm or mdr, then annualise with exponent 12 / n_months. n_months is the months with data for that group, and "last month with data" is per group (O-17). | 6.4, instr 01 B |
| T8 | period_label is YYYY-MM, YYYY-Qn or YYYY. A point shape whose start equals its end is labelled with that month (`2026-09`); any other point shape uses `range` (O-16). | 6.7, instr 01 B |
| T9 | Simulation months are integer calendar months. A loan is live in month t if orig_month < t and it has not exited; it has no row and no draws in orig_month. | instr 01 E |

## Units and storage

| # | Convention | Source |
|---|---|---|
| U1 | Money is AUD, stored to the cent as DECIMAL(18,2) in DuckDB, never float. In pandas, money is integer cents (`Int64`) before it is cast to DECIMAL(18,2) on insert (O-27). | 5.1, instr 01 B |
| U2 | Rates and ratios are stored as decimals (0.0412) and displayed as percent with 2 dp. | 5.2 |
| U3 | Balances display in AUD millions with 1 dp (`A$412.3m`); counts display as integers with thousands separators. | 5.3 |
| U4 | Decimals become float only at the very end of `execute`. | 6.7 |
| U5 | Simulation balances are kept to the cent with `numpy.round(x, 2)` (round half even); default loss is rounded to the cent. | 4.7, instr 01 E.8 |

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
| L8 | The current rate_type and io_flag on `fact_loan_month` are the status that month, and the `rate_type` and `io_flag` query dimensions read them (O-18). | 6.1, instr 01 B |

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
| F2 | `config/cash_rate.csv` stores `period` as YYYY-MM (the month each step starts) and `rate` as a decimal (0.0035), following U2, so the 1.2 test values (0.0035, 0.036) read directly. Confirmed in instr 01 A. | 4.4, 5.2 |
| F3 | `config/hpi_drift.csv` stores regimes wide (`from, to, Sydney, Melbourne, Brisbane, Perth, Adelaide`) with drift in percent as printed in 4.5, because the 4.5 formula divides by 100. Confirmed in instr 01 A. | 4.5 |
| F4 | `config/geography.csv` holds 1 row per area (`city, state, weight, area, beta`), 20 rows; suburbs are derived, not stored. Confirmed in instr 01 A. | 4.3 |
| F5 | `config/originators.csv` holds `code, name, trustee_format`, 5 rows. | 4.2 |
| F6 | Dependencies are pinned in `requirements-lock.txt` by `uv pip compile pyproject.toml --extra test --universal --python-version 3.12 --no-header`, so the same lock installs on Windows and Linux. | 10.5, WORKFLOW Part 6 |
| F7 | pytest runs with `--disable-socket`, `-m "not full"` and `pythonpath = ["."]`. The `full` marker (which replaced `calibration`) covers every test that reads or regenerates the full profile: calibration and full regeneration (1.6), the full truth comparison (2.5), the gold check (5.2) and the replay test (5.5). Reviews, fresh-clone checks and CI also run `pytest -m full` (O-5, O-13, O-31). | 1.3, instr 01 B |
| F8 | `data/canonical/` is git-ignored and rebuilt; `data/llm_cache/` is committed and must never be ignored. | 6.1, 1.3 |
| F9 | `CLAUDE.md` and `PLAN.md` are committed whenever an instruction changes them (O-1). | instr 01 B |
| F10 | Module homes (O-3): `build_deals` in `rmbsq/synth/deals.py`; `generate` in `rmbsq/synth/generate.py`; `dedupe_resubmissions`, `detect_calls`, `enrich`, `build_canonical` in `rmbsq/canonical/build.py`; `CompiledQuery`, `execute` in `rmbsq/semantic/compiler.py`; `Catalog` in `rmbsq/semantic/catalog.py`; `format_table` in `rmbsq/semantic/format.py`; `answer`, `Answer` in `rmbsq/llm/answer.py`; `load_items`, `EvalItem` in `rmbsq/eval/run.py`; `build_trap_failures` in `rmbsq/eval/report.py`; `render_markdown` in `rmbsq/deliverable/render.py`; figures in `scripts/make_figures.py`; table loaders `load_originators`, `load_geography`, `load_cash_steps`, `load_hpi_drift` in `rmbsq/config.py`, each `(path: Path) -> pd.DataFrame`. | instr 01 B |
| F11 | Console entry point `[project.scripts] rmbsq = "rmbsq.cli:main"`, installed with `uv pip install -e . --no-deps` (O-4). | instr 01 B |
| F12 | `scripts/run_all.py` and `docs/METHODS.md` are not built (O-33). | instr 01 B |
| F13 | `outputs/canonical_row_counts.csv` has columns `table, trustee_format, rows`, with trustee_format `all` for tables not split by format (O-14). | instr 01 B |
| F14 | Floats in output CSVs are written with `%.10f`. | instr 01 F, H 1.6 |

## Synthetic generator (Section 1)

| # | Convention | Source |
|---|---|---|
| G1 | One generator `Generator(PCG64(seed))`, used in this order only: HPI noise `standard_normal((60, 128))`, then 12 loan arrays per deal in deal_id order, then 4 uniform arrays per month over the live loans sorted by loan_id (O-6). | instr 01 D, E |
| G2 | HPI: 128 noise draws per suburb for 2016-02 to 2026-09; e and HPI at 2016-01 are 0 and 100 (O-7). The zero-noise test measures log HPI(2023-01) − log HPI(2022-03), 10 months of drift (O-8). | instr 01 B, D.1 |
| G3 | The month loop is the ordered pseudo-code of instr 01 part E (O-9). | instr 01 E |
| G4 | Every profile uses issue_month(k) = first_issue + floor((k − 1) × issue_span_months / n_deals) with its own n_deals. Resubmissions apply only to listed deal-months whose deal exists and whose month is in the emitted rows: D004 2023-06 on the small profile (O-10). | instr 01 B |
| G5 | Calibration statistics are the formulas of instr 01 part F (O-11). | instr 01 F |
| G6 | Trustee schemas are instr 01 part G: months as YYYY-MM strings, flags int8, format B money as int64 cents, acronyms written as words (`OrigLtv`, `IoFlag`) (O-12). | instr 01 G |
| G8 | The true panel carries a boolean `hardship_entry` after `hardship_flag`, true in the month a loan enters hardship at E.5. It is used only inside `rmbsq/synth/` and its tests, and is not written to the trustee files. Hardship spells are split at entry rows (O-34). | instr 01b B.1 |
| G7 | Tests force paths with a modified copy of `Config` built with `dataclasses.replace`; where a path can't be forced to certainty, the test checks a property of every realised path (O-26). | instr 01 B |

## Later sections (decided in instruction 01 part B)

| # | Convention | Source |
|---|---|---|
| S1 | `pool_monthly_truth.csv` has the columns of `pool_monthly.csv`. Test 2.5 compares truth and canonical on the small profile in a temp folder; a second, `full` test compares the committed full truth with the canonical layer built from the committed full raw data (O-13). | instr 01 B |
| S2 | Test 2.3 uses a constructed frame with a known call month to prove the mechanics, and asserts on the small profile that recovered format B calls equal the true called exits, an equality where empty on both sides is allowed; a `full` test checks that all 7 called format B deals of the full profile are recovered with exact call months and loan counts (O-28 as amended). | instr 01 B, instr 01b B.3 |
| S3 | The 5 rows of test 2.4 are the first loan_id of each originator among loans that have a row with closing_balance > 0, at the latest period where that loan has such a row, in the small profile (O-29, amended by O-36 (a)). | instr 01 B, instr 03 A |
| S4 | `compile(spec, catalog, route="auto")` (O-15). | instr 01 B |
| S5 | Catalogue YAML keys: metric `name, kind, numerator, denominator, display, definition`; dimension `name, column, table, level, labels, definition` (O-30). | instr 01 B |
| S6 | Number guard: before extracting numbers, strip every catalogue dimension label, every YYYY-MM and YYYY-Qn token and every deal_name, longest match first, then run the 6.9 regex (O-19). | instr 01 B |
| S7 | Entity resolution: exact matching is case-insensitive; fuzzy matching only on deal_name, originator, trustee_format, city, state, area, suburb, rate_type, occupancy; numeric and flag dimensions match exactly or go to `unsupported`; an alias resolves to its deal_name, and a deal_id filter value that matches a deal_name or alias has its key rewritten to deal_name (O-20). | instr 01 B |
| S8 | An empty baseline SQL string counts as correct only on unsupported items (O-21). Row order must match for items with `order` set; otherwise row keys compare as a set (O-22). | instr 01 B |
| S9 | Tiling prefixes deal_name too (`C07-HARB 2021-1`); deal-filtered specs are rewritten to copy `C00-` on the 36x database (O-23). | instr 01 B |
| S10 | CI reads the committed `data/raw/` (O-24). Steps without a named test are checked by review evidence only; 6.5's evidence is the link to the green Actions run (O-25). | instr 01 B |
| S11 | `outputs/arrears_90p_by_vintage.csv` and `outputs/cpr_by_city.csv` are built through `compile` from governed specs (O-32). | instr 01 B |
| S12 | The 7.5 neutrality grep excludes `instructions/` and `.github/`; instruction 07 keeps workflow keywords out of its word list (O-2). | instr 01 B |

## LLM layer (instruction 04)

"instr 04" is `instructions/04_section_4.md`. N4 refines S6: where they differ, the F.2
order applies.

| # | Convention | Source |
|---|---|---|
| N1 | Every read connection is `rmbsq/db.py::connect_readonly(path)`: `duckdb.connect(path, read_only=True, config={"enable_external_access": False, "lock_configuration": True, "threads": 1})`. It blocks `COPY ... TO`, `read_csv` of local files, `INSTALL` and any `SET`; `SELECT` works. DuckDB refuses a second connection to the same file in 1 process with a different configuration, so no read path opens another kind. `build_canonical` keeps its own write connection. `threads: 1` keeps DOUBLE sums deterministic. | instr 04 B |
| N2 | The LLM cache key is the SHA-256 hex of `json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` encoded in UTF-8, where `request = {model, max_tokens, temperature, system, messages, tools, tool_choice}` with model, max_tokens and temperature from `[llm]`. A narration request has `tools = []` and `tool_choice = null` in the key; in record mode neither is sent to the API. | instr 04 C.1, C.2 |
| N3 | Cache files `data/llm_cache/<key>.json` hold `{key, request, response, latency_s}`, written with sorted keys, indent 1, `ensure_ascii=False` and a trailing LF, with no timestamp. | instr 04 C.3 |
| N4 | Number guard order: strip every `\d{4}-\d{2}` and `\d{4}-Q[1-4]` token, then every catalogue deal_name, then every fixed dimension label longest first, the label only where no letter, digit or `.` touches it, each replaced by a space. Extract with `-?\d[\d,]*\.?\d*(%|m\b)?`; the token is the number without commas or a trailing `.`, plus its unit. Ignore tokens whose number is a number of the question (units ignored) and bare whole years 2016 to 2026. Allowed tokens come from the same extraction over every display cell. Return the rest in text order, without duplicates. | instr 04 F.2 |
| N5 | Metric columns follow strict spec order, stock and flow alike (O-37 (b)). | instr 04 A |
