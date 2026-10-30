"""Run the generator for a profile (kickoff 7: `generate`).

`run_profile` builds everything in memory with the single generator of instruction 01
part D, in its fixed order: HPI noise, static loan draws, then the month loop.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from rmbsq.config import Config
from rmbsq.synth.geography import build_geography
from rmbsq.synth.hpi import build_hpi
from rmbsq.synth.loans import draw_loans
from rmbsq.synth.rates import build_cash_rate
from rmbsq.synth.simulate import simulate


def profile_config(cfg: Config, profile: str) -> Config:
    """cfg with [deals] n_deals and loans_per_deal taken from [profiles.<profile>]."""
    p = cfg.profiles[profile]
    return dataclasses.replace(cfg, deals=dataclasses.replace(cfg.deals, n_deals=p.n_deals, loans_per_deal=p.loans_per_deal))


def run_profile(cfg: Config, profile: str) -> dict:
    """geo, cash, hpi, loans, panel and deals for a profile, in memory."""
    cfg = profile_config(cfg, profile)
    rng = np.random.Generator(np.random.PCG64(cfg.project.seed))
    geo = build_geography(cfg)
    cash = build_cash_rate(cfg)
    hpi = build_hpi(cfg, geo, rng)
    loans = draw_loans(cfg, geo, cash, rng)
    panel, deals = simulate(cfg, loans, cash, hpi, rng)
    return {"cfg": cfg, "geo": geo, "cash": cash, "hpi": hpi, "loans": loans, "panel": panel, "deals": deals}
