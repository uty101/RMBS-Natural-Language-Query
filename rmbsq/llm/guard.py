"""Number guard (kickoff 6.9; instruction 04 F.2). Step 4.4.

Strips period labels, deal names and fixed dimension labels from the narration, extracts
every number with its unit, ignores numbers from the question and bare years 2016 to
2026, and returns those that are not a number of some display cell, in text order.
"""

from __future__ import annotations

import re

NUMBER = re.compile(r"-?\d[\d,]*\.?\d*(%|m\b)?")             # F.2 step 2
PERIODS = [re.compile(r"\d{4}-\d{2}"), re.compile(r"\d{4}-Q[1-4]")]
YEAR_MIN, YEAR_MAX = 2016, 2026                               # F.2 step 3


def extract(text: str) -> list[tuple[str, str]]:
    """(number, unit) per match: commas removed, a trailing '.' dropped."""
    out = []
    for m in NUMBER.finditer(text):
        unit = m.group(1) or ""
        number = m.group(0)[: len(m.group(0)) - len(unit)].replace(",", "")
        out.append((number.removesuffix("."), unit))
    return out


def _labels(catalog) -> list[str]:
    labels = {label for d in catalog.dimensions.values() for label in d.labels}
    return sorted(labels, key=lambda s: (-len(s), s))


def strip(text: str, catalog) -> str:
    """F.2 step 1: periods, then deal names, then fixed labels longest first, each replaced
    by a space; a label only where no letter, digit or '.' touches it."""
    for pattern in PERIODS:
        text = pattern.sub(" ", text)
    for name in sorted(catalog.allowed_values("deal_name"), key=lambda s: (-len(s), s)):
        text = text.replace(name, " ")
    for label in _labels(catalog):
        text = re.sub(rf"(?<![A-Za-z0-9.]){re.escape(label)}(?![A-Za-z0-9.])", " ", text)
    return text


def number_guard(text: str, question: str, display_table, catalog) -> list[str]:
    asked = {number for number, _ in extract(question)}
    allowed = {number + unit for column in display_table.columns
               for cell in display_table[column] for number, unit in extract(str(cell))}
    offending = []
    for number, unit in extract(strip(text, catalog)):
        if number in asked:
            continue
        if not unit and re.fullmatch(r"\d{4}", number) and YEAR_MIN <= int(number) <= YEAR_MAX:
            continue
        token = number + unit
        if token not in allowed and token not in offending:
            offending.append(token)
    return offending
