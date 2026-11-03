# RMBS Natural Language Query

Ask questions of loan-level RMBS data in plain English, and get numbers you can check. A language model turns each question into a small JSON query spec. A compiler turns the spec into SQL over governed metric definitions, so the model never does the arithmetic. Every answer comes with its spec, its Oracle SQL and the table it came from, and a guard rejects any narrated number that isn't in that table.

All data in this repo is synthetic: 50 Australian RMBS deals, 21,945 loans and 773,336 loan-months from 2021-10 to 2026-09, delivered in 2 trustee formats with the inconsistencies real trustee data has. The reasoning behind the design is in [docs/DESIGN_RESPONSE.md](docs/DESIGN_RESPONSE.md).

## Results

**Governed system against plain text-to-SQL, same 40 questions.** On the 34 questions with a numeric answer, plain text-to-SQL got 33 right and the governed system 31. Neither returned a wrong number (0 and 0), so every miss on both sides was a refusal.

- The governed system couldn't resolve "Queensland", and asked for a day threshold on questions phrased in missed payments.
- Plain SQL declined all 4 ambiguous questions where the governed system asked.

Overall, the governed system got 37 of 40 (92.5%, 95% interval 80.1% to 97.4%) and plain SQL 35 of 40 (87.5%, interval 73.9% to 94.5%). The plain model's prompt held the full written metric definitions and the exact output columns, so this compares 2 ways of delivering the same definitions, not definitions against none. The full reading is in the design response.

| category | questions | governed system | plain text-to-SQL |
|---|---|---|---|
| simple | 10 | 9 (90%) | 10 (100%) |
| grouped | 10 | 10 (100%) | 10 (100%) |
| time | 6 | 6 (100%) | 6 (100%) |
| trap | 8 | 6 (75%) | 7 (88%) |
| ambiguous | 4 | 4 (100%) | 0 (0%) |
| unsupported | 2 | 2 (100%) | 2 (100%) |
| total | 40 | 37 (92%) | 35 (88%) |

![Accuracy by category](outputs/figures/eval_accuracy.png)

**Cleaning, proved row for row.** The raw trustee files hold 774,057 rows, including 721 resubmitted duplicates. Format B codes its 7 clean-up calls as ordinary repayments. The canonical table rebuilt from those files matches the simulated truth on all 773,336 loan-months, with 0 mismatches.

**Compiler, checked against hand-written SQL.** 49 of 49 hand-written queries match the compiler, and the worst difference is 1.6e-15. All 49 render to Oracle without a construct Oracle can't run.

**Scale.** Copied 36 times to 27,840,096 loan-months, all 34 answerable eval questions run in under 0.75 seconds each with DuckDB's default threads; the slowest single-threaded run takes 3.34 seconds.

![Query time at 1x and 36x](outputs/figures/scale_benchmark.png)

## How it works

```mermaid
flowchart LR
  Q[Question] --> S[LLM writes a query spec]
  S --> V{Valid?}
  V -- no --> X[Decline]
  S --> R[Resolve names and aliases]
  R --> C{Clear?}
  C -- no --> K[Ask a clarifying question]
  C -- yes --> P[Compile to SQL over governed metrics]
  P --> D[(Canonical loan-month tables)]
  D --> T[Result table]
  T --> N[LLM narrates from the table]
  N --> G{Every number in the table?}
  G -- yes --> A[Answer with spec, Oracle SQL and table]
  G -- no --> F[Plain table summary instead]
```

## The data

The synthetic pool follows the RBA cash rate from 2016 and suburb house price indices, with interest-only and fixed-rate expiries, lenders mortgage insurance and hardship arrangements. 90+ arrears by balance rise from 0.18% to a peak of 1.54% in 2024-08, then ease to 0.47%.

![90+ arrears by vintage](outputs/figures/arrears_90p_by_vintage.png)

The 2 trustee formats differ in arrears units (days against missed payments), hardship coding, how clean-up calls are reported, and money units. A few months are resubmitted on top of the originals. The canonical layer in `rmbsq/canonical/` undoes all of it.

## Limitations

- The data is synthetic. It is built to carry real traps, not to forecast real deals.
- The eval is 40 questions, run once. Each category holds at most 10 questions, so intervals are wide. Current Claude models don't take a sampling temperature, so a rerun can differ, and repeat-run stability isn't measured. The recorded cache makes this run reproducible.
- Oracle SQL is rendered and checked for constructs Oracle can't run, but not executed against Oracle. The timings are DuckDB timings on 1 machine.

## Running it

```bash
uv venv --python 3.12 .venv
uv pip sync --python .venv requirements-lock.txt
uv pip install --python .venv -e . --no-deps
python scripts/build_canonical.py --raw data/raw --db data/canonical/rmbs.duckdb
rmbsq ask "What is the 90+ arrears rate by balance for each state now?" --show-sql
pytest -q && pytest -q -m full
```

`rmbsq ask` replays from the recorded cache. Add `--live` and set `ANTHROPIC_API_KEY` to ask new questions.

## Repo map

| path | what it holds |
|---|---|
| `rmbsq/synth/` | the synthetic data generator |
| `rmbsq/canonical/` | trustee file ingestion and cleaning |
| `rmbsq/semantic/` | metric catalogue, query spec and compiler |
| `rmbsq/llm/` | prompts, cache, name resolution, narration and number guard |
| `rmbsq/eval/` | eval runner, scoring and scale benchmark |
| `eval/questions.yaml` | the 40 eval questions, with gold specs and SQL |
| `outputs/` | every committed result, as CSV, plus figures |
| `deliverable/` | the 2 PDFs |
| `instructions/`, `review/` | how the repo was built, section by section, and the evidence for each |
