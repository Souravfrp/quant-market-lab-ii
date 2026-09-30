"""Plot the preserved August-cutoff predictions; no fitting or forecast revision."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

def main():
    source = ROOT / 'forecasts/2026-09-30-v0.1/forecasts.csv'
    data = pd.read_csv(source)
    months = ['2026-10', '2026-11', '2026-12']
    methods = [('ridge_expanding', 'Ridge (expanding)'), ('rolling_20d_rms', 'Rolling 20-day RMS'), ('constant', 'Constant baseline')]
    selected = data[data.target_month.isin(months)].copy()
    assert len(selected) == 9 and not selected.duplicated(['target_month', 'method']).any()
    assert set(selected.method) == {m for m, _ in methods}
    assert selected.information_cutoff.eq('2026-08-31').all()
    assert selected.horizon_sessions.eq(5).all()
    assert np.isfinite(selected.forecast_decimal).all() and selected.forecast_decimal.ge(0).all()
    expected = [('2026-10-01','2026-10-07',21),('2026-11-02','2026-11-06',43),('2026-12-01','2026-12-07',63)]
    labels = ['October 1–7\nSessions: 1, 2, 5, 6, 7 Oct\nGap: 21 sessions', 'November 2–6\nSessions: 2, 3, 4, 5, 6 Nov\nGap: 43 sessions', 'December 1–7\nSessions: 1, 2, 3, 4, 7 Dec\nGap: 63 sessions']
    fig, axes = plt.subplots(3, 1, figsize=(13, 12), sharey=True)
    fig.suptitle('SPY | October–December 2026 risk forecasts\nUsing data through August 31, 2026', x=.10, ha='left', fontsize=21, fontweight='bold', y=.98)
    fig.text(.10,.865,'One marker = predicted daily log-return RMS over FIVE trading sessions.\nForecasts only • Actual outcomes pending as of September 30, 2026.\nThese are movement-size forecasts, not price direction or whole-month risk.',fontsize=11,linespacing=1.5)
    for ax, (method, title) in zip(axes, methods):
        rows = selected[selected.method.eq(method)].set_index('target_month').loc[months]
        assert list(zip(rows.target_start, rows.target_end, rows.gap_sessions)) == expected
        values = rows.forecast_decimal.to_numpy()*100
        ax.scatter(range(3),values,marker='x',s=110,linewidths=2.6,color='#128c9b',label='Stored predicted RMS',zorder=3)
        for i, value in enumerate(values):
            ax.annotate(f'{value:.4f}%',(i,value),xytext=(0,13),textcoords='offset points',ha='center',fontsize=12,fontweight='bold')
        ax.set_title(title,loc='left',fontsize=14,fontweight='bold')
        ax.set_ylim(0,1.15); ax.set_xlim(-.5,2.5)
        ax.set_ylabel('Predicted daily RMS (%)')
        ax.set_xticks(range(3),labels,fontsize=10)
        ax.grid(axis='y',alpha=.2); ax.legend(loc='lower right',frameon=False,fontsize=9)
        ax.spines[['top','right']].set_visible(False)
    fig.text(.10,.075,'All nine predictions use the SAME August 31 cutoff; no September prices enter them.\nThe rolling baseline repeats because its 20-return input window is fixed.\nGap = sessions skipped after the cutoff before the five-session target begins.\nSeparate markers show separate windows; no observed values or uncertainty intervals are plotted.',fontsize=10,linespacing=1.4)
    fig.text(.10,.015,'Source: forecasts/2026-09-30-v0.1/forecasts.csv | Created September 30, 2026 (UTC)\nTarget calendar: NYSE 2026 schedule; see docs/forecast_freeze_v0_1.md and docs/references.md.',fontsize=9,color='#555555')
    fig.subplots_adjust(top=.80,bottom=.19,hspace=.66,left=.10,right=.97)
    out=ROOT/'results/figures/october_december_forecasts.png'
    fig.savefig(out,dpi=160); plt.close(fig)
    print('Validated and plotted all nine stored forecasts:',out)

if __name__ == '__main__':
    main()
