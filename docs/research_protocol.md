# Research Protocol: Fixed-Cutoff Prospective Forecasting

## Purpose

This document fixes the experimental rules for the first Quant Market Lab II forecasting study before the forecasting model is implemented. The purpose is to prevent accidental look-ahead bias, make later evaluation auditable, and separate research decisions made before observing future outcomes from conclusions drawn afterward.

## 1. Information cutoff

The frozen information cutoff for the first experiment is:

**31 August 2026**

Any model described as an August-cutoff prospective model must use only information available on or before this date.

This restriction applies to:

- raw observations
- engineered features
- rolling statistics
- normalization or scaling parameters
- hyperparameter selection
- model selection
- baseline selection
- uncertainty estimation
- any diagnostic used to revise the frozen model

Data observed after 31 August 2026 may be used only for later evaluation, unless a new model version is created with a later, explicitly documented cutoff.

## 2. Leakage rule

For a forecast origin t, every predictor supplied to the model must be measurable using information available at or before t.

If a feature at time t depends on observations from t+1 or later, then that feature is retrospective and cannot be used in the prospective forecasting pipeline.

Examples of disallowed leakage include:

- centering or scaling with statistics computed from the full dataset
- choosing a filtering parameter after inspecting future outcomes
- using a forward-looking rolling window
- using a symmetric smoother whose value at t depends on future observations
- revising a stored forecast after the realized outcome becomes known

A transformation may still be useful for retrospective visualization, but it must be labelled separately from the live forecasting feature set.

## 3. Causal signal-processing requirement

Signal-processing features used in a prospective model must be causal or otherwise constructed strictly from the historical information set available at the forecast origin.

For example, a one-sided filter may be admissible if its output at time t depends only on observations up to t. A forward-backward filter or other two-sided smoother is not admissible for live prospective feature construction because it uses future values implicitly.

Frequency-domain analysis may be used to study historical periodic structure, but any forecast feature derived from it must be recomputed using only the training window available at that historical forecast origin.

## 4. Historical validation design

Model comparison will be chronological.

The preferred design is rolling-origin or expanding-window validation:

1. choose a historical training window ending at time t;
2. fit all learned preprocessing only on that training window;
3. fit the candidate model on the same information set;
4. forecast the predefined future target;
5. move the forecast origin forward and repeat;
6. aggregate errors only after all historical forecasts have been generated.

Random train-test shuffling will not be used for the main time-series forecasting comparison.

The exact first training date, refit frequency, forecast horizon, and minimum training length will be fixed when the primary target is selected.

## 5. Primary target decision

The primary forecasting target is intentionally not fixed in this protocol yet.

The next research decision will compare a small number of defensible forward risk targets, most likely:

- 5-trading-day realized volatility
- 20-trading-day realized volatility

The chosen target must be defined mathematically before the first model comparison is run. The choice will be justified using interpretability, sample size, forecast horizon, and relevance to the prospective October-December evaluation.

Once chosen for the frozen v0.1 experiment, the primary target will not be changed merely because another target gives better results.

## 6. Baseline requirement

Every signal-processing or time-series model must be compared with simple baselines.

Candidate baselines include:

- persistence or last observed risk estimate
- rolling historical volatility
- constant historical mean risk estimate

The exact baseline definitions must use the same forecast origin and information set as the candidate model.

A more complicated method will not be considered useful merely because it fits historical data better. Its value must be assessed through chronological out-of-sample performance, interpretability, or a clearly stated complementary diagnostic.

## 7. September 2026 status

September 2026 is not a genuinely untouched future period for this project because development began after September had already started and part of the month was observable.

Therefore September results must be labelled as one of the following, depending on the exact experiment:

- retrospective evaluation
- holdout-style evaluation
- pseudo-out-of-sample evaluation

They must not be described as forecasts made before September began.

## 8. October-December prospective record

Forecasts intended to count as genuinely prospective must be created and committed before the corresponding evaluation period is observed.

For each frozen forecast version, the repository should record:

- forecast creation date
- information cutoff
- target definition
- model version
- feature version
- forecast horizon
- point forecast
- uncertainty interval or dispersion measure, when available

The original committed forecast values should remain unchanged after the outcomes become known. Later model improvements must produce new versioned forecast files rather than overwrite the original research record.

## 9. Model-version rule

If the method is changed after observing later data, the new method must receive a new version and a new stated information cutoff.

For example, a wavelet or state-space extension developed after October begins may still be evaluated historically, but it cannot be described as an August-cutoff October forecast unless that exact method and forecast had already been frozen before October data were observed.

## 10. Evaluation metrics

The primary metrics will be chosen to match the final target, with likely candidates including:

- mean absolute error
- root mean squared error
- relative error versus baseline
- interval coverage, if predictive intervals are produced
- forecast stability across historical folds

Model comparison will use the same realized target dates wherever possible.

## 11. Reproducibility record

Each major research stage should be represented by a separate Git commit with a descriptive message. The repository history should show the real development sequence rather than a reconstructed or backdated sequence.

At minimum, the project should preserve separate stages for:

1. research scope
2. protocol and leakage rules
3. data-cutoff validation
4. target definition
5. baseline forecasting
6. signal-processing model
7. chronological comparison
8. frozen prospective forecasts
9. realized-outcome evaluation

## 12. Interpretation standard

A negative result is acceptable.

If the signal-processing method does not outperform a simple baseline, the result should be reported directly. The research question is whether the method adds evidence of forecasting value under a controlled prospective design, not whether the project can be made to produce a positive result.

This protocol is part of the research record and may be extended later. Any later change that materially affects the experiment should be documented explicitly rather than silently replacing the original rule.