"""Reconstruct my approved comparisons from saved outputs, without model fitting."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
METHODS = [('ridge_expanding', 'Ridge (expanding)'), ('rolling_20d_rms', 'Rolling 20-day RMS'), ('constant', 'Constant baseline')]


def pairs(ax, x, b):
    actual, forecast = b.actual.to_numpy()*100, b.forecast.to_numpy()*100
    ax.vlines(x, actual, forecast, color='#a5adb6', label='Absolute error', zorder=1)
    ax.scatter(x, actual, color='#303c46', label='Observed RMS', zorder=2)
    ax.scatter(x, forecast, marker='x', color='#128c9b', label='Predicted RMS', zorder=3)
    ax.set_ylabel('Daily RMS (%)')
    ax.grid(axis='y', alpha=.2)
    ax.legend(loc='upper right', fontsize=8)
    ax.set_ylim(bottom=0)


def main():
    release = ROOT/'forecasts/2026-09-30-v0.1'
    h = pd.read_csv(release/'historical_predictions.csv')
    hist = h[(h.evaluation=='historical_monthly') & (h.gap_sessions==0)].copy()
    april = h[h.evaluation=='april_fixed_origin'].copy()
    sep = pd.read_csv(ROOT/'results/september_2026_holdout.csv')
    prices = pd.read_csv(ROOT/'results/evaluation_inputs/spy_september_evaluation.csv')
    expected = ['2026-08-31','2026-09-01','2026-09-02','2026-09-03','2026-09-04','2026-09-08']
    assert prices.Date.tolist() == expected
    p = prices.SPY.to_numpy(dtype=float)
    assert np.isfinite(p).all() and (p>0).all()
    returns = np.diff(np.log(p))
    actual = np.sqrt(np.mean(returns**2))
    np.testing.assert_allclose(sep.actual_rms, actual, rtol=1e-10, atol=1e-12)
    frozen = pd.read_csv(release/'forecasts.csv')
    frozen = frozen[frozen.target_month=='2026-09'].set_index('method')
    np.testing.assert_allclose(sep.forecast_decimal, frozen.loc[sep.method,'forecast_decimal'], rtol=1e-10)
    np.testing.assert_allclose(sep.error, sep.forecast_decimal-sep.actual_rms, atol=1e-14)
    np.testing.assert_allclose(sep.absolute_error, abs(sep.error), atol=1e-14)
    sep = sep.rename(columns={'forecast_decimal':'forecast','actual_rms':'actual'})
    sep['origin'], sep['gap_sessions'], sep['evaluation'] = '2026-08-31', 0, 'september_retrospective'
    recent = pd.concat([april,sep], ignore_index=True)
    all_rows = pd.concat([hist,recent], ignore_index=True)
    keys = ['evaluation','origin','gap_sessions','target_start','target_end']
    assert not all_rows.duplicated(keys+['method']).any()
    for _, b in all_rows.groupby(keys):
        assert set(b.method)==set(m for m,_ in METHODS)
        assert b.actual.nunique()==1
    assert all_rows[['forecast','actual']].notna().all().all()
    assert np.isfinite(all_rows[['forecast','actual']]).all().all()
    for method,_ in METHODS:
        assert len(hist[hist.method==method])==87
        assert len(recent[recent.method==method])==5
    assert hist.target_start.min()=='2019-02-01' and hist.target_end.max()=='2026-04-08'
    all_rows['error']=all_rows.forecast-all_rows.actual
    all_rows['absolute_error']=abs(all_rows.error)
    all_rows[keys+['method','forecast','actual','error','absolute_error']].to_csv(ROOT/'results/figure_values.csv',index=False)
    all_rows[keys].drop_duplicates().sort_values('target_start').to_csv(ROOT/'results/figure_windows.csv',index=False)
    out=ROOT/'results/figures/rebuilt'
    out.mkdir(parents=True,exist_ok=True)
    fig, axes=plt.subplots(3,1,figsize=(14,12),sharex=True,sharey=True)
    fig.suptitle('SPY | Predicted versus observed five-day risk\n1 February 2019–8 April 2026',fontsize=19,fontweight='bold')
    fig.text(.09,.91,'Each monthly marker summarizes the first FIVE TRADING SESSIONS as one RMS value.\nHistorical development; gap 0; no lines connect months.',fontsize=11)
    for ax,(method,name) in zip(axes,METHODS):
        b=hist[hist.method==method].sort_values('target_start')
        pairs(ax,pd.to_datetime(b.target_start),b)
        mae=abs(b.forecast-b.actual).mean()*100
        ax.set_title(f'{name} | MAE: {mae:.4f} pp | {len(b)} windows',loc='left')
    axes[-1].set_xlabel('Window start date; each point summarizes five trading sessions')
    fig.text(.09,.025,'Source: forecasts/2026-09-30-v0.1/historical_predictions.csv\nDevelopment evidence, not an untouched test. pp = percentage points.',fontsize=10)
    fig.subplots_adjust(top=.84,bottom=.10,hspace=.35)
    fig.savefig(out/'historical_five_day_comparison.png',dpi=150)
    plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(14,12),sharey=True)
    fig.suptitle('SPY | Five-day risk comparisons: May–September 2026',fontsize=18,fontweight='bold')
    fig.text(.09,.91,'One pair = one five-session window, not a whole month.\nMay–August: April 30 cutoff. September: August 31 cutoff, retrospective.',fontsize=11)
    for ax,(method,name) in zip(axes,METHODS):
        b=recent[recent.method==method].sort_values('target_start')
        pairs(ax,np.arange(5),b)
        ax.axvspan(3.5,4.5,color='#eee5d7',alpha=.6,zorder=0)
        labels=[f'{s[5:]} to {e[5:]}\ngap: {g} sessions' for s,e,g in zip(b.target_start,b.target_end,b.gap_sessions)]
        ax.set_xticks(range(5),labels)
        ax.set_title(name,loc='left')
        for i,err in enumerate(abs(b.forecast-b.actual)*100):
            ax.text(i,.03,f'Error: {err:.4f} pp',ha='center',fontsize=9)
        ax.set_ylim(0,1.7)
    fig.text(.09,.025,'Shading marks the changed September cutoff. None of these windows is a live forward test.\nSources: saved historical predictions and results/september_2026_holdout.csv.',fontsize=10)
    fig.subplots_adjust(top=.84,bottom=.10,hspace=.5)
    fig.savefig(out/'may_september_risk_comparison.png',dpi=150)
    plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(13,11))
    fig.suptitle('SPY | September retrospective evaluation',fontsize=19,fontweight='bold')
    fig.text(.1,.92,'Target: September 1–8, 2026 | Five sessions | Input cutoff: August 31',fontsize=11)
    axes[0].bar(range(5),returns*100,color='#307e94')
    axes[0].set_xticks(range(5),[d[5:] for d in expected[1:]])
    axes[0].axhline(0,color='gray')
    axes[0].set_ylabel('Daily log return (%)')
    axes[0].set_xlabel('Observed trading date, 2026')
    axes[0].set_title('A | What I observed each day',loc='left')
    order=['rolling_20d_rms','ridge_expanding','constant']
    b=sep.set_index('method').loc[order]
    axes[1].scatter(range(3),b.forecast*100,color='#307e94',s=90,label='Stored retrospective forecast')
    axes[1].axhline(actual*100,color='#bc602b',linestyle='--',label=f'Observed RMS: {actual*100:.4f}%')
    axes[1].set_xticks(range(3),['Rolling 20-day RMS','Ridge (expanding)','Constant baseline'])
    for i,v in enumerate(b.forecast*100): axes[1].annotate(f'{v:.4f}%',(i,v),xytext=(0,12),textcoords='offset points',ha='center')
    axes[1].set_ylim(0,1.1)
    axes[1].set_ylabel('Daily RMS (%)')
    axes[1].set_title('B | Forecasts compared with observed RMS',loc='left')
    axes[1].legend(loc='lower left')
    fig.text(.1,.035,'I recorded these forecasts on September 30: this is retrospective.\nRolling RMS is slightly closer in this one window; one window cannot establish superiority.\nSources: results/evaluation_inputs/spy_september_evaluation.csv and stored forecast/evaluation files.',fontsize=10)
    fig.subplots_adjust(top=.85,bottom=.16,hspace=.45)
    fig.savefig(out/'september_risk_comparison.png',dpi=150)
    plt.close(fig)
    print('Validated: 87 historical windows per method; 5 recent windows per method; September RMS and stored predictions. No fitting.')
    print('Observed September RMS:',actual)

if __name__=='__main__':
    main()
