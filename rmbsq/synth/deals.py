"""Deal table (kickoff 4.2, instruction 01 D.2). No random draws."""

from __future__ import annotations

import pandas as pd

from rmbsq.config import Config, load_originators
from rmbsq.synth.months import month_index, to_period

DEAL_COLUMNS = ["deal_id", "deal_name", "originator", "originator_name", "trustee_format", "issue_month"]


def build_deals(cfg: Config, n_deals: int) -> pd.DataFrame:
    """issue_month(k) = first_issue + floor((k - 1) * issue_span_months / n_deals);
    originator = codes[(k - 1) mod 5]; deal_name = "{code} {issue_year}-{n}", with n
    counting that originator's deals in that issue year in deal_id order, from 1."""
    orig = load_originators(cfg.table_path("originators"))
    first = month_index(cfg.deals.first_issue)
    rows, seen = [], {}
    for k in range(1, n_deals + 1):
        o = orig.iloc[(k - 1) % len(orig)]
        issue = first + (k - 1) * cfg.deals.issue_span_months // n_deals
        year = 1970 + issue // 12
        seen[(o["code"], year)] = seen.get((o["code"], year), 0) + 1
        rows.append(
            {
                "deal_id": f"D{k:03d}",
                "deal_name": f"{o['code']} {year}-{seen[(o['code'], year)]}",
                "originator": o["code"],
                "originator_name": o["name"],
                "trustee_format": o["trustee_format"],
                "issue_month": issue,
            }
        )
    df = pd.DataFrame(rows, columns=DEAL_COLUMNS)
    df["issue_month"] = to_period(df["issue_month"].to_numpy())
    return df
