# 10 Language pass

Session 10 instructions for Claude Code. Replace the 3 document templates with chat Claude's rewrite, change the labels below in code, and rebuild everything. No API call is made, and no number changes. This file beats `PLAN.md` (rule 13). Status file: `instructions/10_language.status.md`.

Files committed by chat Claude for this session (copy byte for byte over the current copies; never edit):

| source | destination |
|---|---|
| `instructions/10_templates/DESIGN_RESPONSE.md.tmpl` | `templates/DESIGN_RESPONSE.md.tmpl` |
| `instructions/10_templates/README.md.tmpl` | `templates/README.md.tmpl` |
| `instructions/10_templates/RESULTS_SUMMARY.md.tmpl` | `templates/RESULTS_SUMMARY.md.tmpl` |

Chat Claude checked that the new templates use exactly the same placeholders as the current ones, contain only literal numbers already in `templates/fixed_numbers.txt`, and contain no dashes between clauses.

---

## A. Approval of session 9

Session 9 is approved. Chat Claude checked it on Linux with no key set: 246 and 58 tests pass, both PDFs were rendered and read page by page, and no key appears in the repo.

---

## B. Label changes in code

The 2 systems are now called **compiled approach** and **direct SQL** everywhere a reader sees them. CSV values stay `system` and `baseline`.

| where | old | new |
|---|---|---|
| `rmbsq/deliverable/figures.py` `SYSTEM_LABELS` | `governed system`, `plain text-to-SQL` | `compiled approach`, `direct SQL` |
| `rmbsq/deliverable/writeup.py` `TABLE_SYSTEMS` | `governed system`, `plain text-to-SQL` | `compiled approach`, `direct SQL` |
| scale figure title | `Query time per eval question, 1x and 36x data` | `Query time per test question, at 1x and 36x data volume` |
| accuracy figure y label | `correct` | `share correct` |
| `trap_table` header | `trap, question, correct, naive mistake gives` | `mistake, question, correct, with the mistake` |
| `trap_table` row label, arrears_units | `Arrears units` | `2 missed payments read as 60+ days` |
| row label, call_as_prepay | `Calls as prepayments` | `Clean-up calls counted as prepayments` |
| row label, exit_rows | `Exit rows as live loans` | `Exit month counted as a live loan` |
| row label, weighting | `Unweighted average` | `Simple average, not balance-weighted` |
| row label, compounding | `Averaging CPR (dropped, gap too small)` | `Monthly CPR averaged, not compounded (dropped)` |
| `eval_table` column headers | `category, questions, governed system, plain text-to-SQL` | `category, questions, compiled approach, direct SQL` |

The new arrears_units label holds the literal numbers `2`, `60` and `90` (from `60+`). Add `60` to `templates/fixed_numbers.txt`, since `2` and `90` are already there. The trap table is a block, so it is excluded from the number check anyway. This keeps the list complete.

Update any test that asserts the old labels, changing only the expected strings.

---

## C. Steps

**10.1 Templates and labels.** Copy the 3 templates and apply B.

**10.2 Rebuild.**
- Run `python scripts/build_writeup.py` in the recorded state. The summary must still fit 1 page under instruction 07 D.3.
- Run both pytest commands.
- Grep the rendered `README.md`, `docs/DESIGN_RESPONSE.md` and `deliverable/results_summary.md`, plus the text of both PDFs, for `governed`, `plain text-to-SQL`, `plain English`, `plain SQL` and `naive`. Expect no hits; report any.

**10.3 Commit** by explicit path, as `step 10: language pass on the documents and labels`:
- the templates, `fixed_numbers.txt`, the code and test changes;
- `README.md`, `docs/DESIGN_RESPONSE.md`, `deliverable/claims.csv` and `deliverable/results_summary.md`;
- both PDFs and the figures, plus any other file `build_writeup.py` changed.

Push.

---

## D. Review evidence (`review/section_10.md`)

1. The 10.2 grep command and its output.
2. Page counts of both PDFs and the summary image height.
3. The extracted text of `Results_Summary.pdf` in full.
4. Both pytest outputs from a fresh clone, with no key set.

Then write `instructions/10_language.status.md` and push.
