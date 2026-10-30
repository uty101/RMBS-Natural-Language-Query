"""Step 1.2: geography, cash rate and HPI (instruction 01 D.1, H 1.2)."""

import dataclasses

import numpy as np
import pandas as pd

from rmbsq.synth.geography import build_geography
from rmbsq.synth.hpi import build_hpi, hpi_matrix, hpi_unrounded
from rmbsq.synth.rates import build_cash_rate


def _rng(cfg):
    return np.random.Generator(np.random.PCG64(cfg.project.seed))


def test_sixty_suburbs_in_order(cfg):
    geo = build_geography(cfg)
    assert list(geo.columns) == ["city", "state", "area", "beta", "suburb"]
    assert len(geo) == 60 and geo["suburb"].is_unique
    assert list(dict.fromkeys(geo["city"])) == ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"]
    assert geo["suburb"].iloc[:4].tolist() == [
        "Blacktown North", "Blacktown Central", "Blacktown South", "Parramatta North",
    ]
    assert geo["suburb"].iloc[-1] == "Charles Sturt South"


def test_cash_rate_points(cfg):
    cash = build_cash_rate(cfg).set_index("period")["rate"]
    assert len(cash) == 129
    assert cash[pd.Timestamp("2022-05-01")] == 0.0035
    assert cash[pd.Timestamp("2023-11-01")] == 0.0435
    assert cash[pd.Timestamp("2026-09-01")] == 0.036


def test_hpi_deterministic(cfg):
    geo = build_geography(cfg)
    a = build_hpi(cfg, geo, _rng(cfg))
    b = build_hpi(cfg, geo, _rng(cfg))
    pd.testing.assert_frame_equal(a, b)


def test_hpi_zero_noise_blacktown_north(cfg):
    zero = dataclasses.replace(cfg, hpi=dataclasses.replace(cfg.hpi, noise_sd=0.0))
    hpi = build_hpi(zero, build_geography(zero), _rng(zero))
    s = hpi[hpi["suburb"] == "Blacktown North"].set_index("period")["hpi"]
    change = np.log(s[pd.Timestamp("2023-01-01")]) - np.log(s[pd.Timestamp("2022-03-01")])
    # instruction 01 H 1.2: beta 1.2 x 10 months x drift -1.4 % / 100
    assert abs(change - 1.2 * 10 * (-1.4) / 100) <= 0.005


def test_hpi_frame_rows(cfg):
    hpi = build_hpi(cfg, build_geography(cfg), _rng(cfg))
    assert len(hpi) == 60 * 129
    assert (hpi[hpi["period"] == pd.Timestamp("2016-01-01")]["hpi"] == 100.0).all()


def test_hpi_rounded(cfg):
    geo = build_geography(cfg)
    _, raw = hpi_unrounded(cfg, geo, _rng(cfg))
    _, rounded = hpi_matrix(cfg, geo, _rng(cfg))
    assert np.array_equal(rounded, np.round(raw, cfg.hpi.round_dp))
    frame = build_hpi(cfg, geo, _rng(cfg))["hpi"].to_numpy()
    assert np.array_equal(frame, rounded.reshape(-1))
    # at most round_dp decimal places: rounding again changes nothing
    assert np.array_equal(np.round(frame, cfg.hpi.round_dp), frame)
    assert cfg.hpi.round_dp == 6
