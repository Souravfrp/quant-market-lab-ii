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



## Sources consulted for the 7 October signal plan and status update

5. [NIST/SEMATECH: Single Exponential Smoothing](https://itl.nist.gov/div898/handbook/pmc/section4/pmc431.htm). Source for exponential weighting and the need to choose an initialization and smoothing parameter. I apply smoothing to squared returns as a proposed experiment; this page does not validate financial forecast performance.
6. [pandas 2.2: DataFrame.ewm](https://pandas.pydata.org/pandas-docs/version/2.2/reference/api/pandas.DataFrame.ewm.html). Source for `adjust=False` recursion and smoothing-parameter conventions. My lambda is the previous-state weight; pandas alpha is `1-lambda`. The 20-observation seed is my explicit experiment choice.
7. [NYSE: Hours and Calendars](https://www.nyse.com/markets/hours-calendars). Source for regular-session closing time. For October 7, 2026, I convert 16:00 America/New_York to 01:30 Asia/Kolkata on October 8; provider availability can be later.
8. [SciPy: filtfilt](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.filtfilt.html). Source for forward-and-backward filtering; this explains why that operation is not my live causal feature construction.
9. [statsmodels: State space methods](https://www.statsmodels.org/stable/statespace.html). Source for the alternative class of state-space models, which is deferred rather than implemented here.
10. [Stock Analysis: SPY historical prices](https://stockanalysis.com/etf/spy/history/). Public displayed adjusted-close source for the five-price September 30–October 6 partial snapshot, transcribed October 7. The page attributes historical data to S&P Global Market Intelligence. Prices are displayed to two decimals. This is a new evaluation source, not the original frozen training data vendor or vintage.
11. [ChartExchange: SPY historical prices](https://chartexchange.com/symbol/nyse-spy/historical/). Historical-table close prices cross-checked for those same five dates. Agreement of displayed closes does not verify all adjustment conventions or eliminate later data revisions.

The new [price provenance JSON](../results/evaluation_inputs/spy_october_partial_2026-10-06_provenance.json) describes acquisition and limitations. The plotting script saves SHA-256 fingerprints of its CSV inputs alongside the derived summary. The September value remains the existing repository result, with its existing researcher-supplied provenance; I do not replace it with a differently rounded source. These references support definitions and provenance, not a claim of external validation or forecasting superiority.


## Sources and reproducibility for the completed October evaluation (8 October 2026)

- Stock Analysis historical tables, displayed **Adj. Close**: [SPY](https://stockanalysis.com/etf/spy/history/), [QQQ](https://stockanalysis.com/etf/qqq/history/), [IWM](https://stockanalysis.com/etf/iwm/history/), [TLT](https://stockanalysis.com/etf/tlt/history/), [GLD](https://stockanalysis.com/etf/gld/history/), [USO](https://stockanalysis.com/etf/uso/history/), [EEM](https://stockanalysis.com/etf/eem/history/), [VNQ](https://stockanalysis.com/etf/vnq/history/). I inspected six dates per ETF on October 8 and transcribed the rounded displayed values. The pages attribute historical data to S&P Global Market Intelligence.
- [ChartExchange SPY historical Close](https://chartexchange.com/symbol/nyse-spy/historical/). Earlier five closes agree; October 7 differs (777.30 versus 777.22). This is a cross-check with a recorded discrepancy, not confirmation of adjusted-price agreement.
- [Snapshot and provenance](../results/evaluation_inputs/etf_october_2026_provenance.json), [evaluation equations and interpretation](october_2026_baseline_evaluation.md), [scoring code](../src/evaluate_october_2026.py), and [figure code](../src/plot_october_2026.py). The original [forecast manifest](../forecasts/2026-09-30-v0.1/manifest.json) supplies the hash used to check forecast preservation.

These source links support the archived price snapshot, not future performance claims. Original-provider replication and vendor reconciliation remain open.


## Method review recorded 8 October 2026

The [signal-method review](signal_processing_methods_review.md#references-and-status) lists primary NIST, pandas, SciPy, PyWavelets, statsmodels and arch documentation alongside the formulations and requirements. Reviewed methods are distinguished from implemented experiments.


## EWMA snapshot and session calendar — 8 October 2026

- Yahoo Finance chart responses: `https://query1.finance.yahoo.com/v8/finance/chart/{ticker}`. I used `indicators.adjclose[0].adjclose`, daily interval, 2015-01-01 inclusive to 2026-10-08 exclusive. Exact responses and provenance are in [the saved snapshot](../data/raw/yahoo_2026-10-08/README.md); this endpoint is a provider data response, not a guaranteed stable API contract.
- [exchange_calendars](https://github.com/gerrymanoim/exchange_calendars), version 4.13.2, XNYS calendar. This is a community-maintained calendar package, not the exchange itself.
- [NYSE hours and calendars](https://www.nyse.com/trade/hours-calendars): official 2026 holidays checked against the saved schedule.
