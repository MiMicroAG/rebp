"""Loan repayment schedule utilities.

Provides a function to compute an annual repayment summary given:
- principal
- annual interest rate (percent or decimal)
- repayment period in years
- repayment method: 'equal_principal' (元本均等) or 'equal_total' (元利均等)
- start_month: integer 1-12 indicating which month the first payment occurs (for calendar-year aggregation)

Returns a dict with 'monthly' list and 'annual' aggregated list.
"""
from typing import List, Dict, Any

# Optional external rate schedule can be injected here (list of dicts).
# Example: [{'start_year':1,'end_year':5,'annual_rate':1.5}, ...]
rate_schedule = None


def _to_monthly_rate(annual_rate: float) -> float:
    # Accept annual_rate as percent (e.g. 3.5) or decimal (0.035)
    if abs(annual_rate) > 1:
        annual_rate = annual_rate / 100.0
    return annual_rate / 12.0


def loan_schedule_annually(
    principal: float,
    annual_rate: float,
    years: int,
    start_month: int = 1,
    method: str = "equal_total",
    group_by: str = "calendar",
) -> Dict[str, Any]:
    """Compute yearly repayment summary and monthly schedule.

    Args:
        principal: initial loan amount (positive)
        annual_rate: annual interest (percent or decimal). e.g. 3.5 or 0.035
        years: repayment period in years (positive int)
        start_month: month number 1-12 for first payment (calendar alignment)
        method: 'equal_principal' (元本均等) or 'equal_total' (元利均等)

    Returns:
        dict {
            'monthly': [ {month_index, payment, principal, interest, balance_after} ... ],
            'annual': [ {year_index, months, principal_paid, interest_paid, total_paid, cumulative_paid, balance_end} ... ]
        }
    """
    if principal <= 0:
        raise ValueError("principal must be > 0")
    if years <= 0:
        raise ValueError("years must be > 0")
    if not (1 <= start_month <= 12):
        raise ValueError("start_month must be between 1 and 12")
    if method not in ("equal_principal", "equal_total"):
        raise ValueError("method must be 'equal_principal' or 'equal_total'")
    if group_by not in ("calendar", "anniversary"):
        raise ValueError("group_by must be 'calendar' or 'anniversary'")
    # rate_schedule: optional list of dicts with {start_year, end_year, annual_rate}
    # If provided, it overrides the flat annual_rate. Structure example:
    # [{"start_year":1, "end_year":5, "annual_rate":1.5}, {"start_year":6, "end_year":35, "annual_rate":2.0}]

    total_months = years * 12
    # If a rate schedule is provided via outer scope or kwargs, the caller should
    # pass it in. For backward compatibility we keep annual_rate param as default.
    # module-level optional rate_schedule can be injected (list of dicts)
    try:
        rate_schedule = globals().get("rate_schedule", None)
    except Exception:
        rate_schedule = None

    def _rate_for_month(m_index: int) -> float:
        # determine loan-year for this payment (1-based)
        year_of_payment = (m_index - 1) // 12 + 1
        if rate_schedule:
            for entry in rate_schedule:
                sy = int(entry.get("start_year", 1))
                ey = int(entry.get("end_year", sy))
                if sy <= year_of_payment <= ey:
                    return _to_monthly_rate(float(entry["annual_rate"]))
        # fallback to flat annual_rate
        return _to_monthly_rate(annual_rate)

    monthly = []
    balance = float(principal)

    if method == "equal_principal":
        principal_component_fixed = principal / total_months
        for m in range(1, total_months + 1):
            interest = balance * _rate_for_month(m)
            principal_comp = principal_component_fixed
            payment = principal_comp + interest
            balance -= principal_comp
            if balance < 1e-12:
                balance = 0.0
            monthly.append(
                {"month": m, "payment": payment, "principal": principal_comp, "interest": interest, "balance": balance}
            )
    else:  # equal_total (annuity) with support for variable monthly rate
        balance = float(principal)
        current_rate = None
        payment = None
        for m in range(1, total_months + 1):
            this_rate = _rate_for_month(m)
            remaining_months = total_months - (m - 1)
            # recompute payment when rate changes or at first month
            if current_rate is None or abs(this_rate - current_rate) > 1e-14 or payment is None:
                current_rate = this_rate
                if current_rate == 0:
                    payment = balance / remaining_months
                else:
                    r = current_rate
                    payment = balance * (r * (1 + r) ** remaining_months) / ((1 + r) ** remaining_months - 1)

            interest = balance * current_rate
            principal_comp = payment - interest
            # guard rounding / last payment
            if m == total_months or principal_comp >= balance:
                principal_comp = balance
                payment = principal_comp + interest
                balance = 0.0
            else:
                balance -= principal_comp
                if balance < 1e-12:
                    balance = 0.0

            monthly.append(
                {"month": m, "payment": payment, "principal": principal_comp, "interest": interest, "balance": balance}
            )

    # Aggregate based on group_by
    annual = []
    months_remaining = total_months
    idx = 0
    cumulative = 0.0
    year_index = 1

    if group_by == "calendar":
        # First calendar year: from start_month to December
        first_year_months = min(13 - start_month, months_remaining)
        if first_year_months > 0:
            slice_months = monthly[idx : idx + first_year_months]
            principal_paid = sum(m["principal"] for m in slice_months)
            interest_paid = sum(m["interest"] for m in slice_months)
            total_paid = sum(m["payment"] for m in slice_months)
            cumulative += total_paid
            balance_end = slice_months[-1]["balance"] if slice_months else balance
            annual.append(
                {
                    "year_index": year_index,
                    "months": len(slice_months),
                    "principal_paid": principal_paid,
                    "interest_paid": interest_paid,
                    "total_paid": total_paid,
                    "cumulative_paid": cumulative,
                    "balance_end": balance_end,
                }
            )
            idx += first_year_months
            months_remaining -= first_year_months
            year_index += 1

        # Full calendar years (12 months)
        while months_remaining >= 12:
            slice_months = monthly[idx : idx + 12]
            principal_paid = sum(m["principal"] for m in slice_months)
            interest_paid = sum(m["interest"] for m in slice_months)
            total_paid = sum(m["payment"] for m in slice_months)
            cumulative += total_paid
            balance_end = slice_months[-1]["balance"] if slice_months else balance
            annual.append(
                {
                    "year_index": year_index,
                    "months": 12,
                    "principal_paid": principal_paid,
                    "interest_paid": interest_paid,
                    "total_paid": total_paid,
                    "cumulative_paid": cumulative,
                    "balance_end": balance_end,
                }
            )
            idx += 12
            months_remaining -= 12
            year_index += 1

        # Final partial calendar year
        if months_remaining > 0:
            slice_months = monthly[idx : idx + months_remaining]
            principal_paid = sum(m["principal"] for m in slice_months)
            interest_paid = sum(m["interest"] for m in slice_months)
            total_paid = sum(m["payment"] for m in slice_months)
            cumulative += total_paid
            balance_end = slice_months[-1]["balance"] if slice_months else balance
            annual.append(
                {
                    "year_index": year_index,
                    "months": len(slice_months),
                    "principal_paid": principal_paid,
                    "interest_paid": interest_paid,
                    "total_paid": total_paid,
                    "cumulative_paid": cumulative,
                    "balance_end": balance_end,
                }
            )

    else:  # anniversary grouping: consecutive 12-month blocks from first payment
        # Full anniversary years
        while months_remaining >= 12:
            slice_months = monthly[idx : idx + 12]
            principal_paid = sum(m["principal"] for m in slice_months)
            interest_paid = sum(m["interest"] for m in slice_months)
            total_paid = sum(m["payment"] for m in slice_months)
            cumulative += total_paid
            balance_end = slice_months[-1]["balance"] if slice_months else balance
            annual.append(
                {
                    "year_index": year_index,
                    "months": 12,
                    "principal_paid": principal_paid,
                    "interest_paid": interest_paid,
                    "total_paid": total_paid,
                    "cumulative_paid": cumulative,
                    "balance_end": balance_end,
                }
            )
            idx += 12
            months_remaining -= 12
            year_index += 1

        # Final partial period (if any)
        if months_remaining > 0:
            slice_months = monthly[idx : idx + months_remaining]
            principal_paid = sum(m["principal"] for m in slice_months)
            interest_paid = sum(m["interest"] for m in slice_months)
            total_paid = sum(m["payment"] for m in slice_months)
            cumulative += total_paid
            balance_end = slice_months[-1]["balance"] if slice_months else balance
            annual.append(
                {
                    "year_index": year_index,
                    "months": len(slice_months),
                    "principal_paid": principal_paid,
                    "interest_paid": interest_paid,
                    "total_paid": total_paid,
                    "cumulative_paid": cumulative,
                    "balance_end": balance_end,
                }
            )

    return {"monthly": monthly, "annual": annual}
