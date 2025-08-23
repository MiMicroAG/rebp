from tax import compute_annual_taxes


def test_compute_annual_taxes_default():
    # simple known inputs
    land_val = 88559000.0
    building_val = 35654400.0
    land_area = 273.76
    units = 12

    years = 40
    res = compute_annual_taxes(
        land_assessed_value=land_val,
        building_assessed_value=building_val,
        land_area_m2=land_area,
        units=units,
        years=years,
    )

    assert len(res) == years
    # default correction rates are 1.0 so first year building taxes are:
    expected_fixed_land = land_val * (1.0 / 6.0) * 0.014
    expected_city_land = land_val * (1.0 / 3.0) * 0.003
    expected_fixed_building = building_val * 0.014
    expected_city_building = building_val * 0.003

    first = res[0]
    assert abs(first["fixed_tax_land"] - expected_fixed_land) < 1e-6
    assert abs(first["city_tax_land"] - expected_city_land) < 1e-6
    assert abs(first["fixed_tax_building"] - expected_fixed_building) < 1e-6
    assert abs(first["city_tax_building"] - expected_city_building) < 1e-6


def test_compute_annual_taxes_pair_csv(tmp_path):
    # create a pair-style csv: only year 3 specified as 0.5
    p = tmp_path / "pair.csv"
    p.write_text("3,0.5\n")

    res = compute_annual_taxes(
        land_assessed_value=100.0,
        building_assessed_value=200.0,
        land_area_m2=100.0,
        units=1,
        years=5,
        loan_config_rate_file=str(p),
    )

    # year3 building multiplier should be applied, others 1.0
    assert res[0]["fixed_tax_building"] == 200.0 * 0.014
    assert res[1]["fixed_tax_building"] == 200.0 * 0.014
    assert res[2]["fixed_tax_building"] == 200.0 * 0.5 * 0.014
    assert res[3]["fixed_tax_building"] == 200.0 * 0.014
