import unittest
import numpy as np
import pandas as pd
from src.validate_october_inputs import ASSETS, DATES, read_prices
from src.evaluate_october_2026 import ARCHIVE, calculate_measures, score_forecasts, load_and_evaluate

class OctoberEvaluationTests(unittest.TestCase):
    def test_known_returns_and_rms_not_demeaned_sd(self):
        r = np.array([.01, -.02, .03, -.04, .05])
        p = 100 * np.exp(np.r_[0, np.cumsum(r)])
        frame = pd.DataFrame({a:p for a in ASSETS}, index=DATES)
        returns, profile = calculate_measures(frame)
        np.testing.assert_allclose(returns.SPY, r, atol=1e-14, rtol=0)
        self.assertAlmostEqual(profile.loc['SPY','five_return_rms_decimal'], np.sqrt(np.mean(r*r)), places=14)
        self.assertAlmostEqual(profile.loc['SPY','population_daily_log_return_sd_decimal'], np.std(r), places=14)
        self.assertNotAlmostEqual(np.sqrt(np.mean(r*r)), np.std(r), places=8)

    def test_uniform_price_rescaling_preserves_returns(self):
        p = read_prices()
        r, profile = calculate_measures(p)
        scaled, scaled_profile = calculate_measures(p * np.arange(1,9))
        np.testing.assert_allclose(r, scaled, atol=1e-14, rtol=0)
        np.testing.assert_allclose(profile, scaled_profile, atol=1e-14, rtol=0)

    def test_scoring_sign_absolute_error_and_window_guards(self):
        f = pd.read_csv(ARCHIVE / 'forecasts.csv')
        actual = .01
        scores = score_forecasts(f, actual)
        np.testing.assert_allclose(scores.error_decimal, scores.forecast_decimal-actual)
        np.testing.assert_allclose(scores.absolute_error_decimal, abs(scores.forecast_decimal-actual))
        changed = f.copy()
        changed.loc[changed.target_month.eq('2026-10'), 'target_end'] = '2026-10-06'
        with self.assertRaises(ValueError):
            score_forecasts(changed, actual)
        with self.assertRaises(ValueError):
            score_forecasts(f.loc[~((f.target_month=='2026-10') & (f.method=='constant'))], actual)

    def test_snapshot_calculation_and_price_disagreement(self):
        p, r, _, scores, summary = load_and_evaluate()
        independent = sum(float(np.log(p.SPY.iloc[i]/p.SPY.iloc[i-1]))**2 for i in range(1,6))**.5 / np.sqrt(5)
        self.assertAlmostEqual(summary['actual_rms_decimal'], independent, places=14)
        self.assertEqual(len(r), 5)
        self.assertEqual(len(scores), 3)
        self.assertEqual(summary['closest_method_this_window'], 'rolling_20d_rms')
        self.assertEqual(summary['sensitivity']['closest_method'], 'rolling_20d_rms')
        self.assertLess(summary['sensitivity']['change_in_rms_decimal'], 0)

if __name__ == '__main__':
    unittest.main()
