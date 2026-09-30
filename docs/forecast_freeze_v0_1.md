# My first frozen SPY risk forecasts

## What I reuse

I extend [Quant AI Market Lab](https://github.com/Souravfrp/quant-ai-market-lab/tree/e41010ec71ca615188874f9bb501fe9dd518621b), at commit `e41010ec71ca615188874f9bb501fe9dd518621b`. I retain its log-return calculation, three features, five-day RMS target, standardized Ridge regression with alpha 1, and constant and trailing-20-day RMS baselines. The relevant source files are `src/compute_returns.py`, `src/regime_features.py`, `src/risk_forecasting.py`, and `src/ridge_risk_forecasting.py`.

I use an expanding training history as a fixed starting specification. It had lower aggregate historical MAE than the adaptive method in the original study, but it did not win every period. I do not run a new window or alpha search for this release. I use the SVD solver for the same Ridge objective and project negative Ridge predictions to zero. I preserve raw predictions so this change remains visible.

## What I forecast

I forecast the RMS of five daily SPY log returns. This is daily return magnitude, not the five-day cumulative return, sample standard deviation, annualized volatility, market direction, or an entire month's risk.

For adjusted price P, I calculate r_t = log(P_t / P_(t-1)). At historical origin t and gap g, my target is

    y_(t,g) = sqrt((r_(t+g+1)^2 + ... + r_(t+g+5)^2) / 5).

My inputs at t are SPY's daily log return, its trailing 20-return sample standard deviation, and the sample standard deviation of that day's returns across the eight ETFs. Both standard deviations use ddof=1. I fit the scaler only on eligible training rows.

The final input date is August 31, 2026. I fit a separate direct Ridge model for each gap. I do not invent future features or update the frozen models with September data.

| Target month | Gap in sessions | First return date | Fifth return date | Previous close anchoring the first return |
| --- | ---: | --- | --- | --- |
| September | 0 | 2026-09-01 | 2026-09-08 | 2026-08-31 |
| October | 21 | 2026-10-01 | 2026-10-07 | 2026-09-30 |
| November | 43 | 2026-11-02 | 2026-11-06 | 2026-10-30 |
| December | 63 | 2026-12-01 | 2026-12-07 | 2026-11-30 |

I use the [NYSE 2026 calendar](https://www.nyse.com/publicdocs/nyse/ICE_NYSE_2026_Yearly_Trading_Calendar.pdf). September 7 and November 26 are excluded; scheduled early-close sessions still count as sessions. These are the first five scheduled sessions in each month. If an unexpected closure changes the calendar, I preserve this original schedule and document the discrepancy before evaluation rather than silently shifting dates. Post-cutoff prices needed to calculate outcomes are evaluation inputs only.

## Training and comparisons

A training row at s is eligible at t only if s+g+5 is observable by t. I also require all features and the target to be finite and at least 504 eligible training examples. The last available training origin therefore differs by gap.

My constant baseline averages the same eligible target labels used by Ridge. My rolling baseline uses the latest 20 observed SPY returns at the information origin. Because all four forecasts share August 31 as that origin, the rolling baseline is identical across months. This is intentional.

I run a compact development check at month-end origins from January 2019, using only targets completed by April 30, 2026. I refit each gap model at each origin. I also fit once at April 30 and evaluate its four matching-gap predictions using already available May-August data. These delayed windows need not be the first five sessions of their historical calendar months: their purpose is to match the lead times exactly.

I report MAE, RMSE, and mean error separately by gap and method. The April check contains only one outcome per gap and cannot establish general superiority. Historical outcomes have been inspected during earlier development, so neither check is an untouched test. Target windows can overlap and share market conditions. I make no independence or statistical-significance claim. I retain the fixed model even if a baseline wins these checks.

## September and the prospective record

I create September predictions retrospectively. I keep September outcomes unopened until I preserve the forecast release, then use them for holdout evaluation. An August input cutoff is not evidence that I issued a forecast in August.

For October onward, I record the actual creation time and preserve the outputs on GitHub before each target starts. A close-to-close return dated October 1 starts at the September 30 US close. I therefore freeze the October forecast before that close, rather than waiting for October 1's opening bell. The code labels a forecast retrospective if its creation misses the corresponding preceding-close boundary. I also check publication timing before describing a forecast as prospective.

I save the point predictions, baseline predictions, fitted coefficients and scaling parameters, source and data hashes, package versions, training ranges, and UTC/IST creation timestamps. I never overwrite a release directory. A rerun belongs in a new directory and carries its own actual timestamp. The GitHub commit is the external publication record.

The uploaded file identifies the exact snapshot I used. Its original download timestamp has not been independently verified. Date filtering alone does not prove a point-in-time data vintage; later vendor adjustments or revisions remain a limitation. I have not loaded post-August observations for this release.

## Reproduction

I keep the raw CSV outside Git. With the original `adjusted_close.csv` in `data/raw/`, I run from the repository root:

```bash
python -m pip install -r requirements-freeze.txt
python -m unittest discover -s tests -v
python -m src.freeze_forecasts --data data/raw/adjusted_close.csv --output forecasts/reproduction_run
```

The new directory must not already exist. Numerical predictions should agree within floating-point tolerance using the same input fingerprint and recorded dependencies. Timestamps and any timing-dependent status will reflect the actual rerun, not the original issue time. I use decimal units in CSV files: 0.01 means a daily RMS of 1%.

## Scope and cost

This release establishes a prospective baseline. It does not yet implement the signal-processing extension, predictive intervals, trading decisions, or profitability analysis. I retain those as later, separately versioned work.

For n observations, p=3 features and K historical fits, target and feature construction take O(n) work for fixed horizon and asset count. Each dense SVD Ridge fit costs approximately O(n*p^2 + p^3), giving O(K*n*p^2) overall here. Working arrays require O(n*p) memory, excluding the saved historical output. I keep the search space fixed to limit both runtime and opportunities for overfitting.

## Method references

- Original definitions and findings: [five-day baselines](https://github.com/Souravfrp/quant-ai-market-lab/blob/e41010ec71ca615188874f9bb501fe9dd518621b/docs/risk_forecasting_baselines.md) and [walk-forward study](https://github.com/Souravfrp/quant-ai-market-lab/blob/e41010ec71ca615188874f9bb501fe9dd518621b/docs/walk_forward_window_selection.md).
- Implementation: [scikit-learn Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html) and [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).
- Calendar: NYSE 2026 trading calendar linked above.
