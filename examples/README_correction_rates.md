# 建物補正率ファイルのフォーマット例（CSVのみ）

このプロジェクトでは補正率ファイルを CSV 形式のみサポートします。

- ファイル名例: `building_correction_rates.csv`
- 各行に 1 つの倍率（乗算）を置きます。ヘッダ行は不要です。

例:

1.00
0.99
0.98

ペア形式（推奨）:

年番号（1始まり）,倍率 のペアを並べることもできます。指定した年のみ上書きされ、未指定年は 1.0 のままになります。

例:

1,1.00
5,0.96  # 5年目を0.96に設定


注意点:
- ファイルのエントリ数が `years` 引数より短い場合、残りは 1.0 で埋めます。
- ファイルが存在しないか `.csv` でない場合、全て 1.0 を使用します。

補足:
- 付属サンプルは40年分のテンプレートになっています。`years=40` でそのまま使えます。

使い方の例（Python）:

from tax import compute_annual_taxes
res = compute_annual_taxes(
  land_assessed_value=88559000.0,
  building_assessed_value=35654400.0,
  land_area_m2=273.76,
  units=12,
  years=40,
  loan_config_rate_file='examples/building_correction_rates.csv',
)
