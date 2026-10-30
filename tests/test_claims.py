"""Step 6.2: claims traced to the committed CSVs (instruction 06 D, J 6.2)."""

import math
from pathlib import Path

import pandas as pd

from rmbsq.deliverable.claims import build_claims
from rmbsq.deliverable.render import names_used

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TEMPLATES = [ROOT / "templates" / "README.md.tmpl", ROOT / "templates" / "DESIGN_RESPONSE.md.tmpl"]
BLOCKS = {"eval_table"}


def _expected() -> dict:
    """Each pending claim's value, recomputed from its source CSV by its D rule."""
    s = pd.read_csv(OUT / "data_summary.csv", dtype=str).set_index("stat")["value"]
    c = pd.read_csv(OUT / "compiler_check.csv")
    b = pd.read_csv(OUT / "scale_benchmark.csv")
    t = pd.read_csv(OUT / "trap_effects.csv").set_index("item_id")
    x36 = b[b["db"] == "36x"]
    exp = {k: int(s[k]) for k in ["n_deals", "n_loans", "n_loan_months", "n_raw_rows", "n_resubmission_duplicates",
                                  "n_called_deals", "n_called_deals_b", "canonical_truth_mismatches"]}
    exp.update({f"arrears_90p_{w}_pct": float(s[f"arrears_90p_{w}"]) for w in ["first", "peak", "latest"]})
    exp["arrears_90p_peak_month"] = s["arrears_90p_peak_month"]
    exp.update(gold_total=len(c), gold_matched=int((c["max_scaled_diff"] <= 1e-9).sum()),
               gold_worst_diff=float(c["max_scaled_diff"].max()), oracle_ok=int(c["oracle_ok"].sum()))
    exp.update(rows_36x=int(x36["db_rows"].unique().item()),
               x36_max_default_s=float(x36[x36["threads"] == 0]["median_s"].max()),
               x36_max_single_s=float(x36[x36["threads"] == 1]["median_s"].max()))
    exp.update(trap_call_deal="CST 2019-1", trap_call_gold_pct=t.loc["Q29", "gold"],
               trap_call_naive_pct=t.loc["Q29", "naive"],
               trap_exit_extra_loans=int(t.loc["Q32", "naive"] - t.loc["Q32", "gold"]),
               trap_exit_month="November 2025", trap_weight_gold_pct=t.loc["Q33", "gold"],
               trap_weight_naive_pct=t.loc["Q33", "naive"], trap_compound_cpr_pct=t.loc["Q2_2025", "gold"],
               trap_compound_gap=abs(t.loc["Q2_2025", "gold"] - t.loc["Q2_2025", "naive"]))
    return exp


def test_claims_pending(tmp_path):
    claims = build_claims(False, out=tmp_path / "claims.csv")
    ids = list(claims["claim_id"])

    for template in TEMPLATES:
        used = set(names_used(template.read_text(encoding="utf-8"), eval_recorded=False)) - BLOCKS
        assert used <= set(ids), (template.name, sorted(used - set(ids)))

    expected = _expected()
    assert ids == list(expected)
    for _, row in claims.iterrows():
        want = expected[row["claim_id"]]
        source = row["source_file"]
        assert (ROOT / source).is_file(), source
        if isinstance(want, str):
            assert row["value"] == want, row["claim_id"]
        else:
            assert math.isclose(float(row["value"]), float(want), rel_tol=1e-12, abs_tol=0), row["claim_id"]

    display = dict(zip(claims["claim_id"], claims["display"]))
    assert display["n_loans"] == f"{expected['n_loans']:,}"
    assert display["arrears_90p_peak_pct"] == f"{expected['arrears_90p_peak_pct'] * 100:.2f}%"
    assert display["trap_call_gold_pct"] == f"{expected['trap_call_gold_pct'] * 100:.1f}%"
    assert display["gold_worst_diff"] == f"{expected['gold_worst_diff']:.1e}"
    # rounded up: the stated bound holds
    assert float(display["x36_max_default_s"]) >= expected["x36_max_default_s"]
    assert float(display["x36_max_default_s"]) - expected["x36_max_default_s"] < 0.01
    assert display["x36_max_single_s"] == f"{expected['x36_max_single_s']:.2f}"
