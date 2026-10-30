# PLAN: RMBS Natural Language Query

The step list in `instructions/00_kickoff.md` Section 9, expanded to one paragraph per
step. It adds and removes no steps. Section numbers below are kickoff sections unless
marked otherwise. Session 0 marked every point the kickoff left unspecified as open
(O-n); instruction 01 part B decided all of them (O-1 to O-33), and each paragraph below
now states the decision with its O-number. Where a paragraph proposes a name the kickoff
does not give (a test id, a column), it is a proposal, and an instruction file overrides
it (precedence rule 13).

Shared test fixtures, used by every section: `tests/conftest.py` holds a session-scoped
fixture that runs the small profile once per test session into `tmp_path_factory` and
writes its raw files there, and from Section 2 a fixture `small_db` that runs
`build_canonical` on it. Tests never read `data/raw/` (kickoff 1.4), except the tests
marked `full` (O-5): they read or regenerate the full profile. `addopts` excludes them
with `-m "not full"`, and every review, fresh-clone check and CI run also runs
`pytest -m full` as a second command.

Review evidence for every step also includes the step's test output, verbatim.

Module homes (O-3): `build_deals` in `rmbsq/synth/deals.py`; `generate` in
`rmbsq/synth/generate.py`; `dedupe_resubmissions`, `detect_calls`, `enrich`,
`build_canonical` in `rmbsq/canonical/build.py`; `CompiledQuery` and `execute` in
`rmbsq/semantic/compiler.py`; `Catalog` in `rmbsq/semantic/catalog.py`; `format_table` in
`rmbsq/semantic/format.py`; `answer` and `Answer` in `rmbsq/llm/answer.py`; `load_items`
and `EvalItem` in `rmbsq/eval/run.py`; `build_trap_failures` in `rmbsq/eval/report.py`;
`render_markdown` in `rmbsq/deliverable/render.py`; figures in `scripts/make_figures.py`;
config table loaders `load_originators`, `load_geography`, `load_cash_steps`,
`load_hpi_drift` in `rmbsq/config.py`, each `(path: Path) -> pd.DataFrame`.

`scripts/run_all.py` and `docs/METHODS.md` are not built (O-33); Section 7 has its own
regeneration check.

---

## Section 1: synthetic data generator

Instruction 01 parts D to G fix the generator exactly: the order of every `rng` call
(part D, O-6), the month loop (part E, O-9), the calibration statistics (part F, O-11)
and both trustee schemas (part G, O-12). Part C amends `config.toml` (call threshold
0.25, a0 −6.0, p_cure_90 0.10, default after 9 months at 90+, a 12-month payment shock
lookback, arrears_90p_min 0.001, and at least 3 format B deals called).

**Step 1.0: plan and config updates.** Applies instruction 01 part C to `config.toml`,
records every part B decision in this file and in `docs/CONVENTIONS_RESOLVED.md`, adds the
`full` marker rule to `CLAUDE.md`, and swaps the `calibration` marker for `full` in
`pyproject.toml`, with `addopts` gaining `-m "not full"`. `CLAUDE.md` and `PLAN.md` are
committed here and whenever an instruction changes them (O-1). Review evidence: the
`config.toml` diff.

**Step 1.1: config and table loaders.** File `rmbsq/config.py`. Implements
`load_config(path: Path = Path("config.toml")) -> Config`, a frozen dataclass tree that
exposes every section and key of `config.toml` unchanged (lists as tuples), plus the 4
table loaders `load_originators`, `load_geography`, `load_cash_steps` and
`load_hpi_drift`, each `(path: Path) -> pd.DataFrame` (O-3). Tests modify a copy of the
tree with `dataclasses.replace` (O-26). Tests in `tests/test_config.py`:
`test_config_round_trip` (every key and value read through `Config` equals a `tomllib`
parse of `config.toml`), `test_originators_csv` (all 5 originators),
`test_geography_csv` (4 betas), `test_cash_rate_csv` (5 cash steps) and
`test_hpi_drift_csv` (3 drift cells), each against literals written into the test. No
outputs. Review evidence: the 4 loaded tables printed in full, with dtypes.

**Step 1.2: geography, cash rate, HPI.** Files `rmbsq/synth/geography.py`
(`build_geography(cfg) -> DataFrame[city, state, area, beta, suburb]`, 60 rows in
instruction 01 D.1 order: city order of 4.3, areas as listed, then North, Central,
South), `rmbsq/synth/rates.py` (`build_cash_rate(cfg) -> DataFrame[period, rate]`, every
month 2016-01 to 2026-09, each step held until the next change) and `rmbsq/synth/hpi.py`
(`build_hpi(cfg, geo, rng) -> DataFrame[suburb, period, hpi]`). HPI noise is 1 draw
`rng.standard_normal((60, 128))` for months 2016-02 to 2026-09; e and the log return are
0 at 2016-01 and HPI is 100 there (O-7). Tests in `tests/test_synth_market.py`:
`test_sixty_suburbs_in_order`; `test_cash_rate_points` (2022-05 = 0.0035,
2023-11 = 0.0435, 2026-09 = 0.036); `test_hpi_deterministic` (2 runs with the same seed
are equal); `test_hpi_zero_noise_blacktown_north` (noise_sd = 0 through a modified
config, log HPI(2023-01) − log HPI(2022-03) = 1.2 × 10 × (−1.4) / 100 = −0.168 within
0.005; 10 months of drift, O-8); `test_hpi_frame_rows` (60 × 129). No committed outputs.
Review evidence: the 60 row geography table; the 129 row cash rate path; HPI for 1 suburb
per city at 2016-01, 2022-03, 2022-04, 2023-01 and 2026-09; the zero-noise comparison.

**Step 1.3: deals and static loan attributes.** Files `rmbsq/synth/deals.py`
(`build_deals(cfg, n_deals) -> DataFrame`, no draws: issue_month(k) = first_issue +
floor((k − 1) × issue_span_months / n_deals) with each profile's own n_deals (O-10),
originator codes[(k − 1) mod 5], deal_name `"{code} {issue_year}-{n}"`) and
`rmbsq/synth/loans.py` (`draw_loans(cfg, geo, cash, rng) -> DataFrame`, 1 row per loan,
drawn deal by deal in deal_id order, 12 arrays of length loans_per_deal per deal in the
exact order of instruction 01 D.3, every array drawn for every loan and then masked).
Tests in `tests/test_synth_loans.py`: `test_loans_per_deal_unique_ids`;
`test_ltv_range_and_lmi_flag` (orig_ltv in [0.35, 0.95], lmi_flag iff orig_ltv > 0.80);
`test_fixed_share_by_era` (full profile loan draw only, fixed share per era within 3 pp of
0.15, 0.40 and 0.10); `test_null_end_months` (fixed_end_month null iff variable,
io_end_month null iff not IO); `test_deal_names` (D001 `HARB 2019-1`, D006
`HARB 2019-2`). No committed outputs. Review evidence: the deal table; the first 5 loans
of D001 with every column; the fixed share table by era; orig_ltv min and max; the
lmi_flag × (orig_ltv > 0.80) crosstab.

**Step 1.4: monthly simulation.** File `rmbsq/synth/simulate.py`. Implements
`simulate(cfg, loans, cash, hpi, rng) -> (panel, deals)`, following the ordered month
loop of instruction 01 part E (O-9): live set, issue reset, 4 uniform arrays (hardship,
transition, prepay, repurchase) over all live loans sorted by loan_id, month quantities
with the 12-month payment shock lookback, hardship entry, transitions on the
start-of-month bucket, exits (called > defaulted > repurchased > prepaid, suppressed
before issue), cash flows rounded to the cent, end-of-month flags, issue balance, call
trigger at 25% of issue balance, and rows. The panel has the part E columns, including
months_in_90 and indexed_value, plus a boolean `hardship_entry` after `hardship_flag`, true
in the month a loan enters hardship at E.5 (instruction 01b B.1; used only inside
`rmbsq/synth/` and its tests, never written to the trustee files). The deals frame carries
issue_balance. Tests in
`tests/test_synth_simulate.py`, on constructed loan frames with a modified config where
a path must be forced (O-26), or on a property of every realised path:
`test_pi_annuity_matches_npf_pmt`; `test_io_switch_at_io_end`;
`test_fixed_to_variable_switch`; `test_hardship_rows_frozen` and
`test_hardship_spell_lengths` (p_hardship = 1 and p_repurchase = 0; each loan's hardship
rows split into spells at its entry rows; every spell is hardship_min to hardship_max rows
and starts on an entry row, except that a loan's last spell is excluded if it includes
the loan's last emitted row; O-34, instruction 01b B.1); `test_default_after_months_in_90`
(a0 = 50, 200 loans); `test_call_property_small`; `test_every_deal_full_at_issue`;
`test_simulate_deterministic`. No committed outputs. Review evidence: the test output;
the hand-built cases' rows; the loans-at-issue count per small-profile deal.

**Step 1.5: trustee files.** File `rmbsq/synth/trustee_formats.py`. Implements
`write_trustee_files(cfg, panel, loans, out_dir: Path, rng_aux) -> dict[str, str]`
(relative POSIX path → SHA-256), 1 parquet per deal in `trustee_a/` or `trustee_b/` with
the exact schemas of instruction 01 part G (O-12): months as YYYY-MM strings, flags int8,
format B money as int64 cents and acronyms written as words. arrears_days use
`PCG64(seed_aux)` (G.1). Resubmissions apply only to listed deal-months that exist in the
profile, which is D004 2023-06 on the small profile (O-10). `rmbsq/synth/generate.py`
writes `deals.parquet`, `hpi.parquet`, `cash_rate.parquet` and `MANIFEST.json` (G.4).
Tests in `tests/test_trustee_formats.py`, on the small profile:
`test_arrears_days_in_bucket_range`; `test_format_b_cents_int64`;
`test_called_exit_codes` (CALL in A, P in B); `test_resubmissions_exactly_d004`;
`test_column_lists`; `test_manifest_hashes`. Review evidence: listed in instruction 01
part I.

**Step 1.6: full generation and calibration.** Script `scripts/generate_data.py --profile
{full,small} --out DIR`, calling `generate(cfg, profile: str, out_dir: Path) -> None` in
`rmbsq/synth/generate.py` (O-3). It writes the raw files, then
`outputs/pool_monthly_truth.csv` (the `pool_monthly.csv` columns, 1 row per window month,
floats `%.10f`, O-13) and `outputs/calibration.csv` (`stat, value, band_lo, band_hi,
pass`, with every statistic defined as a formula in instruction 01 part F, O-11). The
full profile is generated into `data/raw/` and committed. Tests in
`tests/test_full_profile.py`, both marked `full`: `test_calibration_bands` (every row of
`calibration.csv` passes) and `test_full_regenerates_identically` (regenerating into a
temp folder reproduces every MANIFEST hash, O-24). A failed band is a stop: report the
measured value and tune nothing. Review evidence: instruction 01 part I.

## Section 2: canonical layer

**Step 2.1: ingestion.** File `rmbsq/canonical/ingest.py`. Implements
`ingest_format_a(path: Path) -> DataFrame` and `ingest_format_b(path: Path) -> DataFrame`.
Both return the same canonical columns: the fact columns of 6.1 that come from the raw
file, submission_seq, and the static fields. They map arrears to dpd_bucket (6.2),
hardship to hardship_flag with dpd_bucket 0 on hardship rows, exit codes to exit_reason,
cents to dollars, and report_month to a first-of-month DATE. Money columns are integer
cents (`Int64`) in pandas and cast to DECIMAL(18,2) on insert (O-27). Test
`tests/test_canonical_ingest.py::test_formats_same_columns_and_dtypes` (1 A and 1 B file
from the small profile). Review evidence: column and dtype table for each format after
ingest; 3 ingested rows from each.

**Step 2.2: resubmissions.** Implements `dedupe_resubmissions(df) -> DataFrame` in
`rmbsq/canonical/build.py` (keep max submission_seq per (loan_id, period)). Test
`tests/test_canonical_dedupe.py::test_resubmission_months_one_row_true_values`: the
resubmission deal-month present in the small profile (D004 2023-06, O-10) has 1 row per
loan with the true closing_balance and curtailment. Review evidence: rows before and
after dedupe for 2 loans of that deal-month.

**Step 2.3: call detection.** Implements `detect_calls(df) -> DataFrame` in
`rmbsq/canonical/build.py` (6.2 rule, share from `call_detect_share`, both formats).
Tests in `tests/test_canonical_calls.py` (O-28, amended by instruction 01b B.3):
`test_format_b_calls_recovered` uses a constructed frame with a known call month to prove
the mechanics, and also asserts on the small profile that the recovered format B calls
equal the true panel's called exits, as an equality where empty on both sides is allowed
(after the 01b recalibration the small profile has no called format B deal). A new test
marked `full` checks that all 7 called format B deals of the full profile are recovered
with their exact call months and loan counts. Instruction 02 specifies these tests.
`test_format_a_calls_unchanged`. Review evidence:
for every called deal, the call month and number of called loans, truth vs canonical; for
format A, CALL rows before and after detection.

**Step 2.4: enrichment.** Implements `enrich(df, hpi, cfg) -> DataFrame` in
`rmbsq/canonical/build.py`: indexed_value and indexed_ltv (opening balance on exit rows,
5.4), ltv_bucket_orig, ltv_bucket_indexed and seasoning_bucket (6.2 edges), current
rate_type and io_flag, seasoning_months, vintage_year. Test
`tests/test_canonical_enrich.py::test_indexed_ltv_by_hand_five_rows`; the 5 rows are the
first loan_id of each originator, at the latest period where that loan has a row with
closing_balance > 0, in the small profile (O-29). Review evidence: the 5 rows with HPI at
orig_month and period, orig_valuation, balance, and the hand calculation next to the
computed value.

**Step 2.5: canonical database.** Implements `build_canonical(raw_dir: Path, db_path:
Path, cfg) -> None` in `rmbsq/canonical/build.py` and script `scripts/build_canonical.py`,
writing `data/canonical/rmbs.duckdb` (not committed) with `dim_deal`, `dim_loan`,
`fact_loan_month`, `hpi`, `cash_rate` and `agg_deal_month` as 6.1. Money is
DECIMAL(18,2). `agg_deal_month` holds every numerator and denominator column the 12
metrics need. Tests in `tests/test_canonical_build.py` (O-13):
`test_pool_monthly_matches_truth` compares truth and canonical on the small profile in a
temp folder, to 1e-9; a second test, marked `full`, compares the committed full
`outputs/pool_monthly_truth.csv` with the canonical layer built from the committed full
raw data; `test_agg_sums_equal_fact_sums`. Outputs `outputs/pool_monthly.csv` (columns per
Section 7) and `outputs/canonical_row_counts.csv` with columns `table, trustee_format,
rows`, trustee_format `all` for tables not split by format (O-14). Review evidence:
`DESCRIBE` of every table; row counts; `pool_monthly.csv` first 3 and last 3 rows; max
absolute difference against truth per column.

**Step 2.6: canonical equals truth.** Added by instruction 02 (D 2.6). New test file
`tests/test_canonical_truth.py`. `test_canonical_equals_truth_panel` joins
`fact_loan_month`, built by `build_canonical` from the small profile's raw trustee files,
to the true panel from `simulate` on loan_id and period, and asserts: the same row count
with no unmatched row on either side; every money column equal to the cent;
interest_rate, indexed_value and indexed_ltv equal to 1e-9; dpd_bucket, hardship_flag and
exit_reason identical. `test_full_canonical_equals_truth_panel`, marked `full`, makes the
same comparison between the canonical layer built from the committed full `data/raw/` and
the full panel regenerated in memory. Passing it proves the canonical layer undoes all 4
trustee traps, so every later number rests on cleaning that is proved, not assumed.
Review evidence: both test outputs, verbatim.

## Section 3: semantic layer and compiler

Instruction 03 parts B to D fix the query semantics (B), the 2 catalogue files (C) and the
compiler's shape (D). Its 15 gold specs and 20 spec examples are committed as
`tests/fixtures/compiler_gold.json` and `tests/fixtures/spec_examples.json`, byte for byte
copies of the instruction's 2 JSON files, never edited.

**Step 3.0: fixtures and `dim_period`.** Added by instruction 03 (E 3.0). Copies the 2
JSON fixtures. `build_canonical` writes a new table `dim_period(period DATE, month_label,
quarter_label, year_label VARCHAR)`, 1 row per month from window_start to window_end (60
rows, for example `2025-04-01, 2025-04, 2025-Q2, 2025`), and
`outputs/canonical_row_counts.csv` gains the row `dim_period, all, 60`. Both data scripts
take `--outputs DIR`. It defaults to the repo's `outputs/` only for `--profile full`, or
when `--raw` is the repo's `data/raw/`; otherwise to `<--out or --raw>/../outputs`, so a
small run never overwrites the committed full-profile CSVs. Tests:
`tests/test_canonical_build.py::test_dim_period` (60 rows; spot checks 2021-10, 2024-12,
2026-09) and `tests/test_scripts.py::test_small_run_leaves_repo_outputs_alone` (both
scripts on the small profile in a temp folder; SHA-256 of every file in `outputs/`
unchanged). Every Section 2 test still passes.

**Step 3.1: catalogue.** Files `semantic/metrics.yaml` (exactly the 12 metrics of 6.3),
`semantic/dimensions.yaml` (exactly the 18 dimensions of 6.5, with the 5 deal level ones
marked) and `rmbsq/semantic/catalog.py` (`load_catalog(metrics_yaml: Path, dims_yaml:
Path) -> Catalog`, allowed values loaded from the canonical DB). Metric keys are `name,
kind, numerator, denominator, display, definition`; dimension keys are `name, column,
table, level, labels, definition` (O-30). Metric names, kinds, displays and
definitions are instruction 03 C.1 verbatim; dimension rows are C.2.
`Catalog.allowed_values(name)` returns the fixed labels where C.2 gives them, otherwise
the sorted distinct values from the database. Tests in `tests/test_catalog.py`:
`test_twelve_metrics`, `test_eighteen_dimensions`, `test_allowed_values_from_db` (on
`small_db`). Review evidence: both YAML files in full; allowed values per categorical
dimension.

**Step 3.2: QuerySpec.** File `rmbsq/semantic/spec.py`, pydantic v2 `QuerySpec` with the
6.6 rules: intents; 1 to 3 metrics; 0 to 2 group_by; order limit 1 to 20; 2 to 4 clarify
options; field requirements per intent; default time 2026-09 point month;
start ≥ window_start and end ≤ window_end. Tests in `tests/test_spec.py`:
`test_valid_examples` and `test_invalid_examples`, with the examples supplied in
instruction 03. Review evidence: each example with accepted or rejected and the
validation message.

**Step 3.3: compiler and time aggregation.** Files `rmbsq/semantic/compiler.py`
(`compile(spec, catalog, route="auto") -> CompiledQuery(sql_duckdb, sql_oracle, route)`,
the Section 7 signature (O-15), and `execute(compiled, con) -> DataFrame`) and
`rmbsq/semantic/timeagg.py` (6.4). The statement is a `sqlglot` tree with values as
literals. Output columns are group_by, then period_label, then 1 per metric. Rows sort by
group_by and period_label unless `order` is set. Decimals become float only at the end.
When a point shape's start equals its end, period_label is that month (`2026-09`);
otherwise point shape uses `range` (O-16). n_months for flow compounding is the months
with data for that group, and "last month with data" for stock metrics is per group
(O-17). The `rate_type` and `io_flag` dimensions read the current status that month from
`fact_loan_month` (O-18). The query semantics are instruction 03 part B. The statement
is 1 tree with the CTEs `parts`, `b`, `keys`, `stock`, `flow` and a final select (D.1);
`stock` or `flow` is left out when no metric needs it. **Oracle-safe constructs (D.3):**
conditional aggregates are `SUM(CASE WHEN … THEN x ELSE 0 END)`, never `FILTER`; period
labels come from a join to `dim_period`, never date functions; flag and bucket labels are
`CASE` expressions; math uses only `EXP`, `LN`, `POWER` and `ROW_NUMBER`; booleans are
compared as columns (`NOT f.hardship_flag`, Oracle 23ai). Tests in
`tests/test_compiler.py`: `test_fifteen_specs_match_hand_sql` (15 gold specs on
`small_db`: same columns and row order, dimensions equal as strings, metrics within 1e-9
after scaling by max(1, |value|), row count `rows_small`),
`test_quarter_compounding_hand_example` (instruction 03 B.8, to 1e-10) and
`test_full_fifteen_specs_match_hand_sql` (marked `full`, row count `rows_full`). Review
evidence: per spec, the DuckDB SQL, the hand SQL and the max abs difference; the hand
example's arithmetic line by line.

**Step 3.4: routing.** In `compiler.py`: route `auto` picks `agg` when every group_by and
filter dimension is deal level, else `fact`; that includes specs with neither (D.2). Route `agg` changes only the
`parts` CTE, which reads `agg_deal_month` joined to `dim_deal`. Tests in
`tests/test_routing.py`: `test_route_auto_choice` (auto route equals `route_auto` for all
15 specs) and `test_fact_and_agg_routes_equal` (S01, S02, S05, S10, S11, S12, equal by the
3.3 rule on `small_db`). Review evidence: per spec, the route `auto` chose and the
max abs difference between routes.

**Step 3.5: Oracle rendering.** In `compiler.py`: `sql_oracle` rendered from the same tree
with `dialect="oracle"` and `pretty=True`. Test
`tests/test_oracle_render.py::test_specs_render_to_oracle` (instruction 03 E 3.5): for all
15 specs, no `sqlglot` warning (logger captured at WARNING, `unsupported_level=
ErrorLevel.RAISE`); none of `FILTER(`, `FILTER (`, `YEAR(`, `QUARTER(`, `STRFTIME`, `CLOB`,
`LIMIT `, `::` in the text, case-insensitive; the text parses back with
`sqlglot.parse_one(text, read="oracle")`. Review evidence: the Oracle SQL for 3 test specs;
the captured warning list (expected empty).

**Step 3.6: display formatting.** Implements `format_table(df, catalog) -> DataFrame` in
`rmbsq/semantic/format.py`: percentages with 2 dp, balances as `A$412.3m`, counts as
integers with thousands separators (5.2, 5.3), years as plain integers, NULL as `n/a`,
dimensions and period_label unchanged; every cell a string. Test
`tests/test_format_table.py::test_display_rules`, including round-half-even for 0.000125
(recorded as Python's format gives it). Review evidence: 1 raw frame and its
formatted frame side by side.

## Section 4: LLM layer

Instruction 04 fixes the client and cache (C), the spec call (D), entity resolution (E),
narration and the number guard (F), the baseline (G) and the pipeline (H). Its 3 prompts
are committed as `prompts/spec_system.md`, `prompts/narrate_system.md` and
`prompts/baseline_system.md`, and its guard cases as `tests/fixtures/guard_cases.json`,
byte for byte copies, never edited. No live API call is made in this section: every test
runs in replay mode from hand-written fixture responses in
`tests/fixtures/llm_responses/<name>.json`, which the tests key with the client's own key
function and write into a temp cache dir. No test reads `data/llm_cache/`.

**Step 4.0: fixtures, prompts, locked connection.** Copies the files above and
`instructions/04_compiler_gold.json` over `tests/fixtures/compiler_gold.json`. Metric
columns follow strict spec order (O-37 (b)). New `rmbsq/db.py::connect_readonly(path) ->
DuckDBPyConnection`: `read_only=True` with `enable_external_access: False`,
`lock_configuration: True` and `threads: 1`. Every read connection uses it (catalogue,
`scripts/build_canonical.py`, the pipeline, the baseline and the tests);
`build_canonical` keeps its write connection. Tests:
`tests/test_compiler.py::test_fifteen_specs_match_hand_sql` with the new fixture, and
`tests/test_db.py::test_readonly_blocks` (CREATE, `COPY ... TO`, `read_csv` and `SET
threads=4` raise; `SELECT` works; no file is created).

**Step 4.1: cached client.** `rmbsq/llm/client.py`: `LLMClient(cfg, mode="replay",
cache_dir=Path("data/llm_cache"))` with `.build_request(...)` and `.call(system,
messages, tools, tool_choice) -> dict`. The request is `{model, max_tokens, temperature,
system, messages, tools, tool_choice}`; its key `request_key(request)` is the SHA-256 hex
of `json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` in
UTF-8. The cache file `<key>.json` is `{key, request, response, latency_s}` written with
sorted keys, indent 1 and a trailing LF, with no timestamp. `replay`: a miss raises
`CacheMiss(key)`. `record`: a hit never calls the API; a miss raises `MissingApiKey`
without `ANTHROPIC_API_KEY`, creates the SDK client on first use, and retries HTTP 429,
529 and 5xx 3 times after 2, 4 and 8 s. `calls` logs `{key, hit, latency_s,
input_tokens, output_tokens}`. Tests in `tests/test_llm_client.py`: `test_key_stable`,
`test_replay_hit`, `test_replay_miss_raises`, `test_record_hit_does_not_call_api`,
`test_missing_key_raises`, `test_cache_file_format`.

**Step 4.2: spec agent.** `rmbsq/llm/spec_agent.py`: `render_spec_prompt(catalog, cfg)`
fills `n_deals` (rows of `dim_deal`), the window, `latest`, the metric and dimension
tables in YAML order and 1 allowed-values line per dimension (deal_name adds the alias
note); an unfilled placeholder raises. Tool `submit_spec` with
`QuerySpec.model_json_schema()` inlined (no `$ref`, `$defs` or `title`), forced.
`question_to_spec(question, client, catalog) -> tuple[QuerySpec, bool]`: a missing block
or a validation error gives `unsupported` with `invalid spec from model: <first error, at
most 200 chars>` and False. Tests in `tests/test_spec_agent.py`:
`test_prompt_has_every_name`, `test_tool_schema_inlined`, `test_parse_fixture_answer`,
`test_parse_fixture_clarify`, `test_parse_fixture_unsupported`, `test_parse_invalid_spec`,
`test_parse_missing_tool_block`.

**Step 4.3: entity resolution.** `rmbsq/llm/resolve.py`: `deal_aliases(catalog)` (alias
-> deal_name; `Harbour 19-1`, `HARB 19-1`, `HARB19-1` for HARB 2019-1) and
`resolve_entities(spec, catalog, aliases) -> QuerySpec` for answer specs: exact
case-insensitive, then deal aliases (a deal_id value that is a deal_name or alias moves to
deal_name), then flags (`yes, no, true, false, y, n`), years and dpd_bucket, then
`token_set_ratio` on the text dimensions only (O-20) with `resolve.accept`,
`resolve.clarify` and `resolve.top_k`. The first clarify or unsupported value decides.
Tests in `tests/test_resolve.py`: `test_exact_case_insensitive`, `test_aliases`,
`test_deal_id_to_deal_name`, `test_fuzzy_accept`, `test_fuzzy_clarify`,
`test_fuzzy_tie_clarifies`, `test_unknown_unsupported`, `test_flags_and_years`,
`test_first_failure_decides`, `test_non_answer_unchanged`.

**Step 4.4: narration and number guard.** `rmbsq/llm/narrate.py`: `narrate(question,
spec, display_table, client, cfg, catalog) -> tuple[str, bool, list[str]]` (no tools; at
most `narration_max_rows` rows with a `truncated` flag; a trip returns the template) and
`template_answer(spec, display_table)`. `rmbsq/llm/guard.py`: `number_guard(text,
question, display_table, catalog) -> list[str]`, the F.2 order: strip periods, deal names
and fixed labels (longest first, not touching a letter, digit or `.`), extract with
`-?\d[\d,]*\.?\d*(%|m\b)?`, ignore question numbers and bare years 2016 to 2026, allow the
numbers of every display cell. Tests in `tests/test_guard.py`: `test_guard_cases` (13
cases), `test_narrate_passes`, `test_narrate_trips_to_template`, `test_template_formats`,
`test_truncation_flag`.

**Step 4.5: baseline.** `rmbsq/llm/baseline.py`: `baseline_sql(question, output_columns,
client, cfg) -> str` (tool `submit_sql`, forced; "" when the block is missing) and
`run_baseline_sql(sql, con, cfg) -> pd.DataFrame | None` (None for "", a
`threading.Timer(baseline_timeout_s, con.interrupt)`, `BaselineError` on any database
error or interrupt). Tests in `tests/test_baseline.py`: `test_baseline_parse`,
`test_baseline_timeout` (1 s through a config copy, O-26), `test_baseline_cannot_write`,
`test_baseline_runs_select`.

**Step 4.6: pipeline and CLI.** `rmbsq/llm/answer.py::answer(question, client, con,
catalog, cfg) -> Answer` (question, spec_raw, spec_valid, spec, route, sql_duckdb,
sql_oracle, table, display, text, guard_tripped, offending, calls). `rmbsq/cli.py`:
`rmbsq ask "<question>" [--live] [--show-sql] [--db PATH]`, replay by default, default db
`data/canonical/rmbs.duckdb`; a replay cache miss prints `not in the cache; run with
--live` and exits 2. The console entry point is `[project.scripts] rmbsq =
"rmbsq.cli:main"`, installed with `uv pip install -e . --no-deps` (O-4). Tests in
`tests/test_answer.py`: `test_answer_end_to_end_replay` (S02's spec and a narration;
the table equals the S02 gold), `test_answer_clarify`, `test_answer_unsupported`,
`test_cli_cache_miss_exit_2`.

**Step 4.7: docs.** This section of `PLAN.md`, and `docs/CONVENTIONS_RESOLVED.md` for the
locked connection (B), the cache key (C.2) and the guard order (F.2).

## Section 5: eval

Instruction 05 fixes the questions (B), scoring (C), the runs (D) and the benchmark (E).
Its questions file is committed as `eval/questions.yaml`, a byte for byte copy, never
edited. This is the only section that calls the API, and only through
`scripts/run_eval.py --mode record` (D.3). Without `ANTHROPIC_API_KEY` the live run is
left for later by design: every other step is built in full, `data/llm_cache/` stays
empty and no eval output CSV is written.

**The trap set (instruction 05 B.1, amending kickoff 6.11 and part 7).** The traps are
definition traps, 2 items each: `arrears_units` (Q27, Q28: "2 or more missed payments"
read as 60+ days), `call_as_prepay` (Q29, Q30: clean-up call exits counted as
prepayments), `exit_rows` (Q31, Q32: exit rows counted as live loans) and `weighting`
(Q33, Q34: a simple mean where the metric is balance-weighted). The kickoff's `hardship`
and `resubmission` traps are dropped: both are undone in the canonical layer that both
systems read, and Section 2 proved that row for row. `outputs/trap_failures.csv` uses
these 4 names.

**Step 5.0: questions.** `eval/questions.yaml`, loaded by `load_items(path) ->
list[EvalItem]` in `rmbsq/eval/run.py`; `gold_spec` is parsed as a `QuerySpec`. Test
`tests/test_eval_items.py::test_questions_file`: 40 items (simple 10, grouped 10, time 6,
trap 8, ambiguous 4, unsupported 2), 2 items per trap name, every answer item has
gold_spec, output_columns and gold_sql, every gold_spec validates. Review evidence: id,
category and trap for all 40 items.

**Step 5.1: gold check.** Test `tests/test_eval_gold.py::test_gold_spec_equals_gold_sql`,
marked `full`: for every answer item, `execute(compile(gold_spec))` equals `gold_sql`'s
result by the C.3 rule. Review evidence: per item, values compared and max abs error.

**Step 5.2: scoring (instruction 05 C).** `rmbsq/eval/score.py`.
- Answer items: the system is correct only if its final spec intent is answer, spec_valid
  is true, the query ran, and the result matches gold by C.3. The baseline is correct only
  if its SQL ran and the result matches.
- Ambiguous items: the system is correct if its intent is clarify. The baseline is never
  correct (O-21 (b)); its intent is recorded.
- Unsupported items: the system is correct if its intent is unsupported; the baseline if
  its SQL is the empty string.
- C.3 result comparison against `gold_sql` run on the same connection: every
  `output_columns` name must be a result column (extras ignored); the key columns are the
  gold group_by dimensions plus `period_label`, each cell normalised (bool to yes/no, a
  whole-number int or float to `str(int(v))`, else `str(v).strip()`), and the result's
  key rows must equal gold's as a multiset, or in order when the gold spec has `order`
  (O-22 (a)); values are matched by key for each metric column, `pct` within absolute
  `tol_ratio_abs`, `aud_m` within relative `tol_balance_rel`, `count` equal after rounding
  and within 1e-9 of an integer; a null where gold is not null is wrong.
  `n_values_checked` counts compared cells and `max_abs_err` is the largest absolute
  difference, blank when nothing was compared.
- `wilson(k, n, z)`: centre (k + z²/2) / (n + z²), half width
  z √(k(n − k)/n + z²/4) / (n + z²).

Tests in `tests/test_eval_score.py`: key order with and without `order`, each tolerance
on both sides of its bound, extra columns ignored, a missing column, a null, bool and
float key normalisation, the C.2 rules for both systems, and `wilson` at (7, 10) and
(40, 40) against hand values with 6 dp.

**Step 5.3: runner (instruction 05 D.1, D.2).** `rmbsq/eval/run.py` (`run_system`,
`run_baseline`, `run_eval`), `rmbsq/eval/report.py` (`summarise`, `build_trap_failures`,
writers) and `scripts/run_eval.py --mode {record,replay}`.
- Per item the system runs `answer`: 1 spec call, plus 1 narration call when its intent
  ends as answer. The baseline makes 1 `baseline_sql` call with the item's
  `output_columns`, or `["period_label"]` for non-answer items.
- Record mode makes the missing calls into `data/llm_cache/`, then runs again in replay
  mode; the outputs always come from the replay pass. The database is
  `data/canonical/rmbs.duckdb` through `connect_readonly`.
- Outputs, LF, floats `%.10f`: `outputs/eval_results.csv` (kickoff part 7 columns; the
  baseline's intent is `sql`, `decline` or `error`; latency_s and the token columns are
  summed over the item's calls, from the cache), `outputs/eval_summary.csv` (system ×
  each category and `total`), `outputs/trap_failures.csv` and `outputs/eval_detail.jsonl`.
- `outputs/eval_detail.jsonl` holds 1 JSON object per (system, item), sorted keys: the
  question, intent, spec (system only), `sql_duckdb` or the baseline `sql`, the result
  rows as display strings (at most 20), text (system only), correct and error.

Tests in `tests/test_eval_run.py`, in replay against fixture caches for Q02, Q35 and Q39
in a temp cache dir, with a temp outputs dir: the 3 result rows per system, and the D.2
formats.

**Step 5.4: live run (instruction 05 D.3).** `python scripts/run_eval.py --mode record`
with `ANTHROPIC_API_KEY` set in the environment (never written to any file). About 40
spec, 34 narration and 40 baseline calls. Every file in `data/llm_cache/` is committed
with the outputs. Review evidence: `eval_summary.csv` in full; per item intent and
correct for both systems; the detail lines of every wrong item; 3 complete system
answers (Q11, Q35, Q39); guard trips; calls, tokens and live wall time.

**Step 5.5: replay reproduces.** Test
`tests/test_eval_replay.py::test_eval_replay_reproduces`, marked `full`: replay from the
committed cache into a temp dir reproduces `eval_results.csv`, `eval_summary.csv`,
`trap_failures.csv` and `eval_detail.jsonl` byte for byte (latency comes from the cache).
When `data/llm_cache/` is empty it calls `pytest.skip("no recorded eval cache")`, the one
permitted skip.

**Step 5.6: trap failures.** `build_trap_failures` in `rmbsq/eval/report.py`: 1 row per
wrong trap answer, `system, item_id, trap, expected, got`. `expected` is the gold first
metric's first value formatted by `format_table`; `got` is the same for the result, or the
intent or error text when there is no value. Test
`tests/test_eval_run.py::test_trap_failures_row_count`: the row count equals the number of
wrong trap answers in `eval_results.csv`.

**Step 5.7: scale benchmark (instruction 05 E, kickoff 6.12, O-23 (a)).**
`rmbsq/eval/benchmark.py` (`build_tiled_db(src, dst, copies)`, `run_benchmark(items,
src_db, tiled_db, cfg)`) and `scripts/run_benchmark.py`.
- `data/canonical/rmbs_x36.duckdb` (git-ignored): `fact_loan_month` and `dim_loan` copied
  with loan_id and deal_id prefixed `C{c:02d}-`, `dim_deal` with deal_id and deal_name
  prefixed the same way, `dim_period`, `hpi` and `cash_rate` copied once, and
  `agg_deal_month` rebuilt from the tiled fact with the Section 2 statement.
- All 34 answer items' gold specs through `compile` and `execute`, on the 1x and 36x
  databases, routes auto and fact, threads 1 and DuckDB's default (`threads = 0`); deal
  filters rewritten to copy `C00-` on 36x; 1 untimed warm-up then 5 timed repeats with
  `time.perf_counter`. `connect_readonly` gains `threads: int = 1`, 0 meaning DuckDB's
  default; the default connection stays 1 thread.
- Output `outputs/scale_benchmark.csv`: `item_id, db, db_rows, route, threads, median_s,
  max_s`. Timings are excluded from every byte check.

Tests in `tests/test_benchmark.py` on the small profile with copies = 3: the tiled row
count is 3 × the source; for S01 and S12, ratio metrics on the tiled database equal the
1x values to 1e-9, and balance_total and loan_count are 3 × to 1e-9 relative. Review
evidence: per (db, route, threads) the median and max of median_s over the 34 items, the
tiled build time and both database sizes.

## Section 6: repo write-up

Instruction 06 replaces the earlier plan for this section. Chat Claude wrote all the
prose, as 2 templates; Claude Code writes only code, generated tables, figures and the
values that fill the placeholders. No API call is made.

**Two states.** The eval is *pending* while `outputs/eval_summary.csv` doesn't exist (the
state committed in this section) and *recorded* once it does. `scripts/build_writeup.py`
regenerates every write-up file for whichever state the repo is in, so a reader who
records the eval with their own key gets updated documents from 1 command.

**Step 6.0: templates and render.** `templates/README.md.tmpl` and
`templates/DESIGN_RESPONSE.md.tmpl`, copied byte for byte from `instructions/06_templates/`,
and `templates/fixed_numbers.txt` (the design constants written as literals in the
templates). `rmbsq/deliverable/render.py::render(template_text, claims, blocks,
eval_recorded) -> str`: `{{name}}` scalars and blocks, `{{#eval}}` and `{{^eval}}`
sections. `rmbsq/deliverable/numbers.py::unexplained_numbers(rendered, claims, blocks,
fixed) -> list[str]`, the number check, also used by Section 7. Tests
`tests/test_render.py::test_render_sections`, `tests/test_numbers.py::test_number_check`.

**Step 6.1: summary outputs.** `scripts/build_summary.py`, run after `build_canonical.py`,
writes `outputs/data_summary.csv` (`rmbsq/eval/summary.py::data_summary`, with the step 2.6
comparison moved into `rmbsq/canonical/truth_check.py`), `outputs/compiler_check.csv`
(`compiler_check`: the 15 compiler gold specs and the 34 eval answer items, by the step 3.3
and 3.5 rules) and `outputs/trap_effects.csv` (`rmbsq/eval/traps.py`, gold through the
compiler and naive by SQL, including the dropped compounding trap). Full tests in
`tests/test_summary.py`: `test_data_summary_values`, `test_compiler_check`,
`test_trap_effects`.

**Step 6.2: claims.** `rmbsq/deliverable/claims.py::build_claims(eval_recorded) ->
pd.DataFrame` writes `deliverable/claims.csv` (`claim_id, value, display, source_file,
source_rule`); the eval claims exist only in the recorded state. Test
`tests/test_claims.py::test_claims_pending`.

**Step 6.3: figures and worked example.** `scripts/make_figures.py` (drawing code in
`rmbsq/deliverable/figures.py`) builds `outputs/arrears_90p_by_vintage.csv` through
`compile` and `execute` (O-32 (a)), then `outputs/figures/arrears_90p_by_vintage.png` and
`scale_benchmark.png`, and `eval_accuracy.png` in the recorded state only (deleted when
pending). The kickoff's `cpr_by_city.png` is dropped, as no document uses it.
`rmbsq/deliverable/examples.py` writes `outputs/worked_example.md` (eval item Q11's gold
spec through the compiler, no LLM) and, in the recorded state only,
`outputs/transcripts/01_answer.md`, `02_clarify.md` and `03_unsupported.md` (Q11, Q35 and
Q39, replayed). Test `tests/test_figures.py::test_figures_deterministic`.

**Step 6.4: documents.** `scripts/build_writeup.py` (with `rmbsq/deliverable/writeup.py`)
renders `README.md` and `docs/DESIGN_RESPONSE.md` and runs the number check on both. The
`eval_table` block is generated from `eval_summary.csv`. `docs/DESIGN_NOTE.md` is replaced
by `docs/DESIGN_RESPONSE.md`, and `tests/test_readme.py` by `tests/test_documents.py`:
`test_documents_current`, `test_documents_numbers_explained` and
`test_recorded_state_renders` (a constructed `eval_summary.csv` with made-up k values).

**Step 6.5: CI.** `.github/workflows/ci.yml`: on push and pull request to main,
`ubuntu-latest`, Python 3.12 through `astral-sh/setup-uv`, then `uv venv`,
`uv pip sync requirements-lock.txt`, `uv pip install -e . --no-deps`, `pytest -q` and
`pytest -q -m full`. No secrets. CI reads the committed `data/raw/`; the `full`
regeneration test of step 1.6 also proves the generator reproduces `MANIFEST.json`
(O-24). The 7.5 neutrality grep excludes `instructions/` and `.github/` (O-2). Review
evidence: the Actions run URL and result (O-25).

**Step 6.6: plan.** This section, updated for instruction 06.

## Section 7: send pack (`deliverable/`)

**Step 7.1: claims.** File `rmbsq/deliverable/claims.py` (`load_claims(path) -> dict[str,
str]`) and `deliverable/claims.csv` (`claim_id, value, source_file,
source_row_filter`), with every number either PDF uses. Test
`tests/test_claims.py::test_claims_recompute` (every claim recomputes from its source
and matches its display string). Review evidence: `claims.csv` in full, each with its
recomputed value.

**Step 7.2: design response.** `deliverable/design_response.md.tmpl` (from instruction
07) rendered by `render_markdown(template, claims) -> str` in
`rmbsq/deliverable/render.py` to `deliverable/design_response.md`. An unknown claim id
raises. Tests in `tests/test_design_response.py`: `test_no_unresolved_placeholders` and
`test_numbers_in_claims` (the 6.9 guard logic applied against `claims.csv`). Review
evidence: the rendered markdown in full.

**Step 7.3: results summary.** `deliverable/results_summary.md.tmpl` rendered to
`deliverable/results_summary.md`: the headline eval table with Wilson intervals,
`eval_accuracy.png`, the trap failure table, the scale result and the clarify
transcript, on exactly 1 A4 page. The page check runs in step 7.4. Review evidence: the
rendered markdown in full.

**Step 7.4: PDFs.** File `rmbsq/deliverable/pdf.py`: `build_pdf(markdown_text, figures,
out)` (reportlab Platypus, `page_size`, `font`) and `build_onepager(cfg, out)`, producing
`deliverable/Design_Response.pdf` and `deliverable/Results_Summary.pdf`. Tests in
`tests/test_pdf.py`: `test_page_counts` (≤ `design_max_pages`, = `summary_max_pages`,
read with pypdf), `test_figures_exist`, `test_claims_in_pdf_text` and
`test_build_twice_identical_text`. Review evidence: page counts; the extracted text of
the 1 page summary in full.

**Step 7.5: neutrality.** Test `tests/test_neutrality.py::test_no_banned_words`: a grep
over the whole repo, excluding `instructions/` and `.github/` (O-2), for the word list in
instruction 07 finds nothing. Instruction 07 keeps workflow keywords out of its word
list. Review evidence: the grep command and its (empty) output.

**Step 7.6: fresh-clone PDFs.** A fresh clone regenerates both PDFs from the committed
CSVs, with no network and no API key. No test; review evidence only (O-25): the
commands, and the extracted page text of both PDFs diffed against the committed build.
