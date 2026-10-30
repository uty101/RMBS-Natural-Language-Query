"""Metric and dimension catalogue (kickoff 6.3 and 6.5; instruction 03 part C). Step 3.1.

`load_catalog` reads `semantic/metrics.yaml` and `semantic/dimensions.yaml`. Allowed
values come from a dimension's fixed labels, or from the canonical database when it has
none, so a catalogue that answers `allowed_values` for those dimensions is loaded with
`db`, the DuckDB file to read.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[2]
METRICS_YAML = ROOT / "semantic" / "metrics.yaml"
DIMS_YAML = ROOT / "semantic" / "dimensions.yaml"


@dataclass(frozen=True)
class Metric:
    name: str
    kind: str          # stock | flow
    numerator: str     # a monthly part of instruction 03 B.2, empty for flow metrics
    denominator: str   # a monthly part, or empty
    display: str       # count | aud_m | pct
    definition: str


@dataclass(frozen=True)
class Dimension:
    name: str
    column: str
    table: str
    level: str               # deal | loan
    labels: tuple[str, ...]  # fixed output values, empty when they come from the database
    definition: str


@dataclass(frozen=True)
class Catalog:
    metrics: dict[str, Metric]
    dimensions: dict[str, Dimension]
    db: Path | None = None

    @property
    def deal_level(self) -> list[str]:
        """Dimensions routable to agg_deal_month (kickoff 6.5)."""
        return [d.name for d in self.dimensions.values() if d.level == "deal"]

    def allowed_values(self, name: str) -> list:
        """Instruction 03 C.2: the labels where fixed, otherwise the sorted distinct values
        from the database."""
        dim = self.dimensions[name]
        if dim.labels:
            return list(dim.labels)
        if self.db is None:
            raise ValueError(f"allowed values of {name} come from the database; load the catalogue with db")
        con = duckdb.connect(str(self.db), read_only=True)
        try:
            rows = con.execute(
                f"SELECT DISTINCT {dim.column} FROM {dim.table} WHERE {dim.column} IS NOT NULL ORDER BY 1"
            ).fetchall()
        finally:
            con.close()
        return [r[0] for r in rows]


def _read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_catalog(metrics_yaml: Path = METRICS_YAML, dims_yaml: Path = DIMS_YAML, db: Path | None = None) -> Catalog:
    metrics = {m["name"]: Metric(**m) for m in _read(metrics_yaml)}
    dims = {d["name"]: Dimension(**{**d, "labels": tuple(d["labels"])}) for d in _read(dims_yaml)}
    return Catalog(metrics=metrics, dimensions=dims, db=None if db is None else Path(db))
