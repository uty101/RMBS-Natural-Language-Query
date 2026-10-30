"""QuerySpec model (kickoff 6.6; instruction 03 E 3.2). Step 3.2.

Metric and dimension names are `Literal` types built from the catalogue YAML, so an
unknown name fails validation. Window bounds and the default month come from
`config.toml` (`[calendar]`).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from rmbsq.config import load_config
from rmbsq.semantic.catalog import ROOT, load_catalog

_CATALOG = load_catalog()
_CALENDAR = load_config(ROOT / "config.toml").calendar

MetricName = Literal[tuple(_CATALOG.metrics)]
DimensionName = Literal[tuple(_CATALOG.dimensions)]
Month = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


def _unique(values: list, what: str) -> list:
    if len(set(values)) != len(values):
        raise ValueError(f"{what} has duplicates: {values}")
    return values


class TimeSpec(BaseModel):
    grain: Literal["month", "quarter", "year"]
    start: str = Month
    end: str = Month
    shape: Literal["series", "point"]

    @model_validator(mode="after")
    def _window(self):
        # YYYY-MM strings compare in calendar order
        if not _CALENDAR.window_start <= self.start <= self.end <= _CALENDAR.window_end:
            raise ValueError(f"time must satisfy {_CALENDAR.window_start} <= start <= end <= {_CALENDAR.window_end}, "
                             f"got start {self.start}, end {self.end}")
        return self


class OrderSpec(BaseModel):
    metric: MetricName
    direction: Literal["desc", "asc"]
    limit: int = Field(ge=1, le=20)


class ClarifySpec(BaseModel):
    question: str
    options: list[str] = Field(min_length=2, max_length=4)


class QuerySpec(BaseModel):
    intent: Literal["answer", "clarify", "unsupported"]
    metrics: list[MetricName] = Field(default_factory=list, max_length=3)
    group_by: list[DimensionName] = Field(default_factory=list, max_length=2)
    filters: dict[DimensionName, list[str | int]] = Field(default_factory=dict)
    time: TimeSpec | None = None
    order: OrderSpec | None = None
    clarify: ClarifySpec | None = None
    unsupported_reason: str | None = None

    @field_validator("metrics")
    @classmethod
    def _metrics_unique(cls, v):
        return _unique(v, "metrics")

    @field_validator("group_by")
    @classmethod
    def _group_by_unique(cls, v):
        return _unique(v, "group_by")

    @field_validator("filters")
    @classmethod
    def _filter_sizes(cls, v):
        for name, values in v.items():
            if not 1 <= len(values) <= 20:
                raise ValueError(f"filter {name} needs 1 to 20 values, got {len(values)}")
        return v

    @model_validator(mode="after")
    def _intent_rules(self):
        if self.intent == "answer":
            if not self.metrics:
                raise ValueError("answer needs 1 to 3 metrics")
            if self.clarify is not None or self.unsupported_reason is not None:
                raise ValueError("answer forbids clarify and unsupported_reason")
            if self.order is not None and self.order.metric not in self.metrics:
                raise ValueError(f"order metric {self.order.metric} is not among the metrics {self.metrics}")
            if self.time is None:
                # kickoff 6.6: the default when the question gives no time
                self.time = TimeSpec(grain="month", start=_CALENDAR.latest, end=_CALENDAR.latest, shape="point")
            return self
        extra = {
            "metrics": bool(self.metrics), "group_by": bool(self.group_by), "filters": bool(self.filters),
            "time": self.time is not None, "order": self.order is not None,
        }
        if self.intent == "clarify":
            extra["unsupported_reason"] = self.unsupported_reason is not None
            if self.clarify is None:
                raise ValueError("clarify needs clarify")
        else:
            extra["clarify"] = self.clarify is not None
            if self.unsupported_reason is None:
                raise ValueError("unsupported needs unsupported_reason")
        bad = [k for k, present in extra.items() if present]
        if bad:
            raise ValueError(f"{self.intent} must not carry {', '.join(bad)}")
        return self
