"""My dated observation chart reads saved values only and never refits a forecast."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1]
PRICE_PATH='results/evaluation_inputs/spy_october_partial_2026-10-06.csv'
EXPECTED=pd.to_datetime(['2026-09-30','2026-10-01','2026-10-02','2026-10-05','2026-10-06'])
METHODS=('ridge_expanding','constant','rolling_20d_rms')
LABELS=('Ridge','Constant','Rolling RMS')
COLORS=('#2563eb','#a855f7','#d97706')

def partial_measures(prices):
    if not prices.index.equals(pd.DatetimeIndex(EXPECTED)) or list(prices.columns)!=['SPY']:
        raise ValueError('Require exactly the five partial-window closes in order.')
    x=prices.SPY.to_numpy(dtype=float)
    if not np.isfinite(x).all() or (x<=0).any():raise ValueError('Invalid prices.')
    r=np.log(x[1:]/x[:-1]);s=float(r@r)
    table=pd.DataFrame({'date':EXPECTED[1:].strftime('%Y-%m-%d'),'log_return':r,'squared_log_return':r*r})
    summary={'as_of_session':'2026-10-06','status':'partial; fifth return unavailable','completed_returns':4,'expected_returns':5,
             'partial_four_return_rms':float(np.sqrt(s/4)),'five_return_rms_lower_bound':float(np.sqrt(s/5)),
             'final_five_return_rms':None,'precision_note':'Two-decimal public prices; not a final forecast score.'}
    return table,summary

def check_forecasts(frame):
    rows=frame.loc[frame.target_month=='2026-10'].copy()
    if len(rows)!=3 or set(rows.method)!=set(METHODS):raise ValueError('Missing frozen methods.')
    for column,value in [('information_cutoff','2026-08-31'),('target_start','2026-10-01'),('target_end','2026-10-07'),('return_anchor_date','2026-09-30'),('horizon_sessions',5)]:
        if not (rows[column]==value).all():raise ValueError('Frozen window changed.')
    if not np.isfinite(rows.forecast_decimal).all():raise ValueError('Invalid forecast.')
    return rows

def main():
    r,summary=partial_measures(pd.read_csv(ROOT/PRICE_PATH,index_col='Date',parse_dates=True))
    fp=ROOT/'forecasts/2026-09-30-v0.1/forecasts.csv'
    forecasts=check_forecasts(pd.read_csv(fp))
    vp=ROOT/'results/figure_values.csv';values=pd.read_csv(vp)
    saved=values.loc[(values.evaluation=='april_fixed_origin')|((values.target_start=='2026-09-01')&(values.target_end=='2026-09-08'))].copy()
    saved['month']=saved.target_start.str[:7];months=['2026-05','2026-06','2026-07','2026-08','2026-09']
    saved=saved.loc[saved.month.isin(months)].sort_values(['month','method'])
    if len(saved)!=15 or saved.duplicated(['month','method']).any():raise ValueError('Expected 15 comparison rows.')
    for month in months:
        block=saved.loc[saved.month==month]
        if set(block.method)!=set(METHODS) or not np.allclose(block.actual,block.actual.iloc[0],rtol=0,atol=1e-12):raise ValueError('Unmatched values.')
    summary['input_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/PRICE_PATH,fp,vp)}
    summary['source']='See the evaluation-input provenance JSON for acquisition and limitations.'
    r.to_csv(ROOT/'results/october_partial_2026-10-06_returns.csv',index=False,float_format='%.17g')
    (ROOT/'results/october_partial_2026-10-06_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig=plt.figure(figsize=(16,9),facecolor='#f8fafc');gs=fig.add_gridspec(2,2,height_ratios=[.8,2],hspace=.45,wspace=.28)
    ax=fig.add_subplot(gs[0,:]);ax.set_axis_off()
    boxes=[('31 AUGUST','Frozen input cutoff','2,932 price rows\n2,931 returns','#dbeafe'),('1–8 SEPTEMBER','Retrospective evaluation','Five-session actual\nalready recorded','#e2e8f0'),('30 SEPTEMBER','Forecast record created','October–December\nbaselines preserved','#ede9fe'),('1–6 OCTOBER','Partial observations','Four completed returns\nseparate evaluation input','#dcfce7'),('7 OCTOBER','Fifth return pending','No final actual\nin this dated record','#fef3c7')]
    for i,(date,title,detail,color) in enumerate(boxes):
        x=i/5+.006;ax.add_patch(FancyBboxPatch((x,.07),.185,.86,boxstyle='round,pad=0.008',facecolor=color,edgecolor='#cbd5e1',transform=ax.transAxes))
        for y,text,size,weight in [(.80,date,11,'bold'),(.57,title,9.5,'normal'),(.25,detail,9,'normal')]:ax.text(x+.012,y,text,transform=ax.transAxes,fontsize=size,fontweight=weight,color='#334155')
    ax=fig.add_subplot(gs[1,0]);ax.set_facecolor('white')
    for j,(method,label,color) in enumerate(zip(METHODS,LABELS,COLORS)):
        block=saved.loc[saved.method==method].set_index('month')
        y=[100*block.loc[m,'forecast'] for m in months]+[100*forecasts.loc[forecasts.method==method,'forecast_decimal'].iloc[0]]
        ax.scatter(np.arange(6)+(j-1)*.13,y,color=color,s=52,label=label,zorder=3)
    actual=[100*saved.loc[saved.month==m,'actual'].iloc[0] for m in months]
    ax.scatter(np.arange(5),actual,color='#0f172a',marker='x',s=65,label='Completed actual',zorder=4)
    ax.axvspan(3.5,4.5,color='#e2e8f0',alpha=.6);ax.axvspan(4.5,5.5,color='#fef3c7',alpha=.4)
    ax.text(5,1.27,'Actual pending',ha='center',fontsize=9,color='#92400e')
    ax.set(xticks=np.arange(6),xticklabels=['May','June','July','August','September','October'],ylabel='Five-return daily RMS (%)',title='Saved five-return windows, not whole-month risk',ylim=(0,1.4),xlim=(-.45,5.45));ax.grid(axis='y',alpha=.18);ax.legend(loc='lower left',fontsize=9,ncol=2)
    ax.text(.01,-.19,'May–August: April 30 origin, different gaps.\nSeptember–October: August 31 origin; October forecast only.',transform=ax.transAxes,fontsize=9,color='#475569')
    ax=fig.add_subplot(gs[1,1]);ax.set_facecolor('white');daily=r.log_return.to_numpy()*100
    ax.bar(np.arange(4),daily,color='#0f766e',width=.6)
    for i,value in enumerate(daily):ax.text(i,value+.025,f'{value:+.3f}%',ha='center',fontsize=10)
    ax.axvspan(3.5,4.5,color='#fef3c7',alpha=.7);ax.text(4,.35,'Pending\nnot zero',ha='center',color='#92400e',fontsize=11)
    ax.set(xticks=np.arange(5),xticklabels=['Oct 1','Oct 2','Oct 5','Oct 6','Oct 7'],ylabel='Observed daily log return (%)',title='October: four completed returns out of five',ylim=(-.05,.92),xlim=(-.5,4.5));ax.axhline(0,color='#64748b',lw=.8);ax.grid(axis='y',alpha=.18)
    ax.text(.02,-.19,f'Four-return RMS: {100*summary["partial_four_return_rms"]:.4f}%\nFive-return RMS lower bound: {100*summary["five_return_rms_lower_bound"]:.4f}% — not a final actual',transform=ax.transAxes,fontsize=9,color='#475569')
    fig.suptitle('My baseline forecast record and the next signal-processing experiment',fontsize=18,fontweight='bold',color='#0f172a',y=.98)
    fig.text(.5,.935,'Status dated 7 October 2026, before the US close • Observation cutoff: 6 October • EWMA model remains planned',ha='center',fontsize=11,color='#475569');fig.subplots_adjust(top=.88,bottom=.16,left=.06,right=.97)
    fig.text(.06,.045,'Sources: saved repository outputs; October displayed adjusted closes from Stock Analysis, historical closes checked on ChartExchange.\nPartial prices are rounded to cents and use a different source/vintage from the frozen training snapshot. No forecasts were refitted.',fontsize=9,color='#64748b')
    output=ROOT/'results/figures/evaluation_status_2026-10-07.png';output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=150,facecolor=fig.get_facecolor());plt.close(fig)
    print(json.dumps(summary,indent=2));print('Saved:',output)

if __name__=='__main__':main()
