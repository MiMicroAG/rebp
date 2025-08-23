from income import compute_income, compute_income_from_config, sum_income


def test_income_basic_growth_and_vacancy():
    rows = compute_income(
        monthly_rent=100000,
        units=10,
        years=5,
        rent_change_rates=[0.02, 0.02],  # 以降は据置
        vacancy_rates=[0.05, 0.1],       # 以降は据置
        round_to_yen=True,
    )
    assert len(rows) == 5
    # 年1
    assert rows[0]['year'] == 1
    # 年2は賃料上昇（2%）が入る
    assert rows[1]['monthly_rent'] >= rows[0]['monthly_rent']
    # 空室率の影響（10%）を反映
    assert rows[1]['annual_income'] <= rows[1]['annual_gross']


def test_income_from_config_like_section(tmp_path):
    yaml_text = """
    income:
      monthly_rent: 80000
      units: 8
      rent_change_rates: [0.0, 0.01]
      vacancy_rates: [0.05]
    """
    p = tmp_path / "cfg.yml"
    p.write_text(yaml_text, encoding='utf-8')
    rows = compute_income_from_config(str(p), years=3)
    assert len(rows) == 3
    total = sum_income(rows)
    assert total > 0
