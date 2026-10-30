"""Trap effects: each trap's gold value and the naive reading's value on the canonical
database (instruction 06 C.3). Step 6.1.

The gold values come from the compiler. The naive values come from the SQL below, which
applies the C.3 naive rule to the B.2 monthly parts. The months and the deal name are the
C.3 table's; the compounding is instruction 03 B.6.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from rmbsq.semantic.compiler import FACT_PARTS, compile, execute
from rmbsq.semantic.spec import QuerySpec

COLUMNS = ["trap", "item_id", "gold", "naive", "naive_rule"]


def _spec(metric: str, start: str, end: str, filters: dict | None = None) -> QuerySpec:
    return QuerySpec.model_validate({"intent": "answer", "metrics": [metric], "filters": filters or {},
                                     "time": {"grain": "month", "start": start, "end": end, "shape": "point"}})


def _call_as_prepay(start: str, end: str, deal_name: str | None = None) -> str:
    """B.6 compounding with `called` treated as `prepaid` in both smm_num and smm_den."""
    deal = "" if deal_name is None else f" AND d.deal_name = '{deal_name}'"
    return f"""
WITH m AS (
  SELECT f.period,
    SUM(CASE WHEN f.opening_balance > 0 THEN f.curtailment ELSE 0 END)
      + SUM(CASE WHEN f.opening_balance > 0 AND f.exit_reason IN ('prepaid', 'called')
                 THEN f.exit_balance ELSE 0 END) AS num,
    SUM(CASE WHEN f.opening_balance > 0 AND (f.exit_reason IS NULL OR f.exit_reason IN ('prepaid', 'called'))
             THEN f.opening_balance - f.scheduled_principal ELSE 0 END) AS den
  FROM fact_loan_month f JOIN dim_deal d ON d.deal_id = f.deal_id
  WHERE f.period BETWEEN DATE '{start}-01' AND DATE '{end}-01'{deal}
  GROUP BY f.period
), r AS (
  SELECT CAST(num AS DOUBLE) / CAST(den AS DOUBLE) AS m FROM m WHERE den > 0
), p AS (
  SELECT CASE WHEN MAX(m) >= 1 THEN 1.0 ELSE 1 - EXP(SUM(CASE WHEN m < 1 THEN LN(1 - m) ELSE 0 END)) END AS p,
         COUNT(*) AS n
  FROM r
)
SELECT 1 - POWER(1 - p, 12.0 / n) FROM p"""


ARREARS_60 = f"""
SELECT CAST(SUM(CASE WHEN f.closing_balance > 0 AND f.dpd_bucket >= 3 AND NOT f.hardship_flag
                     THEN f.closing_balance ELSE 0 END) AS DOUBLE) / CAST({FACT_PARTS['bal']} AS DOUBLE)
FROM fact_loan_month f WHERE f.period = DATE '2026-09-01'"""

EXIT_ROWS = "SELECT COUNT(*) FROM fact_loan_month f WHERE f.period = DATE '2025-11-01'"

SIMPLE_MEAN = ("SELECT AVG(f.indexed_ltv) FROM fact_loan_month f"
               " WHERE f.period = DATE '2024-12-01' AND f.closing_balance > 0")

MONTHLY_CPR_MEAN = f"""
WITH m AS (
  SELECT f.period, {FACT_PARTS['smm_num']} AS num, {FACT_PARTS['smm_den']} AS den
  FROM fact_loan_month f
  WHERE f.period BETWEEN DATE '2025-04-01' AND DATE '2025-06-01'
  GROUP BY f.period
)
SELECT AVG(1 - POWER(1 - CAST(num AS DOUBLE) / CAST(den AS DOUBLE), 12)) FROM m WHERE den > 0"""


@dataclass(frozen=True)
class Trap:
    trap: str
    item_id: str
    gold: QuerySpec
    naive_sql: str
    naive_rule: str


CALL_RULE = "clean-up call exits counted as prepayments"
TRAPS = [
    Trap("arrears_units", "Q27", _spec("arrears_30p_bal", "2026-09", "2026-09"), ARREARS_60,
         "2 or more missed payments read as 60+ days"),
    Trap("call_as_prepay", "Q29", _spec("cpr", "2025-01", "2025-12", {"deal_name": ["CST 2019-1"]}),
         _call_as_prepay("2025-01", "2025-12", "CST 2019-1"), CALL_RULE),
    Trap("call_as_prepay", "Q30", _spec("cpr", "2025-11", "2025-11"), _call_as_prepay("2025-11", "2025-11"),
         CALL_RULE),
    Trap("exit_rows", "Q32", _spec("loan_count", "2025-11", "2025-11"), EXIT_ROWS,
         "exit rows counted as live loans"),
    Trap("weighting", "Q33", _spec("wa_indexed_ltv", "2024-12", "2024-12"), SIMPLE_MEAN,
         "simple mean instead of balance weighting"),
    Trap("compounding", "Q2_2025", _spec("cpr", "2025-04", "2025-06"), MONTHLY_CPR_MEAN,
         "monthly CPR averaged instead of compounded"),
]


def trap_effects(con, catalog) -> pd.DataFrame:
    rows = []
    for t in TRAPS:
        gold = execute(compile(t.gold, catalog), con)[t.gold.metrics[0]].iloc[0]
        naive = con.execute(t.naive_sql).fetchone()[0]
        if t.gold.metrics[0] == "loan_count":
            gold, naive = int(gold), int(naive)
        else:
            gold, naive = float(gold), float(naive)
        rows.append([t.trap, t.item_id, gold, naive, t.naive_rule])
    # object columns keep the loan counts as integers next to the float ratios
    return pd.DataFrame(rows, columns=COLUMNS, dtype=object)
