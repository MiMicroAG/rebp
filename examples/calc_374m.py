from pathlib import Path
import sys
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
from loan import loan_schedule_annually
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

# try load config from unified project_config.yml
cfg_path = project_root / 'project_config.yml'
if cfg_path.exists() and yaml is not None:
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)  # type: ignore
else:
    cfg = {}

PRINCIPAL = cfg.get('principal', 374_000_000)
ANNUAL_RATE = cfg.get('annual_rate', 1.5)
YEARS = cfg.get('years', 35)
START_MONTH = cfg.get('start_month', 6)
METHOD = cfg.get('method', 'equal_principal')
GROUP_BY = cfg.get('group_by', 'calendar')
RATE_SCHEDULE = cfg.get('rate_schedule')

# pass rate_schedule if provided (loan_schedule_annually accepts it via global var)
if RATE_SCHEDULE:
    # inject into loan module by assigning a variable the function will check
    import loan as _loan_mod
    _loan_mod.rate_schedule = RATE_SCHEDULE

res = loan_schedule_annually(PRINCIPAL, ANNUAL_RATE, YEARS, start_month=START_MONTH, method=METHOD, group_by=GROUP_BY)

print('Annual summary:')
for y in res['annual']:
    print(f"Year {y['year_index']:2d}: months={y['months']:2d}, principal={y['principal_paid']:12,.0f}, interest={y['interest_paid']:12,.0f}, total={y['total_paid']:12,.0f}, cumulative={y['cumulative_paid']:12,.0f}, balance_end={y['balance_end']:12,.0f}")

# Totals
total_principal = sum(y['principal_paid'] for y in res['annual'])
total_interest = sum(y['interest_paid'] for y in res['annual'])
total_paid = sum(y['total_paid'] for y in res['annual'])
print('\nTotals:')
print(f"Total principal: {total_principal:,.0f}")
print(f"Total interest:  {total_interest:,.0f}")
print(f"Total paid:      {total_paid:,.0f}")
