"""I diagnose my existing risk experiment without fitting a new forecast model."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
 'data/raw/original_august_verified/adjusted_close.csv':'33b69eeda3f8b6c51f3e07c47ad037fd9ae4a700',
 'data/raw/yahoo_2026-10-08/october_adjusted_close.csv':'65d4d1c5fa668aa2a268fd7d83770c3d96c57a2e',
 'forecasts/2026-10-08-ewma-october/signals.csv':'4c8aca8385186d527c8802d8c907dd272a440bd1',
 'results/ewma_2026-10-08/august_known_outcomes.csv':'608dfc438c3bf9973b6a829c253014cb942ea3ec',
 'results/ewma_2026-10-08/cutoff_comparison.csv':'a7e7513d594fa57de20b04ae9028e71ccba8ca4c',
 'forecasts/2026-10-08-ewma-august-original-verified/historical_metrics.csv':'f1e564a99a991d7ba7e1333fd9069efd3b321d48',
}

def sample_acf(values, max_lag=40):
    """I use common-N autocovariances; direct work costs O(N * max_lag)."""
    x=np.asarray(values,dtype=float)
    if x.ndim!=1 or len(x)<2 or not np.isfinite(x).all():
        raise ValueError('Require at least two finite one-dimensional observations.')
    if not isinstance(max_lag,(int,np.integer)) or not 0<=max_lag<len(x):
        raise ValueError('Require an integer lag between zero and N-1.')
    z=x-x.mean();den=z@z
    if den==0:raise ValueError('ACF is undefined for a constant series.')
    return np.array([z[:len(z)-k]@z[k:]/den for k in range(max_lag+1)])

def five_return_labels(returns):
    """I return the overlapping five-return mean-square and RMS labels."""
    r=np.asarray(returns,float)
    if r.ndim!=1 or len(r)<5 or not np.isfinite(r).all():
        raise ValueError('Require at least five finite returns.')
    ms=np.convolve(r*r,np.ones(5)/5,mode='valid')
    return ms,np.sqrt(ms)

def main(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if output.exists():raise FileExistsError('I preserve outputs; choose a new --output directory.')
    provenance={}
    for rel,expected in INPUTS.items():
        b=(ROOT/rel).read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        if blob!=expected:raise ValueError('Input vintage mismatch: '+rel)
        provenance[rel]={'git_blob':blob,'sha256':hashlib.sha256(b).hexdigest()}
    output.mkdir(parents=True);D=output/'figures';D.mkdir()
    def save(fig,path):
        fig.savefig(path,metadata={'Date':None})
    plt.rcParams.update({'svg.hashsalt':'market-lab-ii-acf-v1','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
    original=pd.read_csv(ROOT/'data/raw/original_august_verified/adjusted_close.csv',index_col='Date',parse_dates=True)
    updated=pd.read_csv(ROOT/'data/raw/yahoo_2026-10-08/october_adjusted_close.csv',index_col='Date',parse_dates=True)
    r=np.log(original.SPY/original.SPY.shift()).dropna()
    ru=np.log(updated.SPY/updated.SPY.shift()).dropna()
    sig=pd.read_csv(ROOT/'forecasts/2026-10-08-ewma-october/signals.csv',index_col='Date',parse_dates=True)
    assert len(r)==2931 and r.index[-1]==pd.Timestamp('2026-08-31')
    assert ru.index[-1]==pd.Timestamp('2026-10-07')
    series={'Signed return':r,'Squared return':r*r,'Absolute return':abs(r)}
    a={name:sample_acf(x,40) for name,x in series.items()}
    print('Verified ACF:',{k:np.round(v[[1,2,5,20]],6).tolist() for k,v in a.items()})
    fig,axs=plt.subplots(1,3,figsize=(10.4,3.0),sharey=True)
    for ax,(name,v) in zip(axs,a.items()):
        ax.vlines(np.arange(1,41),0,v[1:],color='#267c91');ax.axhline(0,color='gray',lw=.7)
        band=1.96/np.sqrt(len(r));ax.axhspan(-band,band,color='#dbe6ed');ax.set_title(name);ax.set_xlabel('Lag (trading days)')
    axs[0].set_ylabel('Sample autocorrelation');fig.tight_layout();save(fig, D/'acf.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(10.4,3.2)); z=sig.loc['2026-08-03':'2026-10-07']
    ax.plot(z.index,100*z.rolling_20d_rms,label='Rolling 20-session RMS',color='#267c91');ax.plot(z.index,100*z.ewma_rms,label='EWMA RMS (decay 0.80)',color='#d47828')
    ax.axvline(pd.Timestamp('2026-08-31'),ls='--',color='gray');ax.axvline(pd.Timestamp('2026-09-30'),ls=':',color='gray')
    ax.set_ylabel('Daily RMS signal (%)');ax.legend(loc='upper left',fontsize=9);fig.autofmt_xdate();fig.tight_layout();save(fig, D/'signals.svg');plt.close(fig)
    known=pd.read_csv(ROOT/'results/ewma_2026-10-08/august_known_outcomes.csv');metrics=pd.read_csv(ROOT/'forecasts/2026-10-08-ewma-august-original-verified/historical_metrics.csv');future=pd.read_csv(ROOT/'results/ewma_2026-10-08/cutoff_comparison.csv')
    methods=['constant','rolling_20d_rms','ridge_expanding','ewma','ridge_ewma'];names=['Constant','Rolling RMS','Ridge','EWMA','Ridge + EWMA']
    fig,axs=plt.subplots(1,2,figsize=(10.4,3.2),sharey=True)
    for ax,month in zip(axs,['2026-09','2026-10']):
        t=known[known.target_month==month].set_index('method').loc[methods];ax.bar(np.arange(5),100*t.forecast_decimal,color=['#a2adb5','#267c91','#819c67','#d47828','#816b9b']);ax.axhline(100*t.actual_decimal.iloc[0],color='#242e39',ls='--',label='Observed RMS')
        ax.set_xticks(np.arange(5),names,rotation=25,ha='right',fontsize=8);ax.set_title(month+' first five returns');ax.legend(fontsize=8)
    axs[0].set_ylabel('Daily RMS (%)');fig.tight_layout();save(fig, D/'known.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(10.4,2.6));t=metrics.set_index('method').loc[methods];ax.barh(names[::-1],(100*t.mae).values[::-1],color='#267c91');ax.set_xlabel('MAE (percentage points; lower is better)');fig.tight_layout();save(fig, D/'historical.svg');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10.4,3.2),sharey=True)
    for ax,month in zip(axs,['2026-11','2026-12']):
        x=np.arange(5)
        for j,(cut,lab,col) in enumerate([('2026-08-31','August 31 reconstructed','#267c91'),('2026-10-07','October 7 update','#d47828')]):
            t=future[(future.target_month==month)&(future.information_cutoff==cut)].set_index('method').loc[methods];ax.bar(x+(j-.5)*.36,100*t.forecast_decimal,.36,label=lab,color=col)
        ax.set_xticks(x,names,rotation=25,ha='right',fontsize=8);ax.set_title(month+' first five returns');ax.legend(fontsize=7)
    axs[0].set_ylabel('Forecast daily RMS (%)');fig.tight_layout();save(fig, D/'future.svg');plt.close(fig)

    if len(original)!=2932 or len(updated)!=2958:
        raise ValueError('Unexpected price counts.')
    np.testing.assert_allclose(sig.spy_return.values,ru.values,rtol=1e-10,atol=1e-14)
    for month,start,end in [('2026-09','2026-09-01','2026-09-08'),('2026-10','2026-10-01','2026-10-07')]:
        target=ru.loc[start:end]
        if len(target)!=5:raise ValueError('Expected five target returns.')
        np.testing.assert_allclose(known.loc[known.target_month==month,'actual_decimal'],np.sqrt(np.mean(target**2)),rtol=1e-10)
    pd.DataFrame([{'series':name,'lag_sessions':k,'acf':value,'n':len(r)} for name,v in a.items() for k,value in enumerate(v)]).to_csv(output/'august_acf.csv',index=False,float_format='%.12g')
    ms,rms=five_return_labels(r)
    labels={'Mean square overlapping':ms,'RMS overlapping':rms,'Mean square non-overlapping':ms[::5],'RMS non-overlapping':rms[::5]}
    pd.DataFrame([{'series':name,'lag_in_labels':k,'acf':value,'n_labels':len(x)} for name,x in labels.items() for k,value in enumerate(sample_acf(x,10))]).to_csv(output/'target_overlap_acf.csv',index=False,float_format='%.12g')
    fig,axes=plt.subplots(1,2,figsize=(10.4,3.2),sharey=True)
    for ax,stride,label in zip(axes,[1,5],['Every day (overlapping)','Every fifth day (non-overlapping)']):
        ax.plot(np.arange(1,11),sample_acf(ms[::stride],10)[1:],'o-',label='Mean square')
        ax.plot(np.arange(1,11),sample_acf(rms[::stride],10)[1:],'s-',label='RMS')
        ax.set_title(label);ax.set_xlabel('Lag in labels'+(' (5 sessions each)' if stride==5 else ' (1 session each)'));ax.legend(fontsize=8)
    axes[0].set_ylabel('Sample autocorrelation');fig.tight_layout();save(fig,D/'target_overlap.svg');plt.close(fig)
    manifest={'created_at_utc':datetime.now(timezone.utc).isoformat(),'source_repository_commit':'9d686a085f095f857af3d24ecf1a0df439294b16','acf_cutoff':'2026-08-31','observed_extension_cutoff':'2026-10-07','original_returns':len(r),'scope':'Historical diagnostics and existing-output plots; no new forecasting model or retuning','inputs':provenance,'versions':{'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__},'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    manifest['outputs_sha256']={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.rglob('*')) if p.is_file()}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('I saved six figures and two ACF tables in',output)
    print('No forecast archive was changed. PACF, Ljung-Box, AR and residual studies are outside this implementation.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'results/autocorrelation_2026-10-10/rebuilt')
    main(parser.parse_args().output)
