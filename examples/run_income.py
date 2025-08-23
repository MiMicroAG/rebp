import sys
from pathlib import Path

# Ensure project root is importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from income import compute_income_from_config, sum_income


def _fmt_money(v: int) -> str:
    return f"{v:,}"


def _fmt_pct(v: float) -> str:
    return f"{v*100:.2f}%"


def main() -> None:
    rows = compute_income_from_config()

    # Header and column widths (Japanese labels)
    headers = ["年", "年額賃料", "空室率", "収入合計"]
    widths = [2, 15, 8, 16]

    def pr_row(cols):
        line = "  ".join(str(c).rjust(w) for c, w in zip(cols, widths))
        print(line)

    # Print header
    pr_row(headers)
    print("-" * (sum(widths) + 2 * (len(widths) - 1)))

    # Print all 40 years
    for r in rows:
        pr_row([
            r["year"],
            _fmt_money(int(r["annual_gross"])),
            _fmt_pct(float(r["vacancy_rate"])),
            _fmt_money(int(r["annual_income"])),
        ])

    # Footer total
    total = int(sum_income(rows))
    print("-" * (sum(widths) + 2 * (len(widths) - 1)))
    print(f"合計（収入合計の総和）: {_fmt_money(total)}")


if __name__ == "__main__":
    main()
