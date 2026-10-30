# Worked example: the compiler path (spec written by hand)

## Question

Show the 90+ arrears rate by balance for each state at the latest month.

## Spec

```json
{
  "intent": "answer",
  "metrics": [
    "arrears_90p_bal"
  ],
  "group_by": [
    "state"
  ],
  "filters": {},
  "time": {
    "grain": "month",
    "start": "2026-09",
    "end": "2026-09",
    "shape": "point"
  },
  "order": null,
  "clarify": null,
  "unsupported_reason": null
}
```

## Oracle SQL

```sql
WITH parts AS (
  SELECT
    l.state AS state,
    f.period,
    SUM(CASE WHEN f.closing_balance > 0 THEN 1 ELSE 0 END) AS loan_count,
    SUM(CASE WHEN f.closing_balance > 0 THEN f.closing_balance ELSE 0 END) AS bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0 AND f.dpd_bucket >= 2 AND NOT f.hardship_flag
        THEN f.closing_balance
        ELSE 0
      END
    ) AS a30_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0 AND f.dpd_bucket = 4 AND NOT f.hardship_flag
        THEN f.closing_balance
        ELSE 0
      END
    ) AS a90_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0 AND f.dpd_bucket = 4 AND NOT f.hardship_flag
        THEN 1
        ELSE 0
      END
    ) AS a90_cnt,
    SUM(
      CASE
        WHEN f.closing_balance > 0 AND f.hardship_flag
        THEN f.closing_balance
        ELSE 0
      END
    ) AS hard_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0
        THEN CAST(f.closing_balance AS DOUBLE PRECISION) * l.orig_ltv
        ELSE 0
      END
    ) AS orig_ltv_x_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0
        THEN CAST(f.closing_balance AS DOUBLE PRECISION) * f.indexed_ltv
        ELSE 0
      END
    ) AS idx_ltv_x_bal,
    SUM(
      CASE
        WHEN f.closing_balance > 0
        THEN CAST(f.closing_balance AS DOUBLE PRECISION) * f.interest_rate
        ELSE 0
      END
    ) AS rate_x_bal,
    SUM(CASE WHEN f.opening_balance > 0 THEN f.curtailment ELSE 0 END) + SUM(
      CASE
        WHEN f.opening_balance > 0 AND f.exit_reason = 'prepaid'
        THEN f.exit_balance
        ELSE 0
      END
    ) AS smm_num,
    SUM(
      CASE
        WHEN f.opening_balance > 0
        AND (
          f.exit_reason IS NULL OR f.exit_reason = 'prepaid'
        )
        THEN f.opening_balance - f.scheduled_principal
        ELSE 0
      END
    ) AS smm_den,
    SUM(
      CASE
        WHEN f.opening_balance > 0 AND f.exit_reason = 'defaulted'
        THEN f.exit_balance
        ELSE 0
      END
    ) AS mdr_num,
    SUM(CASE WHEN f.opening_balance > 0 THEN f.opening_balance ELSE 0 END) AS mdr_den
  FROM fact_loan_month f
  JOIN dim_loan l
    ON l.loan_id = f.loan_id
  JOIN dim_deal d
    ON d.deal_id = f.deal_id
  WHERE
    f.period BETWEEN TO_DATE('2026-09-01', 'YYYY-MM-DD') AND TO_DATE('2026-09-01', 'YYYY-MM-DD')
  GROUP BY
    l.state,
    f.period
), b AS (
  SELECT
    parts.*,
    '2026-09' AS period_label
  FROM parts
), keys AS (
  SELECT DISTINCT
    state,
    period_label
  FROM b
), stock AS (
  SELECT
    state,
    period_label,
    CAST(a90_bal AS DOUBLE PRECISION) / CAST(bal AS DOUBLE PRECISION) AS arrears_90p_bal
  FROM (
    SELECT
      b.*,
      ROW_NUMBER() OVER (PARTITION BY state, period_label ORDER BY period DESC NULLS LAST) AS rn
    FROM b
    WHERE
      loan_count > 0
  ) r
  WHERE
    rn = 1
)
SELECT
  k.state,
  k.period_label,
  s.arrears_90p_bal
FROM keys k
LEFT JOIN stock s
  ON s.state = k.state AND s.period_label = k.period_label
ORDER BY
  k.state,
  k.period_label
```

## Result

| state | period_label | arrears_90p_bal |
|---|---|---|
| NSW | 2026-09 | 0.55% |
| QLD | 2026-09 | 0.34% |
| SA | 2026-09 | 0.19% |
| VIC | 2026-09 | 0.35% |
| WA | 2026-09 | 0.91% |
