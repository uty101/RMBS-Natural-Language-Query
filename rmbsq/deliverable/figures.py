"""Figures for the write-up (instruction 06 F). Step 6.3.

Each figure is drawn from 1 committed CSV, at a fixed size and 150 dpi, with the footnote
"Synthetic data. Source: <csv path>." at the bottom left. The Agg backend, a fixed
`svg.hashsalt` and no `Software` metadata make 2 runs byte-identical.
`arrears_90p_by_vintage.csv` is built through `compile` and `execute` from the governed
spec of O-32 (a).
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter, PercentFormatter  # noqa: E402

from rmbsq.db import connect_readonly  # noqa: E402
from rmbsq.eval.report import write_table  # noqa: E402
from rmbsq.semantic.catalog import load_catalog  # noqa: E402
from rmbsq.semantic.compiler import compile, execute  # noqa: E402
from rmbsq.semantic.spec import QuerySpec  # noqa: E402

DPI = 150
SIZE = (8.0, 4.5)
SAVE = {"dpi": DPI, "metadata": {"Software": None}}
SYSTEM_LABELS = {"system": "governed system", "baseline": "plain text-to-SQL"}

ARREARS_BY_VINTAGE = QuerySpec.model_validate({
    "intent": "answer", "metrics": ["arrears_90p_bal"], "group_by": ["vintage_year"],
    "time": {"grain": "quarter", "start": "2021-10", "end": "2026-09", "shape": "series"},
})

FIGURES = {
    "arrears": ("figures/arrears_90p_by_vintage.png", "arrears_90p_by_vintage.csv"),
    "scale": ("figures/scale_benchmark.png", "scale_benchmark.csv"),
    "eval": ("figures/eval_accuracy.png", "eval_summary.csv"),
}


def build_arrears_by_vintage(db: Path, outputs: Path) -> Path:
    con = connect_readonly(db)
    try:
        df = execute(compile(ARREARS_BY_VINTAGE, load_catalog()), con)
    finally:
        con.close()
    path = Path(outputs) / "arrears_90p_by_vintage.csv"
    write_table(df, path)
    return path


def _seconds(v: float, _pos) -> str:
    """Log axis tick labels in plain seconds, at the 1, 2 and 5 steps only."""
    if v <= 0:
        return ""
    lead = round(v / 10 ** math.floor(math.log10(v)))
    return f"{v:g}" if lead in (1, 2, 5) else ""


def _figure():
    plt.rcParams["svg.hashsalt"] = "rmbsq"
    return plt.subplots(figsize=SIZE)


def _save(fig, outputs: Path, key: str) -> Path:
    png, source = FIGURES[key]
    fig.text(0.01, 0.01, f"Synthetic data. Source: outputs/{source}.", fontsize=8, color="grey",
             ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    path = Path(outputs) / png
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, **SAVE)
    plt.close(fig)
    return path


def arrears_figure(outputs: Path) -> Path:
    df = pd.read_csv(Path(outputs) / "arrears_90p_by_vintage.csv", dtype={"period_label": str})
    quarters = sorted(df["period_label"].unique())
    pos = {q: i for i, q in enumerate(quarters)}
    fig, ax = _figure()
    for year, g in df.groupby("vintage_year", sort=True):
        g = g.sort_values("period_label")
        ax.plot([pos[q] for q in g["period_label"]], g["arrears_90p_bal"], label=str(year), linewidth=1.5)
    ax.set_xticks(range(0, len(quarters), 4), quarters[::4])
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylabel("90+ arrears by balance")
    ax.set_xlabel("quarter")
    ax.legend(title="vintage", fontsize=8, title_fontsize=8, loc="upper left")
    return _save(fig, outputs, "arrears")


def scale_figure(outputs: Path) -> Path:
    b = pd.read_csv(Path(outputs) / "scale_benchmark.csv")
    b = b[(b["route"] == "auto") & (b["threads"] == 0)]
    wide = b.pivot(index="item_id", columns="db", values="median_s")
    tiled = [c for c in wide.columns if c != "1x"][0]
    wide = wide.sort_values([tiled, "1x"]).reset_index()
    fig, ax = _figure()
    x = range(len(wide))
    ax.scatter(x, wide["1x"], s=18, label="1x")
    ax.scatter(x, wide[tiled], s=18, label=tiled)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(_seconds))
    ax.yaxis.set_minor_formatter(FuncFormatter(_seconds))
    ax.set_xticks(list(x), wide["item_id"], rotation=90, fontsize=7)
    ax.set_ylabel("median query time (s)")
    ax.set_title("Query time per eval question, 1x and 36x data")
    ax.legend(fontsize=8, loc="upper left")
    return _save(fig, outputs, "scale")


def eval_figure(outputs: Path) -> Path:
    s = pd.read_csv(Path(outputs) / "eval_summary.csv")
    s = s[s["category"] != "total"]
    categories = list(dict.fromkeys(s["category"]))
    width = 0.38
    fig, ax = _figure()
    for j, (system, label) in enumerate(SYSTEM_LABELS.items()):
        part = s[s["system"] == system].set_index("category").loc[categories]
        x = [i + (j - 0.5) * width for i in range(len(categories))]
        acc = part["accuracy"].to_numpy()
        err = [acc - part["wilson_lo"].to_numpy(), part["wilson_hi"].to_numpy() - acc]
        ax.bar(x, acc, width, yerr=err, capsize=3, label=label)
    ax.set_xticks(range(len(categories)), categories)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylabel("correct")
    ax.legend(fontsize=8, loc="upper right")
    return _save(fig, outputs, "eval")


def make_figures(outputs: Path, eval_recorded: bool) -> list[Path]:
    """The 2 figures, plus eval_accuracy.png in the recorded state; in the pending state
    eval_accuracy.png is deleted if present."""
    written = [arrears_figure(outputs), scale_figure(outputs)]
    eval_png = Path(outputs) / FIGURES["eval"][0]
    if eval_recorded:
        written.append(eval_figure(outputs))
    elif eval_png.exists():
        eval_png.unlink()
    return written
