# What my models can answer, and where I stop

Recorded on 8 October 2026. This section covers the frozen Quant Market Lab II RMS baselines and the separately recorded EWMA experiments.

I use these models to study the magnitude of SPY's daily log returns over specified five-session windows. I want to make the scope clear: a risk forecast does not by itself answer which way the market will move, which ETF will outperform, or whether a trading strategy will make money. I separate what I calculated from what the evidence allows me to conclude.

## Questions and limits

| Question | What I can report | What I cannot conclude |
|---|---|---|
| How large might SPY's daily returns be in a specified five-session window? | A point prediction of five-return daily RMS from the constant, rolling-20 RMS, Ridge, standalone EWMA and Ridge + EWMA methods. | A guarantee, a price path, or a forecast of each day's return. |
| How close was a published prediction to its outcome? | Once all five sessions finish, actual RMS, signed error and absolute error against the unchanged prediction. | That a model is consistently better from one successful window. |
| Did adding EWMA help in the historical comparison? | Matched-window MAE and RMSE for Ridge with and without the EWMA feature. | Untouched out-of-sample success, statistical significance or guaranteed future improvement. The assessment period is development-aware. |
| How did predictions change between August 31 and October 7 cutoffs? | Predictions for the same future windows, with each cutoff and data vintage identified. | That the change was caused solely by EWMA. Updating the information set also changes signal states and eligible training labels. |
| Did recent observations change the risk signal? | The observed rolling-RMS and causal EWMA signal curves through the saved cutoff. | That every point on those curves was a forecast published before its outcome. |
| Will SPY rise or fall? | No directional prediction from these RMS models. | A positive or negative expected return from the magnitude forecast. |
| Which ETF will perform best? | Descriptive observed profiles for eight ETFs; the published forecast target is SPY RMS. | Future ETF return ranking, outperformance or an optimal allocation. |
| What will the whole month's risk be? | Only the explicitly named first five trading sessions. | Whole-month November or December volatility, or five-day cumulative return volatility. |
| What is the probability of a crash or a specified loss? | No calibrated probability from the current implementation. | Validated tail probabilities, Value at Risk, Expected Shortfall or prediction intervals. |
| Can I trade profitably using these forecasts? | No established trading result. | Profitability without a tested decision rule, transaction costs, slippage and execution assumptions. |
| Will the model work in a different market regime? | Its recorded behavior on the studied windows. | Robustness to new regimes, extreme shocks or assets not tested prospectively. |
| Does a lower forecast mean an ETF is safer overall? | A lower predicted RMS for this target and information set. | Lower liquidity, credit, drawdown or every other form of risk. |

## Why magnitude does not give direction

For daily log returns r, I predict the target

$$
y=\sqrt{\frac{1}{5}\sum_{j=1}^{5}r_j^2}.
$$

For example, five returns of +1% and five returns of -1% both have RMS 1%, although their directions are opposite. Squaring removes the sign. RMS also includes the mean component:

$$
\mathrm{RMS}^2=\mathrm{SD}_{\mathrm{population}}^2+\overline r^2.
$$

I therefore do not describe RMS as exactly the same as demeaned standard deviation. My displayed percentages are daily RMS over five observations, without annualization. I do not interpret them as a forecast of the cumulative five-day return.

## How I distinguish the evidence

| Record | What it establishes | Boundary |
|---|---|---|
| Original frozen October RMS forecasts and completed evaluation | The predictions were preserved before the target anchoring close, and I can measure their errors on the completed window. | One prospective window is limited evidence. The later Yahoo reconciliation changes source precision, not the forecasts. |
| Earlier decay selection and matched historical assessment | The selected parameters and measured historical errors under the documented walk-forward rules. | Historical assessment is development-aware; a current adjusted-price vintage is not proof of point-in-time vendor history at every earlier origin. |
| September/October EWMA calculations made on October 8 | Retrospective comparisons using an August information cutoff. | An earlier data cutoff does not make a later-created calculation a prospective forecast. |
| November/December EWMA freezes published on October 8 | Fixed predictions with documented cutoffs, inputs, parameters and publication evidence. | Their actual outcomes and prospective errors are not yet available. |
| Verified original August CSV and the later Yahoo download | Exact recovery of the original input and measured differences between data vintages. | The cause of each provider adjustment is not independently established. Small differences here do not guarantee that future revisions will always be small. |

## Specific limitations of my implementations

Standalone EWMA carries its cutoff second moment forward, so its November and December predictions are equal at the same cutoff. That is a persistence assumption, not evidence that risk will stay constant. The square root of a forecast second moment is a plug-in prediction; it is not an exact conditional expectation of the future square-root RMS target.

I selected decays on earlier gap-zero five-session windows and transferred them to the delayed future windows. I have not established that those choices are optimal at the longer lead times. Ridge is a linear model with the documented features; omitted information and changing relationships can affect its predictions. Projecting a negative Ridge prediction to zero enforces a valid output range, but does not establish forecast accuracy.

I reviewed alternative methods and their requirements. I do not claim that reviewing their equations means I fitted all of them, or that choosing EWMA establishes superiority over methods not compared experimentally. Code tests verify particular calculations and timing rules; they do not prove economic predictability.

## What would allow stronger conclusions

I will keep each published prediction unchanged and score it after its exact target window completes. More prospective matched windows are needed to assess consistency. A claim about uncertainty would require a separately validated interval or distribution model. A directional or ETF-ranking claim would need a different target and experiment. A profitability claim would need a separate trading study with realistic costs and execution.

I preserved my original price file and verified its frozen hash. Comparing it with a later download showed me that adjusted historical prices can differ between download vintages. I now identify the input snapshot explicitly and retain each source-specific result rather than silently replacing the underlying data.

My conclusion is deliberately limited: I can report the predictions, the observations and the errors for the defined experiment. I cannot turn those measurements into claims about direction, broad model superiority or profitability without further evidence.

## Supporting records

- [Original October evaluation and Yahoo reconciliation](october_2026_baseline_evaluation.md).
- [EWMA equations, algorithm and complexity](ewma_experiment.md).
- [EWMA freezes and historical comparisons](ewma_freeze_2026-10-08.md).
- [Original input verification and data-vintage comparison](original_august_verification.md).
- [Alternative methods and their execution requirements](signal_processing_methods_review.md).



## My autocorrelation diagnostic: 10 October 2026

I now use [autocorrelation](autocorrelation_analysis.md) to examine persistence in signed returns and move sizes in the preserved August data. This helps me interpret the existing rolling RMS and EWMA experiment. I also check how shared returns affect target dependence. I do not change any frozen forecast or select a new model from this diagnostic.

| What I can report | What I cannot conclude |
|---|---|
| Historical sample ACF and separate signed/size patterns. | Stationarity across all regimes, causation or profitable direction forecasting. |
| Overlap and non-overlap target ACF. | Independence from non-overlap or zero correlation alone. |
| Already saved matched model errors. | Statistical significance or general superiority from ACF. |
| Preserved future five-return RMS predictions. | Actual November/December performance before target completion. |

The rough white-noise ACF band is not robust inference for heavy-tailed clustered volatility. The overlap-only formula applies to averages of independent squared returns with finite variance of those squares; it is not an exact RMS formula. I have not reproduced the earlier draft's PACF, Ljung-Box or AR results here. Residual serial-dependence diagnostics remain planned and must respect target spacing.
