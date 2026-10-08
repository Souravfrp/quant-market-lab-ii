"""Causal second-moment EWMA with an explicit observed-return seed."""
import numpy as np
import pandas as pd

def ewma_second_moment(returns, decay, seed_size=20):
    if not 0 < decay < 1 or not np.isfinite(decay):
        raise ValueError('Decay must be finite and strictly between zero and one.')
    if isinstance(seed_size, bool) or not isinstance(seed_size, int) or seed_size < 1:
        raise ValueError('Seed size must be a positive integer.')
    if not isinstance(returns, pd.Series):
        raise TypeError('Returns must be a pandas Series with chronological dates.')
    if returns.index.has_duplicates or not returns.index.is_monotonic_increasing:
        raise ValueError('Return dates must be unique and chronological.')
    r = returns.to_numpy(dtype=float)
    if not np.isfinite(r).all():
        raise ValueError('Returns must be finite; missing observations are not filled.')
    result = np.full(len(r), np.nan)
    if len(r) >= seed_size:
        result[seed_size-1] = np.mean(r[:seed_size] ** 2)
        for i in range(seed_size, len(r)):
            result[i] = decay * result[i-1] + (1-decay) * r[i] ** 2
    return pd.Series(result, index=returns.index, name='ewma_second_moment')

def ewma_rms(returns, decay, seed_size=20):
    return np.sqrt(ewma_second_moment(returns, decay, seed_size)).rename('ewma_rms')

def advance_second_moment(state, new_return, decay):
    if not (np.isfinite(state) and state >= 0 and np.isfinite(new_return)
            and np.isfinite(decay) and 0 < decay < 1):
        raise ValueError('Require a finite nonnegative state, finite return and valid decay.')
    return decay * state + (1-decay) * new_return ** 2
