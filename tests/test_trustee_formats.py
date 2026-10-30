"""Step 1.5: trustee files on the small profile (instruction 01 part G, H 1.5)."""

import hashlib
import json

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# instruction 01 G.1 and G.2, column for column
FORMAT_A_COLUMNS = [
    "loan_id", "deal_id", "report_month", "submission_seq", "opening_balance",
    "scheduled_principal", "curtailment", "closing_balance", "interest_rate", "arrears_days",
    "hardship_flag", "exit_code", "exit_balance", "loss_amount", "orig_month", "orig_balance",
    "orig_valuation", "orig_ltv", "rate_type", "fixed_end_month", "io_flag", "io_end_month",
    "occupancy", "lmi_flag", "city", "state", "area", "suburb",
]
FORMAT_B_COLUMNS = [
    "LoanId", "DealId", "ReportMonth", "SubmissionSeq", "OpeningBalanceCents",
    "ScheduledPrincipalCents", "CurtailmentCents", "ClosingBalanceCents", "InterestRate",
    "MissedPayments", "Status", "ExitCode", "ExitBalanceCents", "LossAmountCents", "OrigMonth",
    "OrigBalanceCents", "OrigValuationCents", "OrigLtv", "RateType", "FixedEndMonth", "IoFlag",
    "IoEndMonth", "Occupancy", "LmiFlag", "City", "State", "Area", "Suburb",
]


def _read(path):
    return pq.read_table(path).to_pandas()


def _files(small_raw, sub):
    return sorted((small_raw / sub).glob("*.parquet"))


def _truth(small):
    p = small["panel"].copy()
    p["month"] = p["period"].dt.strftime("%Y-%m")
    return p.set_index(["loan_id", "month"])


def test_arrears_days_in_bucket_range(small, small_raw):
    truth = _truth(small)
    files = _files(small_raw, "trustee_a")
    assert files
    for f in files:
        a = _read(f)
        t = truth.loc[list(zip(a["loan_id"], a["report_month"]))]
        bucket, m90 = t["dpd_bucket"].to_numpy(), t["months_in_90"].to_numpy()
        lo = np.select([bucket == 0, bucket == 1, bucket == 2, bucket == 3], [0, 1, 30, 60], 90 + 30 * (m90 - 1))
        hi = np.select([bucket == 0, bucket == 1, bucket == 2, bucket == 3], [0, 29, 59, 89], 90 + 30 * (m90 - 1) + 29)
        days = a["arrears_days"].to_numpy()
        assert ((days >= lo) & (days <= hi)).all(), f.name
        assert (days[a["hardship_flag"].to_numpy() == 1] == 0).all(), f.name


def test_format_b_cents_int64(small_raw):
    files = _files(small_raw, "trustee_b")
    assert files
    for f in files:
        schema = pq.read_schema(f)
        cents = [n for n in schema.names if n.endswith("Cents")]
        assert len(cents) == 8
        assert all(str(schema.field(n).type) == "int64" for n in cents), f.name


def test_called_exit_codes(small, small_raw):
    called = small["panel"][small["panel"]["exit_reason"] == "called"]
    assert len(called) > 0
    keys = set(zip(called["loan_id"], called["period"].dt.strftime("%Y-%m")))
    n_seen = 0
    for f in _files(small_raw, "trustee_a"):
        a = _read(f)
        is_called = [(k in keys) for k in zip(a["loan_id"], a["report_month"])]
        assert (a.loc[is_called, "exit_code"] == "CALL").all()
        assert ((a["exit_code"] == "CALL") == pd.Series(is_called)).all()
        n_seen += sum(is_called)
    for f in _files(small_raw, "trustee_b"):
        b = _read(f)
        is_called = [(k in keys) for k in zip(b["LoanId"], b["ReportMonth"])]
        assert (b.loc[is_called, "ExitCode"] == "P").all()
        assert not b["ExitCode"].isin(["CALL"]).any()
        n_seen += sum(is_called)
    assert n_seen == len(called)


def test_resubmissions_exactly_d004(cfg, small, small_raw):
    seen = []
    for sub, seq, month, loan in [("trustee_a", "submission_seq", "report_month", "loan_id"),
                                  ("trustee_b", "SubmissionSeq", "ReportMonth", "LoanId")]:
        for f in _files(small_raw, sub):
            df = _read(f)
            for m in sorted(df.loc[df[seq] == 2, month].unique()):
                seen.append((f.stem, m))
    assert seen == [("D004", "2023-06")]

    b = _read(small_raw / "trustee_b" / "D004.parquet")
    month = b[b["ReportMonth"] == "2023-06"]
    truth = _truth(small).xs("2023-06", level="month")
    truth = truth[truth["deal_id"] == "D004"]
    assert len(month) == 2 * len(truth)
    s1 = month[month["SubmissionSeq"] == 1].set_index("LoanId").loc[truth.index]
    s2 = month[month["SubmissionSeq"] == 2].set_index("LoanId").loc[truth.index]
    true_close = np.round(truth["closing_balance"].to_numpy() * 100).astype(np.int64)
    true_curt = np.round(truth["curtailment"].to_numpy() * 100).astype(np.int64)
    assert (s2["ClosingBalanceCents"].to_numpy() == true_close).all()
    assert (s2["CurtailmentCents"].to_numpy() == true_curt).all()
    inflate = cfg.resubmissions.inflate
    assert (s1["ClosingBalanceCents"].to_numpy() == np.round(true_close * inflate).astype(np.int64)).all()
    assert (s1["CurtailmentCents"].to_numpy() == np.round(true_curt * inflate).astype(np.int64)).all()
    assert (s1["ClosingBalanceCents"] > s2["ClosingBalanceCents"]).any()
    # seq 1 comes first, rows sorted by report month then loan_id
    pos = month.reset_index(drop=True)
    assert (pos["SubmissionSeq"].to_numpy()[::2] == 1).all() and (pos["SubmissionSeq"].to_numpy()[1::2] == 2).all()


def test_column_lists(small_raw):
    for f in _files(small_raw, "trustee_a"):
        assert pq.read_schema(f).names == FORMAT_A_COLUMNS
    for f in _files(small_raw, "trustee_b"):
        assert pq.read_schema(f).names == FORMAT_B_COLUMNS


def test_manifest_hashes(small_raw):
    manifest = json.loads((small_raw / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    on_disk = sorted(p.relative_to(small_raw).as_posix() for p in small_raw.rglob("*") if p.is_file())
    assert sorted(manifest) == [p for p in on_disk if p != "MANIFEST.json"]
    for rel, digest in manifest.items():
        assert hashlib.sha256((small_raw / rel).read_bytes()).hexdigest() == digest, rel
    raw = (small_raw / "MANIFEST.json").read_bytes()
    assert b"\r" not in raw and raw.endswith(b"\n")
