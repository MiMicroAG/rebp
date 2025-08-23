from tax import compute_annual_taxes
res = compute_annual_taxes(88559000.0,35654400.0,273.76,12,years=40)
print('years:', len(res))
print('first:', res[0])
