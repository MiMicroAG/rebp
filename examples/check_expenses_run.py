from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from expenses import compute_expenses_from_config, sum_expenses

rows = compute_expenses_from_config()
print('ROWS:', len(rows))
for r in rows[:5]:
    print(r)
print('TOTAL:', sum_expenses(rows))
