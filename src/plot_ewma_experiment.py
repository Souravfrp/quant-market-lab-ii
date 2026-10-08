"""Plot only saved experiment outputs; never invent missing market forecasts."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

def plot(folder):
    signals=pd.read_csv(folder/'signals.csv',parse_dates=['Date'])
    scores=pd.read_csv(folder/'historical_metrics.csv')
    forecasts=pd.read_csv(folder/'forecasts.csv')
    figures=folder/'figures';figures.mkdir(exist_ok=True)
    fig,ax=plt.subplots(figsize=(11,4))
    recent=signals.loc[signals.Date>='2026-01-01']
    for column in ['rolling_20d_rms','ewma_rms','ridge_ewma_signal']:
        ax.plot(recent.Date,100*recent[column],label=column)
    ax.set(title='Observed-data signals through the saved cutoff',ylabel='Daily RMS (%)')
    if recent.Date.max()>pd.Timestamp('2026-08-31'):
        ax.axvline(pd.Timestamp('2026-08-31'),color='gray',linestyle='--',label='August cutoff')
    ax.legend();fig.autofmt_xdate();fig.tight_layout();fig.savefig(figures/'signals.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4))
    ax.bar(scores.method,100*scores.mae)
    ax.set(title='Development-aware historical comparison: 2023–August 2026',ylabel='MAE (percentage points)')
    ax.tick_params(axis='x',labelrotation=15);fig.tight_layout();fig.savefig(figures/'historical_mae.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5))
    for method,b in forecasts.groupby('method',sort=False):
        ax.plot(b.target_month,100*b.forecast_decimal,marker='o',label=method)
    ax.set(title=f"Five-session RMS forecasts; information cutoff {forecasts.information_cutoff.iloc[0]}",ylabel='Predicted daily RMS (%)',xlabel='Target month; see CSV for exact dates and retrospective/prospective status')
    if (forecasts.target_month<'2026-11').any():
        ax.text(.02,.02,'Sep/Oct: retrospective reconstruction; Nov/Dec: future targets',transform=ax.transAxes,fontsize=9)
    ax.legend();fig.tight_layout();fig.savefig(figures/'forecasts.png',dpi=160);plt.close(fig)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path)
    plot(parser.parse_args().folder)
