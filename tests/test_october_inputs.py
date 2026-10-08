import unittest
import numpy as np
from src.validate_october_inputs import read_prices, validate_prices

class OctoberInputTests(unittest.TestCase):
    def test_missing_duplicate_or_reordered_dates_rejected(self):
        p = read_prices()
        for bad in [p.iloc[:-1], p.iloc[::-1], p.iloc[[0,1,2,3,4,4]]]:
            with self.assertRaises(ValueError):
                validate_prices(bad)

    def test_bad_values_or_asset_schema_rejected(self):
        p = read_prices()
        for value in [0, -1, np.nan, np.inf]:
            bad = p.copy()
            bad.iloc[0,0] = value
            with self.assertRaises(ValueError):
                validate_prices(bad)
        with self.assertRaises(ValueError):
            validate_prices(p.drop(columns='TLT'))

if __name__ == '__main__':
    unittest.main()
