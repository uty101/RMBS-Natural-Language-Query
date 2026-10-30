"""Step 1.1: config round trip and the config/*.csv tables (kickoff 4.2 to 4.5)."""

import tomllib
from pathlib import Path

import pytest

from rmbsq.config import (
    config_to_dict,
    load_cash_steps,
    load_config,
    load_geography,
    load_hpi_drift,
    load_originators,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def cfg():
    return load_config(ROOT / "config.toml")


def test_config_round_trip(cfg):
    with open(ROOT / "config.toml", "rb") as f:
        raw = tomllib.load(f)
    assert config_to_dict(cfg) == raw


def test_originators_csv(cfg):
    df = load_originators(cfg.table_path("originators"))
    assert df.to_dict("records") == [
        {"code": "HARB", "name": "Harbour Home Loans", "trustee_format": "A"},
        {"code": "KOO", "name": "Kookaburra Mutual", "trustee_format": "A"},
        {"code": "WAT", "name": "Wattle Lending", "trustee_format": "A"},
        {"code": "CST", "name": "Coastline Bank", "trustee_format": "B"},
        {"code": "RED", "name": "Redgum Finance", "trustee_format": "B"},
    ]


def test_geography_csv(cfg):
    df = load_geography(cfg.table_path("geography")).set_index("area")
    assert len(df) == 20
    assert df.loc["Blacktown", "beta"] == 1.2
    assert df.loc["Boroondara", "beta"] == 0.8
    assert df.loc["Logan", "beta"] == 1.3
    assert df.loc["Charles Sturt", "beta"] == 0.9
    assert df.loc["Wanneroo", ["city", "state", "weight"]].tolist() == ["Perth", "WA", 0.12]


def test_cash_rate_csv(cfg):
    df = load_cash_steps(cfg.table_path("cash_rate")).set_index("period")["rate"]
    assert len(df) == 24
    assert df["2016-01"] == 0.0200
    assert df["2020-11"] == 0.0010
    assert df["2022-05"] == 0.0035
    assert df["2023-11"] == 0.0435
    assert df["2025-08"] == 0.0360


def test_hpi_drift_csv(cfg):
    df = load_hpi_drift(cfg.table_path("hpi_drift")).set_index("from")
    assert len(df) == 8
    assert df.loc["2016-01", "Perth"] == -0.2
    assert df.loc["2022-04", "Sydney"] == -1.4
    assert df.loc["2022-04", "to"] == "2023-01"
    assert df.loc["2025-01", "Adelaide"] == 0.6
