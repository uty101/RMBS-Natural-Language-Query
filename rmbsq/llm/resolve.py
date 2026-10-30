"""Entity resolution of filter values (kickoff 6.8; instruction 04 E). Step 4.3.

Every filter value of an `answer` spec is resolved, in this order: exact match
(case-insensitive) against the dimension's allowed values; deal aliases; the flag, year
and dpd rules; then `rapidfuzz.fuzz.token_set_ratio` for the text dimensions only. The
first value that becomes clarify or unsupported decides the result. Filters are processed
in the spec's key order, values in list order.
"""

from __future__ import annotations

from rapidfuzz import fuzz

from rmbsq.config import load_config
from rmbsq.db import connect_readonly
from rmbsq.semantic.catalog import ROOT
from rmbsq.semantic.spec import ClarifySpec, QuerySpec

_RESOLVE = load_config(ROOT / "config.toml").resolve  # accept, clarify, top_k

FUZZY = ["deal_name", "originator", "trustee_format", "city", "state", "area", "suburb", "rate_type", "occupancy"]
FLAGS = {"io_flag", "lmi_flag"}
FLAG_WORDS = {"yes": "yes", "no": "no", "true": "yes", "false": "no", "y": "yes", "n": "no"}  # E.3


def deal_aliases(catalog) -> dict[str, str]:
    """Alias -> deal_name. For HARB 2019-1 of Harbour Home Loans: Harbour 19-1, HARB 19-1
    and HARB19-1, with the 2-digit year zero padded (E.2)."""
    con = connect_readonly(catalog.db)
    try:
        rows = con.execute("SELECT deal_name, originator, originator_name, issue_year FROM dim_deal "
                           "ORDER BY deal_name").fetchall()
    finally:
        con.close()
    out = {}
    for name, code, originator_name, issue_year in rows:
        series = name.rsplit("-", 1)[1]
        yy = f"{issue_year % 100:02d}-{series}"
        for alias in (f"{originator_name.split()[0]} {yy}", f"{code} {yy}", f"{code}{yy}"):
            out[alias] = name
    return out


class _Stop(Exception):
    """Carries the clarify or unsupported spec that decides the result."""

    def __init__(self, spec: QuerySpec):
        self.spec = spec


def _unknown(dim: str, value) -> _Stop:
    return _Stop(QuerySpec(intent="unsupported", unsupported_reason=f"unknown {dim} value '{value}'"))


def _fuzzy(dim: str, value: str, candidates: dict[str, str]):
    """candidates: candidate string -> canonical value. Returns the canonical value or raises _Stop."""
    best: dict[str, float] = {}
    for cand, canon in candidates.items():
        score = fuzz.token_set_ratio(value.lower(), cand.lower())
        best[canon] = max(best.get(canon, 0.0), score)
    ranked = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))
    top = ranked[0][1]
    if top < _RESOLVE.clarify:
        raise _unknown(dim, value)
    tie = len(ranked) > 1 and ranked[1][1] == top
    if top >= _RESOLVE.accept and not tie:
        return ranked[0][0]
    options = [canon for canon, _ in ranked[:_RESOLVE.top_k]]
    raise _Stop(QuerySpec(intent="clarify",
                          clarify=ClarifySpec(question=f"Which {dim} did you mean by '{value}'?", options=options)))


def _resolve_value(dim: str, value, catalog, aliases: dict[str, str]) -> tuple[str, object]:
    """Returns (dimension, resolved value); the dimension changes only for a deal_id that is
    a deal_name or an alias."""
    allowed = catalog.allowed_values(dim)
    text = str(value).strip()
    for a in allowed:                                     # 1. exact, case-insensitive
        if str(a).lower() == text.lower():
            return dim, a
    lower_aliases = {k.lower(): v for k, v in aliases.items()}
    if dim in ("deal_name", "deal_id"):                   # 2. deal aliases
        if text.lower() in lower_aliases:
            return "deal_name", lower_aliases[text.lower()]
        if dim == "deal_id":
            for name in catalog.allowed_values("deal_name"):
                if name.lower() == text.lower():
                    return "deal_name", name
    if dim in FLAGS and text.lower() in FLAG_WORDS:       # 3. flags, years, dpd_bucket
        return dim, FLAG_WORDS[text.lower()]
    if dim not in FUZZY:
        raise _unknown(dim, value)
    candidates = {str(a): str(a) for a in allowed}        # 4. fuzzy, text dimensions only
    if dim == "deal_name":
        candidates.update(aliases)
    return dim, _fuzzy(dim, text, candidates)


def resolve_entities(spec: QuerySpec, catalog, aliases: dict[str, str]) -> QuerySpec:
    if spec.intent != "answer":
        return spec
    filters: dict[str, list] = {}
    try:
        for dim, values in spec.filters.items():
            for value in values:
                target, resolved = _resolve_value(dim, value, catalog, aliases)
                kept = filters.setdefault(target, [])
                if resolved not in kept:
                    kept.append(resolved)
    except _Stop as stop:
        return stop.spec
    return QuerySpec.model_validate({**spec.model_dump(), "filters": filters})
