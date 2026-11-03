# Status: 10_language

## Outcome

Complete. Chat Claude carried out this instruction directly, not through a Claude Code session.

- The 3 templates are copied byte for byte from `instructions/10_templates/`.
- Every label change in section B is applied, and `60` is added to `templates/fixed_numbers.txt`.
- 2 tests used old sentences to tell the pending state from the recorded state, so their markers were changed:
  - `tests/test_documents.py` now asserts `in this copy` is absent in the recorded state;
  - `tests/test_results_summary.py` now asserts `hasn't been run in this copy` is present in the pending state.

  No other assertion changed.
- `build_writeup.py` ran in the recorded state, with these results:
  - `Design_Response.pdf` is 3 pages;
  - `Results_Summary.pdf` is 1 page at 5.5 cm.
- A search of the 3 rendered documents and the text of both PDFs for `governed`, `plain text-to-SQL`, `plain English`, `plain SQL` and `naive` found nothing.
- `pytest -q`: 246 passed. `pytest -q -m full`: 58 passed. Both were run on Linux with no key set.
- The figures and PDFs were rebuilt on Linux. Their bytes differ from a Windows build, as noted in Section 6, and their content is the same.
