# My first signal-processing experiment

Planning record: 7 October 2026, before the US regular session for that date. This is a new research plan, not a backdated August decision. I have not fitted or selected the EWMA extension, generated its forecasts, or established that it improves accuracy.

## Implementation update: 8 October 2026

The causal recurrence and cutoff-specific experiment runner are now implemented and tested. Numerical fitting and forecast publication remain blocked by the missing complete adjusted-price history. The [fixed experiment protocol](ewma_experiment.md) documents the implemented seed, decay grid, validation rule, two cutoffs, algorithm complexity and commands. This original planning record is retained as dated context.

## What I want to find out

I want to test whether weighting recent squared SPY returns more heavily helps forecast the RMS of the next five returns. I already have a rolling-20-return RMS baseline and a Ridge model. The new experiment should show whether a different weighting scheme adds information, rather than just adding a more complicated name.

My current published forecasts are Ridge, a constant baseline and rolling RMS. They are not signal-processing forecasts from this new experiment. The [dated evaluation note](evaluation_status_2026-10-07.md) distinguishes those forecasts from the work I am planning now.

## Why I start with exponential smoothing

I choose a one-sided exponentially weighted moving average (EWMA) of squared returns. It gives me one state and one weighting parameter, is nonnegative, and can be updated after each observed return. I can explain every input and check that a future return cannot change an earlier signal. NIST describes exponential weighting; pandas documents the corresponding recursive calculation [5, 6 in references.md].

The rolling baseline assigns equal weight to the last 20 observations and then drops an observation abruptly. EWMA reduces the weight gradually. This is the particular difference I want to test. I do not assume gradual weighting is better.

My separate autocorrelation draft motivated a closer look at move-size persistence. Its implementation and reported scores are not yet in this repository. I do not use those unverified scores as evidence that EWMA works. Its next-day absolute-return target also differs from this experiment's five-day RMS target.

| Alternative | Why I am not starting there | What would justify testing it later |
|---|---|---|
| Fourier/spectral features | A frequency peak does not by itself give a causal risk forecast. Window length, stability and feature construction would introduce more choices. | A stable historical structure, tested using training-window-only transforms. |
| Wavelet features | Wavelet family, scale, boundary treatment and reconstruction introduce more choices; some constructions use future observations. | Evidence that time-local, multi-scale features add value under matched chronological tests. |
| State-space risk model | It requires a latent-state and observation specification, initialization and parameter estimation. | A reason to model latent risk explicitly and an identifiable model that improves the comparison. |
| GARCH-type model | It introduces a conditional-variance model and parameter constraints, rather than only a new smoothing rule. | A separate volatility-model question with checked estimation and diagnostic assumptions. |
| Two-sided smoothing | A smoothed value can depend on later observations. For example, forward-backward filtering uses both directions [8]. | Retrospective visualization only, unless replaced by a causal forecasting construction. |

This is a choice of first experiment, not proof that the alternatives are inferior. I leave them for separate versions so that I can identify which change affects the result.

## What remains fixed

For adjusted close $P_t$, I use $r_t=\log(P_t/P_{t-1})$ and

$$Y_{t,0}=\sqrt{\frac15\sum_{j=1}^{5}r_{t+j}^2}.$$

This is RMS of daily returns: it is not whole-month risk, cumulative return or demeaned standard deviation. I retain this target to compare with the original project. My first new historical comparison is gap zero. I do not compare its scores with the frozen delayed-gap October forecast as if they were the same experiment.

## How I construct the signal

Let $0<\lambda<1$. After the first 20 observed returns, I initialize

$$v_{20}=\frac1{20}\sum_{i=1}^{20}r_i^2.$$

For $t>20$ I update

$$v_t=\lambda v_{t-1}+(1-\lambda)r_t^2,\qquad s_t=\sqrt{v_t}.$$

I make the first 19 signal values unavailable. This initialization uses only observations already available at its first signal date; I do not fill earlier dates with information from day 20. In an expanding historical run the state is carried forward from this documented initialization. If I change to a rolling training window, I must document any reinitialization separately.

Expanding the recursion for $m$ updates gives

$$v_t=\lambda^m v_{t-m}+(1-\lambda)\sum_{j=0}^{m-1}\lambda^j r_{t-j}^2.$$

The weights are nonnegative and sum to one including the initial-state term. Larger $\lambda$ retains more history; it does not mean a forecast is more accurate. The half-life in sessions is

$$h_{1/2}=\frac{\log(1/2)}{\log\lambda}.$$

With pandas, my update corresponds to `alpha=1-lambda, adjust=False`, but the default first-observation initialization differs from my 20-observation initialization. I must seed the recurrence explicitly and test equivalence after that seed, rather than assume one library call reproduces my plan.

I smooth squared returns because this preserves move magnitude when signs change. Smoothing signed returns could make large positive and negative moves cancel. I call $v_t$ a smoothed second moment, not an estimated demeaned variance unless I introduce additional assumptions. The signal is causal after observing the close at $t$.

## Why this is a signal-processing operation

Writing $u_t=r_t^2$ makes the recurrence a causal first-order filter: $v_t=\lambda v_{t-1}+(1-\lambda)u_t$. Its zero-state impulse weights are $h_j=(1-\lambda)\lambda^j$ for $j\ge0$. The transfer function, apart from the separately documented initial-state contribution, is

$$H(z)=\frac{1-\lambda}{1-\lambda z^{-1}}.$$

The pole is at $z=\lambda$, inside the unit circle. The impulse weights are summable, so bounded inputs give bounded outputs. At frequency zero the gain is one; at the highest discrete frequency the magnitude is $(1-\lambda)/(1+\lambda)$. This explains why the operation smooths rapid changes in squared-return magnitude. It does not establish that those changes are noise or that smoothing improves forecasts. Larger lambda also creates more lag after a shock. The square-root step is nonlinear; I apply this linear-filter interpretation to $v_t$, not to the complete map from signed returns to $s_t$.

## Two comparisons, with different questions

1. **EWMA alone:** $\widehat Y^{EWMA}_{t,0}=s_t$. This asks whether weighting alone improves on the rolling-RMS baseline. It is a persistence forecast. Even if $v_t$ approximates a conditional second moment, $\sqrt{v_t}$ is not automatically the conditional expectation of future RMS: square root is nonlinear.
2. **Ridge plus EWMA:** add $s_t$ to the existing three features, using the existing Ridge penalty as the starting fixed specification. Compare the original three-feature Ridge with the four-feature Ridge on exactly the same dates. This asks whether the signal adds information after the existing features.

I retain the constant, rolling-20-day RMS and original Ridge baselines. A standalone EWMA and an augmented Ridge answer different questions; I report them separately. No parameters or features from this new comparison are written into the existing v0.1 models or forecast files.

## How I choose parameters and compare fairly

My planned candidate grid is $\lambda\in\{0.80,0.90,0.94,0.97,0.99\}$. These are experiment choices, not asserted optimal financial constants. I will check sensitivity across the grid and avoid enlarging it after seeing the final comparison just to obtain a better score.

- Use month-end gap-zero forecast origins, with at least 504 completed training labels. Use only labels whose fifth return is observed by each fitting origin.
- Use earlier expanding-origin validation windows with target endpoints in 2021–2022 to select lambda by MAE. Initialize and update each candidate causally, and fit scaling and Ridge only on the eligible training rows at each origin.
- Select lambda separately for EWMA alone and for the augmented Ridge, since their loss functions can favor different settings. Fix the selected choices before the later historical comparison.
- Assess the frozen choices on matching month-end windows with target endpoints from January 2023 through August 2026. These are later chronological historical comparisons, not untouched prospective evidence: these years have already appeared in project development.
- For ties at recorded numerical precision, prefer the larger lambda as a predeclared slower-changing rule; report the tie rather than claim a unique optimum. The comparison script must record its numerical precision.
- Report MAE as the primary metric, RMSE and mean error as additional metrics, errors by period, number of matched windows and signal availability. Report when a baseline wins.

The mathematical notes define training eligibility and metrics. If I later use daily overlapping targets instead, I must label the dependence and use an appropriate uncertainty calculation; five daily labels are not five independent windows. Even non-overlapping targets can remain dependent through market conditions.

## Checks before I freeze a new forecast

I need a direct-loop recurrence check, nonnegativity, correct initialization and missing-prefix handling, a constant-return case, a shock-decay case, and prefix invariance after changing future observations. I also need checks that validation choices use only earlier data, scaling uses only training rows, and targets end before the fit. These are planned checks, not tests already passed.

A genuine prospective new forecast must be published before its target window and, under my existing protocol, before the closing price that anchors its first return. I will choose a cutoff and any session gap that give enough time to obtain the input closes, run the checks and publish. I will not claim a same-close gap-zero freeze was published before a close it needed as input.

If I use September or the first four October returns to choose the method, those outcomes become development information. I will record that choice and move the final prospective assessment to a later window. A new August-cutoff model created on October 7 is still a new October-created model, not a forecast made in August.

## Cost and reproducibility

For $n$ returns, one EWMA pass takes $O(n)$ operations. A single update needs $O(1)$ time and state; retaining the whole signal needs $O(n)$ storage. With $L$ candidate lambda values, computing their histories costs $O(Ln)$. With $p$ features and $K$ historical fits per candidate, dense SVD Ridge fitting costs approximately $O(LK(np^2+p^3))$ using $n$ as an upper bound for each training length. The augmented model has $p=4$ rather than $p=3$. These are operation estimates, not benchmarks.

I will save the data and source fingerprints, candidate grid, split endpoints, initialization, selected parameters, matched forecasts and actual values. The plots must show dated observed returns, the causal signal, target endpoints, forecasts and errors with units. A smooth line will represent the signal, not a fictitious daily path for a five-return forecast.

## Work completed in this update

I have recorded the plan, clarified the timing, preserved a five-price partial-October evaluation snapshot with provenance, and added reproducible status figures. I have not implemented the EWMA forecasting experiment. The October plots are observations and frozen-baseline values, not results of the proposed signal model.


## Method review added 8 October 2026

My [method review](signal_processing_methods_review.md) describes alternative formulations, what each estimates and execution requirements before explaining why I selected EWMA first. Several alternatives can also use my existing observations without extra samples. This is a choice based on alignment with rolling RMS and fewer modelling decisions, not measured superiority. Implementation remains pending.
