"""Step 6.0: the number check on a rendered document (instruction 06 B, J 6.0)."""

from rmbsq.deliverable.numbers import unexplained_numbers

FIXED = ["2", "95%"]
DOC = """# Title

The pool held 21,945 loans in 2 formats from 2021-10 to 2026-Q3, with a 95% interval.
Deal CST 2019-1 is named, and 2024 is a bare year.
The worst difference was 7.25.

```bash
python --version 3.12 && echo 4321
```

    $env:KEY = "123"

| a | b |
|---|---|
| 1 | 99.9% |
"""
BLOCKS = {"table": "| a | b |\n|---|---|\n| 1 | 99.9% |\n"}


def test_number_check():
    claims = {"n_loans": "21,945"}
    # 7.25 is the only number not explained: code, the block, periods, deal names and the year are removed
    assert unexplained_numbers(DOC, claims, BLOCKS, FIXED) == ["7.25"]
    assert unexplained_numbers(DOC, {**claims, "worst": "7.25"}, BLOCKS, FIXED) == []
    # without the block removed, its numbers are unexplained too
    assert unexplained_numbers(DOC, {**claims, "worst": "7.25"}, {}, FIXED) == ["1", "99.9%"]
