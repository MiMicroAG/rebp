from loan import loan_schedule_annually


def test_variable_annuity_zero_end():
    # small loan 1200, 2 years, rate schedule changes after year 1
    rate_schedule = [
        {"start_year": 1, "end_year": 1, "annual_rate": 12},
        {"start_year": 2, "end_year": 2, "annual_rate": 6},
    ]
    import loan as _loan
    _loan.rate_schedule = rate_schedule

    res = loan_schedule_annually(1200, 0, 2, start_month=1, method='equal_total')
    monthly = res['monthly']
    # last balance should be zero
    assert monthly[-1]['balance'] == 0.0
    # number of months should be 24
    assert len(monthly) == 24


def test_variable_annuity_totals():
    # Compare constant rate vs variable schedule total paid difference
    import loan as _loan
    _loan.rate_schedule = None
    res_fixed = loan_schedule_annually(1200, 6, 2, start_month=1, method='equal_total')
    total_fixed = sum(m['interest'] for m in res_fixed['monthly'])

    _loan.rate_schedule = [
        {"start_year": 1, "end_year": 1, "annual_rate": 12},
        {"start_year": 2, "end_year": 2, "annual_rate": 0},
    ]
    res_var = loan_schedule_annually(1200, 6, 2, start_month=1, method='equal_total')
    total_var = sum(m['interest'] for m in res_var['monthly'])

    assert total_var != total_fixed
    assert res_var['monthly'][-1]['balance'] == 0.0
