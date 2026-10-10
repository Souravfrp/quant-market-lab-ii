# Signal-processing methods I reviewed and why I chose EWMA first

Recorded on 8 October 2026. This is a method review and selection rationale, not evidence that I implemented or tested all these methods. Update on 10 October: EWMA was implemented, tested and published on October 8; its future outcomes remain pending. The other methods below remain a review, not claimed implementations.

## Existing data and research question

I already have daily adjusted prices for eight ETFs and 2,931 historical daily returns through August 31, a rolling-20 RMS baseline, Ridge features and chronological evaluation machinery. For adjusted close $A_t$,

$$
r_t=\log(A_t/A_{t-1}),\quad q_t=r_t^2,\quad
Y_t=\sqrt{\frac15\sum_{h=1}^{5}r_{t+h}^2}.
$$

My question is whether a signal constructed from past observations improves the forecast of this five-return SPY RMS. A filter estimates a current signal; a transform represents observations; a forecasting model predicts future quantities. Each needs an explicit connection to this target.

Existing historical data allow all the methods below to be attempted without collecting extra samples. That does not establish adequate sample size, model assumptions or predictive value. The six-price October outcome snapshot is not enough by itself for model selection. New experiments receive separate cutoffs and publication records; existing forecasts stay frozen.

## Methods, formulas and requirements

### Weighted moving averages

$$
v_t=\sum_{j=0}^{m-1}w_jq_{t-j},\quad w_j\ge0,\quad\sum_jw_j=1,\quad s_t=\sqrt{v_t}.
$$

**What it estimates:** weighted recent return magnitude. Equal weights with $m=20$ reproduce my rolling-RMS baseline. Using $s_t$ as a future forecast is a persistence rule, not guaranteed accuracy.

**Requirements:** past returns, window length, weights and missing-data handling. Returns are available; different windows/weights still require validation.

### EWMA

$$
v_t=\lambda v_{t-1}+(1-\lambda)q_t,\quad0<\lambda<1,\quad s_t=\sqrt{v_t}.
$$

$$
v_t=\lambda^mv_{t-m}+(1-\lambda)\sum_{j=0}^{m-1}\lambda^jq_{t-j}.
$$

**What it estimates:** a smoothed second moment with gradually declining weights. It does not predict direction. My standalone forecast rule would be $\widehat Y_t=s_t$.

**Requirements:** returns, decay parameter, seed and causal updating. Data are available; initialization, validation and tests remain necessary. The [experiment plan](signal_processing_plan.md) specifies a 20-return seed, candidate grid and comparison dates. My lambda corresponds to pandas alpha $1-\lambda$, with explicit seed handling.

### Holt level-and-trend smoothing

For a chosen observed series $x_t$,

$$
\ell_t=\alpha x_t+(1-\alpha)(\ell_{t-1}+b_{t-1}),
$$
$$
b_t=\beta(\ell_t-\ell_{t-1})+(1-\beta)b_{t-1},\quad
\widehat x_{t+h}=\ell_t+hb_t.
$$

**What it estimates:** level and trend, with trend extrapolation. This does not establish a persistent trend in financial risk.

**Requirements:** input series, initial level/trend and smoothing parameters. Existing returns supply squared returns or another risk series. Positivity and target mapping need attention; logarithmic modelling requires a zero-handling rule and careful back-transformation. Seasonal Holt–Winters additionally needs a justified seasonal period and adequate repeated cycles, which I have not established.

### General digital filters: FIR and IIR

FIR:

$$
s_t=\sum_{j=0}^{m}b_jx_{t-j}.
$$

IIR, with leading denominator coefficient normalized to one:

$$
s_t=\sum_{j=0}^{m}b_jx_{t-j}-\sum_{k=1}^{p}a_ks_{t-k}.
$$

**What they estimate:** components retained by a filter design. Low-pass filtering suppresses fast variation; it does not prove that suppressed variation is irrelevant noise. Moving averages are FIR examples; EWMA is a first-order IIR example.

**Requirements:** coefficients, initial state, order/cutoff where applicable, stability checks and forecast rule. Existing daily series suffice for daily-resolution filtering. General filters may yield negative filtered squared returns. Centered and forward-backward filters can use future observations, making their retrospective output unsuitable as an earlier live feature.

### Fourier/spectral analysis

For a trailing window of $N$ values,

$$
X_k=\sum_{n=0}^{N-1}x_ne^{-2\pi i kn/N},\quad
E_{\mathcal B}=\sum_{k\in\mathcal B}|X_k|^2.
$$

**What it describes:** frequency components and energy in selected bands. A peak does not establish a stable market cycle or produce a forecast by itself.

**Requirements:** window, sampling convention, centering/detrending, window function, frequency bands and a forecasting model using the features. Daily data allow computation, but not intraday inference. Historical transforms must use only the trailing information available at each origin.

### Wavelet analysis

A discrete-observation approximation is

$$
W(a,b)=\frac1{\sqrt a}\sum_nx_n
\overline{\psi\left(\frac{n-b}{a}\right)},\quad a>0.
$$

The wavelet $\psi$ examines scale $a$ around location $b$.

**What it describes:** time-local variation at different scales. It does not establish forecast improvement.

**Requirements:** wavelet family, scales, normalization, boundary handling and feature-to-forecast rule. Existing daily data suffice to attempt it. Centered support and endpoint treatment can introduce future information; whole-sample coefficients must not be treated as historically available features.

### AR, ARMA and ARIMA

AR:

$$
x_t=c+\sum_{j=1}^{p}\phi_jx_{t-j}+\varepsilon_t.
$$

ARMA:

$$
x_t=c+\sum_{j=1}^{p}\phi_jx_{t-j}+
\varepsilon_t+\sum_{k=1}^{q}\theta_k\varepsilon_{t-k}.
$$

ARIMA:

$$
\phi(B)(1-B)^dx_t=c+\theta(B)\varepsilon_t,\quad Bx_t=x_{t-1}.
$$

**What they model:** dependence on past observations and innovations; ARIMA also differences the series. The ARMA moving-average term means past innovations, not my rolling squared-return average.

**Requirements:** input series, lag orders, differencing where justified, fitting and residual/stability diagnostics. Existing data permit experiments on returns, absolute returns or squared returns. These targets differ; a next-day absolute-return forecast is not a five-day RMS forecast. Positivity and horizon mapping need specification.

I have now reproduced the historical ACF and target-overlap diagnostics in [my autocorrelation study](autocorrelation_analysis.md). The earlier draft's AR, PACF and Ljung-Box scores remain unverified here; I do not use them to claim success. No new forecasting model is added by the ACF diagnostic.

### State-space models and Kalman filtering

An illustrative local-level specification is

$$
z_t=z_{t-1}+\eta_t,\qquad x_t=z_t+\epsilon_t.
$$

A linear Gaussian filtering update is

$$
\widehat z_{t|t}=\widehat z_{t|t-1}
+K_t(x_t-\widehat z_{t|t-1}).
$$

**What it estimates:** a hidden state under specified dynamics/noise assumptions. Kalman filtering is an estimation procedure, not one unique market model.

**Requirements:** state/observation equations, noise variances/distributions, initial uncertainty and parameter estimation. Existing observations do not determine those assumptions. A positive-risk specification and RMS mapping remain necessary. Filtering differs from retrospective smoothing, which can use later data.

### ARCH/GARCH conditional variance models

GARCH(1,1):

$$
r_t=\mu_t+\varepsilon_t,\quad \varepsilon_t=\sigma_tz_t,
$$
$$
\sigma_t^2=\omega+\alpha\varepsilon_{t-1}^2+\beta\sigma_{t-1}^2.
$$

Typical constraints are $\omega>0$, $\alpha,\beta\ge0$; under the standard standardized-innovation specification, $\alpha+\beta<1$ supports finite unconditional variance. GJR-GARCH and EGARCH extend how shocks affect variance.

**What it models:** conditional variance persistence, not automatically the non-demeaned RMS target.

**Requirements:** mean model, variance specification, innovation distribution, constrained estimation, seed, convergence and diagnostics. Existing returns allow fitting attempts without new samples, but these choices add modelling work.

The target connection is

$$
\mathbb E[r_{t+h}^2\mid\mathcal F_t]
=\mathrm{Var}(r_{t+h}\mid\mathcal F_t)
+\mathbb E[r_{t+h}\mid\mathcal F_t]^2.
$$

A plug-in forecast $\sqrt{\frac15\sum_h\mathbb E[r_{t+h}^2\mid\mathcal F_t]}$ generally differs from $\mathbb E[Y_t\mid\mathcal F_t]$ because square root is nonlinear. I must say which quantity is scored.

## Requirements already satisfied and work still needed

| Method | Existing daily data usable without extra samples? | Additional decisions/work |
|---|---|---|
| Weighted moving average | Yes | Window, weights and validation |
| EWMA | Yes | Seed, decay selection, causal tests and forecast comparison |
| Holt | Yes | Series choice, trend settings, positivity and target mapping |
| FIR/IIR | Yes | Filter design, stability, endpoints and forecast rule |
| Fourier | Yes, at daily resolution | Spectral features and forecasting model |
| Wavelets | Yes, at daily resolution | Family, scales, boundaries and forecasting model |
| AR/ARIMA | Yes | Series/order selection, fitting, diagnostics and target mapping |
| State-space/Kalman | Yes | State/noise specification, estimation and forecast mapping |
| GARCH | Yes | Mean/variance/distribution choices, fitting and horizon aggregation |

“Yes” means observations are available to attempt the method, not that the assumptions or sample adequacy are established.

## Why EWMA is my first choice

EWMA is the closest controlled extension of my existing rolling-RMS baseline: both use squared returns; the principal change is the weighting scheme. I retain the same data transformation and five-return target. I do not need new tick data, spectral-band design, a latent-state model or a conditional-variance likelihood for this first comparison.

EWMA is not uniquely possible with my data. AR and GARCH also use existing returns. I choose it for alignment, interpretability and fewer simultaneous changes, not because the alternatives are inferior or EWMA has demonstrated better accuracy.

I have compared standalone EWMA with rolling RMS and constant baselines, and tested EWMA as an added Ridge feature on matched historical windows. The [October 8 freeze report](ewma_freeze_2026-10-08.md) records implementation, selected parameters, tests and predictions; future outcome evaluation remains pending. The [detailed plan](signal_processing_plan.md) supplies these rules. October's known outcome is not a basis for tuning an apparently prospective October forecast. Later forecasts need separate, timely publication.

## References and status

These sources inform the formulations; citations do not imply implementation or performance validation.

- [NIST smoothing](https://itl.nist.gov/div898/handbook/pmc/section4/pmc43.htm), [Holt](https://itl.nist.gov/div898/handbook/pmc/section4/pmc433.htm), [pandas EWMA](https://pandas.pydata.org/pandas-docs/version/2.2/reference/api/pandas.DataFrame.ewm.html).
- [SciPy Butterworth filters](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html), [forward-backward filtering](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.filtfilt.html), [Fourier transforms](https://docs.scipy.org/doc/scipy/tutorial/fft.html).
- [PyWavelets](https://pywavelets.readthedocs.io/en/latest/ref/cwt.html).
- [statsmodels time series](https://www.statsmodels.org/stable/tsa.html), [state space](https://www.statsmodels.org/stable/statespace.html).
- [arch GARCH](https://arch.readthedocs.io/en/stable/univariate/generated/arch.univariate.GARCH.html).

Completed: method review, formulations, selection rationale, EWMA implementation and its historical assessment and prospective freezes, plus the October 10 ACF diagnostic. Pending: future outcome evaluation and any separately specified alternative-model experiments. Historical error differences do not establish significant or universal improvement.

