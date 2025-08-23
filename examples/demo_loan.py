import sys
from pathlib import Path

# Add project root to sys.path so this example can be run directly
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from loan import loan_schedule_annually


def print_summary(res):
    print("Annual summary:")
    for y in res["annual"]:
        print(f"Year {y['year_index']}: months={y['months']}, principal={y['principal_paid']:.2f}, interest={y['interest_paid']:.2f}, total={y['total_paid']:.2f}, cumulative={y['cumulative_paid']:.2f}, balance_end={y['balance_end']:.2f}")


if __name__ == '__main__':
    # sample: 1,000, 5% annual, 2 years, start in April, equal_principal
    res = loan_schedule_annually(1000, 5, 2, start_month=4, method='equal_principal')
    print_summary(res)
    print('\nMonthly sample (first 6 months):')
    for m in res['monthly'][:6]:
        print(f"m={m['month']}, payment={m['payment']:.2f}, principal={m['principal']:.2f}, interest={m['interest']:.2f}, balance={m['balance']:.2f}")
