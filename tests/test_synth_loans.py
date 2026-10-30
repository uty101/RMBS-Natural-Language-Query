"""Step 1.3: deals and static loan attributes (instruction 01 D.2, D.3, H 1.3)."""

import dataclasses

import numpy as np
import pandas as pd
import pytest

from rmbsq.synth.deals import build_deals
from rmbsq.synth.geography import build_geography
from rmbsq.synth.hpi import build_hpi
from rmbsq.synth.loans import draw_loans
from rmbsq.synth.rates import build_cash_rate


def _loans(cfg):
    """The loan draw alone, after the HPI noise draw, as in generate."""
    rng = np.random.Generator(np.random.PCG64(cfg.project.seed))
    geo = build_geography(cfg)
    build_hpi(cfg, geo, rng)
    return draw_loans(cfg, geo, build_cash_rate(cfg), rng)


def _profile(cfg, name):
    p = cfg.profiles[name]
    return dataclasses.replace(
        cfg, deals=dataclasses.replace(cfg.deals, n_deals=p.n_deals, loans_per_deal=p.loans_per_deal)
    )


@pytest.fixture(scope="module")
def full_loans(cfg):
    return _loans(_profile(cfg, "full"))


@pytest.fixture(scope="module")
def small_loans(cfg):
    return _loans(_profile(cfg, "small"))


@pytest.mark.parametrize("profile", ["small", "full"])
def test_loans_per_deal_unique_ids(cfg, profile, small_loans, full_loans):
    loans = small_loans if profile == "small" else full_loans
    p = cfg.profiles[profile]
    counts = loans.groupby("deal_id").size()
    assert len(counts) == p.n_deals
    assert (counts == p.loans_per_deal).all()
    assert loans["loan_id"].is_unique
    assert loans["loan_id"].is_monotonic_increasing


def test_ltv_range_and_lmi_flag(full_loans):
    ltv = full_loans["orig_ltv"]
    assert ltv.min() >= 0.35 and ltv.max() <= 0.95
    assert (full_loans["lmi_flag"] == (ltv > 0.80)).all()


def test_fixed_share_by_era(cfg, full_loans):
    m = full_loans["orig_month"]
    fixed = full_loans["rate_type"] == "fixed"
    eras = {
        "pre2020": (m < pd.Timestamp("2020-01-01"), cfg.loans.p_fixed_pre2020),
        "2020_2022": ((m >= pd.Timestamp("2020-01-01")) & (m <= pd.Timestamp("2022-03-01")), cfg.loans.p_fixed_2020_2022),
        "post2022": (m > pd.Timestamp("2022-03-01"), cfg.loans.p_fixed_post2022),
    }
    for name, (mask, target) in eras.items():
        assert mask.sum() > 0, name
        assert abs(fixed[mask].mean() - target) <= 0.03, name


def test_null_end_months(full_loans):
    fixed = full_loans["rate_type"] == "fixed"
    assert (full_loans["fixed_end_month"].isna() == ~fixed).all()
    assert (full_loans["fixed_rate"].isna() == ~fixed).all()
    assert (full_loans["io_end_month"].isna() == ~full_loans["io_flag"]).all()


def test_deal_names(cfg):
    deals = build_deals(cfg, cfg.profiles["full"].n_deals).set_index("deal_id")
    assert deals.loc["D001", "deal_name"] == "HARB 2019-1"
    assert deals.loc["D006", "deal_name"] == "HARB 2019-2"
