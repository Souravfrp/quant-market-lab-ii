"""Synthetic fixtures test causality; they are not market evidence."""
import unittest
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from src.run_ewma_experiment import fit_forecasts, target_windows, validate_panel
from src.validate_cutoff import EXPECTED_ETFS

class ExperimentTests(unittest.TestCase):
    def test_future_returns_cannot_change_forecast(self):
        rng=np.random.default_rng(7)
        dates=pd.bdate_range('2018-01-01',periods=900)
        r=pd.DataFrame(rng.normal(0,.01,(900,8)),index=dates,columns=EXPECTED_ETFS)
        origin=dates[800]; decays={'ewma':.94,'ridge_ewma':.97}
        expected,detail=fit_forecasts(r,origin,12,decays)
        changed=r.copy();changed.loc[changed.index>origin]*=100
        actual,_=fit_forecasts(changed,origin,12,decays)
        np.testing.assert_allclose(list(expected.values()),list(actual.values()),rtol=0,atol=1e-14)
        self.assertLessEqual(pd.Timestamp(detail['last_training_target_end']),origin)
        self.assertTrue(all(v>=0 for v in actual.values()))

    def test_calendar_and_retrospective_labels(self):
        # This is a deliberately limited calendar fixture, not an NYSE data source.
        sessions=pd.bdate_range('2026-08-31','2026-12-07').difference(pd.DatetimeIndex(['2026-09-07','2026-11-26']))
        now=datetime(2026,10,8,tzinfo=timezone.utc)
        windows=target_windows('2026-08-31',sessions,now)
        self.assertEqual([w['gap_sessions'] for w in windows],[0,21,43,63])
        self.assertTrue(all(w['status'].startswith('retrospective') for w in windows[:2]))
        self.assertTrue(all(w['status'].startswith('prospective') for w in windows[2:]))
        self.assertEqual(len(target_windows('2026-10-07',sessions,now)),2)

    def test_missing_session_and_later_price_are_rejected(self):
        sessions=pd.bdate_range('2019-01-01','2026-08-31')
        prices=pd.DataFrame(100.,index=sessions,columns=EXPECTED_ETFS)
        validate_panel(prices,'2026-08-31',sessions)
        with self.assertRaises(ValueError):validate_panel(prices.drop(sessions[50]),'2026-08-31',sessions)
        with self.assertRaises(ValueError):validate_panel(prices,'2026-08-28',sessions)

if __name__=='__main__':unittest.main()
