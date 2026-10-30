"""Display formatting of a result table (kickoff 5.2, 5.3; instruction 03 E 3.6). Step 3.6.

Every cell becomes a string: pct as `0.00%`, aud_m as `A$412.3m` (dollars / 1e6, 1 dp),
count as `12,345`, year dimensions as plain integers, NULL metrics as `n/a`. Other
dimensions and period_label are unchanged. Rounding is Python's format rounding of the
binary value; 0.000125 shows as `0.01%`.
"""

from __future__ import annotations

import pandas as pd

YEARS = {"issue_year", "vintage_year"}
NULL = "n/a"

DISPLAY = {
    "pct": lambda v: format(v, ".2%"),
    "aud_m": lambda v: f"A${v / 1e6:.1f}m",
    "count": lambda v: f"{int(v):,}",
}


def format_table(df: pd.DataFrame, catalog) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for c in df.columns:
        if c in catalog.metrics:
            show = DISPLAY[catalog.metrics[c].display]
            out[c] = [NULL if pd.isna(v) else show(float(v)) for v in df[c]]
        elif c in YEARS:
            out[c] = [str(int(v)) for v in df[c]]
        else:
            out[c] = [str(v) for v in df[c]]
    return out
