# Status: session 9 (09_eval_writeup)

## Outcome

Complete. Steps 9.1 to 9.3 are done, committed and pushed. Evidence is in
`review/section_9.md`.

- Last step reached: 9.3.
- Stop reason: none.
- No API call was made, and no recorded result changed.

## Results

- The 3 templates are byte copies of the instruction sources.
- The 7 C claims match the expected values: `answer_n` 34, `sys_answer_k` 31,
  `base_answer_k` 33, `sys_wrong_numbers` 0, `base_wrong_numbers` 0,
  `base_ambig_declined` 4 and `sys_clarified_traps` 2.
- `test_new_eval_claims` and `test_eval_prose_conditions` are added, and both pass.
- `build_writeup.py` ran in the recorded state. `Design_Response.pdf` is 3 pages, and
  `Results_Summary.pdf` is 1 page at 5.5 cm.
- `pytest -q` 246 passed, and `pytest -q -m full` 58 passed.
- Fresh clone of `3c3bf3e` with no key set:
  - `pytest -q` 246 passed, and `pytest -q -m full` 58 passed;
  - `build_writeup.py` exit 0;
  - `git status` clean.

## Deviations (detail in the review)

- `tests/test_documents.py::render_recorded` now also copies the committed
  `outputs/eval_results.csv` into its constructed recorded-state folder. Without it,
  `test_recorded_state_renders` and `test_recorded_state_pdfs` failed with
  `FileNotFoundError`, because the new claims read that file. No assertion changed.
- `answer_n` cites `eval/questions.yaml` as its source file.

## Questions for the reviewer

None.

## Not done, for the user

- The fresh-clone folder `C:\s9fc` is left on disk. It is safe to delete, and so is
  `C:\s8fc` from session 8.

## Last 3 commits on origin (before this file)

```
3c3bf3e step 9: eval write-up matches the recorded result
0bc4549 instruction 09: write up the recorded eval as it came out
0478610 section 8: status file
```
