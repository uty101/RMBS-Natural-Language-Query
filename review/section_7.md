# Review: Section 7, the PDFs

Follow this template exactly. Every number below must be backed by raw rows or raw
output printed in full in this file (CLAUDE.md rule 10). No paraphrased results.

## 1. Outcome

- Instruction file: `instructions/07_section_7.md`
- Outcome: complete
- Last step reached: 7.5
- Stop reason (if stopped): none. The summary fits 1 page at the first image height,
  5.5 cm, so D.3's stop condition was not reached. The design response is 3 pages, within
  the limit of 4.
- No API call was made in this session. The write-up stays in the pending state.

## 2. Commits

Output of `git log --oneline` for this section's commits, oldest last, pasted verbatim.

```
47e047a step 7.5: PLAN.md Section 7 rewritten for instruction 07, with the stale names removed
d6a7ae3 step 7.4: neutrality test over tracked text files and the text of both PDFs
7e67d5f step 7.3: build_writeup renders results_summary.md and builds both PDFs, 3 pages and 1 page at 5.5 cm
01aad97 step 7.2: markdown subset to PDF with reportlab, header, footer with page N of M, deterministic builds
7caaa58 step 7.1: trap table and clarify transcript blocks, with the recorded-state helper writing a made-up Q35 detail row
49b2ade step 7.0: deliverable config keys, the results summary template and its pending render with the trap table
```

Steps 7.0 to 7.5 were pushed together after the 7.5 commit, so that the fresh clone and CI
tested what is on origin. This review, `decisions/OPEN.md` and the status file follow.

CI run on push of `47e047a`:
https://github.com/uty101/RMBS-Natural-Language-Query/actions/runs/41448281610

```
$ gh run list --limit 1
completed	success	step 7.5: PLAN.md Section 7 rewritten for instruction 07, with the st…	ci	main	push	41448281610	46s	2026-11-02T12:52:54Z
$ gh run view 41448281610 --log | grep -E "passed|failed"
test	pytest -q	2026-11-02T12:53:22.4866659Z 240 passed, 58 deselected in 13.83s
test	pytest -q -m full	2026-11-02T12:53:37.2014876Z 57 passed, 1 skipped, 240 deselected in 13.72s
```

## 3. Steps

Unless a block says otherwise, every number comes from the committed CSVs in `outputs/`,
the pending state.

### Step 7.0: config and template

- Files: `config.toml`, `rmbsq/config.py` (3 fields on `Deliverable`),
  `templates/RESULTS_SUMMARY.md.tmpl` (byte copy), `rmbsq/deliverable/writeup.py`,
  `tests/test_results_summary.py`
- Signatures implemented: `SUMMARY = {"deliverable/results_summary.md":
  "RESULTS_SUMMARY.md.tmpl"}`; `render_documents(claims, blocks, recorded, documents=DOCUMENTS)`;
  `check_documents` looks a document's template up in `TEMPLATE_OF = DOCUMENTS | SUMMARY`
- Tests: `test_summary_template_pending`, and `tests/test_config.py` for the new keys,
  result passed
- Outputs: none committed in this step (`deliverable/results_summary.md` is committed in 7.3)
- Evidence:

```
$ cmp templates/RESULTS_SUMMARY.md.tmpl instructions/07_templates/RESULTS_SUMMARY.md.tmpl && echo same
same
$ sed -n '/\[deliverable\]/,$p' config.toml
[deliverable]
page_size = "A4"
design_max_pages = 4
summary_max_pages = 1
font = "Helvetica"
author = "Utkarsh Malhotra"
date_label = "November 2026"
repo_url = "https://github.com/uty101/RMBS-Natural-Language-Query"
```

```
$ pytest -v tests/test_results_summary.py::test_summary_template_pending tests/test_config.py
tests/test_results_summary.py::test_summary_template_pending PASSED
tests/test_config.py::test_config_round_trip PASSED
tests/test_config.py::test_originators_csv PASSED
tests/test_config.py::test_geography_csv PASSED
tests/test_config.py::test_cash_rate_csv PASSED
tests/test_config.py::test_hpi_drift_csv PASSED
============================== 6 passed in 0.44s ==============================
```

- Deviations from PLAN.md or the instruction file:
  - The pending summary needs the `trap_table` block, so `trap_table` was committed in
    7.0, with the summary wiring. Step 7.1 adds `clarify_transcript` and the 2 block tests.
  - `render_documents` gained a `documents` keyword (default `DOCUMENTS`, so Section 6
    callers are unchanged). The summary is rendered by the same function with `SUMMARY`.

### Step 7.1: blocks

- Files: `rmbsq/deliverable/writeup.py`, `tests/test_results_summary.py`,
  `tests/test_documents.py`
- Signatures implemented: `trap_table(traps: pd.DataFrame) -> str`;
  `clarify_transcript(detail_path: Path) -> str`; `blocks_for(outputs, recorded)` now
  returns `trap_table` in both states, and `eval_table` and `clarify_transcript` in the
  recorded state
- Tests: `test_trap_table`, `test_clarify_transcript_recorded`, and
  `test_recorded_state_renders` re-run, result passed
- Outputs: none
- Evidence: the source rows, then the rendered block.

```
$ cat outputs/trap_effects.csv
trap,item_id,gold,naive,naive_rule
arrears_units,Q27,0.0066313916,0.0058570250,2 or more missed payments read as 60+ days
call_as_prepay,Q29,0.2155508154,1.0000000000,clean-up call exits counted as prepayments
call_as_prepay,Q30,0.1831651907,0.4898374471,clean-up call exits counted as prepayments
exit_rows,Q32,9975,10572,exit rows counted as live loans
weighting,Q33,0.5196431995,0.5091750448,simple mean instead of balance weighting
compounding,Q2_2025,0.1806444857,0.1806323390,monthly CPR averaged instead of compounded
```

```
$ blocks_for(OUT, False)['trap_table']
| trap | question | correct | naive mistake gives |
|---|---|---|---|
| Arrears units | Q27 | 0.66% | 0.59% |
| Calls as prepayments | Q29 | 21.6% | 100.0% |
| Calls as prepayments | Q30 | 18.3% | 49.0% |
| Exit rows as live loans | Q32 | 9,975 | 10,572 |
| Unweighted average | Q33 | 51.96% | 50.92% |
| Averaging CPR (dropped, gap too small) | Q2 2025 CPR | 18.064% | 18.063% |
```

The clarify transcript in the constructed recorded state, from the made-up Q35 row (not a
result):

```
    Which arrears threshold do you mean?
    Options: 30+ days; 90+ days
```

```
$ pytest -v tests/test_results_summary.py::test_trap_table tests/test_results_summary.py::test_clarify_transcript_recorded tests/test_documents.py::test_recorded_state_renders
tests/test_results_summary.py::test_trap_table PASSED
tests/test_results_summary.py::test_clarify_transcript_recorded PASSED
tests/test_documents.py::test_recorded_state_renders PASSED
============================= 3 passed in 10.26s ==============================
```

- Deviations from PLAN.md or the instruction file:
  - `blocks_for` returns `trap_table` in both states, so the README and design response
    number checks also receive it. Neither template uses it, so removing its text from
    those documents is a no-op.
  - `render_recorded` in `tests/test_documents.py` (the Section 6 constructed recorded
    state) now also writes a made-up `eval_detail.jsonl` with 1 system row for Q35, because
    the recorded-state blocks read it. The text is marked made-up in the test. No Section 6
    assertion changed. Instruction 07 G 7.3 asks for this test to be extended.

### Step 7.2: PDF builder

- Files: `rmbsq/deliverable/pdf.py`, `tests/test_pdf.py`
- Signatures implemented: `build_pdf(markdown_text: str, out: Path, cfg, kind:
  Literal["design", "summary"], image_height_cm: float | None = None) -> int`;
  `UnsupportedMarkdown(line_number, text)`; also `parse(markdown_text) -> list[Block]` and
  `fit_summary(markdown_text, out, cfg) -> (pages, image_height_cm)` (D.3)
- Tests: `test_markdown_subset`, `test_pdf_deterministic`, `test_footer_and_header`,
  result passed
- Outputs: none
- Evidence:

```
$ pytest -v tests/test_pdf.py
tests/test_pdf.py::test_markdown_subset PASSED
tests/test_pdf.py::test_pdf_deterministic PASSED
tests/test_pdf.py::test_footer_and_header PASSED
============================== 3 passed in 1.82s ==============================
```

What `test_markdown_subset` checks: a document with every D.1 construct parses to the
blocks `title, heading, para, bullets, table, code, code, image`. It builds to 1 page in
both kinds, and the extracted text holds the bold, code and link text, both bullets, every
table cell and every code line. Page 1 carries 1 image and 1 link annotation to
`https://example.org`. `# T\n\n> quote\n` raises `UnsupportedMarkdown` with line 3 and text
`> quote`.

Other constructs outside D.1 raise too (ad hoc check in this session, not a test):

```
raises line 3: unsupported markdown: '### h3'
raises line 3: unsupported markdown: '* star'
raises line 3: unsupported markdown: '1. num'
raises line 3: unsupported markdown: '---'
raises line 3: unsupported markdown: '<b>x</b>'
raises line 3: unsupported markdown: '# second title'
raises line 3: unsupported markdown: 'text *italic* here'
raises line 4: unsupported markdown: 'continuation'
raises line 3: unsupported markdown: '| a |'
raises line 3: unsupported markdown: '```'
raises line 4: unsupported markdown: '> quote'
```

- Deviations from PLAN.md or the instruction file:
  - Images resolve relative to `cfg.root`, the folder holding `config.toml`, which is the
    repo root (C.3). This lets the recorded-state test point at a temp root holding
    `outputs/figures/eval_accuracy.png`.
  - Layout details D.2 leaves open, chosen to be plain:
    - the title and `##` headings are bold (`Helvetica-Bold`, from `tt2ps(font, 1, 0)`);
    - space after a paragraph is 0.6 × body size, and headings keep with the next block;
    - tables are left-aligned at their natural column widths (scaled down only if wider
      than the text), with 4 pt left and right cell padding;
    - bullets use `•`, and code blocks are indented by 1 body size;
    - images are left-aligned;
    - the footer baseline is 1 cm above the bottom edge;
    - the PDF metadata holds the title and the author.
  - A bullet item followed by a non-blank, non-bullet line raises, rather than being read
    as a continuation of the item. D.1 doesn't list continuation lines.
  - reportlab writes the `•` bullet as the WinAnsi code `\177` (0x7F), which its WinAnsi
    vector maps to the glyph `bullet`. pypdf extracts that code as the control character
    U+007F, not as `•`, on a line of its own before each item; it is invisible in H.3. The
    bullet renders, as checked by eye in this session (H.4). The header's `·` is written as
    `\267` and extracts correctly.

### Step 7.3: both PDFs

- Files: `scripts/build_writeup.py`, `rmbsq/deliverable/writeup.py`,
  `tests/test_deliverable_pdfs.py`, `tests/test_documents.py`,
  `tests/test_results_summary.py`, `deliverable/results_summary.md`,
  `deliverable/Design_Response.pdf`, `deliverable/Results_Summary.pdf`
- Signatures implemented: `write_pdfs(docs, cfg, root=ROOT) -> dict` (page counts, image
  height, paths); `PDFS` maps each kind to its markdown and PDF path
- Tests: `test_page_counts`, `test_claims_in_pdf_text`, `test_recorded_state_pdfs`, and
  `test_summary_current`, result passed
- Outputs: `deliverable/results_summary.md` (35 lines), `deliverable/Design_Response.pdf`
  (3 pages, 9,322 bytes), `deliverable/Results_Summary.pdf` (1 page, 61,214 bytes)
- Evidence:

```
$ .venv/Scripts/python scripts/build_writeup.py
summary outputs in 12.8 s
state: pending
Design_Response.pdf: 3 pages (at most 4)
Results_Summary.pdf: 1 pages (exactly 1), image height 5.5 cm
outputs/data_summary.csv
outputs/compiler_check.csv
outputs/trap_effects.csv
outputs/arrears_90p_by_vintage.csv
outputs/figures/arrears_90p_by_vintage.png
outputs/figures/scale_benchmark.png
outputs/worked_example.md
deliverable/claims.csv
README.md
docs/DESIGN_RESPONSE.md
deliverable/results_summary.md
deliverable/Design_Response.pdf
deliverable/Results_Summary.pdf
$ git status --short
(end of git status)
```

```
$ pytest -v tests/test_deliverable_pdfs.py tests/test_results_summary.py::test_summary_current tests/test_documents.py
tests/test_deliverable_pdfs.py::test_page_counts PASSED
tests/test_deliverable_pdfs.py::test_claims_in_pdf_text PASSED
tests/test_results_summary.py::test_summary_current PASSED
tests/test_documents.py::test_documents_current PASSED
tests/test_documents.py::test_documents_numbers_explained PASSED
tests/test_documents.py::test_recorded_state_renders PASSED
tests/test_documents.py::test_recorded_state_pdfs PASSED
============================= 7 passed in 13.37s ==============================
```

- Deviations from PLAN.md or the instruction file:
  - `test_summary_current` is added: the committed `results_summary.md` must equal the
    render of the committed state, the same guard `test_documents_current` gives the
    README and design response.
  - `build_writeup.py` exits 1 if the design response is above `design_max_pages`, or the
    summary is not exactly `summary_max_pages` after D.3. Neither happened.
  - The PDFs are not compared byte for byte with a fresh build in any test. The summary
    embeds `scale_benchmark.png`, whose bytes can differ across platforms (Section 6).
    Both PDFs are byte-identical across 2 builds on this machine (section 5).

### Step 7.4: neutrality

- Files: `tests/test_neutrality.py`
- Signatures implemented: `test_no_banned_words`
- Tests: `test_no_banned_words`, result passed
- Outputs: none
- Evidence: the grep, with the phrase list read from instruction 07 E into a file outside
  the repo, so the list isn't quoted here (CLAUDE.md rule 16). It prints nothing, and exit
  1 means no match.

```
$ awk '/^## E\./{f=1} f&&/^```/{c++; next} f&&c==1{print}' instructions/07_section_7.md > $SCRATCH/words.txt
$ wc -l < $SCRATCH/words.txt
13
$ git grep -I -i -n -F -f $SCRATCH/words.txt -- ':!instructions' ':!.github' ':!tests/test_neutrality.py'
$ echo $?
1
```

The test scans 164 tracked text files and both PDFs' text (ad hoc count in this session):

```
164 texts scanned; 1045029 chars
self excluded: True | raw included: True
```

```
$ pytest -v tests/test_neutrality.py
tests/test_neutrality.py::test_no_banned_words PASSED
============================== 1 passed in 0.68s ==============================
```

- Deviations from PLAN.md or the instruction file:
  - The test skips itself, because it holds the list. A file is binary, and skipped, when
    its first 8,000 bytes hold a NUL byte, as git decides. The PDFs are read through pypdf
    instead of as bytes.
  - It reads `data/raw/` as text, as E says (every tracked text file). That meets CLAUDE.md
    rule 8, which says tests don't read the full raw data: O-45, question 1 below.

### Step 7.5: plan

- Files: `PLAN.md`
- Signatures implemented: none
- Tests: none
- Outputs: none
- Evidence:

```
$ grep -n "load_claims\|render_markdown\|source_row_filter\|test_claims_recompute" PLAN.md; echo "exit $?"
exit 1
```

- Deviations from PLAN.md or the instruction file: besides Section 7, 3 stale references
  outside it were fixed:
  - the header's module homes named `render_markdown`, now `render`;
  - the header said "Section 7 has its own regeneration check", now it says that
    `scripts/build_writeup.py` regenerates the write-up and both PDFs;
  - step 6.5 named "the 7.5 neutrality grep", now "the 7.4 neutrality test".

### H. Review evidence (instruction 07 H)

**H.1 Page counts and image height.**

```
$ .venv/Scripts/python -c "from pypdf import PdfReader; ..."
deliverable/Design_Response.pdf pages 3
deliverable/Results_Summary.pdf pages 1
```

The summary image height used is 5.5 cm, from the `build_writeup.py` output in step 7.3.

**H.2 The extracted text of `Results_Summary.pdf`, in full** (pypdf, `extract_text()`,
verbatim):

```
https://github.com/uty101/RMBS-Natural-Language-Query
page 1 of 1
Asking RMBS loan data questions in plain English: results
Utkarsh Malhotra · November 2026
A language model turns each question into a small query spec, and a compiler turns the spec into SQL over governed metric
definitions, so the model never does the arithmetic. These results are from a working prototype on synthetic data: 50
Australian RMBS deals, 21,945 loans and 773,336 loan-months in 2 trustee formats.
What is proved
 check
result
Cleaning: canonical table against simulated truth
0 mismatches over 773,336 loan-months
Cleaning: resubmitted duplicates removed
721 of 774,057 raw rows
Cleaning: clean-up calls coded as repayments, recovered
7 deals
Compiler: output against hand-written SQL
49 of 49 match, worst difference 1.6e-15
Compiler: queries that render to Oracle
49 of 49
Scale: slowest question at 27,840,096 loan-months
under 0.75 s with default threads
The traps a plain SQL writer falls into
 trap
question
correct
naive mistake gives
Arrears units
Q27
0.66%
0.59%
Calls as prepayments
Q29
21.6%
100.0%
Calls as prepayments
Q30
18.3%
49.0%
Exit rows as live loans
Q32
9,975
10,572
Unweighted average
Q33
51.96%
50.92%
Averaging CPR (dropped, gap too small)
Q2 2025 CPR
18.064%
18.063%
Governed system against plain text-to-SQL
The 40-question eval compares the 2 on the same questions, but it hasn't been recorded in this copy, because a run needs
an Anthropic API key and none is stored. It takes 2 commands, and this page then regenerates with the results:
 $env:ANTHROPIC_API_KEY = "<your key>"
python scripts/run_eval.py --mode record
python scripts/build_writeup.py

```

**H.3 The extracted text of page 1 of `Design_Response.pdf`** (before each bullet item is
a line holding only the invisible U+007F that pypdf extracts for `•`, see step 7.2):

```
https://github.com/uty101/RMBS-Natural-Language-Query
page 1 of 3
Asking loan-level RMBS data questions in plain English
Utkarsh Malhotra · November 2026
The setting
The question: monthly trustee data for about 300 Australian RMBS deals sits in Oracle. Each deal holds
about 2,000 loans and goes back 5 years, so the database has about 36 million loan-month records. Each
record carries arrears status, prepayments, LVR, interest rate, balance and a suburb that links to local
house prices. How do you let people ask questions of that data in plain English, and trust the answers?
The size is not the hard part. A well partitioned table of 36 million rows answers an aggregate query in
seconds, and the prototype below backs that up. The hard part is meaning. "What are arrears on the 2021
vintage in Western Sydney?" could mean 30 or 90 days past due, by loan count or by balance, at the latest
month or averaged over a year, with hardship loans in or out. A model writing free SQL against raw trustee
tables picks 1 of those readings without telling you, and returns a confident number. On a credit desk, a
confident wrong number is worse than no number.
The short answer
Keep the language model away from the arithmetic.
The model's only job is translation. It turns the question into a small, structured query spec: which metric,
grouped by what, filtered how, over which months. A compiler turns that spec into SQL over metric
definitions written once in code. The database does the maths. The model then writes a short answer from
the finished table, and a guard checks that every number in that answer appears in the table. If the
question is ambiguous, the system asks. If the data can't answer it, the system says so.
Every answer ships with its receipt: the spec, the Oracle SQL and the table. An analyst can check any
answer in about 10 seconds.
The design at production scale
1. Fix the data before any model touches it. Trustee reports from different trustees don't mean the same
thing.

One reports arrears in days and another in missed payments.

Hardship may sit inside or outside arrears.

A clean-up call can arrive coded as an ordinary repayment.

Corrected months get resubmitted on top of the originals.
So the first layer is 1 canonical loan-month table, with a stable loan key and every exit reason tagged
separately: full prepayment, repurchase, default and call. Indexed LVR is computed once, as current
balance over original valuation scaled by the suburb house price index, and stored as a column. Skip this
layer, and the system will one day count a clean-up call as a wave of prepayments and report a CPR spike
that never happened.
2. A semantic layer of governed metrics. Each metric is defined once, in code. Examples:

90+ arrears by balance, hardship excluded;

CPR from voluntary prepayments only, compounded over the period;

balance-weighted indexed LVR.
The dimensions (deal, originator, vintage, state, suburb, LVR band, rate type, interest only) are listed with
their allowed values. The model can only pick from these lists, so it can't invent a metric.
3. A spec, not SQL. The model fills a constrained schema: 1 to 3 metrics, up to 2 groupings, filters, a time
window and an optional ranking. Filling a schema is far more reliable than writing correct window functions
over a loan panel that thins out as loans repay. The spec is validated before anything runs.
4. Resolve names, then compile.

```

**H.4 Page renders.** Not rendered. `pypdfium2` is not installed in the venv, and
`pdftoppm` is not on PATH:

```
$ .venv/Scripts/python -c "import pypdfium2"
ModuleNotFoundError: No module named 'pypdfium2'
$ which pdftoppm
which: no pdftoppm in (...)
```

So `review/section_7_pages/` is not created. Every page of both PDFs, and of the
constructed recorded-state summary, was viewed in this session through Claude Code's PDF
reader. The tables, bullets, `·`, code blocks, figures and footers render as intended. No
render was saved.

**H.5 The constructed recorded-state summary. MADE-UP NUMBERS: the eval table is built
from the made-up k values in `tests/test_documents.py` (`MADE_UP_K`), and the reply to Q35
is the made-up `MADE_UP_CLARIFY`. They are not results.** Built by
`build_recorded_pdfs` (the code of `test_recorded_state_pdfs`) in a temp folder:

```
$ build_recorded_pdfs(tmp)  # page counts and image height, then the summary's pypdf text
{'design_pages': 3, 'summary_pages': 1, 'summary_image_height_cm': 5.5}
https://github.com/uty101/RMBS-Natural-Language-Query
page 1 of 1
Asking RMBS loan data questions in plain English: results
Utkarsh Malhotra · November 2026
A language model turns each question into a small query spec, and a compiler turns the spec into SQL over governed metric
definitions, so the model never does the arithmetic. These results are from a working prototype on synthetic data: 50
Australian RMBS deals, 21,945 loans and 773,336 loan-months in 2 trustee formats.
What is proved
 check
result
Cleaning: canonical table against simulated truth
0 mismatches over 773,336 loan-months
Cleaning: resubmitted duplicates removed
721 of 774,057 raw rows
Cleaning: clean-up calls coded as repayments, recovered
7 deals
Compiler: output against hand-written SQL
49 of 49 match, worst difference 1.6e-15
Compiler: queries that render to Oracle
49 of 49
Scale: slowest question at 27,840,096 loan-months
under 0.75 s with default threads
The traps a plain SQL writer falls into
 trap
question
correct
naive mistake gives
Arrears units
Q27
0.66%
0.59%
Calls as prepayments
Q29
21.6%
100.0%
Calls as prepayments
Q30
18.3%
49.0%
Exit rows as live loans
Q32
9,975
10,572
Unweighted average
Q33
51.96%
50.92%
Averaging CPR (dropped, gap too small)
Q2 2025 CPR
18.064%
18.063%
Governed system against plain text-to-SQL
Same 40 questions. The plain model was given the same table definitions, the same written metric formulas and the exact
output columns.
 category
questions
governed system
plain text-to-SQL
simple
10
9 (90%)
7 (70%)
grouped
10
8 (80%)
5 (50%)
time
6
5 (83%)
3 (50%)
trap
8
7 (88%)
2 (25%)
ambiguous
4
3 (75%)
0 (0%)
unsupported
2
2 (100%)
1 (50%)
total
40
34 (85%)
18 (45%)
Asked "What are arrears in NSW?", the governed system replied:
 Which arrears threshold do you mean?
Options: 30+ days; 90+ days
```

**H.6 The neutrality grep result** is in step 7.4: no match.

**H.7 Both pytest outputs from a fresh clone** are in section 6.

## 4. Full test suite

Command and its complete output (offline, `--disable-socket`), in the working copy at
`47e047a`.

```
$ .venv/Scripts/python -m pytest -q
........................................................................ [ 90%]
........................                                                 [100%]
240 passed, 58 deselected in 137.12s (0:02:17)
$ .venv/Scripts/python -m pytest -q -m full
....................................................s.....               [100%]
57 passed, 1 skipped, 240 deselected in 148.50s (0:02:28)
```

## 5. Determinism

`scripts/build_writeup.py` run twice in the working copy. SHA-256 of each write-up file
after each run, and `git status` afterwards, leaving out `review/` and `decisions/`, which
hold this uncommitted review. It is empty: both runs reproduce the committed files.

```
$ .venv/Scripts/python scripts/build_writeup.py   # run 1
state: pending
Design_Response.pdf: 3 pages (at most 4)
Results_Summary.pdf: 1 pages (exactly 1), image height 5.5 cm
$ sha256sum deliverable/results_summary.md deliverable/Design_Response.pdf deliverable/Results_Summary.pdf deliverable/claims.csv README.md docs/DESIGN_RESPONSE.md
adb8ec26c329d996ff31e45d7d6736c170df2451078ccb03beb1dd8d2821d438 *deliverable/results_summary.md
420769b97fe3be8469badf989d66add60f778227cd1bc9c73509c597c502fd5f *deliverable/Design_Response.pdf
75e833fffa979863ac4f6df22e493f9e61d8e3f694335196d3d32c5f17eea478 *deliverable/Results_Summary.pdf
933d4f098bbe18f3182f9b3c554d3a6ce2e28854acf6c03c123d179a1051384a *deliverable/claims.csv
cc59d161046d1d71c9f073bf61d01f67816f2c0df4235001bf1a6f54a041670b *README.md
ca58bb8aa3978d397ef92abc420a8c5f3d36c89ebb580e364676a62674bbb5eb *docs/DESIGN_RESPONSE.md
$ .venv/Scripts/python scripts/build_writeup.py   # run 2
state: pending
Design_Response.pdf: 3 pages (at most 4)
Results_Summary.pdf: 1 pages (exactly 1), image height 5.5 cm
$ sha256sum deliverable/results_summary.md deliverable/Design_Response.pdf deliverable/Results_Summary.pdf deliverable/claims.csv README.md docs/DESIGN_RESPONSE.md
adb8ec26c329d996ff31e45d7d6736c170df2451078ccb03beb1dd8d2821d438 *deliverable/results_summary.md
420769b97fe3be8469badf989d66add60f778227cd1bc9c73509c597c502fd5f *deliverable/Design_Response.pdf
75e833fffa979863ac4f6df22e493f9e61d8e3f694335196d3d32c5f17eea478 *deliverable/Results_Summary.pdf
933d4f098bbe18f3182f9b3c554d3a6ce2e28854acf6c03c123d179a1051384a *deliverable/claims.csv
cc59d161046d1d71c9f073bf61d01f67816f2c0df4235001bf1a6f54a041670b *README.md
ca58bb8aa3978d397ef92abc420a8c5f3d36c89ebb580e364676a62674bbb5eb *docs/DESIGN_RESPONSE.md
$ git status --short
(end of git status)
```

## 6. Fresh-clone check

Clone into a short temp path, `uv venv --python 3.12`, `uv pip sync requirements-lock.txt`,
run the suite. Paste the commands and the complete output.

```
$ git clone https://github.com/uty101/RMBS-Natural-Language-Query.git r
$ git log --oneline -1
47e047a step 7.5: PLAN.md Section 7 rewritten for instruction 07, with the stale names removed
$ uv venv --python 3.12 .venv
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
$ uv pip sync --python .venv requirements-lock.txt   # last 3 lines of its output
 + typing-extensions==4.16.0
 + typing-inspection==0.4.4
 + tzdata==2026.6
$ .venv/Scripts/python --version
Python 3.12.13
$ .venv/Scripts/python -m pytest -q
........................................................................ [ 90%]
........................                                                 [100%]
240 passed, 58 deselected in 262.10s (0:04:22)
$ .venv/Scripts/python -m pytest -q -m full
....................................................s.....               [100%]
57 passed, 1 skipped, 240 deselected in 70.52s (0:01:10)
$ .venv/Scripts/python scripts/build_writeup.py   # first 4 lines of its output, then its exit code
built C:\s7fc\r\data\canonical\rmbs.duckdb in 22.0 s, 33828864 bytes
          table trustee_format   rows
       dim_deal            all     50
       dim_loan            all  21945
exit 0
$ git status --short
(end of git status)
$ .venv/Scripts/python scripts/build_writeup.py   # second run, database present
summary outputs in 17.3 s
state: pending
Design_Response.pdf: 3 pages (at most 4)
Results_Summary.pdf: 1 pages (exactly 1), image height 5.5 cm
outputs/data_summary.csv
outputs/compiler_check.csv
outputs/trap_effects.csv
outputs/arrears_90p_by_vintage.csv
outputs/figures/arrears_90p_by_vintage.png
outputs/figures/scale_benchmark.png
outputs/worked_example.md
deliverable/claims.csv
README.md
docs/DESIGN_RESPONSE.md
deliverable/results_summary.md
deliverable/Design_Response.pdf
deliverable/Results_Summary.pdf
exit 0
$ git status --short
(end of git status)
```

The clean `git status` after each `build_writeup.py` run means the fresh clone rebuilt both
PDFs, `results_summary.md` and every Section 6 file byte for byte as committed (Windows,
Python 3.12.13). CI on Linux passed both suites at the same commit (section 2).

## 7. Open questions for the reviewer

1. **O-45 (step 7.4): the neutrality test reads `data/raw/`.** Instruction 07 E says it
   reads every tracked text file outside `instructions/` and `.github/`. That includes the
   raw CSVs, and CLAUDE.md rule 8 says tests don't read the full raw data unless marked
   `full`. The instruction file has precedence (rule 13).
   - (a) Keep it as written, in the default suite (about 1 s). **This is what is done.**
   - (b) Skip `data/raw/` in the default test, and search it in a second test marked `full`.
