from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tax

rates = tax._load_rates_from_file('data/building_correction_rates.csv', 40)
print('len:', len(rates))
print('sample:', rates[:10])
