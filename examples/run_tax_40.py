from pathlib import Path
import sys
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from tax import compute_annual_taxes

LAND = 88559000.0
BUILDING = 35654400.0

res = compute_annual_taxes(
    land_assessed_value=LAND,
    building_assessed_value=BUILDING,
    land_area_m2=273.76,
    units=12,
    years=40,
    loan_config_rate_file='data/building_correction_rates.csv'
)

print("{:^6} | {:>15} | {:>15} | {:>15} | {:>15} | {:>15}".format('Year','Fixed Land','City Land','Fixed Bldg','City Bldg','Total'))
print('-'*96)
for r in res:
    y = r['year']
    fl = round(r['fixed_tax_land'])
    cl = round(r['city_tax_land'])
    fb = round(r['fixed_tax_building'])
    cb = round(r['city_tax_building'])
    tot = round(r['total'])
    print(f"{y:4d}   | {fl:15,d} | {cl:15,d} | {fb:15,d} | {cb:15,d} | {tot:15,d}")

# Totals
tp = sum(round(r['fixed_tax_land']) for r in res)
tc = sum(round(r['city_tax_land']) for r in res)
fb = sum(round(r['fixed_tax_building']) for r in res)
cb = sum(round(r['city_tax_building']) for r in res)
print('-'*96)
print(f"TOTAL | {tp:15,d} | {tc:15,d} | {fb:15,d} | {cb:15,d} | {tp+tc+fb+cb:15,d}")
