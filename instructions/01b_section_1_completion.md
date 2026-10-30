# 01b Section 1 completion

Session 1b instructions for Claude Code. Fix the 2 stops from session 1, fix the cross-platform HPI difference, and regenerate the full profile. Nothing new is built. This file beats `PLAN.md`, which beats the kickoff (rule 13). Status file: `instructions/01b_section_1_completion.status.md`.

---

## A. Review of session 1

Steps 1.0 to 1.6 are approved as built. Both stops were caused by chat Claude's instruction, not by the code.

**O-35 (arrears band).** The part C reference values came from a prototype with a bug. It applied the fixed rate to every variable loan for its whole life, because the "no fixed period" placeholder counted as still fixed. Variable borrowers in that prototype never felt the 2022 to 2023 rate rises. That is why its arrears were low, and why the part C parameters were set too low for a correct model.

With that bug fixed, chat Claude's prototype and `rmbsq/synth/simulate.py` agree row for row:

- the small profile: 12,563 rows, identical closing_balance, dpd_bucket and hardship_flag on every row;
- the full profile: 773,971 rows, identical on every row.

Every session 1 calibration value is reproduced, including arrears_90p_max 0.0316166537 and the peak at 2023-08. Part E as written is correct, and the code implements it correctly. The fix is a parameter change (B.2).

**O-34 (hardship spells).** The test was specified so that it could not pass. With p_hardship = 1, a loan re-enters hardship the month after each spell ends, so spells join into one run. Option (a) is taken (B.1).

**A new issue found on Linux.** Chat Claude ran the suite on Linux from the lock file:

- the default run gave 37 passed, plus the expected `test_hardship_spell_lengths` failure, the same as on Windows;
- `test_full_regenerates_identically` failed on Linux, although it passed on Windows.

Only `hpi.parquet` differs; all 52 trustee files match. In 5,658 of its 7,740 values, `exp` returns a different last digit on the 2 platforms. The largest relative difference is 2.3e-15. CI runs on Linux against a manifest built on Windows, so this would fail every CI run. The fix is B.4.

---

## B. Decisions

**B.1, O-34: (a).**

- The true panel gains a boolean column `hardship_entry`, after `hardship_flag`. It is true in the month a loan enters hardship at E.5, and false otherwise. It is not written to the trustee files, and it is not used by anything outside `rmbsq/synth/` and its tests.
- `test_hardship_spell_lengths` is amended:
  - keep p_hardship = 1 and p_repurchase = 0;
  - split each loan's hardship rows into spells at its entry rows;
  - assert every spell is hardship_min to hardship_max rows long and starts on an entry row;
  - exclude the last spell of a loan only if it includes that loan's last emitted row, since the window end or an exit can cut a spell short.
- `PANEL_COLUMNS` and part E's column list in `PLAN.md` gain the new column.

**B.2, O-35: (b).** Make exactly these changes to `config.toml`:

```toml
[behaviour]
a0 = -6.3                      # was -6.0
a_shock = 1.5                  # was 3.0
shock_lookback_months = 24     # was 12
```

Part E is unchanged. Before writing this file, chat Claude measured these values with its corrected prototype, which matches the code row for row. Measured on the full profile:

| statistic (part F of instruction 01) | expected value | band |
|---|---|---|
| rows | 773,336 | [700,000, 1,600,000] |
| arrears_90p_min | 0.0011987201 | ≥ 0.001 |
| arrears_90p_max | 0.0153861877 | ≤ 0.025 |
| arrears_peak_month | 2024-08 | [2023-06, 2025-06] |
| cpr12_min | 0.1685765743 | ≥ 0.08 |
| cpr12_max | 0.1875279271 | ≤ 0.35 |
| fixed_cliff_ratio | 3.5742985933 | ≥ 2.0 |
| deals_called | 17 | ≥ 3 |
| b_deals_called | 7 | ≥ 3 |

Called deals with their call months, in deal order:

- D001 2025-11, D002 2025-03, D003 2025-07, D004 2025-11, D005 2025-04, D006 2025-04, D007 2025-11, D008 2026-02, D009 2026-03, D010 2025-12, D011 2026-09, D012 2026-06, D013 2025-12, D014 2026-02, D015 2026-06, D017 2026-02, D020 2026-04.
- The format B deals among them are D004, D005, D009, D010, D014, D015, D020.

Exits by reason: prepaid 11,566, called 2,542, repurchased 376, defaulted 346.

Small profile: 12,734 rows. 4 called deals (D001 2024-10, D002 2025-12, D003 2025-12, D006 2026-05), all format A. 110 hardship rows.

Pool arrears_90p_bal by year is the mean of monthly values:

| year | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| arrears_90p_bal | 0.17% | 0.19% | 0.69% | 1.33% | 0.78% | 0.57% |

**This is a cross-check against a reference, so rule 4 applies.**

- Row counts, exit counts, the called deal list and call months, the peak month, and both small profile counts must match exactly.
- Float statistics must match to a relative 1e-6.
- On any miss, finish the review and status files, then stop.

**B.3, O-28 amended for Section 2.** The small profile now has no called format B deal, so the small profile part of test 2.3 can't show that recovery works. Instruction 02 will specify:

- the small profile assertion stays an equality: recovered format B calls equal the true panel's called exits, where empty on both sides is allowed;
- the constructed frame test proves the mechanics;
- a new `full` test checks that all 7 format B called deals are recovered with their exact call months and loan counts.

Record this in `PLAN.md` step 2.3 now. Write no Section 2 code.

**B.4 HPI rounding (new).**

- Add `round_dp = 6` under `[hpi]` in `config.toml`.
- In `rmbsq/synth/hpi.py`, run the recursion at full precision exactly as now, then round the whole HPI matrix with `numpy.round(hpi, cfg.hpi.round_dp)`. Everything downstream uses the rounded values: `simulate`, `hpi.parquet`, and later `enrich`.
- Test: the rounded matrix equals `numpy.round` of the unrounded one, and every value has at most 6 decimal places.
- Chat Claude measured that at 6 dp, none of the 7,740 values rounds differently on Windows and Linux. At 10 dp, 3 do.
- The B.2 expected values were measured with this rounding applied. Rounding changes no row of either panel, so they are the same as without it.
- Chat Claude will rerun the `full` tests on Linux in its review.

---

## C. Steps

Commit one per step, continuing the Section 1 numbering.

**1.7 Hardship entry column.**

- Add `hardship_entry` to `simulate` and `PANEL_COLUMNS`.
- Amend `test_hardship_spell_lengths` per B.1.
- Update `PLAN.md` (steps 1.4 and 2.3, per B.1 and B.3) and `docs/CONVENTIONS_RESOLVED.md`.
- Commit `PLAN.md`.

**1.8 HPI rounding.** Apply B.4, with its test.

**1.9 Recalibrated full profile.**

- Apply B.2 to `config.toml`.
- Regenerate the full profile into `data/raw/`, along with `MANIFEST.json`, `outputs/pool_monthly_truth.csv` and `outputs/calibration.csv`.
- Remove any raw file the new run no longer writes, and commit by explicit path.
- Then run both pytest commands.

---

## D. Review evidence

Append a section `## Completion: instruction 01b` to `review/section_1.md`, holding:

1. `outputs/calibration.csv` in full, with the B.2 expected values beside it and a match column.
2. Called deals: deal_id, originator, trustee_format and call month, beside the B.2 list.
3. Exit counts by reason, and the small profile counts.
4. `pool_monthly_truth.csv` rows for 2021-10, 2022-10, 2023-10, 2024-08, 2025-10 and 2026-09.
5. Pool arrears_90p_bal mean by year, beside the B.2 table.
6. The hardship spell test's spell length counts on its test frame: length against number of spells.
7. MANIFEST file count, `data/raw/` size in MB, and the full generation runtime.
8. Both pytest outputs from a fresh clone (default and `-m full`).

Then write `instructions/01b_section_1_completion.status.md` and push.
