# Open decisions

Raised in session 5 (`instructions/05_section_5.md`). Evidence is in
`review/section_5.md`. O-38 and O-39 were both confirmed as (a) by instruction 05 A.

## O-40. Step 5.7: S01 and S12 carry no balance_total or loan_count

F 5.7 says that for S01 and S12, ratio metrics on the tiled database equal the 1x
values, and balance_total and loan_count are 3 ×. S01's only metric is
`arrears_90p_bal`; S12's are `smm_vol` and `cpr`. A spec holds at most 3 metrics, so S12
can't take both totals.

- (a) Run each spec as written for the ratio check, then the same spec (same group_by,
  filters and time) with metrics `[balance_total, loan_count]` for the 3 × check, on
  routes auto and fact. **This is what is built**, in
  `tests/test_benchmark.py::test_tiled_specs_match_1x`.
- (b) Check the totals only where they fit: S01 with `balance_total` and `loan_count`
  added (3 metrics), and S12 with one total replacing `smm_vol`.

## O-41. Step 5.7: what `db_rows` counts

E.2 lists `db_rows` in `outputs/scale_benchmark.csv` without saying which rows.

- (a) The row count of `fact_loan_month`, the table the fact route scans: 773,336 on 1x
  and 27,840,096 on 36x. **This is what is built.**
- (b) The total row count over all 7 canonical tables.

## O-42. Step 5.3: the system's intent when its compile or execute fails

D.2 gives the baseline's error intent (`error`) but not the system's. `answer` raises
on a compile or execute failure, after the spec call, and the spec is not returned.

- (a) Record intent `error` with the exception text in `error`, and score the item
  wrong. A cache miss, a missing key and an API error still stop the run. **This is what
  is built.**
- (b) Record the spec's own intent (`answer`), which needs `answer` to return the spec
  alongside the exception.
