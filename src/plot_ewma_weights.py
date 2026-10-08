"""A mathematical weighting illustration, not a market-data forecast."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from src.run_ewma_experiment import GRID

def main():
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    age=np.arange(61)
    for decay in GRID:
        axes[0].plot(age,(1-decay)*decay**age,label=f'{decay:.2f}')
    axes[0].set(xlabel='Age of squared-return observation (sessions)',ylabel='Weight',title='Candidate EWMA weighting kernels')
    axes[0].legend(title='Decay λ')
    axes[1].bar([str(x) for x in GRID],np.log(.5)/np.log(GRID))
    axes[1].set(xlabel='Decay λ',ylabel='Half-life (sessions)',title='How quickly a shock contribution halves')
    fig.suptitle('Mathematical illustration only — no selected parameter or market prediction')
    fig.tight_layout();path=Path('results/figures/ewma_weights.png');path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=160)

if __name__=='__main__':main()
