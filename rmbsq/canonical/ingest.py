"""Format A and format B ingestion (kickoff 6.2). Built in step 2.1.

Both functions return the canonical row frame of instruction 02 C.1: the same columns,
in the same order, with the same dtypes. Money is integer cents (`Int64`) with a `_c`
suffix (O-27).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# instruction 02 C.1, column for column
CANONICAL_DTYPES = {
    "loan_id": "string",
    "deal_id": "string",
    "period": "datetime64[ns]",
    "submission_seq": "int64",
    "opening_balance_c": "Int64",
    "scheduled_principal_c": "Int64",
    "curtailment_c": "Int64",
    "closing_balance_c": "Int64",
    "exit_balance_c": "Int64",
    "loss_c": "Int64",
    "interest_rate": "float64",
    "dpd_bucket": "int8",
    "hardship_flag": "bool",
    "exit_reason": "string",
    "orig_month": "datetime64[ns]",
    "fixed_end_month": "datetime64[ns]",
    "io_end_month": "datetime64[ns]",
    "orig_balance_c": "Int64",
    "orig_valuation_c": "Int64",
    "orig_ltv": "float64",
    "rate_type_orig": "string",
    "io_flag_orig": "bool",
    "lmi_flag": "bool",
    "occupancy": "string",
    "city": "string",
    "state": "string",
    "area": "string",
    "suburb": "string",
    "trustee_format": "string",
}
CANONICAL_COLUMNS = list(CANONICAL_DTYPES)

EXIT_REASON_A = {"PIF": "prepaid", "REP": "repurchased", "DEF": "defaulted", "CALL": "called"}
EXIT_REASON_B = {"P": "prepaid", "R": "repurchased", "D": "defaulted"}

# canonical cents column -> format A dollars column, format B cents column
MONEY = {
    "opening_balance_c": ("opening_balance", "OpeningBalanceCents"),
    "scheduled_principal_c": ("scheduled_principal", "ScheduledPrincipalCents"),
    "curtailment_c": ("curtailment", "CurtailmentCents"),
    "closing_balance_c": ("closing_balance", "ClosingBalanceCents"),
    "exit_balance_c": ("exit_balance", "ExitBalanceCents"),
    "loss_c": ("loss_amount", "LossAmountCents"),
    "orig_balance_c": ("orig_balance", "OrigBalanceCents"),
    "orig_valuation_c": ("orig_valuation", "OrigValuationCents"),
}
# canonical column -> format A column, format B column, for the columns taken as is
AS_IS = {
    "loan_id": ("loan_id", "LoanId"),
    "deal_id": ("deal_id", "DealId"),
    "submission_seq": ("submission_seq", "SubmissionSeq"),
    "interest_rate": ("interest_rate", "InterestRate"),
    "orig_ltv": ("orig_ltv", "OrigLtv"),
    "rate_type_orig": ("rate_type", "RateType"),
    "occupancy": ("occupancy", "Occupancy"),
    "city": ("city", "City"),
    "state": ("state", "State"),
    "area": ("area", "Area"),
    "suburb": ("suburb", "Suburb"),
}
MONTHS = {
    "period": ("report_month", "ReportMonth"),
    "orig_month": ("orig_month", "OrigMonth"),
    "fixed_end_month": ("fixed_end_month", "FixedEndMonth"),
    "io_end_month": ("io_end_month", "IoEndMonth"),
}
FLAGS = {"io_flag_orig": ("io_flag", "IoFlag"), "lmi_flag": ("lmi_flag", "LmiFlag")}

# instruction 02 C.2 / kickoff 6.2: lower edges of buckets 1 to 4, in days
ARREARS_DAY_EDGES = [1, 30, 60, 90]
MAX_BUCKET = 4  # kickoff 6.2: MissedPayments capped at 4


def arrears_days_to_bucket(days) -> np.ndarray:
    """Instruction 02 C.2: 0 -> 0; 1-29 -> 1; 30-59 -> 2; 60-89 -> 3; 90 and above -> 4."""
    return np.searchsorted(ARREARS_DAY_EDGES, np.asarray(days, dtype=np.int64), side="right").astype(np.int8)


def _months(values: pd.Series) -> pd.Series:
    """'YYYY-MM' strings (None allowed) -> first-of-month datetime64[ns], NaT for None."""
    return pd.to_datetime(values, format="%Y-%m").astype("datetime64[ns]")


def _frame(raw: pd.DataFrame, fmt: str) -> pd.DataFrame:
    """The columns that are mapped the same way in both formats."""
    i = 0 if fmt == "A" else 1
    out = pd.DataFrame(index=raw.index)
    for col, names in AS_IS.items():
        out[col] = raw[names[i]]
    for col, names in MONTHS.items():
        out[col] = _months(raw[names[i]])
    for col, names in FLAGS.items():
        out[col] = raw[names[i]].to_numpy() == 1
    for col, names in MONEY.items():
        src = raw[names[i]].to_numpy()
        out[col] = np.round(src * 100).astype(np.int64) if fmt == "A" else src.astype(np.int64)
    out["trustee_format"] = fmt
    return out


def _finish(out: pd.DataFrame) -> pd.DataFrame:
    """Hardship rows get dpd_bucket 0 (C.2), then the C.1 order and dtypes."""
    out.loc[out["hardship_flag"], "dpd_bucket"] = 0
    out = out[CANONICAL_COLUMNS].reset_index(drop=True)
    return out.astype(CANONICAL_DTYPES)


def ingest_format_a(path: Path) -> pd.DataFrame:
    """A format A trustee file as canonical rows."""
    raw = pq.read_table(path).to_pandas()
    out = _frame(raw, "A")
    out["dpd_bucket"] = arrears_days_to_bucket(raw["arrears_days"].to_numpy())
    out["hardship_flag"] = raw["hardship_flag"].to_numpy() == 1
    out["exit_reason"] = raw["exit_code"].map(EXIT_REASON_A)
    return _finish(out)


def ingest_format_b(path: Path) -> pd.DataFrame:
    """A format B trustee file as canonical rows."""
    raw = pq.read_table(path).to_pandas()
    out = _frame(raw, "B")
    out["dpd_bucket"] = np.minimum(raw["MissedPayments"].to_numpy(), MAX_BUCKET).astype(np.int8)
    out["hardship_flag"] = (raw["Status"] == "H").to_numpy()
    out["exit_reason"] = raw["ExitCode"].map(EXIT_REASON_B)
    return _finish(out)
