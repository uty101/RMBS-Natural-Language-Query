# 08 Record the eval

Session 8 instructions for Claude Code. Run the live eval once, regenerate the write-up and both PDFs with the results, and commit everything, so nobody who clones the repo needs a key. This file beats `PLAN.md` (rule 13). Status file: `instructions/08_record_eval.status.md`.

---

## A. Before anything

1. `ANTHROPIC_API_KEY` must already be set in the environment. Check that it is non-empty without printing it: print only its length and its first 7 characters (`sk-ant-`). If it is missing, stop, write the status file and push.
2. The key must never reach a file, a log, a commit or the status file. That means no `.env` file and no echoing it.

---

## B. Steps

**8.1 Record.**
- Run `python scripts/run_eval.py --mode record`.
- Record the wall time, the number of API calls made, and the input and output tokens summed from the client's call log.
- If a call fails after the C.4 retries, stop and report the error text, with the key redacted.

**8.2 Key check.**
- Before staging anything, search every file in `data/llm_cache/` and `outputs/` for the substring `sk-ant`.
- Any hit is a stop condition: delete nothing, commit nothing, and report the file names only.

**8.3 Regenerate.**
- Run `python scripts/build_writeup.py`. It must report the recorded state, with 1 page for the summary.
- If the summary needs more than 1 page at 3.5 cm, follow instruction 07 D.3: stop and report.

**8.4 Tests.**
- Run `pytest -q` and `pytest -q -m full`.
- `test_eval_replay_reproduces` must now run and pass, not skip.

**8.5 Commit**, by explicit path, in 2 commits:
1. `eval: recorded cache and results`, holding every file in `data/llm_cache/`, plus `outputs/eval_results.csv`, `outputs/eval_summary.csv`, `outputs/trap_failures.csv` and `outputs/eval_detail.jsonl`.
2. `writeup: recorded state`, holding `README.md`, `docs/DESIGN_RESPONSE.md`, `deliverable/claims.csv`, `deliverable/results_summary.md`, both PDFs, `outputs/figures/eval_accuracy.png`, `outputs/transcripts/` and any other file `build_writeup.py` changed.

The commit identity is the repo's usual one.

**8.6 Fresh clone.**
- Clone into a short temp path. Install from the lock file, with no `ANTHROPIC_API_KEY` set in that shell.
- Run both pytest commands, then `build_writeup.py`.
- `git status` must stay clean.

---

## C. Review evidence (`review/section_8.md`)

1. `outputs/eval_summary.csv` in full.
2. For every item: id, category, system intent and correct, baseline intent and correct.
3. For every wrong answer by either system, its full `eval_detail.jsonl` line.
4. `outputs/trap_failures.csv` in full.
5. Every guard trip, with its offending tokens.
6. API calls made, total input and output tokens, and the live wall time.
7. The 8.2 search command and its (empty) output.
8. The summary page count and image height; the extracted text of `Results_Summary.pdf`.
9. Both pytest outputs from the fresh clone, run with no key set.

Then write `instructions/08_record_eval.status.md` and push. The status file says nothing about the key except whether it was present.
