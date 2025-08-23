import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from expenses import compute_expenses_from_config, sum_expenses


def _fmt_money(v: int) -> str:
    return f"{v:,}"


def main() -> None:
    rows = compute_expenses_from_config()

    headers = [
        "年",
        "固資(土)",
        "都計(土)",
        "固資(家)",
        "都計(家)",
        "税(合計)",
        "元金",
        "利息",
        "返済(合計)",
        "管理費",
        "修繕費",
        "保険料",
        "光熱費",
        "大規模修繕",
        "設備修繕",
        "運営(合計)",
        "支出合計",
        "支出累計",
    ]
    widths = [2, 10, 10, 10, 10, 12, 12, 12, 13, 10, 10, 10, 10, 12, 12, 12, 14, 14]

    def pr_row(cols):
        print("  ".join(str(c).rjust(w) for c, w in zip(cols, widths)))

    pr_row(headers)
    print("-" * (sum(widths) + 2 * (len(widths) - 1)))

    running_total = 0
    for r in rows:
        running_total += int(r.get("total_expenses", 0))
        pr_row([
            r["year"],
            _fmt_money(int(r["fixed_tax_land"])),
            _fmt_money(int(r["city_tax_land"])),
            _fmt_money(int(r["fixed_tax_building"])),
            _fmt_money(int(r["city_tax_building"])),
            _fmt_money(int(r["taxes_total"])),
            _fmt_money(int(r["loan_principal"])),
            _fmt_money(int(r["loan_interest"])),
            _fmt_money(int(r["loan_total"])),
            _fmt_money(int(r["management_fee"])),
            _fmt_money(int(r["repairs"])),
            _fmt_money(int(r["insurance"])),
            _fmt_money(int(r["utilities"])),
            _fmt_money(int(r["capex_large"])),
            _fmt_money(int(r["equipment_repairs"])),
            _fmt_money(int(r["operations_total"])),
            _fmt_money(int(r["total_expenses"])),
            _fmt_money(running_total),
        ])

    total = int(sum_expenses(rows))
    print("-" * (sum(widths) + 2 * (len(widths) - 1)))
    print(f"合計（支出合計の総和）: {_fmt_money(total)}")

    # Write CSV output for further analysis
    out_path = Path(__file__).resolve().parent / "expenses_40y.csv"
    import csv

    # Japanese CSV headers (ordered)
    csv_labels = [
        "年",
        "固定資産税(土地)",
        "都市計画税(土地)",
        "固定資産税(家屋)",
        "都市計画税(家屋)",
        "税(合計)",
        "元金",
        "利息",
        "返済(合計)",
        "管理費",
        "修繕費",
        "保険料",
        "光熱費",
        "大規模修繕費",
        "設備修繕費",
        "運営(合計)",
    "支出合計",
    "支出累計",
    ]

    # Use UTF-8 with BOM for Excel compatibility on Windows
    with open(out_path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(csv_labels)
        running = 0
        for r in rows:
            running += int(r.get("total_expenses", 0))
            row_vals = [
                int(r.get("year", 0)),
                int(r.get("fixed_tax_land", 0)),
                int(r.get("city_tax_land", 0)),
                int(r.get("fixed_tax_building", 0)),
                int(r.get("city_tax_building", 0)),
                int(r.get("taxes_total", 0)),
                int(r.get("loan_principal", 0)),
                int(r.get("loan_interest", 0)),
                int(r.get("loan_total", 0)),
                int(r.get("management_fee", 0)),
                int(r.get("repairs", 0)),
                int(r.get("insurance", 0)),
                int(r.get("utilities", 0)),
                int(r.get("capex_large", 0)),
                int(r.get("equipment_repairs", 0)),
                int(r.get("operations_total", 0)),
                int(r.get("total_expenses", 0)),
                int(running),
            ]
            writer.writerow(row_vals)

    print(f"CSV written: {out_path}")


if __name__ == "__main__":
    main()
