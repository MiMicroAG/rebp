from income import compute_income_from_config
from expenses import compute_expenses_from_config
import pprint

# 収入を計算
print('=== 収入計算 ===')
try:
    income_data = compute_income_from_config('project_config.yml')
    print(f'最初の3年間の収入:')
    for i in range(min(3, len(income_data))):
        row = income_data[i]
        annual_income = row.get('annual_income', 0)
        print(f'年{i+1}: 年収入={annual_income:,}円')
except Exception as e:
    print(f'収入計算エラー: {e}')

print()
print('=== 支出計算 ===')
try:
    expenses_data = compute_expenses_from_config('project_config.yml')
    print(f'最初の3年間の支出:')
    for i in range(min(3, len(expenses_data))):
        row = expenses_data[i]
        total_expenses = row.get('total_expenses', 0)
        print(f'年{i+1}: 総支出={total_expenses:,}円')
except Exception as e:
    print(f'支出計算エラー: {e}')
