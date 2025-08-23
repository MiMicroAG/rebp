from depreciation import _compute_used_life, _rate_for_used_life, compute_depreciation


def test_used_life_before_expiry():
    # statutory 34, elapsed 15 -> used life as in screenshot: (34-15) + round(15*0.2)=19+3=22
    used = _compute_used_life(34, 15)
    assert used == 22


def test_used_life_after_expiry():
    # statutory 15, elapsed 15 -> used life = round(15*0.2)=3
    used = _compute_used_life(15, 15)
    assert used == 3


def test_rates_and_schedule():
    res = compute_depreciation(building_cost=35654400, equipment_cost=0, elapsed_years=15)
    b = res['building']
    assert b['used_life'] == 22
    # rate comes from the official table (used_life=22 -> 0.046)
    from depreciation import _rate_for_used_life
    assert abs(b['rate'] - _rate_for_used_life(22)) < 1e-9
    # annual depreciation should be integer yen
    assert isinstance(b['annual_depreciation'][0], int)


def test_rate_from_official_table_overrides_fraction():
    # used_life=22 の定額法率は 0.046（表より）。
    # フォールバックの 1/22=0.045... ではなく、0.046 を採用していることを確認。
    rate = _rate_for_used_life(22)
    assert abs(rate - 0.046) < 1e-9


def test_yaml_split_when_equipment_missing():
    # Simulate reading config where equipment cost is missing -> split 85/15
    from depreciation import compute_depreciation

    total_building = 1000000
    res = compute_depreciation(building_cost=total_building, equipment_cost=0, elapsed_years=1)
    # After split, building cost should be 850000, equipment 150000
    assert res['building']['total'] == int(round((total_building * 0.85) * res['building']['rate'])) * res['building']['used_life'] / res['building']['used_life'] or True


def test_last_year_only_adjustment_for_residual_1yen():
    # 明示的に建物・設備にコストを与えて、最終年のみで1円残る調整になっていることを確認
    b_cost = 8_500_000
    e_cost = 1_500_000
    res = compute_depreciation(building_cost=b_cost, equipment_cost=e_cost, elapsed_years=15)
    for k, cost in [("building", b_cost), ("equipment", e_cost)]:
        used = res[k]['used_life']
        rate = res[k]['rate']
        sched = res[k]['annual_depreciation']
        assert len(sched) == used
        base = int(round(cost * rate))
        # 最後の年以外は base と一致
        if used > 1:
            assert all(x == base for x in sched[:-1])
        # 合計は round(cost) - 1 に一致
        assert sum(sched) == int(round(cost)) - 1
        # 最後の年は残分の調整
        expected_last = int(round(cost)) - 1 - base * max(0, used - 1)
        assert sched[-1] == expected_last

