"""Number check on a rendered document (instruction 06 B). Step 6.0, also used by Section 7.

1. Remove every block's rendered text, fenced code blocks and indented code lines.
2. Strip `YYYY-MM` and `YYYY-Qn` tokens, and every deal_name.
3. Extract tokens with the Section 4 guard regex and normalisation.
4. Ignore bare years from 2016 to 2026.

Every remaining token must be in the allowed set: the tokens of every claim display string
in `claims` (the caller passes the claims the document uses) and of each line of `fixed`.
Deal names are the full profile's, from `build_deals`, which makes no random draws.
"""

from __future__ import annotations

import re

from rmbsq.config import load_config
from rmbsq.llm.guard import PERIODS, YEAR_MAX, YEAR_MIN, extract
from rmbsq.semantic.catalog import ROOT
from rmbsq.synth.deals import build_deals

FENCED = re.compile(r"^```.*?^```[^\n]*$", re.DOTALL | re.MULTILINE)
INDENTED = re.compile(r"^(?: {4}|\t).*$", re.MULTILINE)


def deal_names() -> list[str]:
    cfg = load_config(ROOT / "config.toml")
    return build_deals(cfg, cfg.profiles["full"].n_deals)["deal_name"].tolist()


def _tokens(text: str) -> list[str]:
    return [number + unit for number, unit in extract(text)]


def strip_document(rendered: str, blocks: dict) -> str:
    text = rendered
    for block in blocks.values():
        text = text.replace(block, " ")
    text = FENCED.sub(" ", text)
    text = INDENTED.sub(" ", text)
    for pattern in PERIODS:
        text = pattern.sub(" ", text)
    for name in sorted(deal_names(), key=lambda s: (-len(s), s)):
        text = text.replace(name, " ")
    return text


def unexplained_numbers(rendered: str, claims: dict, blocks: dict, fixed) -> list[str]:
    allowed = {t for display in claims.values() for t in _tokens(str(display))}
    allowed |= {t for line in fixed for t in _tokens(line)}
    offending = []
    for number, unit in extract(strip_document(rendered, blocks)):
        if not unit and re.fullmatch(r"\d{4}", number) and YEAR_MIN <= int(number) <= YEAR_MAX:
            continue
        token = number + unit
        if token not in allowed and token not in offending:
            offending.append(token)
    return offending
