# Open decisions

Raised in session 3 (`instructions/03_section_3.md`). Evidence is in
`review/section_3.md`, step 3.3.

## O-37. Step 3.3: metric column order when a flow metric comes before a stock metric

Instruction 03 B.7 says the output has "1 column per metric in spec order". Gold spec
S11 has metrics `["cpr", "balance_total"]`, and its hand SQL returns the columns
`period_label, balance_total, cpr`: the stock CTE's columns come first, then the flow
CTE's. `test_fifteen_specs_match_hand_sql` requires identical columns. S11 is the only
gold spec where the 2 orders differ; the other 14 put every stock metric before every
flow metric, or have only one kind.

- (a) Stock metrics in spec order, then flow metrics in spec order, matching the hand
  SQL. **This is what is built**, because the test is fixed (rule 5) and the gold file
  can't be edited. All 15 specs then match on both profiles. It is 1 line in
  `rmbsq/semantic/compiler.py::build_tree`.
- (b) Strict spec order, as B.7's text says. S11's hand SQL in the gold file would need
  its final select changed to `k.period_label, w.cpr, s.balance_total`, since the test
  compares column order.
