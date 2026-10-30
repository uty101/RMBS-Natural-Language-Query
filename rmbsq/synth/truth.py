"""Pool metrics and calibration statistics from the true panel (step 1.6).

Metric definitions are kickoff 6.3; the calibration statistics are instruction 01
part F.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from rmbsq.config import Config
from rmbsq.synth.months import month_index, month_labels, from_period

POOL_COLUMNS = [
    "period", "arrears_30p_bal", "arrears_90p_bal", "hardship_share_bal", "cpr", "cdr",
    "wa_indexed_ltv", "balance_total",
]

# instruction 01 F, fixed_cliff_ratio: baseline rows -6 <= t - fixed_end_month <= -1
CLIFF_BASELINE_FROM = -6
CLIFF_BASELINE_TO = -1


def _flow_parts(panel: pd.DataFrame) -> pd.DataFrame:
    """Per-row numerators and denominators of smm_vol and mdr (kickoff 6.3), on rows with
    opening_balance > 0; other rows contribute 0."""
    flow = panel["opening_balance"] > 0
    reason = panel["exit_reason"]
    prepaid = (reason == "prepaid").to_numpy()
    vol_den_rows = (reason.isna() | (reason == "prepaid")).to_numpy()
    return pd.DataFrame(
        {
            "smm_num": np.where(flow, panel["curtailment"] + np.where(prepaid, panel["exit_balance"], 0.0), 0.0),
            "smm_den": np.where(flow & vol_den_rows, panel["opening_balance"] - panel["scheduled_principal"], 0.0),
            "mdr_num": np.where(flow & (reason == "defaulted").to_numpy(), panel["exit_balance"], 0.0),
            "mdr_den": np.where(flow, panel["opening_balance"], 0.0),
        },
        index=panel.index,
    )


def pool_monthly(panel: pd.DataFrame) -> pd.DataFrame:
    """Pool metrics per period (kickoff 6.3), ratio of sums. period as YYYY-MM."""
    stock = panel["closing_balance"] > 0
    bal = np.where(stock, panel["closing_balance"], 0.0)
    no_h = ~panel["hardship_flag"].to_numpy()
    dpd = panel["dpd_bucket"].to_numpy()
    parts = _flow_parts(panel).assign(
        period=panel["period"].to_numpy(),
        bal=bal,
        a30=np.where((dpd >= 2) & no_h, bal, 0.0),
        a90=np.where((dpd == 4) & no_h, bal, 0.0),
        hs=np.where(~no_h, bal, 0.0),
        ltv=bal * panel["indexed_ltv"].to_numpy(),
    )
    g = parts.groupby("period", sort=True).sum()
    smm = g["smm_num"] / g["smm_den"]
    mdr = g["mdr_num"] / g["mdr_den"]
    out = pd.DataFrame(
        {
            "period": month_labels(from_period(g.index)),
            "arrears_30p_bal": (g["a30"] / g["bal"]).to_numpy(),
            "arrears_90p_bal": (g["a90"] / g["bal"]).to_numpy(),
            "hardship_share_bal": (g["hs"] / g["bal"]).to_numpy(),
            "cpr": (1 - (1 - smm) ** 12).to_numpy(),
            "cdr": (1 - (1 - mdr) ** 12).to_numpy(),
            "wa_indexed_ltv": (g["ltv"] / g["bal"]).to_numpy(),
            "balance_total": g["bal"].to_numpy(),
        }
    )
    return out[POOL_COLUMNS]


def calibration(cfg: Config, panel: pd.DataFrame, loans: pd.DataFrame, deals: pd.DataFrame) -> pd.DataFrame:
    """Instruction 01 part F: stat, value, band_lo, band_hi, pass. A one-sided band has an
    empty band_hi."""
    C = cfg.calibration
    rows = []

    def add(stat, value, lo, hi):
        ok = (lo is None or value >= lo) and (hi is None or value <= hi)
        rows.append({"stat": stat, "value": value, "band_lo": lo, "band_hi": hi, "pass": bool(ok)})

    add("rows", len(panel), C.rows_min, C.rows_max)

    g = panel.assign(**_flow_parts(panel))
    stock = panel["closing_balance"] > 0
    bal = np.where(stock, panel["closing_balance"], 0.0)
    a90 = np.where((panel["dpd_bucket"] == 4) & ~panel["hardship_flag"], bal, 0.0)
    by_m = pd.DataFrame({"period": panel["period"], "bal": bal, "a90": a90}).groupby("period").sum()
    arrears = by_m["a90"] / by_m["bal"]
    labels = month_labels(from_period(arrears.index))
    win = (labels >= cfg.calendar.window_start) & (labels <= cfg.calendar.window_end)
    a = arrears[win]
    add("arrears_90p_min", float(a.min()), C.arrears_90p_min, C.arrears_90p_max)
    add("arrears_90p_max", float(a.max()), C.arrears_90p_min, C.arrears_90p_max)
    peak = labels[win][int(np.argmax(a.to_numpy()))]  # first on ties
    rows.append(
        {"stat": "arrears_peak_month", "value": peak, "band_lo": C.arrears_peak_from, "band_hi": C.arrears_peak_to,
         "pass": bool(C.arrears_peak_from <= peak <= C.arrears_peak_to)}
    )

    # cpr12(m) = 1 - prod(1 - smm_vol) over the 12 months ending m, for m from 2022-09
    # (window_start + 11) to 2026-09; the window has every month, so i - 11 is m - 11
    fm = g.groupby("period")[["smm_num", "smm_den"]].sum()
    surv = 1 - (fm["smm_num"] / fm["smm_den"]).to_numpy()
    months = from_period(fm.index)
    assert (np.diff(months) == 1).all() and months[0] == month_index(cfg.calendar.window_start)
    cpr12 = [1 - np.prod(surv[i - 11 : i + 1]) for i in range(11, len(surv))]
    add("cpr12_min", float(min(cpr12)), C.cpr12_min, C.cpr12_max)
    add("cpr12_max", float(max(cpr12)), C.cpr12_min, C.cpr12_max)

    fe = from_period(loans.set_index("loan_id").loc[panel["loan_id"], "fixed_end_month"])
    rel = from_period(panel["period"]) - fe
    is_fixed = fe >= 0
    cliff = is_fixed & (rel >= 0) & (rel <= cfg.behaviour.fixed_cliff_months - 1)
    before = is_fixed & (rel >= CLIFF_BASELINE_FROM) & (rel <= CLIFF_BASELINE_TO)
    ratio = (g["smm_num"][cliff].sum() / g["smm_den"][cliff].sum()) / (
        g["smm_num"][before].sum() / g["smm_den"][before].sum()
    )
    add("fixed_cliff_ratio", float(ratio), C.fixed_cliff_ratio_min, None)

    called = panel.loc[panel["exit_reason"] == "called", "deal_id"].unique()
    fmt = deals.set_index("deal_id")["trustee_format"]
    add("deals_called", int(len(called)), C.min_deals_called, None)
    add("b_deals_called", int((fmt.loc[called] == "B").sum()), C.min_b_deals_called, None)
    return pd.DataFrame(rows, columns=["stat", "value", "band_lo", "band_hi", "pass"])


def _cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (bool, np.bool_)):
        return str(bool(v))
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        return "%.10f" % v
    return str(v)


def write_csv(df: pd.DataFrame, path) -> None:
    """CSV with floats as %.10f, ints as ints, None as empty, LF line endings."""
    lines = [",".join(df.columns)]
    for row in df.itertuples(index=False):
        lines.append(",".join(_cell(v) for v in row))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
