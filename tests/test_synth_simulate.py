"""Step 1.4: monthly simulation (instruction 01 part E, H 1.4).

Constructed loan frames force a path with a modified copy of Config (O-26). Where a path
can't be forced to certainty, the test checks a property of every realised path.
"""

import dataclasses

import numpy as np
import numpy_financial as npf
import pandas as pd
import pytest

from rmbsq.synth.deals import build_deals
from rmbsq.synth.geography import build_geography
from rmbsq.synth.hpi import build_hpi
from rmbsq.synth.loans import LOAN_COLUMNS
from rmbsq.synth.rates import build_cash_rate
from rmbsq.synth.simulate import simulate

TS = pd.Timestamp


def _with(cfg, **behaviour):
    """cfg with [behaviour] keys replaced; call_threshold is a [deals] key."""
    deals = {k: behaviour.pop(k) for k in ["call_threshold"] if k in behaviour}
    return dataclasses.replace(
        cfg, behaviour=dataclasses.replace(cfg.behaviour, **behaviour), deals=dataclasses.replace(cfg.deals, **deals)
    )


def _frame(cfg, deal_id, n, orig, *, io_end=None, fixed_end=None, fixed_rate=None, balance=500000.0, margin=0.025):
    """n identical constructed loans in one deal (issue month from build_deals)."""
    issue = build_deals(cfg, cfg.deals.n_deals).set_index("deal_id").loc[deal_id, "issue_month"]
    fixed = fixed_end is not None
    rows = [
        {
            "loan_id": f"{deal_id}-{i:04d}", "deal_id": deal_id, "originator": "HARB", "trustee_format": "A",
            "issue_month": issue, "seasoning": (issue.year - TS(orig).year) * 12 + issue.month - TS(orig).month,
            "orig_month": TS(orig), "city": "Sydney", "state": "NSW", "area": "Blacktown", "suburb": "Blacktown North",
            "orig_balance": balance, "orig_ltv": 0.625, "orig_valuation": round(balance / 0.625), "lmi_flag": False,
            "occupancy": "owner", "io_flag": io_end is not None,
            "io_end_month": TS(io_end) if io_end else pd.NaT,
            "rate_type": "fixed" if fixed else "variable", "fixed_term": pd.NA,
            "fixed_end_month": TS(fixed_end) if fixed else pd.NaT,
            "margin": margin, "fixed_rate": fixed_rate if fixed else np.nan,
        }
        for i in range(1, n + 1)
    ]
    df = pd.DataFrame(rows)[LOAN_COLUMNS]
    df["fixed_term"] = df["fixed_term"].astype("Int64")
    return df


def _run(cfg, loans):
    rng = np.random.Generator(np.random.PCG64(cfg.project.seed))
    geo = build_geography(cfg)
    cash = build_cash_rate(cfg)
    hpi = build_hpi(cfg, geo, rng)
    return simulate(cfg, loans, cash, hpi, rng)


@pytest.fixture(scope="module")
def quiet(cfg):
    """No hardship, no arrears, no prepayment, no repurchase: the loan just pays."""
    return _with(cfg, p_hardship=0.0, a0=-50.0, smm_start=0.0, smm_flat=0.0, p_repurchase=0.0)


def test_pi_annuity_matches_npf_pmt(quiet):
    loans = _frame(quiet, "D001", 1, "2018-06")
    panel, _ = _run(quiet, loans)
    row = panel[panel["period"] == TS("2024-03-01")].iloc[0]
    age = (2024 - 2018) * 12 + (3 - 6)
    r, opening = row["interest_rate"], row["opening_balance"]
    pmt = npf.pmt(r / 12, quiet.loans.term - age + 1, -opening)
    # scheduled_principal is rounded to the cent, so it agrees with pmt to half a cent
    assert abs(row["scheduled_principal"] + opening * r / 12 - pmt) <= 0.005 + 1e-9


def test_io_switch_at_io_end(quiet):
    loans = _frame(quiet, "D001", 1, "2018-06", io_end="2023-06")
    panel, _ = _run(quiet, loans)
    before = panel[panel["period"] < TS("2023-06-01")]
    after = panel[panel["period"] >= TS("2023-06-01")]
    assert len(before) > 0 and len(after) > 0
    assert (before["scheduled_principal"] == 0).all()
    assert (after["scheduled_principal"] > 0).all()


def test_fixed_to_variable_switch(quiet):
    loans = _frame(quiet, "D050", 1, "2022-06", fixed_end="2025-06", fixed_rate=0.045, margin=0.025)
    panel, _ = _run(quiet, loans)
    cash = build_cash_rate(quiet).set_index("period")["rate"]
    before = panel[panel["period"] < TS("2025-06-01")]
    after = panel[panel["period"] >= TS("2025-06-01")]
    assert len(before) > 0 and len(after) > 0
    assert (before["interest_rate"] == 0.045).all()
    assert np.allclose(after["interest_rate"], cash.loc[after["period"]].to_numpy() + 0.025, rtol=0, atol=1e-15)


@pytest.fixture(scope="module")
def hardship_panel(cfg):
    hcfg = _with(cfg, p_hardship=1.0, p_repurchase=0.0)
    panel, _ = _run(hcfg, _frame(hcfg, "D001", 50, "2018-06"))
    return panel


def test_hardship_rows_frozen(hardship_panel):
    h = hardship_panel[hardship_panel["hardship_flag"]]
    assert len(h) > 0
    assert (h["dpd_bucket"] == 0).all()
    assert (h["scheduled_principal"] == 0).all()
    assert (h["closing_balance"] == h["opening_balance"]).all()


def test_hardship_spell_lengths(cfg, hardship_panel):
    """Every hardship spell lasts hardship_min to hardship_max consecutive rows."""
    p = hardship_panel.sort_values(["loan_id", "period"])
    for _, g in p.groupby("loan_id"):
        flags = g["hardship_flag"].to_numpy()
        runs, n = [], 0
        for f in flags:
            if f:
                n += 1
            elif n:
                runs.append(n)
                n = 0
        if n:
            runs.append(n)
        assert all(cfg.behaviour.hardship_min <= r <= cfg.behaviour.hardship_max for r in runs), runs


def test_default_after_months_in_90(cfg):
    # a0 = 50 sends every current loan into arrears; the property is checked on every
    # realised path (O-26)
    dcfg = _with(cfg, a0=50.0)
    panel, _ = _run(dcfg, _frame(dcfg, "D050", 200, "2023-05"))
    p = panel.sort_values(["loan_id", "period"]).reset_index(drop=True)
    nxt = p.groupby("loan_id").shift(-1)
    prv = p.groupby("loan_id").shift(1)
    k = dcfg.behaviour.default_after_90_months
    reached = (p["months_in_90"] >= k) & nxt["period"].notna()
    assert reached.sum() > 0
    assert (nxt.loc[reached, "period"] == p.loc[reached, "period"] + pd.DateOffset(months=1)).all()
    assert (nxt.loc[reached, "exit_reason"] == "defaulted").all()
    defaulted = p["exit_reason"] == "defaulted"
    assert (prv.loc[defaulted, "months_in_90"] >= k).all()
    assert (prv.loc[defaulted, "period"] + pd.DateOffset(months=1) == p.loc[defaulted, "period"]).all()


def test_call_property_small(cfg, small):
    panel, deals = small["panel"], small["deals"].set_index("deal_id")
    called = panel[panel["exit_reason"] == "called"]
    assert called["deal_id"].nunique() > 0
    for deal_id, g in called.groupby("deal_id"):
        call_month = g["period"].min()
        rows = panel[panel["deal_id"] == deal_id]
        sums = rows.groupby("period")["closing_balance"].sum()
        below = sums[sums <= cfg.deals.call_threshold * deals.loc[deal_id, "issue_balance"]]
        assert below.index.min() + pd.DateOffset(months=1) == call_month, deal_id
        in_call_month = rows[rows["period"] == call_month]
        assert (in_call_month["exit_reason"] == "called").all(), deal_id
        assert g["period"].nunique() == 1


def test_every_deal_full_at_issue(small):
    cfg, panel, deals = small["cfg"], small["panel"], small["deals"]
    window_start = TS(cfg.calendar.window_start + "-01")
    checked = 0
    for d in deals.itertuples():
        if d.issue_month >= window_start:
            n = ((panel["deal_id"] == d.deal_id) & (panel["period"] == d.issue_month)).sum()
            assert n == cfg.deals.loans_per_deal, d.deal_id
            checked += 1
    assert checked > 0


def test_simulate_deterministic(cfg, small):
    from rmbsq.synth.generate import run_profile

    again = run_profile(cfg, "small")
    pd.testing.assert_frame_equal(small["panel"], again["panel"])
    pd.testing.assert_frame_equal(small["deals"], again["deals"])
