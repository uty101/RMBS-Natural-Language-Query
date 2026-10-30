"""Raw trustee files in formats A and B (kickoff 4.8). Built in step 1.5.

Exact schemas are instruction 01 part G. One parquet file per deal, rows sorted by
report month then loan_id (then submission_seq on resubmitted deal-months).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from rmbsq.config import Config
from rmbsq.synth.months import from_period, month_labels

FORMAT_A = [
    ("loan_id", pa.string()), ("deal_id", pa.string()), ("report_month", pa.string()),
    ("submission_seq", pa.int64()), ("opening_balance", pa.float64()),
    ("scheduled_principal", pa.float64()), ("curtailment", pa.float64()),
    ("closing_balance", pa.float64()), ("interest_rate", pa.float64()),
    ("arrears_days", pa.int64()), ("hardship_flag", pa.int8()), ("exit_code", pa.string()),
    ("exit_balance", pa.float64()), ("loss_amount", pa.float64()), ("orig_month", pa.string()),
    ("orig_balance", pa.float64()), ("orig_valuation", pa.float64()), ("orig_ltv", pa.float64()),
    ("rate_type", pa.string()), ("fixed_end_month", pa.string()), ("io_flag", pa.int8()),
    ("io_end_month", pa.string()), ("occupancy", pa.string()), ("lmi_flag", pa.int8()),
    ("city", pa.string()), ("state", pa.string()), ("area", pa.string()), ("suburb", pa.string()),
]

FORMAT_B = [
    ("LoanId", pa.string()), ("DealId", pa.string()), ("ReportMonth", pa.string()),
    ("SubmissionSeq", pa.int64()), ("OpeningBalanceCents", pa.int64()),
    ("ScheduledPrincipalCents", pa.int64()), ("CurtailmentCents", pa.int64()),
    ("ClosingBalanceCents", pa.int64()), ("InterestRate", pa.float64()),
    ("MissedPayments", pa.int64()), ("Status", pa.string()), ("ExitCode", pa.string()),
    ("ExitBalanceCents", pa.int64()), ("LossAmountCents", pa.int64()), ("OrigMonth", pa.string()),
    ("OrigBalanceCents", pa.int64()), ("OrigValuationCents", pa.int64()), ("OrigLtv", pa.float64()),
    ("RateType", pa.string()), ("FixedEndMonth", pa.string()), ("IoFlag", pa.int8()),
    ("IoEndMonth", pa.string()), ("Occupancy", pa.string()), ("LmiFlag", pa.int8()),
    ("City", pa.string()), ("State", pa.string()), ("Area", pa.string()), ("Suburb", pa.string()),
]

EXIT_CODE_A = {"prepaid": "PIF", "repurchased": "REP", "defaulted": "DEF", "called": "CALL"}
EXIT_CODE_B = {"prepaid": "P", "repurchased": "R", "defaulted": "D", "called": "P"}  # calls look like repayments

# money columns of format A and their format B cents names (instruction 01 G.2)
MONEY = {
    "opening_balance": "OpeningBalanceCents", "scheduled_principal": "ScheduledPrincipalCents",
    "curtailment": "CurtailmentCents", "closing_balance": "ClosingBalanceCents",
    "exit_balance": "ExitBalanceCents", "loss_amount": "LossAmountCents",
    "orig_balance": "OrigBalanceCents", "orig_valuation": "OrigValuationCents",
}
# every other format A column, renamed to UpperCamel with acronyms as words
RENAME_B = {
    "loan_id": "LoanId", "deal_id": "DealId", "report_month": "ReportMonth",
    "submission_seq": "SubmissionSeq", "interest_rate": "InterestRate", "exit_code": "ExitCode",
    "orig_month": "OrigMonth", "orig_ltv": "OrigLtv", "rate_type": "RateType",
    "fixed_end_month": "FixedEndMonth", "io_flag": "IoFlag", "io_end_month": "IoEndMonth",
    "occupancy": "Occupancy", "lmi_flag": "LmiFlag", "city": "City", "state": "State",
    "area": "Area", "suburb": "Suburb",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _months_or_none(values) -> np.ndarray:
    m = from_period(values)
    labels = month_labels(np.maximum(m, 0)).astype(object)
    labels[m < 0] = None
    return labels


def arrears_days(dpd_bucket: np.ndarray, months_in_90: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Instruction 01 G.1: 0 -> 0; 1 -> 1 + floor(29u); 2 -> 30 + floor(30u);
    3 -> 60 + floor(30u); 4 -> 90 + 30 (months_in_90 - 1) + floor(30u)."""
    days = np.zeros(len(dpd_bucket), dtype=np.int64)
    days = np.where(dpd_bucket == 1, 1 + np.floor(29 * u), days)
    days = np.where(dpd_bucket == 2, 30 + np.floor(30 * u), days)
    days = np.where(dpd_bucket == 3, 60 + np.floor(30 * u), days)
    days = np.where(dpd_bucket == 4, 90 + 30 * (months_in_90 - 1) + np.floor(30 * u), days)
    return days.astype(np.int64)


def _format_a_frame(rows: pd.DataFrame, static: pd.DataFrame) -> pd.DataFrame:
    """Format A columns for one deal's panel rows, before arrears days and resubmissions."""
    s = static.loc[rows["loan_id"]].reset_index(drop=True)
    r = rows.reset_index(drop=True)
    return pd.DataFrame(
        {
            "loan_id": r["loan_id"].to_numpy(object),
            "deal_id": r["deal_id"].to_numpy(object),
            "report_month": month_labels(from_period(r["period"])).astype(object),
            "submission_seq": np.ones(len(r), dtype=np.int64),
            "opening_balance": r["opening_balance"].to_numpy(),
            "scheduled_principal": r["scheduled_principal"].to_numpy(),
            "curtailment": r["curtailment"].to_numpy(),
            "closing_balance": r["closing_balance"].to_numpy(),
            "interest_rate": r["interest_rate"].to_numpy(),
            "arrears_days": np.zeros(len(r), dtype=np.int64),
            "hardship_flag": r["hardship_flag"].to_numpy().astype(np.int8),
            "exit_code": r["exit_reason"].map(EXIT_CODE_A).to_numpy(object),
            "exit_balance": r["exit_balance"].to_numpy(),
            "loss_amount": r["loss"].to_numpy(),
            "orig_month": month_labels(from_period(s["orig_month"])).astype(object),
            "orig_balance": s["orig_balance"].to_numpy(),
            "orig_valuation": s["orig_valuation"].to_numpy(),
            "orig_ltv": s["orig_ltv"].to_numpy(),
            "rate_type": s["rate_type"].to_numpy(object),
            "fixed_end_month": _months_or_none(s["fixed_end_month"]),
            "io_flag": s["io_flag"].to_numpy().astype(np.int8),
            "io_end_month": _months_or_none(s["io_end_month"]),
            "occupancy": s["occupancy"].to_numpy(object),
            "lmi_flag": s["lmi_flag"].to_numpy().astype(np.int8),
            "city": s["city"].to_numpy(object),
            "state": s["state"].to_numpy(object),
            "area": s["area"].to_numpy(object),
            "suburb": s["suburb"].to_numpy(object),
        }
    )


def _format_b_frame(a: pd.DataFrame, rows: pd.DataFrame) -> pd.DataFrame:
    """Format B from the format A frame: cents, MissedPayments, Status, ExitCode."""
    r = rows.reset_index(drop=True)
    b = pd.DataFrame({RENAME_B[c]: a[c] for c in RENAME_B})
    for col, cents in MONEY.items():
        b[cents] = np.round(a[col].to_numpy() * 100).astype(np.int64)
    b["MissedPayments"] = r["dpd_bucket"].to_numpy().astype(np.int64)
    hard = r["hardship_flag"].to_numpy()
    b["Status"] = np.where(hard, "H", np.where(r["dpd_bucket"].to_numpy() >= 1, "A", "C")).astype(object)
    b["ExitCode"] = r["exit_reason"].map(EXIT_CODE_B).to_numpy(object)
    return b[[name for name, _ in FORMAT_B]]


def _resubmit(df: pd.DataFrame, month: str, cfg: Config, fmt: str) -> pd.DataFrame:
    """Instruction 01 G.3: every row of the deal-month twice, seq 1 with closing balance and
    curtailment times `inflate`, seq 2 true; seq 1 first."""
    month_col, seq_col, loan_col = ("report_month", "submission_seq", "loan_id") if fmt == "A" else (
        "ReportMonth", "SubmissionSeq", "LoanId")
    hit = df[month_col] == month
    first = df[hit].copy()
    second = df[hit].copy()
    second[seq_col] = 2
    inflate = cfg.resubmissions.inflate
    if fmt == "A":
        for c in ["closing_balance", "curtailment"]:
            first[c] = np.round(first[c].to_numpy() * inflate, 2)
    else:
        for c in ["ClosingBalanceCents", "CurtailmentCents"]:
            first[c] = np.round(first[c].to_numpy() * inflate).astype(np.int64)
    out = pd.concat([df[~hit], first, second], ignore_index=True)
    return out.sort_values([month_col, loan_col, seq_col], kind="stable").reset_index(drop=True)


def _column(s: pd.Series, typ) -> pa.Array:
    if typ == pa.string():
        return pa.array([v if isinstance(v, str) else None for v in s.tolist()], type=typ)
    return pa.array(s.to_numpy(), type=typ)


def _write(df: pd.DataFrame, schema: list, path: Path) -> None:
    table = pa.Table.from_arrays([_column(df[name], typ) for name, typ in schema], schema=pa.schema(schema))
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="snappy")


def write_trustee_files(cfg: Config, panel: pd.DataFrame, loans: pd.DataFrame, out_dir: Path, rng_aux) -> dict[str, str]:
    """1 parquet per deal under trustee_a/ or trustee_b/. Returns {relative POSIX path: sha256}."""
    out_dir = Path(out_dir)
    static = loans.set_index("loan_id")
    fmt_of = loans.drop_duplicates("deal_id").set_index("deal_id")["trustee_format"]
    resub = {}
    for deal_id, month in cfg.resubmissions.deal_months:
        resub.setdefault(deal_id, []).append(month)

    hashes = {}
    for deal_id in sorted(fmt_of.index):
        rows = panel[panel["deal_id"] == deal_id].sort_values(["period", "loan_id"], kind="stable")
        fmt = fmt_of[deal_id]
        a = _format_a_frame(rows, static)
        if fmt == "A":
            u = rng_aux.random(len(a))
            a["arrears_days"] = arrears_days(rows["dpd_bucket"].to_numpy(), rows["months_in_90"].to_numpy(), u)
            df, schema, sub = a, FORMAT_A, "trustee_a"
        else:
            df, schema, sub = _format_b_frame(a, rows), FORMAT_B, "trustee_b"
        month_col = "report_month" if fmt == "A" else "ReportMonth"
        for month in resub.get(deal_id, []):
            if (df[month_col] == month).any():
                df = _resubmit(df, month, cfg, fmt)
        rel = f"{sub}/{deal_id}.parquet"
        _write(df, schema, out_dir / rel)
        hashes[rel] = sha256(out_dir / rel)
    return hashes
