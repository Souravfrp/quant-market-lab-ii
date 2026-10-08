"""Score the original October forecasts; no model fitting or live data access."""
import json
import numpy as np
import pandas as pd
from src.validate_october_inputs import ROOT, INPUT, DATES, read_prices, sha256

ARCHIVE = ROOT / 'forecasts/2026-09-30-v0.1'
OUTPUT = ROOT / 'results/october_2026'
METHODS = ['ridge_expanding', 'constant', 'rolling_20d_rms']

def calculate_measures(prices):
    # Validation also applies when called from a notebook or test.
    from src.validate_october_inputs import validate_prices
    validate_prices(prices)
    returns = np.log(prices / prices.shift(1)).iloc[1:]
    rms = np.sqrt((returns ** 2).mean())
    profile = pd.DataFrame({
        'five_return_rms_decimal': rms,
        'mean_daily_log_return_decimal': returns.mean(),
        'population_daily_log_return_sd_decimal': returns.std(ddof=0),
        'window_simple_return_decimal': prices.iloc[-1] / prices.iloc[0] - 1,
    })
    profile.index.name = 'asset'
    return returns, profile

def score_forecasts(frame, actual):
    if not np.isfinite(actual) or actual < 0:
        raise ValueError('Actual RMS must be finite and nonnegative.')
    selected = frame.loc[frame.target_month.eq('2026-10')].copy()
    if len(selected) != 3 or set(selected.method) != set(METHODS):
        raise ValueError('Require exactly the three original October methods.')
    expected = {'asset':'SPY', 'information_cutoff':'2026-08-31',
                'gap_sessions':21, 'target_start':'2026-10-01',
                'target_end':'2026-10-07', 'return_anchor_date':'2026-09-30',
                'horizon_sessions':5, 'target':'five_day_daily_log_return_rms',
                'evaluation_status':'prospective'}
    for key, value in expected.items():
        if not selected[key].eq(value).all():
            raise ValueError(f'Frozen target mismatch: {key}')
    values = selected.forecast_decimal.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Forecasts must be finite and nonnegative.')
    selected['actual_decimal'] = actual
    selected['error_decimal'] = selected.forecast_decimal - actual
    selected['absolute_error_decimal'] = selected.error_decimal.abs()
    selected['squared_error_decimal'] = selected.error_decimal ** 2
    return selected.set_index('method').loc[METHODS].reset_index()

def load_and_evaluate():
    provenance = INPUT.with_name('etf_october_2026_provenance.json')
    if sha256(INPUT) != json.loads(provenance.read_text())['input_sha256']:
        raise ValueError('Evaluation input hash mismatch.')
    manifest = json.loads((ARCHIVE / 'manifest.json').read_text())
    forecast_path = ARCHIVE / 'forecasts.csv'
    if sha256(forecast_path) != manifest['output_sha256']['forecasts.csv']:
        raise ValueError('Frozen forecast hash mismatch.')
    prices = read_prices()
    returns, profile = calculate_measures(prices)
    actual = float(profile.loc['SPY', 'five_return_rms_decimal'])
    scores = score_forecasts(pd.read_csv(forecast_path, float_precision='round_trip'), actual)
    # This substitution quantifies a disagreement; it is not a second adjusted-price audit.
    alternative = prices.copy()
    alternative.loc[DATES[-1], 'SPY'] = 777.30
    _, other_profile = calculate_measures(alternative)
    other_actual = float(other_profile.loc['SPY', 'five_return_rms_decimal'])
    other_scores = score_forecasts(pd.read_csv(forecast_path, float_precision='round_trip'), other_actual)
    summary = {
        'evaluation_record_date':'2026-10-08',
        'information_cutoff':'2026-08-31',
        'return_anchor_date':'2026-09-30',
        'return_dates':[d.strftime('%Y-%m-%d') for d in DATES[1:]],
        'n_returns':5, 'asset':'SPY',
        'actual_rms_decimal':actual,
        'closest_method_this_window':scores.loc[scores.absolute_error_decimal.idxmin(), 'method'],
        'input_sha256':sha256(INPUT),
        'provenance_sha256':sha256(provenance),
        'forecast_sha256':sha256(forecast_path),
        'frozen_manifest_sha256':sha256(ARCHIVE / 'manifest.json'),
        'data_status':'Complete five-return window on a rounded public snapshot; original-provider reconciliation remains open.',
        'sensitivity':{'alternative_last_spy_close':777.30,
                      'alternative_rms_decimal':other_actual,
                      'change_in_rms_decimal':other_actual-actual,
                      'closest_method':other_scores.loc[other_scores.absolute_error_decimal.idxmin(), 'method'],
                      'interpretation':'Last-price substitution only; not a reconciled adjusted-close actual.'},
        'interpretation':'One window gives one error per method, not evidence of persistent superiority or trading profitability.',
    }
    return prices, returns, profile, scores, summary

def main():
    _, returns, profile, scores, summary = load_and_evaluate()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    returns.to_csv(OUTPUT / 'daily_log_returns.csv', index_label='Date', float_format='%.17g')
    profile.to_csv(OUTPUT / 'etf_observed_profile.csv', float_format='%.17g')
    scores.to_csv(OUTPUT / 'forecast_errors.csv', index=False, float_format='%.17g')
    (OUTPUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
