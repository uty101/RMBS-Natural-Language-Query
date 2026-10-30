# Status: session 1b (01b_section_1_completion)

## Outcome

Complete. Steps 1.7, 1.8 and 1.9 are built and committed. Evidence is in
`review/section_1.md`, section "Completion: instruction 01b".

- Last step reached: 1.9.
- Stop reason: none. The instruction 01b B.2 cross-check (rule 4) matched on every item:
  - rows 773,336;
  - exits: prepaid 11,566, called 2,542, repurchased 376, defaulted 346;
  - 17 called deals, every call month as listed, including the 7 format B deals;
  - peak month 2024-08;
  - small profile: 12,734 rows, 4 called deals with the listed months, 110 hardship rows;
  - all 6 float statistics with relative difference 0;
  - the yearly arrears table at 2 dp.

## What changed

- 1.7: the true panel has `hardship_entry` after `hardship_flag`, and
  `test_hardship_spell_lengths` is amended per B.1. In the test frame, 353 spells are
  checked, all 3 to 6 rows and all starting on an entry row; the 50 last spells cut by
  the window end are excluded. `PLAN.md` (steps 1.4 and 2.3, per B.1 and B.3) and
  `docs/CONVENTIONS_RESOLVED.md` are updated, and `PLAN.md` is committed.
- 1.8: `[hpi] round_dp = 6`. The HPI recursion runs at full precision and is then rounded
  with `numpy.round`. Test: `test_hpi_rounded`.
- 1.9: B.2 is in `config.toml`. `data/raw/`, `MANIFEST.json`,
  `outputs/pool_monthly_truth.csv` and `outputs/calibration.csv` are regenerated, and
  every band passes. The run writes the same 53 hashed files, so none was removed.
  `data/raw/` is 54 files and 28.38 MB. The full generation takes 16.5 s.
- `decisions/OPEN.md` is empty again, because O-34 and O-35 are decided in 01b.

## Deviation

The hardship spell test frame moved from D001 (orig 2018-06) to D050 (orig 2022-06,
issue 2023-11). On D001, 39 of 50 loans enter the window in the middle of a spell that
started before 2021-10, so that first spell could not "start on an entry row". B.1
excludes only a cut last spell. On D050 the issue reset falls inside the window, so all
50 loans start on an entry row and every B.1 assertion holds as written.

## Test results (fresh clone of `8435799`, Windows, Python 3.12.13, from the lock file)

- `pytest -q`: 39 passed, 2 deselected.
- `pytest -q -m full`: 2 passed, 39 deselected.

The Linux rerun of the `full` tests (B.4) is left to the review.

## Questions for the reviewer

None.

## Last 3 commits on origin (before this file)

```
f73119d section 1: review completion for instruction 01b
8435799 step 1.9: recalibrated full profile (instruction 01b B.2), every band passes
7c096b2 step 1.8: HPI rounded to round_dp = 6 after the full-precision recursion
```
