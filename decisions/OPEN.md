# Open decisions

Raised in session 6 (`instructions/06_section_6.md`). Evidence is in
`review/section_6.md`. O-40, O-41 and O-42 were all confirmed as (a) by instruction 06 A.

## O-43. Step 6.6: `PLAN.md` Section 7 and its header predate instruction 06

Step 6.6 updates `PLAN.md` Section 6 only. The header (module homes) and Section 7 still
name things that instruction 06 built differently:

| | `PLAN.md` says | instruction 06 built |
|---|---|---|
| claims | `load_claims(path)` | `build_claims(eval_recorded)` |
| claims columns | `source_row_filter` | `display` and `source_rule` |
| render | `render_markdown(template, claims)` | `render(template_text, claims, blocks, eval_recorded)` |
| claims test | `tests/test_claims.py::test_claims_recompute` | `tests/test_claims.py::test_claims_pending` |

Also, the pending README, written by chat Claude, says `build_writeup.py` regenerates
"the PDFs", but the PDFs are built in Section 7.

- (a) Leave Section 7 and the header for instruction 07 to replace, and add the PDF build
  to `build_writeup.py` in Section 7. **This is what is done.**
- (b) Update Section 7 and the header now, to the names instruction 06 built.

## O-44. Step 6.2: the `pp1` display string

Instruction 06 D lists the format `pp1` as "percentage points with 1 dp", but no claim
uses it, and its exact string (unit, spacing) isn't given.

- (a) Leave it unimplemented until a claim needs it. **This is what is done.**
- (b) Implement it now as the value × 100 with 1 dp, then " pp", for example `3.2 pp`.
