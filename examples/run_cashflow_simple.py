import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from cashflow import compute_cashflow_from_config
import csv

rows = compute_cashflow_from_config()

# print header


headers = ["年", "単年収支", "累計収支", "返済残高", "売却価格", "売却時課税額", "通算損益", "APR"]
print("\t".join(headers))

for r in rows:
    print(f"{r['year']}\t{r['cashflow']}\t{r['cashflow_cum']}\t{r['loan_balance']}\t{r['sale_price']}\t{r['tax_on_sale']}\t{r['net_profit']}\t{r['apr']}")

# CSV output
out_path = "examples/cashflow_simple_40y.csv"
with open(out_path, "w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(headers)
    for r in rows:
        writer.writerow([
            r['year'],
            r['cashflow'],
            r['cashflow_cum'],
            r['loan_balance'],
            r['sale_price'],
            r['tax_on_sale'],
            r['net_profit'],
            r['apr'],
        ])
print(f"CSV written: {out_path}")
