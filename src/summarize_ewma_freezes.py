"""Compare two saved cutoffs and score already-known windows retrospectively."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.validate_cutoff import sha256_file

METHODS=['constant','rolling_20d_rms','ridge_expanding','ewma','ridge_ewma']

def summarize(august,october,prices_path,output):
    if output.exists():raise FileExistsError('Choose a new summary directory.')
    for folder in [august,october]:
        manifest=json.loads((folder/'manifest.json').read_text())
        for name,digest in manifest['output_sha256'].items():
            if sha256_file(folder/name)!=digest:raise ValueError('Frozen output hash mismatch.')
    prices=pd.read_csv(prices_path,parse_dates=['Date']).set_index('Date')
    oct_manifest=json.loads((october/'manifest.json').read_text())
    if sha256_file(prices_path)!=oct_manifest['input_sha256']:raise ValueError('Use the exact October snapshot.')
    returns=np.log(prices.SPY/prices.SPY.shift(1)).dropna()
    a=pd.read_csv(august/'forecasts.csv');o=pd.read_csv(october/'forecasts.csv')
    rows=[]
    for month,b in a.groupby('target_month'):
        start,end=pd.Timestamp(b.target_start.iloc[0]),pd.Timestamp(b.target_end.iloc[0])
        if end>returns.index[-1]:continue
        window=returns.loc[start:end]
        if len(window)!=5:raise ValueError('Incomplete observed target.')
        actual=float(np.sqrt(np.mean(window**2)))
        for row in b.itertuples():
            rows.append({'target_month':month,'target_start':str(start.date()),'target_end':str(end.date()),
                'method':row.method,'forecast_decimal':row.forecast_decimal,'actual_decimal':actual,
                'error':row.forecast_decimal-actual,'absolute_error':abs(row.forecast_decimal-actual),
                'status':'Retrospective: computed after outcomes were known; reconstructed input'})
    known=pd.DataFrame(rows);output.mkdir(parents=True)
    known.to_csv(output/'august_known_outcomes.csv',index=False,float_format='%.17g')
    combined=pd.concat([a.assign(cutoff_label='August 31 reconstructed'),o.assign(cutoff_label='October 7')])
    combined.to_csv(output/'cutoff_comparison.csv',index=False,float_format='%.17g')
    fig,axes=plt.subplots(1,2,figsize=(13,5),sharey=True)
    width=.15;x=np.arange(2)
    for ax,month in zip(axes,['2026-11','2026-12']):
        for i,method in enumerate(METHODS):
            b=combined.loc[(combined.target_month==month)&(combined.method==method)]
            ax.bar(x+(i-2)*width,100*b.forecast_decimal,width,label=method)
        ax.set(xticks=x,xticklabels=['Aug 31 reconstructed','Oct 7 update'],title=month+' first five sessions',ylabel='Predicted daily RMS (%)')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=5,fontsize=9)
    fig.suptitle('Prospective November/December forecasts — same target, different information cutoffs')
    fig.tight_layout(rect=(0,.07,1,1));fig.savefig(output/'future_cutoff_comparison.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,5),sharey=True)
    for ax,(month,b) in zip(axes,known.groupby('target_month')):
        ax.bar(b.method,100*b.forecast_decimal)
        ax.axhline(100*b.actual_decimal.iloc[0],color='black',linestyle='--',label='Observed five-session RMS')
        ax.set(title=month,ylabel='Daily RMS (%)');ax.tick_params(axis='x',labelrotation=22);ax.legend(fontsize=8)
    fig.suptitle('Retrospective August-cutoff reconstruction — September/October outcomes were already known')
    fig.tight_layout();fig.savefig(output/'retrospective_known_outcomes.png',dpi=160);plt.close(fig)
    (output/'manifest.json').write_text(json.dumps({'input_price_sha256':sha256_file(prices_path),
        'august_manifest_sha256':sha256_file(august/'manifest.json'),'october_manifest_sha256':sha256_file(october/'manifest.json'),
        'source_sha256':sha256_file(Path(__file__)),'output_sha256':{p.name:sha256_file(p) for p in output.iterdir()}},indent=2)+'\n')
    print(known.to_string(index=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['august','october','prices','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();summarize(a.august,a.october,a.prices,a.output)
