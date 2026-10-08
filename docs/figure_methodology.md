# How I read my five-day risk figures

I use three figures to explain the same target under different information cutoffs. These are established methods; my contribution here is the experiment, implementation, checks and interpretation. My sources are listed in [references](references.md).

## What one point means

I index trading sessions by integers. For adjusted close $P_t>0$, my log return is $r_t=\log(P_t/P_{t-1})$. At origin $t$, after skipping $g$ sessions, my target is

$$y_{t,g}=\sqrt{\frac15\sum_{j=1}^5 r_{t+g+j}^2}.$$

One point summarizes five trading sessions, not five calendar days or the whole month. February 2019 uses returns dated February 1, 4, 5, 6 and 7, with January 31 as the origin. I plot that window at February 1.

Geometrically, the five returns form a vector $v\in\mathbb R^5$, and RMS is $\|v\|_2/\sqrt5$. Squaring prevents positive and negative movements from cancelling. RMS measures movement size rather than direction. It is not cumulative return, annualized volatility or sample standard deviation. With five-return mean $\bar r$ and sample variance $s^2$, expanding the squares gives $y^2=4s^2/5+\bar r^2$.

CSV values are decimals. Figures multiply them by 100: 0.006646 is approximately 0.6646% daily RMS. Differences between displayed percentages are percentage points (pp).

## Features and training eligibility

My three inputs are SPY's current log return, its trailing 20-return sample standard deviation, and the same-day sample standard deviation across the eight ETFs:

$$x_t=(r_{SPY,t},s_{20,t},d_t),$$
$$s_{20,t}=\sqrt{\frac1{19}\sum_{j=0}^{19}(r_{SPY,t-j}-\bar r_{20,t})^2},\qquad d_t=\sqrt{\frac17\sum_{a=1}^8(r_{a,t}-\bar r_{assets,t})^2}.$$

Both features use ddof=1. The 20-day standard-deviation feature differs from the RMS baseline. I drop unavailable feature rows rather than invent returns.

At origin $t$, a training origin $s$ is eligible only if its entire target has ended:

$$\mathcal E_{t,g}=\{s:s+g+5\le t,\ x_s\text{ and }y_{s,g}\text{ available}\}.$$

Addition means session positions, not calendar days. I require at least 504 eligible examples. Each gap has a separate direct model; I do not chain invented daily forecasts.

## Ridge, optimization and geometry

I estimate feature means and scales on eligible training rows only, then apply $z_{s,k}=(x_{s,k}-\mu_k)/\sigma_k$. StandardScaler uses population variance, ddof=0, and scale 1 for a zero-variance feature [2]. My objective is

$$\min_{b,\beta}\sum_{s\in\mathcal E_{t,g}}(y_{s,g}-b-z_s^\top\beta)^2+\alpha\|\beta\|_2^2,\qquad\alpha=1.$$

The intercept is unpenalized. This is a sum loss: replacing it with a mean loss without rescaling alpha changes the model. I use scikit-learn's SVD solver [1]. For centered design $Z$ and target $y_c$, the normal equation is $(Z^\top Z+\alpha I)\beta=Z^\top y_c$. If $Z=UDV^\top$, then

$$\beta=V\,\mathrm{diag}\left(\frac{d_j}{d_j^2+\alpha}\right)U^\top y_c.$$

This is an algebraic explanation, not an instruction to explicitly invert a matrix. The positive penalty makes the coefficient problem strictly convex and shrinks unstable directions. Stability does not guarantee future accuracy.

I use $\hat y_{t,g}=\max(0,b+z_t^\top\beta)$ and retain the raw prediction. This projects onto the nonnegative half-line. For a nonnegative target, projection cannot increase absolute or squared error.

## Baselines

My constant baseline is the mean of the same eligible target labels:

$$c_{t,g}=\frac1{|\mathcal E_{t,g}|}\sum_{s\in\mathcal E_{t,g}}y_{s,g}.$$

It is constant for one fit, but can change with the origin or gap. The mean minimizes training squared error, not necessarily absolute error. My rolling baseline is

$$q_t=\sqrt{\frac1{20}\sum_{j=0}^{19}r_{SPY,t-j}^2}.$$

It depends on the origin, not the gap. The four April-origin values are therefore identical; September changes because its origin is August 31.

## Which windows I show

| Figure | Saved-row selection | Interpretation |
|---|---|---|
| Historical | historical_monthly, gap 0 | 87 monthly windows, February 1, 2019 through April 8, 2026; historical development |
| May–September | april_fixed_origin, then September | Four April-origin checks plus a separate August-origin retrospective check |
| September detail | September predictions and five observed returns | One retrospective window, September 1, 2, 3, 4 and 8 |

| Target | Information origin | Gap in sessions | First–fifth return dates, 2026 |
|---|---|---:|---|
| May | April 30 | 0 | May 1–7 |
| June | April 30 | 21 | June 2–8 |
| July | April 30 | 43 | July 6–10 |
| August | April 30 | 63 | August 3–7 |
| September | August 31 | 0 | September 1–8 |

The May–August windows match fixed session gaps and are not all the first five sessions of their months. September's zero gap is measured from August 31. [The window table](../results/figure_windows.csv) records origins and endpoints for every selected window; [the value table](../results/figure_values.csv) records every plotted prediction and observation.

Separate markers represent separate windows. Vertical segments show within-window absolute error; they are neither interpolation nor confidence intervals. September shading marks the changed cutoff. In the detailed figure, the observed-RMS horizontal line compares methods, not dates. Daily bars are observed returns, not daily forecasts.

## Metrics and interpretation

With $e_i=\hat y_i-y_i$ over $N$ matched windows,

$$MAE=\frac1N\sum_i|e_i|,\qquad RMSE=\sqrt{\frac1N\sum_i e_i^2},\qquad ME=\frac1N\sum_i e_i.$$

Positive ME means average overprediction. On the same 87 historical windows, MAE is approximately 0.3354 pp for Ridge, 0.4229 pp for rolling RMS and 0.4237 pp for the constant. September's observed RMS is approximately 0.6646%; absolute errors are 0.0866, 0.0914 and 0.2120 pp for rolling RMS, Ridge and constant respectively. Ridge has the lower historical average error, while rolling RMS is slightly closer in this one September window. Neither result establishes universal superiority.

## Algorithm and cost

1. Validate prices; calculate causal log returns and features.
2. For each origin and fixed gap, select only completed labels.
3. Fit the scaler and Ridge; calculate both baselines from allowed information.
4. Preserve predictions, target dates, raw Ridge values, model parameters and provenance.
5. For plotting, read those saved outputs, select the documented rows, verify matching windows, and recompute September RMS from six closes.
6. Calculate errors and render discrete comparisons. Plotting does not fit or tune models.

For $n$ sessions, $p=3$ features, fixed horizon and eight assets, preparation is $O(n)$. Dense SVD fitting is approximately $O(np^2+p^3)$ per fit, or $O(K(np^2+p^3))$ for $K$ origin-gap fits, with $O(np)$ working storage. Plotting $M$ saved rows takes $O(M\log M)$ for sorting and $O(M)$ memory. These are operation estimates, not measured timing claims.

I use Ridge as a small, inspectable regularized model. Rolling RMS asks whether recent movement size is already enough; the constant asks whether features improve over a historical level. Shorter training windows or nonlinear methods need a separate chronological comparison with identical target windows and metrics, and preprocessing fitted within each training split. I will not choose a method using these outcomes and then call them untouched evidence.

## Limits and future work

Historical choices were informed by earlier development. Expanding fits share observations, and the wider multi-gap archive can contain overlapping targets. I make no independence or significance claim. Adjusted-price revisions and the unverified original download timestamp limit point-in-time claims: a date cutoff does not prove data vintage.

September predictions were created September 30, after their target ended. They are retrospective despite the August cutoff. The original fixed-August-cutoff October–December predictions already exist in the frozen release. The proposed month-end refreshed, gap-zero experiment is separate and has not been generated here.

## Reproduction

The three approved PNGs remain in results/figures. I provide a reconstruction script:

```bash
python -m pip install -r requirements-figures.txt
python -m src.plot_risk_comparisons
```

It validates source numbers, writes the window/value tables, and produces comparable figures in results/figures/rebuilt. Layout can differ from the approved rendering; the data and meanings are reproduced. It does not overwrite approved PNGs or frozen forecasts. September's six-close input is a researcher-supplied adjusted-price snapshot, not a fresh vendor verification. The original manifest's source hashes describe the frozen release; I preserve that specification and add this companion explanation.



## Signal-processing extension recorded 7 October 2026

The [EWMA experiment plan](signal_processing_plan.md) adds a separate causal-signal question to these baseline notes. It defines the smoothed second moment $v_t=\lambda v_{t-1}+(1-\lambda)r_t^2$, initialization, geometric weighting and half-life, and distinguishes an EWMA-only persistence forecast from Ridge with an extra signal feature. The proposed choices and complexity are explained there; no improvement result is claimed.

For a gap-zero fit at origin $t$, training labels satisfy $s+5\le t$. With $s_t=\sqrt{v_t}$, the new feature vector would be $x'_t=(r_{SPY,t},s_{20,t},d_t,s_t)$. Scaling still uses eligible training rows only. A signal computed after close $t$ cannot be a prediction of that day's already observed return.

If I compare two methods on matched target windows, the primary MAE improvement is $100(MAE_{baseline}-MAE_{candidate})/MAE_{baseline}$ percent, provided the baseline MAE is nonzero. It is an error reduction, not a return or investment performance measure. A small reduction does not establish statistical significance. The validation stage selects lambda; later historical assessment is reported separately and remains development-aware.

For the incomplete October window, the [dated status note](evaluation_status_2026-10-07.md) distinguishes $\sqrt{S_4/4}$ from the final $\sqrt{(S_4+r_5^2)/5}$. Both equations are needed to prevent a four-return description being mistaken for the frozen five-return target. The plot leaves the fifth return unavailable rather than assuming zero.


## Completed October scoring recorded 8 October 2026

The [completed-window note](october_2026_baseline_evaluation.md) now scores the five-return target using six prices from one saved adjusted-price source. It defines RMS separately from demeaned standard deviation, uses signed error (forecast minus observed) and absolute error, records the original forecast hash, and reports a last-price sensitivity for the vendor discrepancy. Each method has one forecast error for this window, not five independent daily forecast errors. The partial October 7 record remains a dated historical note. The new figures and tables do not change frozen forecasts or implement EWMA.


## Later Yahoo verification on 8 October 2026

The full-precision Yahoo adjusted prices now verify October 6 and 7. Recalculated SPY RMS remains 0.5263% and rolling-20 remains closest. The existing figures retain their cent-rounded Stock Analysis source; the [separate reconciliation](october_2026_baseline_evaluation.md#full-precision-yahoo-reconciliation) reports exact Yahoo values without altering the frozen forecasts.
