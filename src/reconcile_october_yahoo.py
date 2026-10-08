"""Reconcile the preserved October RMS evaluation against saved Yahoo adjusted prices."""
import json
from pathlib import Path
import pandas as pd
from src.evaluate_october_2026 import calculate_measures,score_forecasts
from src.validate_cutoff import sha256_file
ROOT=Path(__file__).resolve().parents[1]

def main():
    source=ROOT/'data/raw/yahoo_2026-10-08/october_adjusted_close.csv'
    provenance=json.loads(source.with_name('october_provenance.json').read_text())
    if sha256_file(source)!=provenance['input_sha256']:raise ValueError('Yahoo snapshot hash mismatch.')
    archive=ROOT/'forecasts/2026-09-30-v0.1'
    frozen=json.loads((archive/'manifest.json').read_text())
    if sha256_file(archive/'forecasts.csv')!=frozen['output_sha256']['forecasts.csv']:raise ValueError('Forecast archive hash mismatch.')
    yahoo=pd.read_csv(source,parse_dates=['Date']).set_index('Date').loc['2026-09-30':'2026-10-07']
    stock=pd.read_csv(ROOT/'results/evaluation_inputs/etf_october_2026_adjusted_close.csv',parse_dates=['Date']).set_index('Date')
    yahoo=yahoo[stock.columns]
    returns,profile=calculate_measures(yahoo);actual=float(profile.loc['SPY','five_return_rms_decimal'])
    scores=score_forecasts(pd.read_csv(archive/'forecasts.csv',float_precision='round_trip'),actual)
    comparison=[]
    for date in yahoo.index:
        for asset in yahoo.columns:
            comparison.append({'Date':str(date.date()),'asset':asset,'stock_analysis_adjusted_close':float(stock.loc[date,asset]),'yahoo_adjusted_close':float(yahoo.loc[date,asset]),'difference':float(yahoo.loc[date,asset]-stock.loc[date,asset]),'matches_when_rounded_to_cents':round(float(yahoo.loc[date,asset]),2)==float(stock.loc[date,asset])})
    output=ROOT/'results/october_2026_yahoo_reconciliation'
    if output.exists():raise FileExistsError('Reconciliation already exists; do not overwrite.')
    output.mkdir()
    for name,table,index in [('adjusted_close.csv',yahoo,True),('daily_log_returns.csv',returns,True),('etf_observed_profile.csv',profile,True),('forecast_errors.csv',scores,False),('source_comparison.csv',pd.DataFrame(comparison),False)]:
        table.to_csv(output/name,index=index,float_format='%.17g')
    previous=json.loads((ROOT/'results/october_2026/summary.json').read_text())['actual_rms_decimal']
    summary={'record_date':'2026-10-08','source':'Yahoo Finance saved chart API adjusted-close snapshot','october_6_spy_adjusted_close':float(yahoo.loc['2026-10-06','SPY']),'october_7_spy_adjusted_close':float(yahoo.loc['2026-10-07','SPY']),
        'actual_rms_decimal':actual,'stock_analysis_actual_rms_decimal':previous,'difference_in_rms_decimal':actual-previous,'closest_method':scores.loc[scores.absolute_error_decimal.idxmin(),'method'],
        'spy_six_prices_match_rounded_cents':all(row['matches_when_rounded_to_cents'] for row in comparison if row['asset']=='SPY'),
        'input_sha256':sha256_file(source),'frozen_forecast_sha256':sha256_file(archive/'forecasts.csv'),'source_sha256':sha256_file(Path(__file__)),
        'preservation':'Original forecasts and Stock Analysis evaluation remain unchanged; this is a separate full-precision Yahoo reconciliation.',
        'output_sha256':{p.name:sha256_file(p) for p in output.iterdir()}}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
