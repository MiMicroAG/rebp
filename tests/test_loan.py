from loan import loan_schedule_annually


def approx_eq(a, b, tol=1e-6):
    return abs(a - b) <= tol


def test_zero_interest_equal_principal_one_year():
    # principal 1200, 1 year, zero interest, equal principal -> 12 payments of 100
    r = loan_schedule_annually(1200, 0, 1, start_month=1, method="equal_principal")
    annual = r["annual"]
    # single year of 12 months
    assert len(annual) == 1
    assert annual[0]["months"] == 12
    assert approx_eq(annual[0]["principal_paid"], 1200)
    assert approx_eq(annual[0]["interest_paid"], 0)
    assert approx_eq(annual[0]["total_paid"], 1200)
    assert approx_eq(annual[0]["balance_end"], 0)


def test_zero_interest_start_month_partial():
    # principal 1200, 1 year, start in April (4)
    # payments span Apr..Mar => first calendar year Apr-Dec = 9 months (900), next year 3 months (300)
    r = loan_schedule_annually(1200, 0, 1, start_month=4, method="equal_principal")
    annual = r["annual"]
    assert len(annual) == 2
    assert annual[0]["months"] == 9
    assert approx_eq(annual[0]["principal_paid"], 900)
    assert annual[1]["months"] == 3
    assert approx_eq(annual[1]["principal_paid"], 300)
    assert approx_eq(annual[-1]["balance_end"], 0)


def test_annuity_basic():
    # small annuity test (non-zero interest) smoke check sums
    r = loan_schedule_annually(1000, 12, 1, start_month=1, method="equal_total")
    annual = r["annual"]
    assert len(annual) == 1
    assert approx_eq(annual[0]["principal_paid"], 1000)
    # interest should be > 0
    assert annual[0]["interest_paid"] > 0
    assert approx_eq(annual[0]["balance_end"], 0)
