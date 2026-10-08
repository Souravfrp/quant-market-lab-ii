"""Validate my six-price evaluation snapshot without changing training data."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ['SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'USO', 'EEM', 'VNQ']
DATES = pd.to_datetime(['2026-09-30', '2026-10-01', '2026-10-02',
                        '2026-10-05', '2026-10-06', '2026-10-07'])
INPUT = ROOT / 'results/evaluation_inputs/etf_october_2026_adjusted_close.csv'

def validate_prices(frame):
    if list(frame.columns) != ASSETS or not frame.index.equals(DATES):
        raise ValueError('Require eight assets and exactly six chronological price dates.')
    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError('Adjusted prices must be finite and strictly positive.')
    return frame

def read_prices():
    return validate_prices(pd.read_csv(INPUT, index_col='Date', parse_dates=True))

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    prices = read_prices()
    provenance = json.loads(INPUT.with_name('etf_october_2026_provenance.json').read_text())
    if sha256(INPUT) != provenance['input_sha256']:
        raise ValueError('Evaluation snapshot no longer matches its provenance hash.')
    print(f'Validated {len(prices)} price dates x {len(ASSETS)} ETFs; five returns available.')

if __name__ == '__main__':
    main()
