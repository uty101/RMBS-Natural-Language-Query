"""Monthly loan simulation (kickoff 4.7). Built in step 1.4.

Follows the ordered month loop of instruction 01 part E. Step numbers in the comments
(E.1, E.4, ...) refer to that part. Months are ints (rmbsq.synth.months).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from rmbsq.config import Config
from rmbsq.synth.deals import build_deals
from rmbsq.synth.months import from_period, month_index, to_period

PANEL_COLUMNS = [
    "loan_id", "deal_id", "period", "opening_balance", "scheduled_principal", "curtailment",
    "closing_balance", "interest_rate", "dpd_bucket", "hardship_flag", "months_in_90",
    "exit_reason", "exit_balance", "loss", "indexed_value", "indexed_ltv",
]

# exit reason codes, in reverse precedence order (E.7: called > defaulted > repurchased > prepaid)
NONE, PREPAID, REPURCHASED, DEFAULTED, CALLED = 0, 1, 2, 3, 4
REASONS = np.array([None, "prepaid", "repurchased", "defaulted", "called"], dtype=object)

# E.6: p_roll_eff = min(p_roll[k] * exp(roll_shock * shock), 0.95 - p_cure[k])
ROLL_CAP = 0.95


def _payment(balance, rate, age, io_now, term):
    """E 'Payment function': interest only while io_now, else the annuity on the
    remaining term n = term - age + 1."""
    i = rate / 12
    n = term - age + 1
    annuity = balance * i / (1 - (1 + i) ** (-n))
    return np.where(io_now, balance * rate / 12, annuity)


def _logistic(x):
    return 1.0 / (1.0 + np.exp(-x))


def simulate(cfg: Config, loans: pd.DataFrame, cash: pd.DataFrame, hpi: pd.DataFrame, rng: np.random.Generator):
    """True loan-month panel (PANEL_COLUMNS) and the deals frame with issue_balance.

    `loans` must be in loan_id order; every monthly array follows that order."""
    if not loans["loan_id"].is_monotonic_increasing:
        raise ValueError("loans must be sorted by loan_id")
    Bh, term = cfg.behaviour, cfg.loans.term

    # deals, indexed 0..D-1 in deal_id order
    deals = build_deals(cfg, cfg.deals.n_deals)
    deals = deals[deals["deal_id"].isin(set(loans["deal_id"]))].reset_index(drop=True)
    deal_pos = {d: i for i, d in enumerate(deals["deal_id"])}
    deal = loans["deal_id"].map(deal_pos).to_numpy()
    deal_issue = from_period(deals["issue_month"])
    issue = deal_issue[deal]
    if not (from_period(loans["issue_month"]) == issue).all():
        raise ValueError("loans.issue_month disagrees with build_deals")
    n_deals = len(deals)

    # static arrays
    orig = from_period(loans["orig_month"])
    io_flag = loans["io_flag"].to_numpy(dtype=bool)
    io_end = from_period(loans["io_end_month"])
    fixed = (loans["rate_type"] == "fixed").to_numpy()
    fixed_end = from_period(loans["fixed_end_month"])
    fixed_rate = np.nan_to_num(loans["fixed_rate"].to_numpy(dtype=float))
    margin = loans["margin"].to_numpy(dtype=float)
    investor = (loans["occupancy"] == "investor").to_numpy()
    orig_balance = loans["orig_balance"].to_numpy(dtype=float)
    orig_valuation = loans["orig_valuation"].to_numpy(dtype=float)

    # market data on a common month axis starting at sim_start
    m0 = month_index(cfg.calendar.sim_start)
    t_end = month_index(cfg.calendar.window_end)
    w_start = month_index(cfg.calendar.window_start)
    cash_m = from_period(cash["period"])
    cash_rate = np.full(t_end - m0 + 1, np.nan)
    cash_rate[cash_m - m0] = cash["rate"].to_numpy()
    suburbs = list(dict.fromkeys(hpi["suburb"]))
    sub_pos = {s: i for i, s in enumerate(suburbs)}
    H = np.full((len(suburbs), t_end - m0 + 1), np.nan)
    H[hpi["suburb"].map(sub_pos).to_numpy(), from_period(hpi["period"]) - m0] = hpi["hpi"].to_numpy()
    sub = loans["suburb"].map(sub_pos).to_numpy()
    hpi_orig = H[sub, orig - m0]

    def rate_at(t, sel):
        """E 'Rate': fixed_rate while fixed and t < fixed_end_month, else cash(t) + margin."""
        on_fixed = fixed[sel] & (t < fixed_end[sel])
        return np.where(on_fixed, fixed_rate[sel], cash_rate[t - m0] + margin[sel])

    # E.1 origination payment, at age 1, stored as the history entry for orig_month
    n = len(loans)
    all_sel = np.arange(n)
    pay_hist = np.full((n, t_end - m0 + 1), np.nan)
    rate_orig = np.where(fixed & (orig < fixed_end), fixed_rate, cash_rate[orig - m0] + margin)
    payment_orig = _payment(orig_balance, rate_orig, 1, io_flag & (orig < io_end), term)
    pay_hist[all_sel, orig - m0] = payment_orig

    # state per loan and per deal
    closing = orig_balance.copy()
    bucket = np.zeros(n, dtype=np.int64)
    months_in_90 = np.zeros(n, dtype=np.int64)
    hardship_remaining = np.zeros(n, dtype=np.int64)
    default_flag = np.zeros(n, dtype=bool)
    exited = np.zeros(n, dtype=bool)
    call_flag = np.zeros(n_deals, dtype=bool)
    issue_balance = np.full(n_deals, np.nan)

    out = []
    for t in range(m0 + 1, t_end + 1):
        # E.3.1 live set, in loan_id order
        idx = np.nonzero((orig < t) & ~exited)[0]
        k = len(idx)

        # E.3.2 issue reset
        reset = idx[issue[idx] == t]
        bucket[reset] = 0
        months_in_90[reset] = 0
        hardship_remaining[reset] = 0
        default_flag[reset] = False

        # E.3.3 draws, over every live loan
        u_h = rng.random(k)
        u_t = rng.random(k)
        u_p = rng.random(k)
        u_r = rng.random(k)

        # E.3.4 month quantities
        opening = closing[idx]
        age = t - orig[idx]
        rate = rate_at(t, idx)
        io_now = io_flag[idx] & (t < io_end[idx])
        payment = _payment(opening, rate, age, io_now, term)
        pay_hist[idx, t - m0] = payment
        m = t - Bh.shock_lookback_months
        use_orig = m <= orig[idx]
        reference = np.where(use_orig, payment_orig[idx], pay_hist[idx, np.maximum(m - m0, 0)])
        shock = np.maximum(payment / reference - 1, 0)
        indexed_value = orig_valuation[idx] * H[sub[idx], t - m0] / hpi_orig[idx]
        ltv_open = opening / indexed_value
        scheduled = np.where(io_now, 0.0, np.minimum(payment - opening * rate / 12, opening))

        # E.3.5 hardship entry
        b = bucket[idx]
        hr = hardship_remaining[idx].copy()
        enter = (b == 0) & (hr == 0) & (u_h < Bh.p_hardship)
        if enter.any():
            span = Bh.hardship_max - Bh.hardship_min + 1
            hr[enter] = Bh.hardship_min + np.floor(span * u_h[enter] / Bh.p_hardship).astype(np.int64)
        in_h = hr > 0

        # E.3.6 transitions on the start-of-month bucket, for loans not in hardship
        new_b = b.copy()
        free = ~in_h
        io_recent = io_flag[idx] & (t - io_end[idx] >= 0) & (t - io_end[idx] < Bh.io_recent_months)
        p01 = _logistic(
            Bh.a0
            + Bh.a_shock * shock
            + Bh.a_ltv * np.maximum(ltv_open - Bh.ltv_knot, 0)
            + Bh.a_investor * investor[idx]
            + Bh.a_io_recent * io_recent
        )
        new_b[free & (b == 0) & (u_t < p01)] = 1
        for kb in (1, 2, 3):
            pc, pr = Bh.p_cure[kb - 1], Bh.p_roll[kb - 1]
            p_roll_eff = np.minimum(pr * np.exp(Bh.roll_shock * shock), ROLL_CAP - pc)
            at = free & (b == kb)
            new_b[at & (u_t < pc)] = 0
            new_b[at & (u_t >= pc) & (u_t < pc + p_roll_eff)] = kb + 1
        new_b[free & (b == 4) & (u_t < Bh.p_cure_90)] = 0
        m90 = np.where(new_b == 4, months_in_90[idx] + 1, 0)

        # E.3.7 exits, suppressed before the deal's issue month
        cash_t = cash_rate[t - m0]
        base = Bh.smm_start + (Bh.smm_flat - Bh.smm_start) * np.minimum(age, Bh.smm_ramp_months) / Bh.smm_ramp_months
        cliff = fixed[idx] & (t - fixed_end[idx] >= 0) & (t - fixed_end[idx] < Bh.fixed_cliff_months)
        incentive = np.where(cliff, Bh.fixed_cliff_mult, 1 + Bh.refi_slope * np.maximum(0, rate - (cash_t + Bh.refi_spread)))
        damp = np.where(ltv_open > Bh.damp_ltv, Bh.damp_mult, 1.0)
        smm = np.minimum(base * incentive * damp, Bh.smm_cap)

        reason = np.full(k, NONE, dtype=np.int64)
        reason = np.where(~in_h & (new_b == 0) & (u_p < smm), PREPAID, reason)
        reason = np.where(u_r < Bh.p_repurchase, REPURCHASED, reason)
        reason = np.where(default_flag[idx], DEFAULTED, reason)
        reason = np.where(call_flag[deal[idx]], CALLED, reason)
        reason[t < issue[idx]] = NONE
        exiting = reason != NONE

        # E.3.8 cash flows, rounded to the cent (numpy round half even)
        payer = ~exiting & ~in_h & (new_b == 0)
        sched_p = np.where(payer, np.round(scheduled, 2), 0.0)
        curt = np.where(payer, np.round(Bh.curtailment * (opening - sched_p), 2), 0.0)
        new_close = np.where(exiting, 0.0, np.round(opening - sched_p - curt, 2))
        exit_balance = np.where(exiting, opening, 0.0)
        loss = np.where(reason == DEFAULTED, np.round(np.maximum(0, opening - Bh.sale_haircut * indexed_value), 2), 0.0)

        # E.3.9 end-of-month flags, and the state carried to t + 1
        default_flag[idx] = ~exiting & (m90 >= Bh.default_after_90_months)
        hardship_remaining[idx] = np.where(in_h, hr - 1, hr)
        bucket[idx] = new_b
        months_in_90[idx] = m90
        closing[idx] = new_close
        exited[idx] = exiting

        # E.3.10 issue balance
        d_idx = deal[idx]
        at_issue = deal_issue == t
        if at_issue.any():
            sums = np.bincount(d_idx, weights=opening, minlength=n_deals)
            issue_balance[at_issue] = sums[at_issue]

        # E.3.11 call trigger: remaining live loans exit as called in t + 1
        deal_closing = np.bincount(d_idx, weights=new_close, minlength=n_deals)
        trig = (t >= deal_issue) & (deal_closing <= cfg.deals.call_threshold * issue_balance)
        call_flag |= trig

        # E.3.12 rows
        emit = (t >= w_start) & (t >= issue[idx])
        if emit.any():
            e = emit
            out.append(
                {
                    "loan": idx[e],
                    "period": np.full(e.sum(), t),
                    "opening_balance": opening[e],
                    "scheduled_principal": sched_p[e],
                    "curtailment": curt[e],
                    "closing_balance": new_close[e],
                    "interest_rate": rate[e],
                    "dpd_bucket": np.where(in_h, 0, new_b)[e],
                    "hardship_flag": in_h[e],
                    "months_in_90": m90[e],
                    "reason": reason[e],
                    "exit_balance": exit_balance[e],
                    "loss": loss[e],
                    "indexed_value": indexed_value[e],
                    "indexed_ltv": np.where(exiting, opening, new_close)[e] / indexed_value[e],
                }
            )

    if not out:
        raise ValueError("no rows emitted")
    cols = {key: np.concatenate([o[key] for o in out]) for key in out[0]}
    li = cols.pop("loan")
    panel = pd.DataFrame(
        {
            "loan_id": loans["loan_id"].to_numpy()[li],
            "deal_id": loans["deal_id"].to_numpy()[li],
            "period": to_period(cols.pop("period")),
            "exit_reason": pd.array(REASONS[cols.pop("reason")], dtype="str"),
            **cols,
        }
    )[PANEL_COLUMNS]
    deals = deals.assign(issue_balance=issue_balance)
    return panel, deals
