"""Step 3.1: the metric and dimension catalogue (instruction 03 C.1, C.2)."""

from rmbsq.db import connect_readonly
from rmbsq.semantic.catalog import load_catalog

# instruction 03 C.1: name, kind, display, definition
C1 = [
    ("loan_count", "stock", "count", "Number of loans with a positive balance at month end."),
    ("balance_total", "stock", "aud_m", "Total outstanding balance in AUD at month end."),
    ("arrears_30p_bal", "stock", "pct", "Share of outstanding balance that is 30 or more days past due, excluding loans in hardship, weighted by balance."),
    ("arrears_90p_bal", "stock", "pct", "Share of outstanding balance that is 90 or more days past due, excluding loans in hardship, weighted by balance."),
    ("arrears_90p_cnt", "stock", "pct", "Share of loans by count that are 90 or more days past due, excluding loans in hardship."),
    ("hardship_share_bal", "stock", "pct", "Share of outstanding balance on a hardship arrangement."),
    ("wa_orig_ltv", "stock", "pct", "Balance-weighted average loan-to-value ratio at origination."),
    ("wa_indexed_ltv", "stock", "pct", "Balance-weighted average current loan-to-value ratio, with property values indexed to suburb house prices."),
    ("wa_rate", "stock", "pct", "Balance-weighted average interest rate."),
    ("smm_vol", "flow", "pct", "Monthly voluntary prepayment rate: full prepayments plus partial curtailments over scheduled balance. Excludes repurchases, defaults and clean-up calls."),
    ("cpr", "flow", "pct", "Conditional prepayment rate: smm_vol annualised. Excludes repurchases, defaults and clean-up calls."),
    ("cdr", "flow", "pct", "Conditional default rate: defaulted balance over opening balance each month, annualised."),
]

# instruction 03 C.2: name, column, table, level, labels, definition
C2 = [
    ("deal_id", "deal_id", "fact_loan_month", "deal", (), "Deal identifier, for example D004."),
    ("deal_name", "deal_name", "dim_deal", "deal", (), "Deal name: originator code, issue year and series number, for example HARB 2019-1."),
    ("originator", "originator", "dim_deal", "deal", (), "Originator code: HARB, KOO, WAT, CST or RED."),
    ("trustee_format", "trustee_format", "dim_deal", "deal", ("A", "B"), "Which trustee report format the deal is delivered in."),
    ("issue_year", "issue_year", "dim_deal", "deal", (), "Year the deal was issued."),
    ("vintage_year", "vintage_year", "dim_loan", "loan", (), "Year the loan was originated."),
    ("city", "city", "dim_loan", "loan", (), "Capital city region of the property."),
    ("state", "state", "dim_loan", "loan", ("NSW", "QLD", "SA", "VIC", "WA"), "State of the property."),
    ("area", "area", "dim_loan", "loan", (), "Local area of the property, for example Blacktown."),
    ("suburb", "suburb", "dim_loan", "loan", (), "Suburb of the property, for example Blacktown North."),
    ("rate_type", "rate_type", "fact_loan_month", "loan", ("fixed", "variable"), "Current rate type that month; a fixed loan becomes variable at its fixed rate expiry."),
    ("io_flag", "io_flag", "fact_loan_month", "loan", ("yes", "no"), "Whether the loan is interest only that month."),
    ("occupancy", "occupancy", "dim_loan", "loan", ("owner", "investor"), "Owner occupied or investment property."),
    ("lmi_flag", "lmi_flag", "dim_loan", "loan", ("yes", "no"), "Whether the loan has lenders mortgage insurance (LTV above 80% at origination)."),
    ("ltv_bucket_orig", "ltv_bucket_orig", "dim_loan", "loan", ("<=60", "60-70", "70-80", "80-90", ">90"), "Origination LTV band, in percent."),
    ("ltv_bucket_indexed", "ltv_bucket_indexed", "fact_loan_month", "loan", ("<=60", "60-70", "70-80", "80-90", ">90"), "Current indexed LTV band, in percent."),
    ("seasoning_bucket", "seasoning_bucket", "fact_loan_month", "loan", ("0-12", "13-24", "25-36", "37-60", ">60"), "Months since origination."),
    ("dpd_bucket", "dpd_bucket", "fact_loan_month", "loan", ("current", "1-29", "30-59", "60-89", "90+"), "Days past due band. Loans in hardship are current."),
]


def test_twelve_metrics():
    cat = load_catalog()
    assert [(m.name, m.kind, m.display, m.definition) for m in cat.metrics.values()] == C1


def test_eighteen_dimensions():
    cat = load_catalog()
    assert cat.deal_level == ["deal_id", "deal_name", "originator", "trustee_format", "issue_year"]
    got = [(d.name, d.column, d.table, d.level, d.labels, d.definition) for d in cat.dimensions.values()]
    assert got == C2


def test_allowed_values_from_db(small_db):
    cat = load_catalog(db=small_db)
    assert cat.allowed_values("state") == ["NSW", "QLD", "SA", "VIC", "WA"]
    con = connect_readonly(small_db)
    try:
        present = [r[0] for r in con.execute("SELECT DISTINCT originator FROM dim_deal ORDER BY 1").fetchall()]
    finally:
        con.close()
    assert cat.allowed_values("originator") == present
    assert set(present) <= {"HARB", "KOO", "WAT", "CST", "RED"}
    assert cat.allowed_values("issue_year") == sorted(cat.allowed_values("issue_year"))
