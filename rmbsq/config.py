"""Config loading: config.toml and the config/*.csv tables (step 1.1).

`load_config` returns a frozen dataclass tree that mirrors `config.toml` section by
section and key by key. TOML arrays become tuples so the tree stays immutable. Tests
change a value with `dataclasses.replace` on a copy (instruction 01, O-26).

`Config.root` is the folder holding `config.toml`. It is not a TOML key: the synth
functions take only `cfg`, and they find the `config/*.csv` tables through it.
"""

from __future__ import annotations

import dataclasses
import tomllib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class Project:
    seed: int
    seed_aux: int


@dataclass(frozen=True)
class Calendar:
    sim_start: str
    window_start: str
    window_end: str
    latest: str


@dataclass(frozen=True)
class Deals:
    n_deals: int
    loans_per_deal: int
    first_issue: str
    issue_span_months: int
    seasoning_min: int
    seasoning_max: int
    call_threshold: float
    call_detect_share: float


@dataclass(frozen=True)
class Profile:
    n_deals: int
    loans_per_deal: int


@dataclass(frozen=True)
class Loans:
    balance_median: int
    balance_sigma: float
    balance_min: int
    balance_max: int
    ltv_floor: float
    ltv_scale: float
    ltv_beta_a: float
    ltv_beta_b: float
    ltv_cap: float
    lmi_ltv: float
    p_investor: float
    p_io_investor: float
    p_io_owner: float
    io_term: int
    p_fixed_pre2020: float
    p_fixed_2020_2022: float
    p_fixed_post2022: float
    fixed_terms: tuple[int, ...]
    margin_mean: float
    margin_sd: float
    margin_min: float
    margin_max: float
    margin_investor: float
    margin_io: float
    fixed_spread_mean: float
    fixed_spread_sd: float
    fixed_rate_min: float
    fixed_rate_max: float
    term: int
    city_mult: dict[str, float]


@dataclass(frozen=True)
class Hpi:
    noise_phi: float
    noise_sd: float
    base: float


@dataclass(frozen=True)
class Behaviour:
    p_hardship: float
    hardship_min: int
    hardship_max: int
    a0: float
    a_shock: float
    a_ltv: float
    ltv_knot: float
    a_investor: float
    a_io_recent: float
    io_recent_months: int
    p_cure: tuple[float, ...]
    p_roll: tuple[float, ...]
    roll_shock: float
    shock_lookback_months: int
    p_cure_90: float
    default_after_90_months: int
    smm_start: float
    smm_flat: float
    smm_ramp_months: int
    fixed_cliff_mult: float
    fixed_cliff_months: int
    refi_spread: float
    refi_slope: float
    damp_ltv: float
    damp_mult: float
    smm_cap: float
    curtailment: float
    p_repurchase: float
    sale_haircut: float


@dataclass(frozen=True)
class Calibration:
    rows_min: int
    rows_max: int
    arrears_90p_min: float
    arrears_90p_max: float
    arrears_peak_from: str
    arrears_peak_to: str
    cpr12_min: float
    cpr12_max: float
    fixed_cliff_ratio_min: float
    min_deals_called: int
    min_b_deals_called: int


@dataclass(frozen=True)
class Resubmissions:
    deal_months: tuple[tuple[str, str], ...]
    inflate: float


@dataclass(frozen=True)
class Resolve:
    accept: int
    clarify: int
    top_k: int


@dataclass(frozen=True)
class Llm:
    model: str
    temperature: int
    max_tokens: int
    narration_max_words: int
    narration_max_rows: int
    baseline_timeout_s: int


@dataclass(frozen=True)
class Eval:
    tol_ratio_abs: float
    tol_balance_rel: float
    gold_tol_abs: float
    wilson_z: float


@dataclass(frozen=True)
class Benchmark:
    copies: int
    repeats: int
    warmup: int
    thread_settings: tuple[int, ...]


@dataclass(frozen=True)
class Deliverable:
    page_size: str
    design_max_pages: int
    summary_max_pages: int
    font: str


@dataclass(frozen=True)
class Config:
    project: Project
    calendar: Calendar
    deals: Deals
    profiles: dict[str, Profile]
    loans: Loans
    hpi: Hpi
    behaviour: Behaviour
    calibration: Calibration
    resubmissions: Resubmissions
    resolve: Resolve
    llm: Llm
    eval: Eval
    benchmark: Benchmark
    deliverable: Deliverable
    root: Path

    def table_path(self, name: str) -> Path:
        """Path of a `config/<name>.csv` table."""
        return self.root / "config" / f"{name}.csv"


def _tuples(value):
    """TOML arrays (nested too) as tuples, so the frozen tree holds no lists."""
    if isinstance(value, list):
        return tuple(_tuples(v) for v in value)
    return value


def _section(cls, raw: dict):
    names = {f.name for f in dataclasses.fields(cls)}
    if set(raw) != names:
        raise ValueError(f"{cls.__name__}: keys {sorted(set(raw) ^ names)} do not match")
    return cls(**{k: _tuples(v) for k, v in raw.items()})


def load_config(path: Path = Path("config.toml")) -> Config:
    path = Path(path)
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return Config(
        project=_section(Project, raw["project"]),
        calendar=_section(Calendar, raw["calendar"]),
        deals=_section(Deals, raw["deals"]),
        profiles={name: _section(Profile, p) for name, p in raw["profiles"].items()},
        loans=_section(Loans, raw["loans"]),
        hpi=_section(Hpi, raw["hpi"]),
        behaviour=_section(Behaviour, raw["behaviour"]),
        calibration=_section(Calibration, raw["calibration"]),
        resubmissions=_section(Resubmissions, raw["resubmissions"]),
        resolve=_section(Resolve, raw["resolve"]),
        llm=_section(Llm, raw["llm"]),
        eval=_section(Eval, raw["eval"]),
        benchmark=_section(Benchmark, raw["benchmark"]),
        deliverable=_section(Deliverable, raw["deliverable"]),
        root=path.resolve().parent,
    )


def config_to_dict(cfg: Config) -> dict:
    """The TOML-shaped dict of a Config (tuples back to lists, `root` dropped)."""

    def plain(value):
        if dataclasses.is_dataclass(value):
            return {f.name: plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
        if isinstance(value, dict):
            return {k: plain(v) for k, v in value.items()}
        if isinstance(value, tuple):
            return [plain(v) for v in value]
        return value

    out = plain(cfg)
    del out["root"]
    return out


def load_originators(path: Path) -> pd.DataFrame:
    """code, name, trustee_format (kickoff 4.2)."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def load_geography(path: Path) -> pd.DataFrame:
    """city, state, weight, area, beta: 1 row per area (kickoff 4.3)."""
    return pd.read_csv(
        path,
        dtype={"city": str, "state": str, "weight": float, "area": str, "beta": float},
        keep_default_na=False,
    )


def load_cash_steps(path: Path) -> pd.DataFrame:
    """period (YYYY-MM the step starts), rate (decimal) (kickoff 4.4)."""
    return pd.read_csv(path, dtype={"period": str, "rate": float}, keep_default_na=False)


def load_hpi_drift(path: Path) -> pd.DataFrame:
    """from, to (YYYY-MM), then 1 column per city with drift in percent (kickoff 4.5)."""
    df = pd.read_csv(path, dtype={"from": str, "to": str}, keep_default_na=False)
    for c in df.columns[2:]:
        df[c] = df[c].astype(float)
    return df
