"""I check the estimator and the precise overlap statement."""
import unittest
import numpy as np
from src.autocorrelation_analysis import sample_acf, five_return_labels

class TestAutocorrelationAnalysis(unittest.TestCase):
    def test_acf_matches_independent_double_loop(self):
        x=np.array([1.,3.,-2.,5.,4.,-1.]);z=x-x.mean()
        expected=[sum(z[i]*z[i+k] for i in range(len(z)-k))/sum(t*t for t in z) for k in range(4)]
        np.testing.assert_allclose(sample_acf(x,3),expected)
        self.assertEqual(sample_acf(x,3)[0],1.)
    def test_invalid_inputs(self):
        for x,k in [([1.,1.,1.],1),([1.,float('nan')],1),([1.,2.],2),([1.,2.],-1),([1.,2.],.5)]:
            with self.assertRaises(ValueError):sample_acf(x,k)
    def test_targets_match_explicit_slices(self):
        x=np.array([1.,-2.,3.,4.,-5.,6.,7.]);ms,rms=five_return_labels(x)
        expected=np.array([np.mean(x[i:i+5]**2) for i in range(3)])
        np.testing.assert_allclose(ms,expected);np.testing.assert_allclose(rms,np.sqrt(expected))
    def test_overlap_formula_for_mean_square_only(self):
        r=np.random.default_rng(2026).normal(size=200000);ms,_=five_return_labels(r)
        np.testing.assert_allclose(sample_acf(ms,5)[1:],[.8,.6,.4,.2,0.],atol=.025)

if __name__=='__main__':unittest.main()
