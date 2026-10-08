import unittest
import numpy as np
import pandas as pd
from src.ewma_signal import ewma_second_moment, ewma_rms, advance_second_moment

class EWMASignalTests(unittest.TestCase):
    def series(self, r):
        return pd.Series(r, index=pd.bdate_range('2020-01-01', periods=len(r)))

    def test_seed_and_constant_magnitude(self):
        r=self.series([.02,-.02]*30)
        v=ewma_second_moment(r,.94)
        self.assertTrue(v.iloc[:19].isna().all())
        np.testing.assert_allclose(v.iloc[19:],.0004)
        np.testing.assert_allclose(ewma_rms(r,.94).iloc[19:],.02)

    def test_impulse_decay_and_nonnegativity(self):
        r=self.series([0.]*20+[.1]+[0.]*10)
        v=ewma_second_moment(r,.9)
        np.testing.assert_allclose(v.iloc[20:],.001*.9**np.arange(11))
        self.assertTrue((v.dropna()>=0).all())

    def test_expanded_weights_and_incremental_update(self):
        r=self.series(np.linspace(-.03,.04,60)); decay=.8
        v=ewma_second_moment(r,decay)
        t=45; m=t-19
        expected=decay**m*np.mean(r.iloc[:20]**2)+(1-decay)*sum(decay**j*r.iloc[t-j]**2 for j in range(m))
        self.assertAlmostEqual(v.iloc[t],expected,places=15)
        self.assertAlmostEqual(advance_second_moment(v.iloc[-2],r.iloc[-1],decay),v.iloc[-1],places=15)

    def test_pandas_recursion_with_explicit_seed(self):
        r=self.series(np.linspace(-.03,.04,60));decay=.97
        seeded=pd.concat([pd.Series([np.mean(r.iloc[:20]**2)],index=[r.index[19]]),r.iloc[20:]**2])
        np.testing.assert_allclose(ewma_second_moment(r,decay).iloc[19:],seeded.ewm(alpha=1-decay,adjust=False).mean())

    def test_prefix_invariance(self):
        r=self.series(np.linspace(-.03,.04,60));changed=r.copy();changed.iloc[40:]=100
        np.testing.assert_allclose(ewma_second_moment(r,.94).iloc[:40],ewma_second_moment(changed,.94).iloc[:40],equal_nan=True)

    def test_invalid_inputs_and_short_prefix(self):
        r=self.series([.01]*30)
        for decay in [0,1,-1,np.nan]:
            with self.assertRaises(ValueError):ewma_second_moment(r,decay)
        with self.assertRaises(ValueError):ewma_second_moment(r.iloc[::-1],.94)
        bad=r.copy();bad.iloc[2]=np.nan
        with self.assertRaises(ValueError):ewma_second_moment(bad,.94)
        self.assertTrue(ewma_second_moment(r.iloc[:10],.94).isna().all())

if __name__=='__main__':unittest.main()
