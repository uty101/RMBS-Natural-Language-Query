# Status: session 6 (06_section_6)

## Outcome

Complete. Steps 6.0 to 6.6 are built, committed and pushed. Evidence is in
`review/section_6.md`.

- Last step reached: 6.6.
- Stop reason: none.
- The write-up is committed in the pending state: `outputs/eval_summary.csv` doesn't
  exist, as instruction 06 A says.
  - There is no `eval_accuracy.png` and no `outputs/transcripts/`.
  - The recorded state is proved by `test_recorded_state_renders` on a constructed
    `eval_summary.csv` with made-up k values. It is printed in the review as K.4, marked
    as made-up.
- No API call was made in this session.
- CI passed first time on push of `4814311`:
  https://github.com/uty101/RMBS-Natural-Language-Query/actions/runs/41120172784
  - `pytest -q`: 229 passed.
  - `pytest -q -m full`: 57 passed, 1 skipped.
- The headline values the documents now carry, all generated from committed CSVs:
  - 773,336 loan-months from 774,057 raw rows, with 721 duplicates;
  - 17 called deals, 7 of them in format B;
  - 0 truth mismatches;
  - 49 of 49 compiler checks match, worst 1.6e-15, and 49 render to Oracle;
  - at 36x, every query runs in under 0.75 s with default threads, and the slowest
    single-threaded run takes 3.34 s;
  - the 6 C.3 trap values match chat Claude's to 1e-4.

## After recording the eval

Run `python scripts/build_writeup.py`. It switches to the recorded state and regenerates
the following, with no key needed after the record run:

- `README.md` and `docs/DESIGN_RESPONSE.md`;
- `deliverable/claims.csv`;
- the figures, including `eval_accuracy.png`;
- the transcripts.

Then commit those files. `test_documents_current` will fail until they are committed,
which is the intended guard.

## What was built

- 6.0:
  - `templates/` (2 template copies and `fixed_numbers.txt`);
  - `rmbsq/deliverable/render.py`;
  - `rmbsq/deliverable/numbers.py`;
  - `tests/test_render.py` and `tests/test_numbers.py`.
- 6.1:
  - `scripts/build_summary.py`;
  - `rmbsq/eval/summary.py`, `rmbsq/eval/traps.py` and `rmbsq/canonical/truth_check.py`;
  - `tests/test_summary.py` (full), plus `tests/test_canonical_truth.py` changed to call
    the moved comparison;
  - 3 CSVs: `data_summary`, `compiler_check` and `trap_effects`.
- 6.2: `rmbsq/deliverable/claims.py` and `tests/test_claims.py`.
- 6.3:
  - `scripts/make_figures.py`;
  - `rmbsq/deliverable/figures.py` and `rmbsq/deliverable/examples.py`;
  - `tests/test_figures.py`;
  - `outputs/arrears_90p_by_vintage.csv`.
- 6.4:
  - `scripts/build_writeup.py` and `rmbsq/deliverable/writeup.py`;
  - `tests/test_documents.py`;
  - `README.md` and `docs/DESIGN_RESPONSE.md`;
  - `deliverable/claims.csv`;
  - the 2 figures;
  - `outputs/worked_example.md`.
- 6.5: `.github/workflows/ci.yml`.
- 6.6: `PLAN.md` Section 6.

## Deviations (detail in the review, per step)

- `render.py` adds `names_used` and `resolve_sections`. The number check is given only
  the claims a document uses.
- The number check reads deal names from `build_deals` (no random draws), not the
  database.
- `build_claims` has 2 extra keyword arguments with defaults (`outputs`, `out`).
- `claims.csv` writes float values in full (`repr`).
- `pp1` is not implemented, because no claim uses it (O-44).
- In `trap_effects.csv`, Q32's loan counts are written as integers.
- The figure drawing code is in `rmbsq/deliverable/figures.py`, with
  `scripts/make_figures.py` as the entry point. Figure layout details F leaves open are
  listed in the review.
- `test_figures_deterministic` compares 2 temp builds, not the committed PNGs.
  - PNG bytes can differ across platforms.
  - On Windows, a fresh-clone `build_writeup.py` did reproduce the committed PNGs.
- The transcript code path is built but not run, because the cache is empty.

## Test results (fresh clone of `4814311`, Windows, Python 3.12.13, from the lock file)

- `pytest -q`: 229 passed, 58 deselected.
- `pytest -q -m full`: 57 passed, 1 skipped (no recorded eval cache), 229 deselected.
- `build_writeup.py` in the same clone, starting with no database: exit 0, and
  `git status` stayed clean.
- `c8938d7` (step 6.6) changes only `PLAN.md`.

## Questions for the reviewer

1. **O-43 (step 6.6): `PLAN.md` Section 7 and its header predate instruction 06.**
   - They name `load_claims`, `render_markdown`, `source_row_filter` and
     `test_claims_recompute`.
   - The pending README says `build_writeup.py` regenerates "the PDFs", which Section 7
     builds.
   - (a) Leave them for instruction 07, and add the PDF build to `build_writeup.py` in
     Section 7. **Done.**
   - (b) Update them now.
2. **O-44 (step 6.2): the `pp1` display string.**
   - (a) Leave it unimplemented until a claim uses it. **Done.**
   - (b) Implement it as × 100, 1 dp, then " pp".

## Not done, for the user

- The fresh-clone folder `C:\s6fc` (with clone `C:\s6fc\r`) is left on disk. It is safe
  to delete, as are the earlier `C:\s3fc`, `C:\s4fc` and `C:\s5fc`. An automatic safety
  check blocked a cleanup `rm -rf` in this session, so nothing was deleted.
- The CI run log has 2 annotations: actions on Node.js 20 forced to Node.js 24, and
  `ubuntu-latest` moving to Ubuntu 26. Neither failed the run.

## Last 3 commits on origin (before this file)

```
0c7a4d4 section 6: review file
c8938d7 step 6.6: PLAN.md Section 6 updated for instruction 06, with the pending and recorded states and the new outputs
4814311 step 6.5: CI runs the suite and the full-profile tests on push and pull request to main
```
