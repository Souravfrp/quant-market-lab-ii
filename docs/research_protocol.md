# Research Protocol: Fixed-Cutoff Prospective Forecasting

## Purpose

I am fixing the experimental rules for the first Quant Market Lab II forecasting study before I implement the forecasting model. I want the development history to show what I decided before observing later outcomes, so that I can identify look-ahead bias, avoid redesigning the experiment after seeing results, and evaluate the forecasts honestly.

## 1. Information cutoff

For my first experiment, I freeze the information set at:

**31 August 2026**

When I describe a model as an August-cutoff prospective model, I will use only information that was available on or before this date.

I apply this restriction to:

- raw observations
- engineered features
- rolling statistics
- normalization or scaling parameters
- hyperparameter selection
- model selection
- baseline selection
- uncertainty estimation
- diagnostics that could influence the frozen model

I will use data observed after 31 August 2026 only for later evaluation, unless I create a new model version with a later and explicitly documented information cutoff.

## 2. How I define leakage

For a forecast origin t, I require every predictor supplied to the model to be measurable using information available at or before t.

If a feature at time t depends on observations from t+1 or later, I will treat that feature as retrospective and will not use it in the prospective forecasting pipeline.

In particular, I will not:

- center or scale using statistics computed from the full dataset
- choose a filtering parameter after inspecting future outcomes
- use a forward-looking rolling window
- use a symmetric smoother whose value at t depends on future observations
- revise a stored forecast after the realized outcome becomes known

I may still use a transformation like this for retrospective visualization or explanation, but I will label it separately from the live forecasting feature set.

## 3. How I will use signal processing prospectively

When I use signal-processing features in a prospective model, I will require them to be causal or otherwise constructed strictly from the historical information available at the forecast origin.

For example, I may use a one-sided filter if its value at time t depends only on observations up to t. I will not use a forward-backward filter or another two-sided smoother as a live forecasting feature because it uses future observations implicitly.

I may use frequency-domain analysis to study historical periodic structure. If I derive a forecasting feature from that analysis, I will recompute it using only the training window available at each historical forecast origin.

## 4. Historical validation design

I will compare models chronologically rather than by randomly shuffling time-series observations.

My preferred design is rolling-origin or expanding-window validation. At each historical forecast origin, I will:

1. choose a training window ending at time t;
2. fit every learned preprocessing step only on that training window;
3. fit the candidate model using the same information set;
4. forecast the predefined future target;
5. move the forecast origin forward and repeat the procedure;
6. aggregate forecast errors only after I have generated the historical sequence of out-of-sample predictions.

I will not use random train-test shuffling for the main forecasting comparison.

For v0.1 I use an expanding history with at least 504 completed training examples, five-return targets, and month-end historical diagnostic origins starting January 2019. Final models are fitted once using the August cutoff. For every gap g, a training origin s is eligible only when its target ends at s+g+5 on or before the fitting origin. I do not refit the frozen models using later observations.

## 5. My primary target for the first freeze

I retain the original project's five-day SPY daily-log-return RMS target. I fit separate direct forecasts for gaps of 0, 21, 43, and 63 sessions after August 31. These correspond to the first five scheduled sessions of September through December. I do not change the primary target to 20-day annualized volatility for this release.

I define the exact windows, features, fixed model settings, baselines, completed-label rule, and diagnostic schedule in [my v0.1 specification](forecast_freeze_v0_1.md). That specification settles the choices left open in the initial protocol. I retain the earlier Git version as the record of those initial plans.

## 6. Baselines I will require

I will compare every signal-processing or time-series model with simple baselines.

Candidate baselines include:

- persistence or the last observed risk estimate
- rolling historical volatility
- a constant historical mean risk estimate

I will define each baseline using the same forecast origin and information set as the candidate model.

I will not treat a more complicated method as useful merely because it fits historical data better. I will look for chronological out-of-sample improvement, interpretable additional information, or another clearly justified diagnostic.

## 7. How I will treat September 2026

I do not consider September 2026 a genuinely untouched future period for this project because I began development after September had already started and part of the month was observable.

Depending on the exact experiment, I will therefore describe September as:

- retrospective evaluation
- holdout-style evaluation
- pseudo-out-of-sample evaluation

I will not describe September results as forecasts made before September began.

## 8. How I will preserve October-December prospective forecasts

For a forecast to count as genuinely prospective, I will create and publish it before its target window begins, including the previous closing price that anchors its first close-to-close return. I preserve September predictions and October-December forecasts together before opening September outcomes. Later model changes belong to separate versions.

For each frozen forecast version, I will record:

- forecast creation date
- information cutoff
- target definition
- model version
- feature version
- forecast horizon
- point forecast
- uncertainty interval or dispersion measure, when available

After an outcome becomes known, I will leave the original committed forecast unchanged. If I improve the model later, I will create a new versioned forecast file rather than overwrite the original research record.

## 9. How I will version model changes

If I change the method after observing later data, I will assign the new method a new version and a new stated information cutoff.

For example, if I develop a wavelet or state-space extension after October begins, I may still evaluate that extension historically. I will not describe it as an August-cutoff October forecast unless that exact method and forecast had already been frozen before October data were observed.

## 10. How I will evaluate forecasts

I will choose metrics that match the final target. Likely candidates include:

- mean absolute error
- root mean squared error
- relative error versus baseline
- interval coverage, if I produce predictive intervals
- forecast stability across historical folds

Wherever possible, I will compare models on the same realized target dates so that the comparison is fair.

## 11. How I will preserve the development record

I will represent each major research stage with a separate Git commit and a descriptive message. I want the repository history to show the real development sequence rather than a reconstructed or backdated one.

At minimum, I plan to preserve separate stages for:

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

I will treat a negative result as a valid result.

If the signal-processing method does not outperform a simple baseline, I will report that directly. My research question is whether the method adds evidence of forecasting value under a controlled prospective design, not whether I can force the project to produce a positive result.

I may extend this protocol later as the project develops. If I make a change that materially affects the experiment, I will document that change explicitly rather than silently replacing the original rule.
