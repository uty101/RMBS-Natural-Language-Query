"""Claims traced to committed CSVs (instruction 06 D). Step 6.2.

`build_claims` reads the summary CSVs in `outputs/` and writes `deliverable/claims.csv`
with 1 row per claim: the raw value, the display string placed in documents, the source
CSV and the rule. The eval claims are built only in the recorded state, from
`eval_summary.csv`.
"""

from __future__ import annotations

import csv
from decimal import ROUND_CEILING, Decimal
from pathlib import Path

import pandas as pd

from rmbsq.semantic.catalog import ROOT

OUTPUTS = ROOT / "outputs"
CLAIMS_CSV = ROOT / "deliverable" / "claims.csv"
COLUMNS = ["claim_id", "value", "display", "source_file", "source_rule"]
GOLD_MATCH_TOL = 1e-9  # instruction 06 D: gold_matched counts max_scaled_diff <= 1e-9

FORMATS = {
    "int": lambda v: f"{int(v):,}",
    "pct2": lambda v: f"{float(v) * 100:.2f}%",
    "pct1": lambda v: f"{float(v) * 100:.1f}%",
    "s2": lambda v: f"{float(v):.2f}",
    "sci1": lambda v: f"{float(v):.1e}",
    "str": str,
}


def _s2_up(v: float) -> str:
    """s2 rounded up, for a value written as "under X seconds" (instruction 06 D)."""
    return str(Decimal(repr(float(v))).quantize(Decimal("0.01"), rounding=ROUND_CEILING))


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _number(s: str):
    return int(s) if s.lstrip("-").isdigit() else float(s)


def _claims(outputs: Path) -> list[tuple]:
    """(claim_id, value, display, source_file, source_rule) in instruction 06 D order."""
    rows = []

    def add(claim_id, value, fmt, source, rule, display=None):
        rows.append((claim_id, value, FORMATS[fmt](value) if display is None else display,
                     f"outputs/{source}", rule))

    summary = _csv(outputs / "data_summary.csv")
    stat = {s: v for s, v in zip(summary["stat"], summary["value"])}
    for name in ["n_deals", "n_loans", "n_loan_months", "n_raw_rows", "n_resubmission_duplicates",
                 "n_called_deals", "n_called_deals_b", "canonical_truth_mismatches"]:
        add(name, int(stat[name]), "int", "data_summary.csv", f"stat {name}")
    for which in ["first", "peak", "latest"]:
        add(f"arrears_90p_{which}_pct", float(stat[f"arrears_90p_{which}"]), "pct2", "data_summary.csv",
            f"stat arrears_90p_{which}")
    add("arrears_90p_peak_month", stat["arrears_90p_peak_month"], "str", "data_summary.csv",
        "stat arrears_90p_peak_month")

    check = _csv(outputs / "compiler_check.csv")
    diffs = check["max_scaled_diff"].astype(float)
    add("gold_total", len(check), "int", "compiler_check.csv", "row count")
    add("gold_matched", int((diffs <= GOLD_MATCH_TOL).sum()), "int", "compiler_check.csv",
        "rows with max_scaled_diff <= 1e-9")
    add("gold_worst_diff", float(diffs.max()), "sci1", "compiler_check.csv", "max of max_scaled_diff")
    add("oracle_ok", int((check["oracle_ok"] == "True").sum()), "int", "compiler_check.csv",
        "rows with oracle_ok true")

    bench = _csv(outputs / "scale_benchmark.csv")
    x36 = bench[bench["db"] == "36x"]
    add("rows_36x", int(x36["db_rows"].iloc[0]), "int", "scale_benchmark.csv", "db_rows where db = 36x")
    default_max = float(x36.loc[x36["threads"] == "0", "median_s"].astype(float).max())
    add("x36_max_default_s", default_max, "s2", "scale_benchmark.csv",
        "max median_s where db = 36x and threads = 0, rounded up to 2 dp", display=_s2_up(default_max))
    add("x36_max_single_s", float(x36.loc[x36["threads"] == "1", "median_s"].astype(float).max()), "s2",
        "scale_benchmark.csv", "max median_s where db = 36x and threads = 1")

    traps = _csv(outputs / "trap_effects.csv").set_index("item_id")
    gold = lambda i: _number(traps.loc[i, "gold"])    # noqa: E731
    naive = lambda i: _number(traps.loc[i, "naive"])  # noqa: E731
    add("trap_call_deal", "CST 2019-1", "str", "trap_effects.csv", "the Q29 deal_name filter")
    add("trap_call_gold_pct", gold("Q29"), "pct1", "trap_effects.csv", "Q29 gold")
    add("trap_call_naive_pct", naive("Q29"), "pct1", "trap_effects.csv", "Q29 naive")
    add("trap_exit_extra_loans", naive("Q32") - gold("Q32"), "int", "trap_effects.csv", "Q32 naive - gold")
    add("trap_exit_month", "November 2025", "str", "trap_effects.csv", "the Q32 month")
    add("trap_weight_gold_pct", gold("Q33"), "pct2", "trap_effects.csv", "Q33 gold")
    add("trap_weight_naive_pct", naive("Q33"), "pct2", "trap_effects.csv", "Q33 naive")
    add("trap_compound_cpr_pct", gold("Q2_2025"), "pct1", "trap_effects.csv", "Q2_2025 gold")
    add("trap_compound_gap", abs(gold("Q2_2025") - naive("Q2_2025")), "sci1", "trap_effects.csv",
        "abs(Q2_2025 gold - naive)")
    return rows


def _eval_claims(outputs: Path) -> list[tuple]:
    summary = _csv(outputs / "eval_summary.csv")
    row = {(s, c): r for s, c, r in zip(summary["system"], summary["category"], summary.to_dict("records"))}
    rows = []
    for prefix, system in [("sys", "system"), ("base", "baseline")]:
        total = row[(system, "total")]
        for name, fmt, col in [("k", "int", "k"), ("n", "int", "n")]:
            value = int(total[col])
            rows.append((f"{prefix}_total_{name}", value, FORMATS[fmt](value), "outputs/eval_summary.csv",
                         f"{col} of category total, system {system}"))
    for prefix, system in [("sys", "system"), ("base", "baseline")]:
        total = row[(system, "total")]
        for name, col in [("pct", "accuracy"), ("lo", "wilson_lo"), ("hi", "wilson_hi")]:
            value = float(total[col])
            rows.append((f"{prefix}_total_{name}", value, FORMATS["pct1"](value), "outputs/eval_summary.csv",
                         f"{col} of category total, system {system}"))
    for claim_id, system, category in [("sys_trap_k", "system", "trap"), ("base_trap_k", "baseline", "trap"),
                                       ("sys_ambig_k", "system", "ambiguous")]:
        value = int(row[(system, category)]["k"])
        rows.append((claim_id, value, FORMATS["int"](value), "outputs/eval_summary.csv",
                     f"k of category {category}, system {system}"))
    return rows


def _value_cell(v) -> str:
    """The raw value in full: floats as repr, so a 1e-15 difference survives."""
    return repr(v) if isinstance(v, float) else str(v)


def write_claims(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLUMNS)
        for row in df.itertuples(index=False):
            w.writerow([row.claim_id, _value_cell(row.value), row.display, row.source_file, row.source_rule])


def build_claims(eval_recorded: bool, outputs: Path = OUTPUTS, out: Path | None = CLAIMS_CSV) -> pd.DataFrame:
    rows = _claims(Path(outputs))
    if eval_recorded:
        rows += _eval_claims(Path(outputs))
    df = pd.DataFrame(rows, columns=COLUMNS, dtype=object)
    if out is not None:
        write_claims(df, Path(out))
    return df
