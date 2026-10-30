"""Scoring against gold results (kickoff 6.11; instruction 05 C). Steps 5.1, 5.2.

`compare_result` is the C.3 rule: the result must hold every output column, its key rows
(the gold group_by dimensions plus period_label, normalised to strings) must equal gold's
as a multiset, or in order when the gold spec has `order`, and every metric value must be
within the tolerance of its display kind. Tolerances come from `config.toml` (`[eval]`),
read once at import like the calendar in `rmbsq/semantic/spec.py`.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd

from rmbsq.config import load_config
from rmbsq.semantic.catalog import ROOT, load_catalog

_EVAL = load_config(ROOT / "config.toml").eval
_CATALOG = load_catalog()
COUNT_INT_TOL = 1e-9  # instruction 05 C.3: a count must be within 1e-9 of an integer


@dataclass(frozen=True)
class Check:
    correct: bool
    n_values_checked: int
    max_abs_err: float | None
    reason: str = ""


def norm_key(v) -> str:
    """C.3.2: bool to yes/no, a whole-number int or float to str(int(v)), else str(v).strip()."""
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)) and math.isfinite(v) and float(v).is_integer():
        return str(int(v))
    return str(v).strip()


def _key_rows(df: pd.DataFrame, keys: list[str]) -> list[tuple[str, ...]]:
    return [tuple(norm_key(v) for v in row) for row in df[keys].itertuples(index=False)]


def _number(v) -> float | None:
    """A cell as float, None for a null; raises ValueError for a non-numeric cell."""
    if v is None or v is pd.NA or (isinstance(v, float) and math.isnan(v)):
        return None
    return float(v)


def _within(display: str, got: float, want: float) -> bool:
    if display == "pct":
        return abs(got - want) <= _EVAL.tol_ratio_abs
    if display == "aud_m":
        return abs(got - want) <= _EVAL.tol_balance_rel * abs(want)
    if display == "count":
        return round(got) == round(want) and abs(got - round(got)) <= COUNT_INT_TOL
    raise ValueError(f"unknown display {display}")


def compare_result(result: pd.DataFrame | None, gold: pd.DataFrame, spec, output_columns) -> Check:
    """C.3: `result` against `gold`, the gold spec's result."""
    if result is None:
        return Check(False, 0, None, "no result")
    missing = [c for c in output_columns if c not in result.columns]
    if missing:
        return Check(False, 0, None, f"missing columns {missing}")
    keys = [*spec.group_by, "period_label"]
    got_keys, want_keys = _key_rows(result, keys), _key_rows(gold, keys)
    if spec.order is not None:
        if got_keys != want_keys:
            return Check(False, 0, None, "key rows differ in order")
    elif Counter(got_keys) != Counter(want_keys):
        return Check(False, 0, None, "key rows differ")

    # match by key; a repeated key pairs its occurrences in row order
    positions = defaultdict(list)
    for j, k in enumerate(got_keys):
        positions[k].append(j)
    pairs = [(i, positions[k].pop(0)) for i, k in enumerate(want_keys)]

    correct, n, max_err, reason = True, 0, None, ""
    for m in spec.metrics:
        display = _CATALOG.metrics[m].display
        for i, j in pairs:
            n += 1
            want = _number(gold[m].iloc[i])
            try:
                got = _number(result[m].iloc[j])
            except (TypeError, ValueError):
                correct, reason = False, reason or f"{m}: non-numeric value"
                continue
            if want is None or got is None:
                if want is not None or got is not None:
                    correct, reason = False, reason or f"{m}: null mismatch"
                continue
            err = abs(got - want)
            max_err = err if max_err is None else max(max_err, err)
            if not _within(display, got, want):
                correct, reason = False, reason or f"{m}: outside tolerance"
    return Check(correct, n, max_err if n else None, reason)


def score_row(row, item) -> Check:
    """C.1 and C.2 for 1 (system, item) row of the run results."""
    system = row["system"] == "system"
    if item.expected_intent == "answer":
        if system:
            ran = row["intent"] == "answer" and bool(row["spec_valid"]) and bool(row["ran"])
        else:
            ran = bool(row["ran"])
        if not ran:
            return Check(False, 0, None, "did not run")
        return compare_result(row["result"], row["gold"], item.gold_spec, item.output_columns)
    if item.expected_intent == "clarify":
        # O-21 (b): the baseline has no way to ask, so it is never correct here
        return Check(system and row["intent"] == "clarify", 0, None)
    if item.expected_intent == "unsupported":
        return Check(row["intent"] == "unsupported" if system else row["sql"] == "", 0, None)
    raise ValueError(f"{item.id}: unknown expected_intent {item.expected_intent}")


def score(results: pd.DataFrame, items) -> pd.DataFrame:
    """Adds category, correct, n_values_checked and max_abs_err to the run results."""
    by_id = {i.id: i for i in items}
    checks = [score_row(row, by_id[row["item_id"]]) for _, row in results.iterrows()]
    out = results.copy()
    out["category"] = [by_id[i].category for i in results["item_id"]]
    out["correct"] = [c.correct for c in checks]
    out["n_values_checked"] = [c.n_values_checked for c in checks]
    out["max_abs_err"] = [c.max_abs_err for c in checks]
    return out


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """C.4: the Wilson score interval."""
    centre = (k + z * z / 2) / (n + z * z)
    half = z * math.sqrt(k * (n - k) / n + z * z / 4) / (n + z * z)
    return centre - half, centre + half
