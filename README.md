# RealEstateBusinessPlan

このリポジトリは、融資（ローン）・税金・減価償却・収支計算など不動産事業計画の主要ロジックをPythonで実装したものです。

## 主な機能

- 年単位での返済集計（元金、利息、総返済、累計、残高）
- 固定資産税・都市計画税の年次計算
- 建物・設備の減価償却費計算
- 収入・支出・キャッシュフロー・APRの算出
- **Webアプリケーション**: ブラウザから設定編集・データ表示・認証機能

## 主要ファイル

- `loan.py` — 返済計算
- `tax.py` — 税金計算
- `depreciation.py` — 減価償却
- `income.py` — 収入計算
- `expenses.py` — 支出計算
- `cashflow.py` — 総合キャッシュフロー
- `project_config.yml` — 設定ファイル
- `app.py` — **Webアプリケーション メインファイル**
- `templates/` — **HTMLテンプレート**
- `examples/` — 実行例・サンプル
- `tests/` — 機能テスト

## クイックスタート

```powershell
cd 'C:\Users\taxa\OneDrive\Develop\work\RealEstateBusinessPlan'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Webアプリケーション起動

```powershell
# 仮想環境を有効化
.\.venv\Scripts\Activate.ps1

# Webアプリケーションを起動
python app.py
```

ブラウザで http://127.0.0.1:5000 にアクセス

### ログイン情報

- **管理者**: admin / admin123
- **一般ユーザー**: user / user123

### Webアプリケーション機能

1. **設定編集**: YAML設定ファイルのパラメータをWebから編集
   - 物件情報（購入価格、自己資金比率、経過年数）
   - ローン条件（年利、返済年数、開始月）
   - 建物・設備情報（価格、法定耐用年数）
   - 税金情報（土地評価額、建物評価額、戸数等）
   - 収入情報（月額賃料、戸数、変動率）
   - 支出情報（管理費率、修繕費、保険料等）

2. **データ表示**: 40年間の財務データを表形式で表示
   - 収入・支出・減価償却・キャッシュフロー
   - 累積キャッシュフロー・ローン残高・APR
   - 項目別フィルタ表示
   - CSVエクスポート機能

3. **認証機能**: ログイン必須でセキュアなアクセス制御

## コマンドライン実行
- **一般ユーザー**: user / user123

### 主要機能

1. **設定編集**: YAML設定ファイルをWebから編集
2. **データ表示**: 40年間の財務データを表形式で表示
3. **認証機能**: ログイン/ログアウト機能
4. **CSVエクスポート**: 計算結果をCSVファイルでダウンロード

## コマンドライン実行

```powershell
.\.venv\Scripts\python.exe examples\demo_loan.py
```

## テスト実行

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## API要点

### ローン返済

```python
loan_schedule_annually(principal, annual_rate, years, start_month=1, method='equal_total')
```

### 税金計算

```python
compute_annual_taxes(land_assessed_value, building_assessed_value, land_area_m2, units, years=40, ...)
```

### 減価償却

```python
compute_depreciation_from_config(yaml_path)
```

---

## 設定例（YAML）

```yaml
elapsed_years: 15
building:
  cost: 35654400
  statutory_life: 34
equipment:
  cost: 0
  statutory_life: 15
```

---

## CSVフォーマット例

### 減価償却率表

```csv
# 国税庁の償却率表（定額法）
service_life,declining_balance_rate,straight_line_rate
22,0.114,0.046
```

### 建物の経年減点補正率

```csv
# 年別の補正倍率
1,0.9659
2,0.9318
```

---

## よくある質問・トラブルシュート

- モジュール参照エラー時は `sys.path` の追加や仮想環境の利用を推奨
- CSV/Excel出力や丸めオプション、GUI/CLI拡張も今後対応予定

---

### ローン返済サンプル（月次明細）

```text
m=2, payment=45.66, principal=41.67, interest=3.99, balance=916.67
m=3, payment=45.49, principal=41.67, interest=3.82, balance=875.00
m=4, payment=45.31, principal=41.67, interest=3.65, balance=833.33
m=5, payment=45.14, principal=41.67, interest=3.47, balance=791.67
m=6, payment=44.97, principal=41.67, interest=3.30, balance=750.00
```

---

## API（要点）

関数:

```python
loan_schedule_annually(principal, annual_rate, years, start_month=1, method='equal_total')
```

- principal: 貸付金額（float > 0）
- annual_rate: 年利（% で与えてもよいし小数で与えても良い; 例えば 3.5 または 0.035）
- years: 返済年数（int > 0）
- start_month: 初回支払月（1〜12） — カレンダー年の切り替えに影響
- method: `'equal_principal'`（元本均等）または `'equal_total'`（元利均等・年利で計算）

戻り値: dict

- `monthly`: 各月の明細リスト（辞書に `month`, `payment`, `principal`, `interest`, `balance`）
- `annual`: 年次集計リスト（辞書に `year_index`, `months`, `principal_paid`, `interest_paid`, `total_paid`, `cumulative_paid`, `balance_end`）

## 税金計算（固定資産税・都市計画税）

このリポジトリには、土地および建物について年次ごとの固定資産税・都市計画税を計算する関数 `compute_annual_taxes`（`tax.py`）があります。主に不動産事業計画での税負担の推移を評価する用途を想定しています。

### 主な特徴

- 土地と家屋それぞれについて、固定資産税と都市計画税を年次で計算して返します。
- 建物評価については経年減点補正率（年ごとの倍率）を適用できます。補正率はCSVファイルで与えます。
- 補正率ファイルが無い場合や不足する年がある場合は、デフォルトで倍率=1.0（補正なし）を使用します。
- デフォルト計算期間は40年です（`years` 引数で変更可能）。

### 関数仕様

```python
compute_annual_taxes(land_assessed_value, building_assessed_value, land_area_m2, units, years=40, fixed_asset_rate=0.014, city_plan_rate=0.003, loan_config_rate_file=None, land_residential_special=None)
```

### 主要引数（抜粋）

- `land_assessed_value`: 土地の課税標準額（数値）
- `building_assessed_value`: 建物の課税標準額（数値）
- `land_area_m2`: 土地面積（m2）
- `units`: 戸数（住宅用地の特例判定に使用）
- `years`: 年数（デフォルト 40）
- `loan_config_rate_file`: 補正率 CSV ファイルのパス（省略時は全て 1.0）
- `land_residential_special`: 明示的に住宅用地の特例を適用する場合に True を渡す（省略時は `land_area_m2 <= units * 200` で判定）

### 補正率 CSV フォーマット

- CSV は 2 つの形式をサポートします（このリポジトリではペア形式を推奨しています）:
  - ペア形式: `年番号,倍率`（年番号は 1 始まり）。指定した年のみ上書きされ、未指定年は 1.0 のままになります。例: `5,0.96`。
  - 単列形式: 各行に倍率を置く（1行目→年1、2行目→年2 …）。

### 返り値

- 年ごとの辞書リスト（長さ `years`）を返します。各辞書に含まれる主要キー:
  - `year`: 年番号（1始まり）
  - `fixed_tax_land`: 固定資産税（土地）
  - `city_tax_land`: 都市計画税（土地）
  - `fixed_tax_building`: 固定資産税（家屋）
  - `city_tax_building`: 都市計画税（家屋）
  - `total`: 上記の合計

### 課税標準額の考え方

- 土地の課税標準額（課税評価額に適用される課税標準）は、通常は土地の評価額そのままを用いますが、住宅用地の特例が適用される場合は軽減された課税標準が使われます。
- 本実装では次の扱いを採用しています（添付のルールに準拠）:
  - 住宅用地の特例適用時の課税標準（土地）: 固定資産税用は評価額の 1/6、都市計画税用は評価額の 1/3
  - 特例が適用されない場合は評価額をそのまま課税標準とします。

### 住宅用地の特例判定ルール

- 判定は以下の基準で行います（関数のデフォルト挙動）:
  - 土地面積が `units * 200 m²` 以下であれば「小規模住宅用地」として扱い、特例を適用します。
  - `units` は戸数（住宅戸数）で、例えば 12 戸であれば上限は 12 × 200 = 2400 m² になります。
  - 明示的に `land_residential_special=True` を渡した場合は強制的に特例を適用し、`False` を渡した場合は適用しません。

### 例

- 土地評価額が 88,559,000 円、戸数 12、土地面積 273.76 m² の場合、上限は 2400 m² であり実際の土地面積はこれを下回るため「住宅用地の特例」が適用されます。よって土地の課税標準は固定資産税用に 88,559,000 × 1/6、都市計画税用に 88,559,000 × 1/3 を用います。

### 簡単な使用例（PowerShell）

```powershell
& C:/Users/taxa/AppData/Local/Programs/Python/Python313/python.exe - <<'PY'
from tax import compute_annual_taxes
res = compute_annual_taxes(
    land_assessed_value=88559000.0,
    building_assessed_value=35654400.0,
    land_area_m2=273.76,
    units=12,
    years=40,
    loan_config_rate_file='data/building_correction_rates.csv'
)
for row in res:
    print(row)
PY
```

### 表示・丸めについて

- 関数は内部計算を浮動小数（float）で行います。通貨（円）単位で丸めたい場合は、呼び出し側で `round(..., 0)` を行うか、必要であれば関数に丸めオプションを追加できます。

## トラブルシュート

- 実行時に `ModuleNotFoundError: No module named 'loan'` が出る場合、カレントディレクトリがモジュール検索パスに含まれていないことが原因です。
  - `examples/demo_loan.py` はプロジェクトルートを `sys.path` に追加する処理を行っています。直接実行するなら上記の仮想環境の python 実行を推奨します。
  - 代替: `python -m examples.demo_loan` で実行すると安定します（`examples` をパッケージ化しています）。

## 今後の改善案

- CSV/Excel 出力オプション追加
- 通貨単位（丸め）オプション
- GUI/CLI の拡張（複数ローン合算、可視化）

## 減価償却（depreciation）

このリポジトリには `depreciation.py` により、建物本体と付属設備の年次減価償却費を算出する機能があります。

### 主なルール

- 法定耐用年数のデフォルト: 建物=34年、付属設備=15年
- 中古耐用年数の算出: 添付資料の計算式に従います（経過年数×20% を加味）。
- 定額法（毎年同額）で償却額を計算します。年率は「国税庁の償却率表（定額法）」を優先し、表に無い場合は 1/中古耐用年数 を小数第3位で四捨五入して適用します。
- YAML 設定はプロジェクトルートの `project_config.yml` を優先して読みます。
- `equipment.cost`（付属設備価格）が YAML に無い、または 0 の場合は、建物価格を 85%（建物）/15%（付属設備）に分割して扱います。

### 設定例（`project_config.yml` に記載）

```yaml
elapsed_years: 15
building:
  cost: 35654400
  statutory_life: 34
equipment:
  cost: 0
  statutory_life: 15
```

### 実行例（PowerShell）

```powershell
# project_config.yml を参照して計算
python .\examples\run_depreciation.py

# もし仮想環境を使うなら
.venv\Scripts\python.exe .\examples\run_depreciation.py
```

### テスト

```powershell
.venv\Scripts\python.exe -m pytest tests/test_depreciation.py -q
```

必要な依存: PyYAML（`compute_depreciation_from_config` を使う場合）

### CSV フォーマット（data/ 配下）

- 減価償却の償却率表: `data/depreciation_rates_jpn.csv`
  - ヘッダ: `service_life,declining_balance_rate,straight_line_rate`
  - 先頭の `#` コメント行は無視されます。
  - 例:
    ```csv
    # 国税庁の償却率表（定額法）
    service_life,declining_balance_rate,straight_line_rate
    22,0.114,0.046
    ```

- 建物の経年減点補正率: `data/building_correction_rates.csv`
  - 書式: `年(1始まり),倍率`（CSV ペア形式）
  - 先頭の `#` コメント行は無視されます。
  - 例:
    ```csv
    # 年別の補正倍率
    1,0.9659
    2,0.9318
    ```

---

質問や追加したい要件（例えば '期間ごとの返済カレンダーをCSVで出力したい' 等）があれば教えてください。
