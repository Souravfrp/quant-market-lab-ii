"""I check target timing and that later observations cannot alter a forecast."""

import unittest

import numpy as np
import pandas as pd

from src.freeze_forecasts import delayed_target, features_from_returns, fit_at_origin


class ForecastTimingTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(23)
        self.returns = pd.DataFrame(rng.normal(0, .01, (900, 8)),
                                   index=pd.bdate_range("2020-01-01", periods=900),
                                   columns=["SPY", "QQQ", "IWM", "TLT", "GLD", "USO", "EEM", "VNQ"])

    def test_explicit_target_slices_and_unavailable_tail(self):
        spy = self.returns.SPY
        for gap in (0, 21, 43, 63):
            y, end = delayed_target(spy, gap)
            expected = np.sqrt(np.mean(spy.iloc[101+gap:106+gap].to_numpy() ** 2))
            self.assertAlmostEqual(y.iloc[100], expected, places=15)
            self.assertEqual(end.iloc[100], spy.index[105+gap])
            self.assertTrue(y.iloc[-(gap+5):].isna().all())

    def test_prefix_invariance_and_completed_labels(self):
        origin = self.returns.index[750]
        changed = self.returns.copy()
        changed.loc[changed.index > origin] *= 1000
        prefix = self.returns.loc[:origin]
        for gap in (0, 21, 43, 63):
            a, detail = fit_at_origin(self.returns, features_from_returns(self.returns), origin, gap)
            b, _ = fit_at_origin(changed, features_from_returns(changed), origin, gap)
            c, _ = fit_at_origin(prefix, features_from_returns(prefix), origin, gap)
            np.testing.assert_allclose(list(a.values()), list(b.values()), rtol=0, atol=1e-14)
            np.testing.assert_allclose(list(a.values()), list(c.values()), rtol=0, atol=1e-14)
            self.assertLessEqual(pd.Timestamp(detail["last_training_target_end"]), origin)
            self.assertEqual(pd.Timestamp(detail["last_training_origin"]), self.returns.index[750-gap-5])

    def test_rms_target_is_not_demeaned_standard_deviation(self):
        spy = pd.Series(.02, index=self.returns.index)
        target, _ = delayed_target(spy, 21)
        self.assertAlmostEqual(target.iloc[0], .02)


if __name__ == "__main__":
    unittest.main()
