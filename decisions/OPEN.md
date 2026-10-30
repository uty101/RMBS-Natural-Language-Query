# Open decisions

Raised in session 1 (`instructions/01_section_1.md`). Evidence for both is in
`review/section_1.md`.

## O-34. Step 1.4: the hardship spell test cannot pass as specified

Instruction 01 H 1.4 asks for "hardship property (p_hardship = 1): every hardship spell
lasts 3 to 6 consecutive rows". Under part E.5, a loan with bucket 0 and
hardship_remaining 0 enters hardship whenever u_h < p_hardship. With p_hardship = 1,
that happens in the month right after every spell ends, so spells join into a single run
of hardship rows that lasts the loan's whole life. In the test frame (50 loans, D001,
orig 2018-06), every loan has 1 run of 60 rows, from 2021-10 to 2026-09. The true panel
has no column that marks where 1 spell ends and the next begins. The test
`test_hardship_spell_lengths` is committed as specified and fails. The per-row half of
the property (dpd_bucket 0, scheduled_principal 0, closing balance unchanged on every
hardship row) is in `test_hardship_rows_frozen`, and it passes.

- (a) The true panel from `simulate` gains a boolean `hardship_entry` column, true in
  the month a loan enters hardship at E.5. It is not written to the trustee files. The
  test keeps p_hardship = 1, splits each run of hardship rows at its entry rows, and
  checks each spell is 3 to 6 rows.
- (b) The test uses the configured p_hardship (0.002) and checks every interior run (one
  that doesn't touch the loan's first row, its last row or an exit row) is 3 to 6 rows.
  Measured: it holds on the small profile (16 interior runs, all 3 to 6). On the full
  profile, 6 of 1,330 interior runs are 9 to 12 rows long, because spells chained, so on
  that profile the property is not certain.

## O-35. Step 1.6: arrears_90p_max fails its band

`outputs/calibration.csv`: arrears_90p_max = 0.0316166537, band [0.001, 0.025]. Every
other band passes. No parameter was changed (instruction 01 F).

The reference values in instruction 01 C differ by more than 1% on several counts:
- rows: 773,971 here, 781,909 in the reference (−1.0%);
- defaulted exits: 656 here, 457 in the reference (+44%);
- called deals: 14 here, 16 in the reference; the list of format B deals called is D004,
  D005, D009, D010, D014 here, against D004, D005, D009, D010, D015, D020.

Checks made on this side:
- An independent scalar re-implementation of part E (loan by loan, plain Python)
  reproduces this panel exactly on the small profile.
- 4 other seeds give arrears_90p_max 0.029 to 0.035 with the peak in 2023-08 or 2023-09.
  So the gap is a rule, not noise.
- The excess sits in IO loans. On IO/fixed loans, 90+ arrears reach 15%. At fixed expiry
  the IO payment moves from about 2% interest to cash + margin, about 7%. Against the
  12-month lookback that is a shock near 2.5, so logistic(−6 + 3 × 2.5) ≈ 0.8 a month.
- Reading the payment as ignoring IO for the shock gives arrears_90p_max 0.0129, which
  is not the reference either. No rule was found that reproduces the reference exactly.

- (a) Chat Claude compares its reference implementation with part E as written (the
  scalar check in the review is a line-by-line reading of part E). Instruction 01b then
  restates the rule where the two differ, most likely in how IO payments enter the
  payment shock.
- (b) Part E stands as written, and instruction 01b sets a new config value. That could
  be the band ceiling (`arrears_90p_max`) or an IO-related behaviour parameter. Section 1
  is then regenerated and re-reviewed.
