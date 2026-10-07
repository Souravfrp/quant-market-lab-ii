"""I check the partial-window calculation and keep missing outcomes unavailable."""
import unittest
import numpy as np
import pandas as pd
from src.plot_evaluation_status import partial_measures, EXPECTED, check_forecasts, ROOT

class PartialWindowTests(unittest.TestCase):
    def test_four_returns_and_lower_bound(self):
        known=np.array([.01,-.02,.03,-.04])
        prices=100*np.exp(np.r_[0,np.cumsum(known)])
        table,summary=partial_measures(pd.DataFrame({'SPY':prices},index=EXPECTED))
        np.testing.assert_allclose(table.log_return,known,rtol=0,atol=1e-14)
        self.assertAlmostEqual(summary['partial_four_return_rms'],np.sqrt(np.mean(known**2)),places=14)
        self.assertAlmostEqual(summary['five_return_rms_lower_bound'],np.sqrt(np.sum(known**2)/5),places=14)
        self.assertIsNone(summary['final_five_return_rms'])

    def test_incomplete_or_expanded_snapshot_is_rejected(self):
        prices=pd.DataFrame({'SPY':np.arange(100,105)},index=EXPECTED)
        with self.assertRaises(ValueError):partial_measures(prices.iloc[:-1])
        extra=pd.concat([prices,pd.DataFrame({'SPY':[105]},index=pd.to_datetime(['2026-10-07']))])
        with self.assertRaises(ValueError):partial_measures(extra)

    def test_changed_target_window_is_rejected(self):
        frame=pd.read_csv(ROOT/'forecasts/2026-09-30-v0.1/forecasts.csv')
        check_forecasts(frame)
        frame.loc[frame.target_month=='2026-10','target_end']='2026-10-06'
        with self.assertRaises(ValueError):check_forecasts(frame)

if __name__=='__main__':unittest.main()
