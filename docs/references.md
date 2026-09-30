# Sources and attribution

I use established methods and explain their role in this experiment in my own wording. The mathematical derivations in the companion notes expand the definitions and objective used in the code; they are not claims of a new RMS or Ridge method.

1. [scikit-learn: Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html). Source for the penalized least-squares objective, unpenalized intercept setting and SVD solver. Consulted September 30, 2026. The frozen run used scikit-learn 1.8.0; the stable documentation can change.
2. [scikit-learn: StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html). Source for feature centering, population-variance scaling and zero-variance handling. Consulted September 30, 2026.
3. [NYSE: 2026 trading calendar](https://www.nyse.com/publicdocs/nyse/ICE_NYSE_2026_Yearly_Trading_Calendar.pdf). Source for the scheduled prospective windows and holiday exclusions. Consulted September 30, 2026. Early closes count as sessions.
4. [My original Quant AI Market Lab](https://github.com/Souravfrp/quant-ai-market-lab/tree/e41010ec71ca615188874f9bb501fe9dd518621b). Prior implementation and experiment reused by this continuation. See the [baseline notes](https://github.com/Souravfrp/quant-ai-market-lab/blob/e41010ec71ca615188874f9bb501fe9dd518621b/docs/risk_forecasting_baselines.md) and [walk-forward study](https://github.com/Souravfrp/quant-ai-market-lab/blob/e41010ec71ca615188874f9bb501fe9dd518621b/docs/walk_forward_window_selection.md). This is prior project provenance, not independent evidence of performance.

## Numerical sources

- [Frozen forecasts](../forecasts/2026-09-30-v0.1/forecasts.csv), [historical predictions](../forecasts/2026-09-30-v0.1/historical_predictions.csv), and [manifest](../forecasts/2026-09-30-v0.1/manifest.json): model outputs and input/source fingerprints.
- [September evaluation](../results/september_2026_holdout.csv) and [six adjusted closes](../results/evaluation_inputs/spy_september_evaluation.csv): numerical sources for the retrospective comparison. The six-close file is a researcher-supplied snapshot, not an independently verified vendor download. I do not infer a vendor or retrieval timestamp from its filename.
- [Reconstruction code](../src/plot_risk_comparisons.py): exact row selection, unit conversion and checks used in the companion figures.

These are the sources used for this documentation update. I have not copied explanatory passages from them. Attribution does not imply that the implementation has received an external audit, and no plagiarism similarity score is claimed.
