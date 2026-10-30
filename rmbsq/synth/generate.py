"""Run the generator for a profile (kickoff 7: `generate`).

`run_profile` builds everything in memory with the single generator of instruction 01
part D, in its fixed order: HPI noise, static loan draws, then the month loop.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from rmbsq.config import Config
from rmbsq.synth.geography import build_geography
from rmbsq.synth.hpi import build_hpi
from rmbsq.synth.loans import draw_loans
from rmbsq.synth.months import from_period, month_labels
from rmbsq.synth.rates import build_cash_rate
from rmbsq.synth.simulate import simulate
from rmbsq.synth.trustee_formats import sha256, write_trustee_files

MANIFEST = "MANIFEST.json"


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


def write_raw(run: dict, out_dir: Path) -> None:
    """Instruction 01 G: trustee files, deals.parquet, hpi.parquet, cash_rate.parquet and
    MANIFEST.json (every file under out_dir except itself)."""
    cfg, out_dir = run["cfg"], Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng_aux = np.random.Generator(np.random.PCG64(cfg.project.seed_aux))
    write_trustee_files(cfg, run["panel"], run["loans"], out_dir, rng_aux)

    d = run["deals"]
    pq.write_table(
        pa.table(
            {
                "deal_id": pa.array(d["deal_id"].tolist(), pa.string()),
                "deal_name": pa.array(d["deal_name"].tolist(), pa.string()),
                "originator": pa.array(d["originator"].tolist(), pa.string()),
                "originator_name": pa.array(d["originator_name"].tolist(), pa.string()),
                "trustee_format": pa.array(d["trustee_format"].tolist(), pa.string()),
                "issue_month": pa.array(month_labels(from_period(d["issue_month"])).tolist(), pa.string()),
                "issue_balance": pa.array(np.round(d["issue_balance"].to_numpy(), 2), pa.float64()),
            }
        ),
        out_dir / "deals.parquet",
        compression="snappy",
    )
    h = run["hpi"]
    pq.write_table(
        pa.table(
            {
                "suburb": pa.array(h["suburb"].tolist(), pa.string()),
                "period": pa.array(month_labels(from_period(h["period"])).tolist(), pa.string()),
                "hpi": pa.array(h["hpi"].to_numpy(), pa.float64()),
            }
        ),
        out_dir / "hpi.parquet",
        compression="snappy",
    )
    c = run["cash"]
    pq.write_table(
        pa.table(
            {
                "period": pa.array(month_labels(from_period(c["period"])).tolist(), pa.string()),
                "rate": pa.array(c["rate"].to_numpy(), pa.float64()),
            }
        ),
        out_dir / "cash_rate.parquet",
        compression="snappy",
    )
    write_manifest(out_dir)


def write_manifest(out_dir: Path) -> dict[str, str]:
    """MANIFEST.json: {"files": {relative POSIX path: sha256}}, sorted keys, indent 2, LF."""
    out_dir = Path(out_dir)
    files = {
        p.relative_to(out_dir).as_posix(): sha256(p)
        for p in sorted(out_dir.rglob("*"))
        if p.is_file() and p.name != MANIFEST
    }
    text = json.dumps({"files": files}, sort_keys=True, indent=2) + "\n"
    (out_dir / MANIFEST).write_bytes(text.encode("utf-8"))
    return files


def generate(cfg: Config, profile: str, out_dir: Path) -> None:
    """Generate a profile's raw files into out_dir."""
    write_raw(run_profile(cfg, profile), out_dir)
