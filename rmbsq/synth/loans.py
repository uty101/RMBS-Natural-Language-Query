"""Static loan attributes at origination (kickoff 4.2 and 4.6). Built in step 1.3.

Instruction 01 D.3: deal by deal in deal_id order, 12 arrays of length loans_per_deal,
in exactly the order below. Every array is drawn for every loan and then masked.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from rmbsq.config import Config
from rmbsq.synth.deals import build_deals
from rmbsq.synth.geography import city_weights
from rmbsq.synth.months import from_period, month_index, to_period

# Fixed-rate origination eras (kickoff 4.6, instruction 01 D.3 step 9):
# before 2020-01; 2020-01 to 2022-03 inclusive; after.
ERA_2020_START = "2020-01"
ERA_2020_END = "2022-03"
# fixed_term = fixed_terms[0] if u_term < 0.5 else fixed_terms[1] (instruction 01 D.3 step 10)
FIXED_TERM_SPLIT = 0.5

LOAN_COLUMNS = [
    "loan_id", "deal_id", "originator", "trustee_format", "issue_month", "seasoning",
    "orig_month", "city", "state", "area", "suburb", "orig_balance", "orig_ltv",
    "orig_valuation", "lmi_flag", "occupancy", "io_flag", "io_end_month", "rate_type",
    "fixed_term", "fixed_end_month", "margin", "fixed_rate",
]


def draw_loans(cfg: Config, geo: pd.DataFrame, cash: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """1 row per loan, in loan_id order (deal_id, then loan number)."""
    L, B = cfg.loans, cfg.deals
    n = B.loans_per_deal
    deals = build_deals(cfg, B.n_deals)

    weights = city_weights(cfg)
    cities = list(weights.index)
    cum_w = np.cumsum(weights.to_numpy())
    areas_of = {c: list(dict.fromkeys(geo.loc[geo["city"] == c, "area"])) for c in cities}
    n_areas = len(areas_of[cities[0]])
    n_sub = len(geo) // (len(cities) * n_areas)
    # D.3 draws rng.integers(0, 4, n) and rng.integers(0, 3, n): the geography must match
    assert n_areas == 4 and n_sub == 3 and len(geo) == 60

    cash_months = from_period(cash["period"])
    cash_rate = cash["rate"].to_numpy()
    era_lo, era_hi = month_index(ERA_2020_START), month_index(ERA_2020_END)
    issue_months = from_period(deals["issue_month"])

    parts = []
    for d, deal in enumerate(deals.itertuples(index=False)):
        seasoning = rng.integers(B.seasoning_min, B.seasoning_max + 1, n)  # 1
        u_city = rng.random(n)  # 2
        area_i = rng.integers(0, 4, n)  # 3
        sub_i = rng.integers(0, 3, n)  # 4 (0 North, 1 Central, 2 South)
        z_bal = rng.standard_normal(n)  # 5
        b_ltv = rng.beta(L.ltv_beta_a, L.ltv_beta_b, n)  # 6
        u_inv = rng.random(n)  # 7
        u_io = rng.random(n)  # 8
        u_fix = rng.random(n)  # 9
        u_term = rng.random(n)  # 10
        z_margin = rng.standard_normal(n)  # 11
        z_fixed = rng.standard_normal(n)  # 12

        city_i = np.minimum(np.searchsorted(cum_w, u_city, side="right"), len(cities) - 1)
        geo_row = city_i * n_areas * n_sub + area_i * n_sub + sub_i
        city = geo["city"].to_numpy()[geo_row]

        orig_month = issue_months[d] - seasoning
        city_mult = np.array([L.city_mult[c] for c in city])
        orig_balance = np.round(
            np.clip(np.exp(np.log(L.balance_median * city_mult) + L.balance_sigma * z_bal), L.balance_min, L.balance_max)
        )
        orig_ltv = np.minimum(L.ltv_floor + L.ltv_scale * b_ltv, L.ltv_cap)
        orig_valuation = np.round(orig_balance / orig_ltv)

        investor = u_inv < L.p_investor
        io_flag = u_io < np.where(investor, L.p_io_investor, L.p_io_owner)
        p_fixed = np.where(
            orig_month < era_lo, L.p_fixed_pre2020, np.where(orig_month <= era_hi, L.p_fixed_2020_2022, L.p_fixed_post2022)
        )
        fixed = u_fix < p_fixed
        fixed_term = np.where(u_term < FIXED_TERM_SPLIT, L.fixed_terms[0], L.fixed_terms[1])

        margin = (
            np.clip(L.margin_mean + L.margin_sd * z_margin, L.margin_min, L.margin_max)
            + L.margin_investor * investor
            + L.margin_io * io_flag
        )
        cash_at_orig = cash_rate[np.searchsorted(cash_months, orig_month)]
        fixed_rate = np.clip(cash_at_orig + L.fixed_spread_mean + L.fixed_spread_sd * z_fixed, L.fixed_rate_min, L.fixed_rate_max)

        parts.append(
            pd.DataFrame(
                {
                    "loan_id": [f"{deal.deal_id}-{i:04d}" for i in range(1, n + 1)],
                    "deal_id": deal.deal_id,
                    "originator": deal.originator,
                    "trustee_format": deal.trustee_format,
                    "issue_month": issue_months[d],
                    "seasoning": seasoning,
                    "orig_month": orig_month,
                    "city": city,
                    "state": geo["state"].to_numpy()[geo_row],
                    "area": geo["area"].to_numpy()[geo_row],
                    "suburb": geo["suburb"].to_numpy()[geo_row],
                    "orig_balance": orig_balance,
                    "orig_ltv": orig_ltv,
                    "orig_valuation": orig_valuation,
                    "lmi_flag": orig_ltv > L.lmi_ltv,
                    "occupancy": np.where(investor, "investor", "owner"),
                    "io_flag": io_flag,
                    "io_end_month": np.where(io_flag, orig_month + L.io_term, -1),
                    "rate_type": np.where(fixed, "fixed", "variable"),
                    "fixed_term": np.where(fixed, fixed_term, -1),
                    "fixed_end_month": np.where(fixed, orig_month + fixed_term, -1),
                    "margin": margin,
                    "fixed_rate": np.where(fixed, fixed_rate, np.nan),
                }
            )
        )

    loans = pd.concat(parts, ignore_index=True)[LOAN_COLUMNS]
    for c in ["issue_month", "orig_month", "io_end_month", "fixed_end_month"]:
        m = loans[c].to_numpy()
        loans[c] = np.where(m >= 0, to_period(np.maximum(m, 0)), np.datetime64("NaT", "ns"))
    loans["fixed_term"] = loans["fixed_term"].astype("Int64").mask(loans["fixed_term"] < 0)
    return loans
