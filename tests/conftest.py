"""Shared fixtures. Tests build what they read (CLAUDE.md rule 7)."""

from pathlib import Path

import pytest

from rmbsq.config import load_config
from rmbsq.synth.generate import run_profile, write_raw

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def cfg():
    return load_config(ROOT / "config.toml")


@pytest.fixture(scope="session")
def small(cfg):
    """The small profile run once per session, in memory."""
    return run_profile(cfg, "small")


@pytest.fixture(scope="session")
def small_raw(small, tmp_path_factory):
    """The small profile's raw files, written once per session into a temp folder."""
    out = tmp_path_factory.mktemp("small_raw")
    write_raw(small, out)
    return out
