"""Validate, compare and freeze EWMA experiments using supplied real data."""
import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from src.ewma_signal import ewma_rms
from src.freeze_forecasts import features_from_returns, delayed_target
from src.validate_cutoff import EXPECTED_ETFS, load_price_panel, sha256_file

ROOT=Path(__file__).resolve().parents[1]
GRID=(.80,.90,.94,.97,.99)
MIN_TRAIN=504
WINDOWS=(('2026-09','2026-08-31','2026-09-01','2026-09-08'),
         ('2026-10','2026-09-30','2026-10-01','2026-10-07'),
         ('2026-11','2026-10-30','2026-11-02','2026-11-06'),
         ('2026-12','2026-11-30','2026-12-01','2026-12-07'))

def load_sessions(path):
    sessions=pd.DatetimeIndex(pd.to_datetime(pd.read_csv(path)['Date'],errors='raise'))
    if (sessions.hasnans or sessions.has_duplicates or not sessions.is_monotonic_increasing
        or sessions.tz is not None or not sessions.equals(sessions.normalize())):
        raise ValueError('Calendar must contain unique chronological daily session dates.')
    return sessions

def validate_panel(prices,cutoff,sessions):
    cutoff=pd.Timestamp(cutoff)
    if (prices.empty or prices.columns.has_duplicates or set(prices.columns)!=set(EXPECTED_ETFS)
        or prices.index.hasnans or prices.index.has_duplicates
        or not prices.index.is_monotonic_increasing or prices.index.tz is not None
        or not prices.index.equals(prices.index.normalize())):
        raise ValueError('Require chronological daily dates and exactly the eight ETFs.')
    if prices.index[-1]!=cutoff:
        raise ValueError('Input must end exactly at the requested cutoff; do not silently slice later data.')
    expected=sessions[(sessions>=prices.index[0])&(sessions<=cutoff)]
    if not prices.index.equals(expected):
        raise ValueError('Price dates differ from the supplied complete session calendar.')
    prices=prices.loc[:,list(EXPECTED_ETFS)].apply(pd.to_numeric,errors='raise')
    if not np.isfinite(prices.to_numpy()).all() or (prices<=0).any().any():
        raise ValueError('Prices must be finite, positive and complete.')
    if prices.index[0]>pd.Timestamp('2020-01-01'):
        raise ValueError('Earlier history is required for the predeclared 2021–2022 validation.')
    return prices

def fit_forecasts(returns,origin,gap,decays):
    # All signal states use the same observed-return seed and full causal prefix.
    features=features_from_returns(returns)
    target,ends=delayed_target(returns.SPY,gap)
    origin=pd.Timestamp(origin)
    eligible=features.index[(target.reindex(features.index).notna()) &
                            (ends.reindex(features.index)<=origin)]
    if len(eligible)<MIN_TRAIN:raise ValueError('Insufficient completed training labels.')
    if origin not in features.index:raise ValueError('Forecast origin has no complete features.')
    def ridge_fit(x):
        model=make_pipeline(StandardScaler(),Ridge(alpha=1.,solver='svd'))
        model.fit(x.loc[eligible],target.loc[eligible])
        raw=float(model.predict(x.loc[[origin]])[0])
        scaler=model.named_steps['standardscaler']; ridge=model.named_steps['ridge']
        return max(0.,raw),{'raw_forecast':raw,'feature_names':list(x.columns),
            'forecast_features':x.loc[origin].tolist(),'scaler_mean':scaler.mean_.tolist(),
            'scaler_scale':scaler.scale_.tolist(),'coefficients':ridge.coef_.tolist(),
            'intercept':float(ridge.intercept_)}
    base,base_detail=ridge_fit(features)
    augmented_signal=ewma_rms(returns.SPY,decays['ridge_ewma'])
    augmented=features.assign(ewma_rms=augmented_signal.reindex(features.index))
    if augmented.loc[eligible].isna().any().any():raise ValueError('Unavailable training signal.')
    augmented_prediction,aug_detail=ridge_fit(augmented)
    standalone=ewma_rms(returns.SPY,decays['ewma'])
    recent=returns.loc[:origin,'SPY'].iloc[-20:]
    values={'constant':float(target.loc[eligible].mean()),
            'rolling_20d_rms':float(np.sqrt(np.mean(recent**2))),
            'ridge_expanding':base,'ewma':float(standalone.loc[origin]),
            'ridge_ewma':augmented_prediction}
    details={'training_examples':len(eligible),'last_training_target_end':str(ends.loc[eligible].max().date()),
             'last_training_origin':str(eligible[-1].date()),'ridge_expanding':base_detail,
             'ridge_ewma':aug_detail,'selected_decays':decays}
    return values,details

def monthly_comparison(returns,decays,start,end):
    origins=returns.groupby(returns.index.to_period('M')).tail(1).index
    rows=[]
    for origin in origins:
        pos=returns.index.get_loc(origin)
        if pos+5>=len(returns):continue
        endpoint=returns.index[pos+5]
        if not pd.Timestamp(start)<=endpoint<=pd.Timestamp(end):continue
        values,_=fit_forecasts(returns,origin,0,decays)
        actual=float(np.sqrt(np.mean(returns.SPY.iloc[pos+1:pos+6]**2)))
        for method,value in values.items():
            rows.append({'origin':str(origin.date()),'target_start':str(returns.index[pos+1].date()),
                         'target_end':str(endpoint.date()),'method':method,'forecast':value,'actual':actual,
                         'error':value-actual,'absolute_error':abs(value-actual)})
    if not rows:raise ValueError('No eligible historical windows.')
    return pd.DataFrame(rows)

def metrics(table):
    rows=[]
    for method,b in table.groupby('method'):
        rows.append({'method':method,'n':len(b),'mae':float(b.absolute_error.mean()),
                     'rmse':float(np.sqrt(np.mean(b.error**2))),'mean_error':float(b.error.mean())})
    return pd.DataFrame(rows)

def select_decays(returns):
    rows=[]
    for decay in GRID:
        comparison=monthly_comparison(returns,{'ewma':decay,'ridge_ewma':decay},'2021-01-01','2022-12-31')
        for method in ['ewma','ridge_ewma']:
            b=comparison.loc[comparison.method==method]
            rows.append({'method':method,'decay':decay,'n':len(b),'mae':float(b.absolute_error.mean())})
    scores=pd.DataFrame(rows);selected={}
    for method,b in scores.groupby('method'):
        # The tie rule is numeric rounding to 12 decimal places of MAE.
        rounded=b.mae.round(12);minimum=rounded.min()
        selected[method]=float(b.loc[rounded.eq(minimum),'decay'].max())
    return selected,scores

def target_windows(cutoff,sessions,now):
    cutoff=pd.Timestamp(cutoff);rows=[]
    for month,anchor,start,end in WINDOWS:
        if pd.Timestamp(anchor)<cutoff:continue
        dates=sessions[(sessions>=pd.Timestamp(start))&(sessions<=pd.Timestamp(end))]
        if len(dates)!=5 or dates[0]!=pd.Timestamp(start) or dates[-1]!=pd.Timestamp(end):
            raise ValueError('Supplied calendar disagrees with target window.')
        if sessions.get_loc(pd.Timestamp(start))-1!=sessions.get_loc(pd.Timestamp(anchor)):
            raise ValueError('Anchor is not the session immediately before target.')
        gap=int(sessions.get_loc(pd.Timestamp(start))-sessions.get_loc(cutoff)-1)
        boundary=datetime.fromisoformat(anchor+'T16:00:00').replace(tzinfo=ZoneInfo('America/New_York'))
        status='prospective_pending_publication' if now<boundary else 'retrospective_created_after_anchor'
        rows.append({'target_month':month,'return_anchor_date':anchor,'target_start':start,
                     'target_end':end,'gap_sessions':gap,'status':status})
    return rows

def run(data,calendar,cutoff,output,provenance,require_original_august=False):
    if output.exists():raise FileExistsError('Choose a new output directory; never overwrite a freeze.')
    if cutoff not in ['2026-08-31','2026-10-07']:raise ValueError('This experiment supports the two documented cutoffs.')
    sessions=load_sessions(calendar);prices=validate_panel(load_price_panel(data),cutoff,sessions)
    source=json.loads(provenance.read_text())
    required=['price_source','price_column','retrieved_at_utc','input_sha256','calendar_source']
    if any(not source.get(k) for k in required):raise ValueError('Incomplete provenance.')
    if source['input_sha256']!=sha256_file(data):raise ValueError('Input differs from provenance.')
    if require_original_august:
        original=json.loads((ROOT/'forecasts/2026-09-30-v0.1/manifest.json').read_text())
        if cutoff!='2026-08-31' or sha256_file(data)!=original['input_sha256']:
            raise ValueError('August input does not match the original frozen snapshot.')
    returns=np.log(prices/prices.shift(1)).iloc[1:]
    # Selection is explicitly restricted to data through December 2022.
    selected,selection=select_decays(returns.loc[:'2022-12-31'])
    assessment=monthly_comparison(returns,selected,'2023-01-01','2026-08-31')
    now=datetime.now(timezone.utc);windows=target_windows(cutoff,sessions,now)
    records=[];models=[]
    for window in windows:
        values,detail=fit_forecasts(returns,pd.Timestamp(cutoff),window['gap_sessions'],selected)
        models.append({**window,**detail})
        for method,value in values.items():
            records.append({**window,'information_cutoff':cutoff,'asset':'SPY','method':method,
                            'forecast_decimal':value,'horizon_sessions':5,'created_at_utc':now.isoformat()})
    forecasts=pd.DataFrame(records)
    signals=pd.DataFrame({'spy_return':returns.SPY,'rolling_20d_rms':np.sqrt((returns.SPY**2).rolling(20).mean()),
                         'ewma_rms':ewma_rms(returns.SPY,selected['ewma']),
                         'ridge_ewma_signal':ewma_rms(returns.SPY,selected['ridge_ewma'])})
    output.mkdir(parents=True)
    for name,table in [('selection_scores.csv',selection),('historical_comparison.csv',assessment),
                       ('historical_metrics.csv',metrics(assessment)),('forecasts.csv',forecasts)]:
        table.to_csv(output/name,index=False,float_format='%.17g')
    signals.to_csv(output/'signals.csv',index_label='Date',float_format='%.17g')
    (output/'models.json').write_text(json.dumps(models,indent=2,allow_nan=False)+'\n')
    manifest={'created_at_utc':now.isoformat(),'information_cutoff':cutoff,'input_sha256':sha256_file(data),
        'calendar_sha256':sha256_file(calendar),'provenance':source,'selected_decays':selected,'grid':GRID,
        'seed_size':20,'tie_rule':'Round validation MAE to 12 decimals, then prefer larger decay.',
        'selection_target_endpoints':['2021-01-01','2022-12-31'],
        'assessment_target_endpoints':['2023-01-01','2026-08-31'],
        'assessment_status':'Development-aware historical comparison; not untouched prospective evidence.',
        'delayed_gap_note':'Decay selected at gap zero is transferred to delayed windows; separate lead-time superiority is not established.',
        'publication_note':'Creation time is not publication proof. GitHub publication must precede the target anchoring close.',
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__},
        'source_sha256':{p:sha256_file(ROOT/p) for p in ['src/ewma_signal.py','src/run_ewma_experiment.py','src/freeze_forecasts.py']},
        'output_sha256':{p.name:sha256_file(p) for p in output.iterdir()}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    print(forecasts[['target_month','method','forecast_decimal','status']].to_string(index=False))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['data','calendar','output','provenance']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cutoff',required=True,choices=['2026-08-31','2026-10-07'])
    p.add_argument('--require-original-august',action='store_true')
    a=p.parse_args();run(a.data,a.calendar,a.cutoff,a.output,a.provenance,a.require_original_august)

if __name__=='__main__':main()
