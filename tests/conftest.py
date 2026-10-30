"""Shared fixtures. Tests build what they read (CLAUDE.md rule 7)."""

from pathlib import Path

import pytest

from rmbsq.canonical.build import build_canonical, canonical_rows
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


@pytest.fixture(scope="session")
def small_rows(small_raw, cfg):
    """The small profile's canonical rows (ingested, deduped, calls detected, enriched)."""
    return canonical_rows(small_raw, cfg)


@pytest.fixture(scope="session")
def small_db(small_raw, cfg, tmp_path_factory):
    """build_canonical on the small profile's raw files; the DuckDB file path."""
    db = tmp_path_factory.mktemp("small_db") / "rmbs.duckdb"
    build_canonical(small_raw, db, cfg)
    return db


@pytest.fixture(scope="session")
def full_db(cfg, tmp_path_factory):
    """build_canonical on the committed full data/raw/ (tests marked `full` only)."""
    db = tmp_path_factory.mktemp("full_db") / "rmbs.duckdb"
    build_canonical(ROOT / "data" / "raw", db, cfg)
    return db
