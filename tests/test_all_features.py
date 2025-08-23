
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from income import compute_income_from_config
from expenses import compute_expenses_from_config
from depreciation import compute_depreciation_from_config
from loan import loan_schedule_annually
from tax import compute_annual_taxes
from cashflow import compute_cashflow_from_config

class TestAllFeatures(unittest.TestCase):
    def setUp(self):
        self.yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'project_config.yml'))

    def test_income(self):
        rows = compute_income_from_config(yaml_path=self.yaml_path, years=5)
        self.assertTrue(len(rows) == 5)
        self.assertIn('annual_income', rows[0])

    def test_expenses(self):
        rows = compute_expenses_from_config(yaml_path=self.yaml_path, years=5)
        self.assertTrue(len(rows) == 5)
        self.assertIn('total_expenses', rows[0])

    def test_depreciation(self):
        depr = compute_depreciation_from_config(yaml_path=self.yaml_path)
        self.assertIn('building', depr)
        self.assertIn('equipment', depr)
        self.assertIn('annual_depreciation', depr['building'])

    def test_loan(self):
        # principal, annual_rate, years, start_month, method, group_by
        principal = 100_000_000
        sched = loan_schedule_annually(principal, 1.5, 35, 1, 'equal_principal', 'calendar')
        self.assertIn('annual', sched)
        self.assertTrue(len(sched['annual']) > 0)

    def test_tax(self):
        res = compute_annual_taxes(
            land_assessed_value=88_559_000,
            building_assessed_value=35_654_400,
            land_area_m2=273.76,
            units=12,
            years=5
        )
        self.assertTrue(len(res) == 5)
        self.assertIn('total', res[0])

    def test_cashflow(self):
        rows = compute_cashflow_from_config(yaml_path=self.yaml_path, years=5)
        self.assertTrue(len(rows) == 5)
        self.assertIn('net_profit', rows[0])
        self.assertIn('apr', rows[0])

    def test_invalid_yaml(self):
        with self.assertRaises(FileNotFoundError):
            compute_cashflow_from_config(yaml_path='invalid_path.yml', years=1)

if __name__ == '__main__':
    unittest.main()
