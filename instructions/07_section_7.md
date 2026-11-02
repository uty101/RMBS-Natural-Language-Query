# 07 Section 7: the PDFs

Session 7 instructions for Claude Code. Build all of Section 7 (steps 7.0 to 7.5) in this session, without pausing. No API call is made. This file beats `PLAN.md`, which beats the kickoff (rule 13). Status file: `instructions/07_section_7.status.md`.

Section 6 already built the claims, the rendering and the number check, so this section is mostly about turning rendered markdown into 2 PDFs:

- `deliverable/Design_Response.pdf`, from `docs/DESIGN_RESPONSE.md`, at most 4 A4 pages;
- `deliverable/Results_Summary.pdf`, from a new template, exactly 1 A4 page.

The file committed by chat Claude for this session (copy byte for byte; never edit):

| source | destination |
|---|---|
| `instructions/07_templates/RESULTS_SUMMARY.md.tmpl` | `templates/RESULTS_SUMMARY.md.tmpl` |

As in Section 6, Claude Code writes no prose of its own into either PDF.

---

## A. Approval of Section 6, and O-43, O-44

Section 6 is approved. Chat Claude checked it on Linux, installing from the lock file:

- `pytest -q`: 229 passed. `pytest -q -m full`: 57 passed and 1 skipped.
- `build_writeup.py` on Linux reproduced every committed CSV and document byte for byte. Only the 2 PNGs differ, as the status file predicted.
- Both figures read correctly, and the rendered design response has no `{{` and every number traced.
- CI run 41120172784 is green.

**O-43: (a)** confirmed. This file replaces the stale `PLAN.md` Section 7 (step 7.5 below). **O-44: (a)** confirmed.

---

## B. Config additions (step 7.0)

Add these 3 keys under `[deliverable]` in `config.toml`:

```toml
author = "Utkarsh Malhotra"
date_label = "November 2026"
repo_url = "https://github.com/uty101/RMBS-Natural-Language-Query"
```

`date_label` is fixed in config rather than read from the clock, so builds are deterministic.

---

## C. Results summary template

- `templates/RESULTS_SUMMARY.md.tmpl` renders with the Section 6 `render` to `deliverable/results_summary.md`, with the same pending and recorded rules.
- The rendered file is committed. The number check runs on it, with `trap_table`, `eval_table` and `clarify_transcript` treated as blocks.

**C.1 `trap_table` block,** from `outputs/trap_effects.csv`. It has 1 row per CSV row, in CSV order, with 4 columns: trap, question (item_id), correct, naive mistake gives.

| trap | label | value format |
|---|---|---|
| arrears_units | Arrears units | pct2 |
| call_as_prepay | Calls as prepayments | pct1 |
| exit_rows | Exit rows as live loans | int |
| weighting | Unweighted average | pct2 |
| compounding | Averaging CPR (dropped, gap too small) | pct3 (× 100, 3 dp and %) |

The question column shows the item_id, except that `Q2_2025` displays as `Q2 2025 CPR`.

**C.2 `clarify_transcript` block,** recorded state only. It is the system's text for eval item Q35, from `outputs/eval_detail.jsonl`, rendered as an indented code block, 1 line per line of text.

**C.3 Images.** `![alt](path)` in a template is resolved relative to the repo root.

---

## D. Markdown to PDF (`rmbsq/deliverable/pdf.py`)

`build_pdf(markdown_text: str, out: Path, cfg, kind: Literal["design", "summary"], image_height_cm: float | None = None) -> int` returns the page count. It uses reportlab Platypus with `reportlab.rl_config.invariant = 1`, so 2 builds on 1 machine are byte-identical.

**D.1 Supported markdown,** and nothing else. Anything else raises `UnsupportedMarkdown(line_number, text)`.

| markdown | rendering |
|---|---|
| `# ` | the document title. The first line only, and exactly once |
| `## ` | a section heading |
| a blank line | ends a block |
| a paragraph | consecutive non-blank lines that are not another construct, joined with a space |
| `- ` | a bullet item. Consecutive items make 1 list |
| `**x**` | bold |
| `` `x` `` | monospace (Courier) |
| `[text](url)` | `text` as a link to url |
| a pipe table | header row, separator row, body rows. Every cell is inline markdown |
| a 4-space indented line | a code line. Consecutive ones make 1 block in Courier |
| a fenced block with ``` | a code block in Courier |
| `![alt](path)` | an image, full text width, with its aspect ratio kept |

Mermaid isn't supported. Neither document needs it.

**D.2 Page and styles.**

- A4 with 2 cm margins, font `cfg.deliverable.font`.
- Design response:
  - title 16 pt, headings 12 pt, body 10 pt with 13 pt leading, code 8.5 pt;
  - tables 9 pt with a 0.25 pt grey grid and a bold header row;
  - images with height capped at 8 cm.
- Summary:
  - title 13 pt, headings 10 pt, body and tables 8.5 pt with 10.5 pt leading, code 7.5 pt;
  - images at `image_height_cm`, keeping the aspect ratio by shrinking width.
- **Header block** under the title, in 9 pt grey: `<author> · <date_label>`.
- **Footer** on every page, in 7.5 pt grey: left `<repo_url>`, right `page N of M`. Use a 2-pass build for M.
- **Footnote** at the end of the design response only, in 8 pt grey: `All figures are generated from CSV files committed in the repo. The data is synthetic.`

**D.3 Fitting the summary to 1 page.**

1. Build it with `image_height_cm` 5.5.
2. While the page count is above 1, rebuild with 0.5 cm less, down to 3.5.
3. If it is still above 1 page at 3.5 cm, that is a stop condition: write the review and status files, and report the page count and the overflow.

Record the height used.

---

## E. Neutrality check (`tests/test_neutrality.py`)

`test_no_banned_words` runs `git ls-files` and reads every text file outside `instructions/` and `.github/`. It also extracts the text of both PDFs with pypdf. The test fails if any file contains, case-insensitively, any of these phrases:

```
interview
case study
hiring
recruit
take-home
take home
assessment
applicant
employer
cover letter
vacancy
job description
job application
```

The list lives only in this instruction file and in the test, as rule 16 says. Chat Claude grepped the repo for these phrases before writing this file, and found nothing outside `instructions/` and `.github/`.

---

## F. `build_writeup.py` gains the PDFs

After step 6 of the Section 6 order, it builds `deliverable/results_summary.md`, then both PDFs, in both states. It prints the page counts and the summary image height. The pending README already says it regenerates the PDFs, and this makes that true.

---

## G. Steps, with tests

**7.0 Config and template.** Apply B, then copy the template. Test `test_summary_template_pending`: it renders in the pending state with no `{{`, passes the number check, and the `eval` section is absent.

**7.1 Blocks** (C.1, C.2). Tests:
- `test_trap_table`: 6 rows, with Q29's correct and naive cells `21.6%` and `100.0%`, and Q32's `9,975` and `10,572`;
- `test_clarify_transcript_recorded`: on a constructed `eval_detail.jsonl` in a temp dir.

**7.2 PDF builder** (D). Tests:
- `test_markdown_subset`: every D.1 construct renders, and a line `> quote` raises `UnsupportedMarkdown`;
- `test_pdf_deterministic`: building the design response twice into temp files gives byte-identical PDFs;
- `test_footer_and_header`: the extracted text of page 1 contains the author, the date label and `page 1 of`.

**7.3 Build both PDFs** (F). Run `build_writeup.py` and commit both PDFs and `deliverable/results_summary.md`. Tests:
- `test_page_counts`: the design response has at most `design_max_pages` pages, and the summary exactly `summary_max_pages`;
- `test_claims_in_pdf_text`: every claim display string used by each document appears in that PDF's extracted text, with whitespace collapsed before comparing;
- `test_recorded_state_pdfs`: extend the Section 6 constructed recorded-state test to build both PDFs in a temp dir. The summary fits 1 page within D.3, and the eval table's values appear in its text.

**7.4 Neutrality** (E). Test `test_no_banned_words`.

**7.5 Plan.** Rewrite `PLAN.md` Section 7 to match this file, removing the stale names (`load_claims`, `render_markdown`, `source_row_filter`, `test_claims_recompute`), and commit it.

---

## H. Review evidence (`review/section_7.md`)

1. The page count of each PDF, and the summary image height used.
2. The extracted text of `Results_Summary.pdf`, in full.
3. The extracted text of page 1 of `Design_Response.pdf`.
4. A PNG render of each page of both PDFs, from `pypdfium2` if it is already installed or `pdftoppm` if it is on PATH, otherwise noted as not rendered, in `review/section_7_pages/`. Commit the renders. They are evidence, not outputs.
5. The constructed recorded-state summary: its page count and extracted text, marked as made-up numbers.
6. The neutrality grep result.
7. Both pytest outputs from a fresh clone.

Then write `instructions/07_section_7.status.md` and push.
