"""Rebuild my completed October figures from the saved evaluation snapshot."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src.evaluate_october_2026 import load_and_evaluate, ROOT, METHODS

LABELS = ['Ridge', 'Constant', 'Rolling-20 RMS']
COLORS = ['#2563eb', '#d97706', '#0f766e']

def style(ax):
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='y', alpha=.15)
    ax.set_axisbelow(True)

def main():
    _, returns, profile, scores, summary = load_and_evaluate()
    plt.rcParams.update({'font.size':11, 'axes.titlesize':13, 'axes.titleweight':'bold'})
    out = ROOT / 'results/figures'
    out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2,2,figsize=(14,9))
    fig.suptitle('October baseline: the five-session outcome is now observable',fontsize=19,fontweight='bold',y=.98)
    fig.text(.5,.925,'SPY target: Oct 1, 2, 5, 6, 7 • Frozen inputs: Aug 31 • Evaluation recorded: Oct 8, 2026',ha='center',color='#475569')
    ax = axes[0,0]
    daily = 100*returns.SPY.to_numpy()
    ax.bar(np.arange(5),daily,color=['#0f766e' if v>=0 else '#b45309' for v in daily])
    for i,v in enumerate(daily):
        ax.annotate(f'{v:+.3f}%',(i,v),xytext=(0,7 if v>=0 else -15),textcoords='offset points',ha='center',fontsize=10)
    ax.set(xticks=np.arange(5),xticklabels=['Oct 1','Oct 2','Oct 5','Oct 6','Oct 7'],ylabel='Daily log return (%)',title='Five observed returns, with their signs',ylim=(-.4,.9))
    ax.axhline(0,color='#64748b',lw=.8)
    ax=axes[0,1]
    values=100*scores.forecast_decimal.to_numpy()
    ax.bar(np.arange(3),values,color=COLORS,width=.6)
    actual=100*summary['actual_rms_decimal']
    ax.axhline(actual,color='#111827',lw=2,label=f'Observed RMS: {actual:.4f}%')
    for i,v in enumerate(values):ax.text(i,v+.025,f'{v:.4f}%',ha='center')
    ax.set(xticks=np.arange(3),xticklabels=LABELS,ylabel='Five-return daily RMS (%)',title='Original forecasts compared with the outcome',ylim=(0,1.05))
    ax.legend(loc='upper left',fontsize=10)
    ax=axes[1,0]
    errors=100*scores.absolute_error_decimal.to_numpy()
    ax.bar(np.arange(3),errors,color=COLORS,width=.6)
    for i,v in enumerate(errors):ax.text(i,v+.009,f'{v:.4f} pp',ha='center')
    ax.set(xticks=np.arange(3),xticklabels=LABELS,ylabel='Absolute error (percentage points)',title='Rolling-20 was closest in this window',ylim=(0,.44))
    ax=axes[1,1]
    history=pd.read_csv(ROOT/'results/figure_values.csv')
    months=['2026-05','2026-06','2026-07','2026-08','2026-09']
    actuals=[]
    for j,method in enumerate(METHODS):
        block=history.loc[(history.method==method)&history.target_start.str[:7].isin(months)].copy()
        block['month']=block.target_start.str[:7]
        block=block.set_index('month').loc[months]
        vals=list(100*block.forecast)+[100*scores.loc[scores.method==method,'forecast_decimal'].iloc[0]]
        ax.scatter(np.arange(6)+(j-1)*.13,vals,color=COLORS[j],label=LABELS[j],s=40)
        if j==0:actuals=list(100*block.actual)+[actual]
    ax.scatter(np.arange(6),actuals,color='#111827',marker='x',s=60,label='Observed RMS')
    ax.axvline(4.5,color='#64748b',linestyle=':',lw=1)
    ax.set(xticks=np.arange(6),xticklabels=['May','Jun','Jul','Aug','Sep','Oct'],ylabel='Five-return daily RMS (%)',title='Separate windows; no implied daily forecast path',ylim=(0,1.4))
    ax.legend(fontsize=9,ncol=2,loc='lower left')
    for ax in axes.flat:style(ax)
    fig.subplots_adjust(top=.86,bottom=.16,left=.08,right=.97,hspace=.4,wspace=.25)
    fig.text(.08,.075,'May–August: April 30 origin with different gaps. September: August 31 origin, retrospective. October: prospective baseline.\nOctober uses Stock Analysis displayed adjusted closes rounded to cents; SPY Oct 7 differs from ChartExchange (777.22 vs 777.30).\nLast-price sensitivity gives RMS 0.5253% instead of 0.5263%; the closest method is unchanged. One window does not establish superiority.',fontsize=9,color='#475569')
    fig.savefig(out/'october_2026_baseline_evaluation.png',dpi=150)
    plt.close(fig)

    fig,ax=plt.subplots(figsize=(10,6))
    ordered=profile.sort_values('five_return_rms_decimal')
    values=100*ordered.five_return_rms_decimal
    ax.barh(ordered.index,values,color=['#2563eb' if a=='SPY' else '#94a3b8' for a in ordered.index])
    for i,v in enumerate(values):ax.text(v+.025,i,f'{v:.3f}%',va='center')
    ax.set(xlabel='Observed five-return daily RMS (%)',title='Eight ETFs: observed return magnitude, October 1–7',xlim=(0,float(values.max())*1.2))
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    fig.subplots_adjust(bottom=.2,left=.12,top=.87)
    fig.text(.12,.065,'All six prices per ETF use the same displayed adjusted-close source, including the September 30 anchor.\nThis is a five-session description, not a forecast of ETF returns or a future-performance ranking.',fontsize=9,color='#475569')
    fig.savefig(out/'october_2026_etf_observed_rms.png',dpi=150)
    plt.close(fig)
    print('Saved completed baseline and observed ETF figures.')

if __name__=='__main__':
    main()
