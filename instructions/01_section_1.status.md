# Status: session 1 (01_section_1)

## Outcome

Stopped. Every step from 1.0 to 1.6 is built and committed. 2 stop conditions were
reached, and each is raised as a question below with 2 options. Evidence is in
`review/section_1.md`.

- Last step reached: 1.6.
- Stop reasons:
  1. **Step 1.6, calibration band (instruction 01 F).** `arrears_90p_max` =
     0.0316166537 against the band [0.001, 0.025]. The other 8 statistics pass: rows
     773,971; arrears_90p_min 0.0015363690; peak 2023-08; cpr12 0.1633538401 to
     0.1854878584; fixed cliff ratio 3.0196049946; 14 deals called, 5 of them format B.
     No parameter was changed.
  2. **Step 1.4, a test that cannot pass as specified (CLAUDE.md rule 5).**
     `test_hardship_spell_lengths` fails. With p_hardship = 1, part E.5 puts a loan back
     into hardship in the month after each spell ends, so spells join into one run (60
     rows in the test frame). The test is committed as written and was not loosened.
- Following rule 1 and the instruction 01 F pattern, all work that doesn't depend on these
  2 questions was finished: steps 1.5 and 1.6, `data/raw/` committed, the review file, and
  this file.

## Test results (fresh clone of `1c6b3e5`, Windows, Python 3.12.13, installed from the lock file)

- `pytest -q`: 37 passed, 1 failed (`test_hardship_spell_lengths`), 2 deselected.
- `pytest -q -m full`: 1 passed (`test_full_regenerates_identically`), 1 failed
  (`test_calibration_bands`).

Full generation takes 11.5 s. `data/raw/` is 54 files (53 hashed in `MANIFEST.json`),
28.41 MB. A second full generation reproduced all 54 raw files and both CSVs byte for byte.

## Compared with the instruction 01 part C reference

| statistic | this run | reference |
|---|---|---|
| rows | 773,971 | 781,909 |
| arrears_90p_bal min / max | 0.1536% / 3.1617% | 0.197% / 1.757% |
| peak month | 2023-08 | 2024-06 |
| cpr12 min / max | 16.34% / 18.55% | 16.25% / 17.57% |
| fixed cliff ratio | 3.02 | 2.52 |
| deals called | 14 (D001 to D014) | 16 |
| format B deals called | 5 (D004, D005, D009, D010, D014) | 6 (D004, D005, D009, D010, D015, D020) |
| exits: prepaid, called, defaulted, repurchased | 11,408, 2,078, 656, 386 | 11,217, 2,429, 457, 369 |
| small profile rows, called deals | 12,563, 3 | 12,570, 3 |

An independent scalar re-implementation of part E reproduces this run's small-profile
panel exactly; the script is in the review's appendix. On 4 other seeds the arrears_90p_max
values are 0.029 to 0.035, so the gap is a rule, not noise. The excess sits in IO loans,
which most likely means the reference treats IO payments differently in the payment
shock. Details are in the review, step 1.6.

## Deviations recorded in the review

- `CLAUDE.md`: the new `full` rule is numbered 18, because rule 17 (kickoff 1.8) already
  existed. Claude Code's safety check did not refuse the edit, so `CLAUDE.md` and
  `PLAN.md` are both committed (step 1.0).
- `Config.root` (the folder of `config.toml`) is the one field that isn't a TOML key.
- The hardship property is 2 tests: `test_hardship_rows_frozen` passes and
  `test_hardship_spell_lengths` fails. Both use p_hardship = 1 and p_repurchase = 0.
- In `calibration.csv`, one-sided bands have an empty `band_hi`.

## Questions for the reviewer

Same list as `decisions/OPEN.md` and section 7 of the review.

1. **O-34, step 1.4: the hardship spell test cannot pass as specified.**
   - (a) The true panel gains a boolean `hardship_entry` column (true in the month of
     entry at E.5; not written to the trustee files). The test keeps p_hardship = 1,
     splits runs at entry rows and checks each spell is 3 to 6 rows.
   - (b) The test uses the configured p_hardship (0.002) and checks interior runs (not
     touching the first row, the last row or an exit row). Measured: 16 of 16 are 3 to 6
     rows on the small profile. On the full profile, 6 of 1,330 are 9 to 12 rows.
2. **O-35, step 1.6: arrears_90p_max = 0.0316166537 fails [0.001, 0.025].**
   - (a) Chat Claude compares its reference implementation with part E as written,
     using the scalar script in the review appendix. Instruction 01b then restates the
     rule where the two differ.
   - (b) Part E stands, and instruction 01b sets a new config value (the band ceiling, or
     an IO-related behaviour parameter). Section 1 is then regenerated.

## Last 3 commits on origin (before this file)

```
a9b2b60 section 1: review file and open decisions
1c6b3e5 step 1.6: full profile in data/raw, truth and calibration CSVs (arrears_90p_max band fails)
3810181 step 1.5: trustee files in formats A and B, raw parquet files and manifest
```
