# 09 Write up the recorded eval as it came out

Session 9 instructions for Claude Code. Replace the eval prose with chat Claude's rewrite, add the claims it needs, and rebuild the documents and both PDFs. No API call is made and no recorded result changes. This file beats `PLAN.md` (rule 13). Status file: `instructions/09_eval_writeup.status.md`.

Files committed by chat Claude for this session (copy byte for byte over the current copies; never edit):

| source | destination |
|---|---|
| `instructions/06_templates/DESIGN_RESPONSE.md.tmpl` | `templates/DESIGN_RESPONSE.md.tmpl` |
| `instructions/06_templates/README.md.tmpl` | `templates/README.md.tmpl` |
| `instructions/07_templates/RESULTS_SUMMARY.md.tmpl` | `templates/RESULTS_SUMMARY.md.tmpl` |

---

## A. Approval of session 8c

Session 8c is approved. The eval is recorded and committed: the system got 37 of 40 and the baseline 35 of 40, as the status file reports. The deviation, where the Q11 baseline smoke call was made inside the full run, is accepted. The run made that call live and got a valid reply.

---

## B. Why the prose changes

The old eval paragraphs framed the result as a win for the governed system. The recorded detail shows something narrower:

- On the 34 answer items, the baseline got 33 and the system 31.
- Neither system returned a wrong number. Every miss on both sides was a refusal:
  - the system's misses were Q09 (unsupported, "Queensland" not resolved to `QLD`), and Q27 and Q28 (clarify on "missed payments");
  - the baseline's misses were Q28 and Q35 to Q38, all declines.
- The system's overall lead comes only from the 4 ambiguous items, where it asked and the baseline declined.

Chat Claude rewrote the eval sections of all 3 templates to say this plainly. The rewrite also adds 1 sentence in the design response's trap section, and 1 line in its "next" section. The text is chat Claude's, and Claude Code writes no prose.

---

## C. New claims (recorded state only; amends instruction 06 D)

All are computed from `outputs/eval_results.csv` and `eval/questions.yaml`, and formatted `int`. An "answer item" is an item with `expected_intent` answer.

| claim_id | rule |
|---|---|
| answer_n | number of answer items |
| sys_answer_k | system rows on answer items with correct true |
| base_answer_k | the same, for the baseline |
| sys_wrong_numbers | system rows on answer items with intent `answer`, an empty error, and correct false |
| base_wrong_numbers | baseline rows on answer items with intent `sql`, an empty error, and correct false |
| base_ambig_declined | baseline rows in category ambiguous with intent `decline` |
| sys_clarified_traps | system rows in category trap with intent `clarify` |

Expected values: 34, 31, 33, 0, 0, 4 and 2.

---

## D. Steps

**9.1 Templates and claims.**

- Copy the 3 templates and add the C claims.
- Add `test_new_eval_claims`, which checks the C expected values against the committed CSVs.
- Add `test_eval_prose_conditions`. The prose names specific misses, so this test pins the facts it describes. If a future re-record changes them, the test fails, and the prose gets revisited rather than silently going wrong. It asserts that:
  - the system's wrong items are exactly Q09, Q27 and Q28, with intents unsupported, clarify and clarify;
  - Q09's `unsupported_reason` in `eval_detail.jsonl` contains `Queensland`;
  - the baseline's wrong items all have intent `decline`;
  - `sys_wrong_numbers` and `base_wrong_numbers` are both 0.

**9.2 Rebuild.**

- Run `python scripts/build_writeup.py` in the recorded state.
- The summary must still fit 1 page under instruction 07 D.3.
- Run both pytest commands.

**9.3 Commit** by explicit path:

- the 3 templates and the claims code with its tests;
- `README.md`, `docs/DESIGN_RESPONSE.md`, `deliverable/claims.csv` and `deliverable/results_summary.md`;
- both PDFs, plus any other file `build_writeup.py` changed.

Commit as `step 9: eval write-up matches the recorded result`. Push.

---

## E. Review evidence (`review/section_9.md`)

1. The rendered eval section of `docs/DESIGN_RESPONSE.md`, and the trap section that follows it, in full.
2. The rendered eval section of `README.md`.
3. The extracted text of `Results_Summary.pdf`, plus the page counts of both PDFs and the summary image height.
4. The 7 C claims, with their values.
5. Both pytest outputs from a fresh clone, with no key set.

Then write `instructions/09_eval_writeup.status.md` and push.
