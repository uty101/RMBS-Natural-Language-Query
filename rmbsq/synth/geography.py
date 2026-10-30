"""Cities, areas and suburbs (kickoff 4.3). Built in step 1.2."""

from __future__ import annotations

import pandas as pd

from rmbsq.config import Config, load_geography

SUBURB_SUFFIXES = ("North", "Central", "South")  # kickoff 4.3, instruction 01 D.1


def build_geography(cfg: Config) -> pd.DataFrame:
    """60 suburbs in instruction 01 D.1 order: city order of 4.3, areas as listed, then
    North, Central, South. Columns city, state, area, beta, suburb."""
    areas = load_geography(cfg.table_path("geography"))
    rows = [
        {"city": a.city, "state": a.state, "area": a.area, "beta": a.beta, "suburb": f"{a.area} {s}"}
        for a in areas.itertuples(index=False)
        for s in SUBURB_SUFFIXES
    ]
    return pd.DataFrame(rows, columns=["city", "state", "area", "beta", "suburb"])


def city_weights(cfg: Config) -> pd.Series:
    """City weight by city, in the city order of 4.3."""
    areas = load_geography(cfg.table_path("geography"))
    return areas.drop_duplicates("city").set_index("city")["weight"]
