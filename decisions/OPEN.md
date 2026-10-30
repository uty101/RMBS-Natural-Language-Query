# Open decisions

Raised in session 2 (`instructions/02_section_2.md`). Evidence is in
`review/section_2.md`, step 2.4.

## O-36. Step 2.4: O-29's first RED loan has no row in the window

O-29 picks "the first loan_id of each originator, at the latest period where that loan
has a row with closing_balance > 0, in the small profile". RED's first loan in loan_id
order is D005-0001. It exits before the window opens (2021-10), so it has 0 rows in the
small panel and no row with closing_balance > 0. Read literally, the rule gives 4 rows,
not 5.

- (a) Take the first loan_id of each originator among loans that have a row with
  closing_balance > 0. RED's row is then D005-0002 at 2026-09. The other 4 rows are
  unchanged (D001-0001, D002-0001, D003-0001, D004-0001). **This is what is built**,
  because it is the only reading that gives the 5 rows the test asks for. The test
  passes with every value equal to the hand calculation (difference 0).
- (b) A later instruction names the 5 (loan_id, period) pairs, and the test uses them as
  given.
