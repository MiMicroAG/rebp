from income import compute_income_from_config

def test_income_trend_keys(tmp_path):
    yaml_text = """
    income:
      monthly_rent: 100000
      units: 5
      rent_change:
        initial: -0.01
        trend: -0.02
      vacancy:
        initial: 0.05
        trend: 0.10
    """
    p = tmp_path / "cfg.yml"
    p.write_text(yaml_text, encoding='utf-8')
    rows = compute_income_from_config(str(p), years=5)
    assert len(rows) == 5
    # 前年比減額→月額は非増（下がるか据え置き）になっているはず
    assert rows[1]['monthly_rent'] <= rows[0]['monthly_rent']
    # 空室率はトレンドで増加
    assert rows[1]['vacancy_rate'] >= rows[0]['vacancy_rate']
