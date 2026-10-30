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

**Step 3.1: catalogue.** Files `semantic/metrics.yaml` (exactly the 12 metrics of 6.3),
`semantic/dimensions.yaml` (exactly the 18 dimensions of 6.5, with the 5 deal level ones
marked) and `rmbsq/semantic/catalog.py` (`load_catalog(metrics_yaml: Path, dims_yaml:
Path) -> Catalog`, allowed values loaded from the canonical DB). Metric keys are `name,
kind, numerator, denominator, display, definition`; dimension keys are `name, column,
table, level, labels, definition` (O-30). Tests in `tests/test_catalog.py`:
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
`fact_loan_month` (O-18). Tests in `tests/test_compiler.py`:
`test_fifteen_specs_match_hand_sql` (15 specs and hand SQL supplied in instruction 03,
equal to 1e-9 on `small_db`) and `test_quarter_compounding_hand_example`. Review
evidence: per spec, the DuckDB SQL, the hand SQL and the max abs difference; the hand
example's arithmetic line by line.

**Step 3.4: routing.** In `compiler.py`: route `auto` picks `agg` when every group_by and
filter dimension is deal level, else `fact`. Test
`tests/test_routing.py::test_fact_and_agg_routes_equal` (every deal level test spec,
results equal on both routes). Review evidence: per spec, the route `auto` chose and the
max abs difference between routes.

**Step 3.5: Oracle rendering.** In `compiler.py`: `sql_oracle` rendered from the same tree
with `dialect="oracle"`. Test
`tests/test_oracle_render.py::test_specs_render_to_oracle_without_warnings`, which fails
on any `sqlglot` unsupported warning. Review evidence: the Oracle SQL for 3 test specs;
the captured warning list (expected empty).

**Step 3.6: display formatting.** Implements `format_table(df, catalog) -> DataFrame` in
`rmbsq/semantic/format.py`: percentages with 2 dp, balances as `A$412.3m`, counts as
integers with thousands separators (5.2, 5.3). Test
`tests/test_format_table.py::test_display_rules`. Review evidence: 1 raw frame and its
formatted frame side by side.

## Section 4: LLM layer

**Step 4.1: cached client.** File `rmbsq/llm/client.py`, `LLMClient(cfg, mode="replay")`
with `.call(system, messages, tools, tool_choice) -> dict`. The cache key is the SHA-256
of the JSON of (model, system, messages, tools, tool_choice, temperature).
`data/llm_cache/<key>.json` stores the request and response. `replay` raises
`CacheMiss` on a miss; `record` is the only network path. Tests in
`tests/test_llm_client.py`: `test_cache_key_stable`, `test_replay_hit`,
`test_replay_miss_raises_cachemiss`, `test_sockets_disabled_in_replay`. Fixtures are
hand-written JSON in `tests/fixtures/llm_cache/`. Review evidence: 1 fixture request,
its key, and the fixture file listing.

**Step 4.2: spec prompt and agent.** Files `prompts/spec_system.md` (rendered with the
metric and dimension catalogues, including the clarify and unsupported rules of 6.8) and
`rmbsq/llm/spec_agent.py` (`question_to_spec(question, client, catalog) -> QuerySpec`, 1
tool `submit_spec` with input schema `QuerySpec.model_json_schema()`, `tool_choice`
forced). Tests in `tests/test_spec_agent.py`: `test_prompt_contains_catalog_names` and
`test_fixture_responses_parse`. Review evidence: the rendered prompt in full; each
fixture response and its parsed spec.

**Step 4.3: entity resolution.** File `rmbsq/llm/resolve.py`, `resolve_entities(spec,
catalog, aliases) -> QuerySpec`. An exact match or an alias is kept.
`rapidfuzz.fuzz.token_set_ratio` then decides: unique best ≥ `accept` replaces; best in
[`clarify`, `accept`) or a tie ≥ `clarify` gives clarify with the top `top_k`;
below `clarify` gives unsupported with reason `unknown <dimension> value '<v>'`. Deal
aliases take the 3 forms of 6.8. Decisions (O-20): exact matching is case-insensitive;
fuzzy matching applies to the text dimensions only (deal_name, originator,
trustee_format, city, state, area, suburb, rate_type, occupancy); numeric and flag
dimensions match exactly or go to `unsupported`; an alias resolves to its deal_name, and
a deal_id filter value that is not a deal_id but matches a deal_name or an alias has its
filter key rewritten to deal_name. Tests in `tests/test_resolve.py`: `test_deal_aliases`,
`test_score_bands`, `test_tie_handling`. Review evidence: the alias table for 3 deals;
each band case with its score and outcome.

**Step 4.4: narration and number guard.** Files `prompts/narrate_system.md`,
`rmbsq/llm/narrate.py` (`narrate(question, spec, table, client) -> tuple[str, bool]` and
`template_answer(spec, table) -> str`; at most `narration_max_rows` rows in, at most
`narration_max_words` words out) and `rmbsq/llm/guard.py` (`number_guard(text, question,
table) -> list[str]`, the 6.9 rules; a trip replaces the text with the template answer
and logs the offending number). Before extracting numbers, the guard strips every
dimension label in the catalogue (`30-59`, `60-70`, `<=60`, `>90`, `0-12`, `>60` and the
rest), every YYYY-MM and YYYY-Qn token and every deal_name, longest match first, then runs
the 6.9 regex on what is left (O-19). Test `tests/test_guard.py::test_guard_cases`, with
the cases supplied in instruction 04, including a passing answer and 1 hallucinated
figure. Review evidence: each guard case with its text, its extracted numbers and the
verdict.

**Step 4.5: baseline.** Files `prompts/baseline_system.md` (DDL with a comment on every
column, the 6.3 and 6.4 definitions in prose, and the column-naming instruction) and
`rmbsq/llm/baseline.py` (`baseline_sql(question, output_columns, client) -> str`, tool
`submit_sql`; the SQL runs on a read-only DuckDB connection with a
`baseline_timeout_s` timeout). Tests in `tests/test_baseline.py`:
`test_read_only_rejects_writes` and `test_timeout_enforced`; the timeout test passes a
modified copy of `Config` with a shorter `baseline_timeout_s` (O-26). Review evidence: the
write attempt and its error; the timed-out query with elapsed time.

**Step 4.6: CLI.** File `rmbsq/cli.py`: `rmbsq ask "<question>" [--live] [--show-sql]`,
built on `answer(question, client, con, catalog) -> Answer` (spec, sql, table, text) in
`rmbsq/llm/answer.py`. The console entry point is `[project.scripts] rmbsq =
"rmbsq.cli:main"`, installed with `uv pip install -e . --no-deps` (O-4). Test
`tests/test_cli.py::test_replay_end_to_end` (1 cached question, replay). Review evidence:
the CLI output for that question, verbatim. No live calls in this section.

## Section 5: eval

**Step 5.1: questions.** File `eval/questions.yaml`, exactly as given in instruction 05,
loaded by `load_items(path) -> list[EvalItem]` in `rmbsq/eval/run.py`. Test
`tests/test_eval_items.py::test_forty_items_category_counts` (40 items: simple 10,
grouped 10, time 6, trap 8, ambiguous 4, unsupported 2; each trap type on 2 items).
Review evidence: item_id, category and trap for all 40 items.

**Step 5.2: gold check.** Test `tests/test_gold.py::test_gold_spec_matches_gold_sql`:
compile(gold_spec) equals gold_sql to `gold_tol_abs` on every value, for every answerable
item. It runs on the full data and is marked `full` (O-31). Review evidence: per item,
rows compared and max abs difference.

**Step 5.3: run, score, report.** Files `rmbsq/eval/run.py` (`run_system`,
`run_baseline`), `rmbsq/eval/score.py` (`score`) and `rmbsq/eval/report.py` (`wilson`,
per category accuracy). Scoring follows 6.11: same row keys; abs `tol_ratio_abs` for
ratios and LTVs; rel `tol_balance_rel` for balances; exact for counts. Row order must
match for items with `order` set; otherwise row keys are compared as a set (O-22). An
empty baseline SQL string counts as correct only on unsupported items (O-21). Tests in
`tests/test_scoring.py`: `test_score_synthetic_frames` and `test_wilson_hand_values`
((7, 10) and (40, 40)). Review evidence: the hand Wilson values with the working; each
synthetic scoring case and its verdict.

**Step 5.4: live eval.** Script `scripts/run_eval_live.py`: record mode, writes
`data/llm_cache/`, `outputs/eval_results.csv` and `outputs/eval_summary.csv` (Section 7
columns). A missing `ANTHROPIC_API_KEY` is a stop condition: finish 5.1 to 5.3 and 5.5's
code, then stop and report. No test; the step is checked by review evidence only (O-25):
`eval_summary.csv` in full; `eval_results.csv` in full; the cache file count.

**Step 5.5: replay.** Test `tests/test_eval_replay.py::test_replay_reproduces_csvs`:
re-running the eval from the committed cache reproduces both CSVs on every column
except `latency_s`. It runs on the full data and is marked `full` (O-31). Review
evidence: the column-by-column comparison result.

**Step 5.6: trap failures.** `outputs/trap_failures.csv` (`system, item_id, trap,
expected, got`), built from the eval results by `build_trap_failures` in
`rmbsq/eval/report.py`. Test
`tests/test_trap_failures.py::test_row_count_matches_wrong_traps`. Review evidence: the
CSV in full.

**Step 5.7: scale benchmark.** File `rmbsq/eval/benchmark.py` (`build_tiled_db(src, dst,
copies)`, `run_benchmark(items, src_db, tiled_db, cfg)`) and script
`scripts/run_benchmark.py`, following 6.12: 36 copies with `C{cc}-` prefixes on loan_id,
deal_id and deal_name (`C07-HARB 2021-1`), `agg_deal_month` rebuilt, every answerable
gold spec on 1x and 36x, routes `auto` and `fact`, `warmup` then `repeats` timed runs,
each `thread_settings` value. Deal-filtered specs are rewritten to copy `C00-` on the 36x
database (O-23). Output `outputs/scale_benchmark.csv`, with timings excluded from byte
checks. Tests in `tests/test_benchmark.py`: `test_tiled_row_count` (copies × source rows)
and `test_tiled_pool_spec_matches_1x` (ratios equal, totals × copies), both on the small
profile. Review evidence: `scale_benchmark.csv` in full; the row count of each database.

## Section 6: repo write-up

**Step 6.1: figures.** `outputs/figures/eval_accuracy.png`,
`arrears_90p_by_vintage.png`, `cpr_by_city.png` and `scale_benchmark.png`, drawn by
`scripts/make_figures.py` from CSVs, each stating that the data is synthetic. The
by-vintage and by-city figures read `outputs/arrears_90p_by_vintage.csv` and
`outputs/cpr_by_city.csv`, built through `compile` from governed specs (O-32). No test;
review evidence only (O-25): each figure embedded, with its source CSV rows.

**Step 6.2: transcripts.** `outputs/transcripts/01_answer.md`, `02_clarify.md`,
`03_unsupported.md` from cached runs of the questions named in instruction 06. Each
holds the question, spec JSON, Oracle SQL, result table and narration. No test; review
evidence only (O-25): the 3 files in full.

**Step 6.3: design note.** `docs/DESIGN_NOTE.md`, at most 1,100 words, with the structure
given in instruction 06. It lists HPI regression and roll rate tools as phase 2
(correction 3.7). No test; review evidence only (O-25): the word count.

**Step 6.4: README.** `README.md`: a 1 paragraph summary, a mermaid architecture diagram,
the headline eval table generated from `eval_summary.csv`, the scale result, limitations
(including N = 1 per question and the baseline being given the definitions in writing),
and how to run it. Test `tests/test_readme.py::test_readme_numbers_match_csvs`. Review
evidence: the generated table and the CSV rows it came from.

**Step 6.5: CI.** `.github/workflows/ci.yml`: the suite offline on push, plus
`pytest -m full`. CI reads the committed `data/raw/`; the `full` regeneration test of
step 1.6 also proves the generator reproduces `MANIFEST.json` (O-24). The 7.5 neutrality
grep excludes `instructions/` and `.github/` (O-2). No test; the evidence is the link to
the green Actions run (O-25). Review evidence: the workflow file and that link.

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
