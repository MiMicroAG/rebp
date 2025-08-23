import unittest
import os
from cashflow import compute_cashflow_from_config

class TestCashflowFeatures(unittest.TestCase):
    def setUp(self):
        self.yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'project_config.yml'))

    def test_basic_run(self):
        rows = compute_cashflow_from_config(yaml_path=self.yaml_path, years=5)
        self.assertTrue(len(rows) == 5)
        for r in rows:
            self.assertIn('cashflow', r)
            self.assertIn('cashflow_cum', r)
            self.assertIn('loan_balance', r)
            self.assertIn('sale_price', r)
            self.assertIn('tax_on_sale', r)
            self.assertIn('net_profit', r)
            self.assertIn('apr', r)

    def test_apr_calculation(self):
        rows = compute_cashflow_from_config(yaml_path=self.yaml_path, years=1)
        apr = rows[0]['apr']
        self.assertIsInstance(apr, float)

    def test_initial_capital_ratio(self):
        rows = compute_cashflow_from_config(yaml_path=self.yaml_path, years=1)
        self.assertGreaterEqual(rows[0]['apr'], -1)

    def test_zero_years(self):
        rows = compute_cashflow_from_config(yaml_path=self.yaml_path, years=0)
        self.assertEqual(rows, [])

    def test_invalid_yaml(self):
        with self.assertRaises(FileNotFoundError):
            compute_cashflow_from_config(yaml_path='invalid_path.yml', years=1)

if __name__ == '__main__':
    unittest.main()
