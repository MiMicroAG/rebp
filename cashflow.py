
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from typing import List, Dict, Any, Optional
import yaml  # type: ignore
from utils import to_float, to_int
from utils import to_float, to_int

def compute_cashflow_from_config(yaml_path: Optional[str] = None, years: int = 40) -> List[Dict[str, Any]]:
	# --- YAMLパスの事前セット ---
	if yaml_path is None:
		from income import _find_project_config
		yaml_path = _find_project_config()

	# --- 減価償却累計 ---
	from depreciation import compute_depreciation_from_config
	depr = compute_depreciation_from_config(yaml_path)
	b_depr = depr["building"]["annual_depreciation"]
	e_depr = depr["equipment"]["annual_depreciation"]
	# 年次で合算した減価償却累計リスト
	depr_cum = []
	total = 0
	for y in range(years):
		b = b_depr[y] if y < len(b_depr) else 0
		e = e_depr[y] if y < len(e_depr) else 0
		total += b + e
		depr_cum.append(total)

	# --- 購入価格 ---
	with open(yaml_path, "r", encoding="utf-8") as fh:
		cfg = yaml.safe_load(fh) or {}
		if "purchase_price" not in cfg:
			raise ValueError("YAMLに 'purchase_price' が未指定です。必ず設定してください。")
		purchase_price = to_float(cfg.get("purchase_price", 0), 0.0)
		initial_capital_ratio = to_float(cfg.get("initial_capital_ratio", 0.2), 0.2)
		initial_capital = purchase_price * initial_capital_ratio
	"""
	YAMLから年次収入・支出を取得し、単年収支・累計収支を計算して返す。
	戻り値: [{year, annual_income, total_expenses, cashflow, cashflow_cum}]
	"""
	# 収入
	from income import compute_income_from_config
	income_rows = compute_income_from_config(yaml_path=yaml_path, years=years, round_to_yen=True)
	# 支出
	from expenses import compute_expenses_from_config
	expense_rows = compute_expenses_from_config(yaml_path=yaml_path, years=years)

	# --- 返済残高 ---
	from loan import loan_schedule_annually
	# ローン設定は project_config.yml から取得
	if yaml_path is None:
		from income import _find_project_config
		yaml_path = _find_project_config()
	with open(yaml_path, "r", encoding="utf-8") as fh:
		cfg = yaml.safe_load(fh) or {}
	purchase_price = to_float(cfg.get("purchase_price", 450000000), 450000000)
	initial_capital_ratio = to_float(cfg.get("initial_capital_ratio", 0.2), 0.2)
	initial_capital = purchase_price * initial_capital_ratio
	principal = purchase_price - initial_capital
	annual_rate = to_float(cfg.get("annual_rate", 0), 0.0)
	loan_years = to_int(cfg.get("years", years), years)
	start_month = to_int(cfg.get("start_month", 1), 1)
	method = str(cfg.get("method", "equal_principal"))
	group_by = str(cfg.get("group_by", "calendar"))
	loan_sched = loan_schedule_annually(principal, annual_rate, loan_years, start_month, method, group_by)
	loan_annual = loan_sched.get("annual", [])

	# --- 売却価格 ---
	gross_yield = float(cfg.get("gross_yield", 0.045))  # デフォルト4.5%
	# 空室無しの年間家賃合計（年ごと）
	monthly_rent = to_float(cfg.get("income", {}).get("monthly_rent", 0), 0.0)
	units = to_int(cfg.get("income", {}).get("units", 1), 1)
	annual_gross_rent = [int(monthly_rent * 12 * units)] * years
	# rent_change_rates, rent_change, などのトレンドも考慮
	# income_rows の annual_gross を使う
	if income_rows and "annual_gross" in income_rows[0]:
		annual_gross_rent = [int(r.get("annual_gross", 0)) for r in income_rows]

	out: List[Dict[str, Any]] = []
	cum = 0
	for y in range(years):
		inc = int(income_rows[y].get("annual_income", 0)) if y < len(income_rows) else 0
		exp = int(expense_rows[y].get("total_expenses", 0)) if y < len(expense_rows) else 0
		cf = inc - exp
		cum += cf
		# 返済残高
		balance = 0
		if y < len(loan_annual):
			balance = int(round(loan_annual[y].get("balance_end", 0)))
		# 売却価格
		sale_price = 0
		if y < len(annual_gross_rent) and gross_yield > 0:
			sale_price = int(round(annual_gross_rent[y] / gross_yield))
		# 売却時課税額
		tax_on_sale = 0
		if y < len(depr_cum):
			gain = sale_price - purchase_price + depr_cum[y]
			tax_on_sale = int(round(max(gain * 0.20315, 0)))
		# 通算損益: 累計収支 + 売却価格 - 返済残高 - 売却時課税額 - 自己資金
		net_profit = cum + sale_price - balance - tax_on_sale - initial_capital
		apr = net_profit / initial_capital if initial_capital else 0
		out.append({
			"year": y + 1,
			"annual_income": inc,
			"total_expenses": exp,
			"cashflow": cf,
			"cashflow_cum": cum,
			"loan_balance": balance,
			"sale_price": sale_price,
			"tax_on_sale": tax_on_sale,
			"net_profit": net_profit,
			"apr": apr,
		})
	return out
