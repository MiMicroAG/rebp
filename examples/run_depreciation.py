import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

# This example prefers the repository-level `project_config.yml`.
# If you want to test with a custom YAML, call compute_depreciation_from_config(path)
from depreciation import compute_depreciation_from_config


def _fmt_list(lst):
    return [f"{int(x):,}" for x in lst]


if __name__ == "__main__":
    # Prefer project_config.yml in the project root; compute_depreciation_from_config
    # will search the project tree if no path is provided.
    res = compute_depreciation_from_config()

    print("Building:")
    b = res["building"]
    print(f" statutory_life: {b['statutory_life']}")
    print(f" elapsed_years: {b['elapsed_years']}")
    print(f" used_life: {b['used_life']}")
    print(f" rate: {b['rate']}")
    print(f" annual (first..): {_fmt_list(b['annual_depreciation'][:5])}")
    print(f" total: {int(b['total']):,}")

    print('\nEquipment:')
    e = res['equipment']
    print(f" statutory_life: {e['statutory_life']}")
    print(f" elapsed_years: {e['elapsed_years']}")
    print(f" used_life: {e['used_life']}")
    print(f" rate: {e['rate']}")
    print(f" annual (first..): {_fmt_list(e['annual_depreciation'][:5])}")
    print(f" total: {int(e['total']):,}")
