# Quant Market Lab II — Signal Processing & Prospective Forecasting

I am building Quant Market Lab II as a focused continuation of my earlier **Quant AI Market Lab** research project. My academic background is in mathematics and computer and system sciences, with research experience in probability, algorithms, optimization, randomized methods, and geometric reasoning. This project extends that foundation into quantitative finance by asking a narrower forward-looking question: whether carefully constructed market signals contain useful information for prospective risk forecasting when the information set is frozen in advance.

The purpose is not to claim that markets are reliably predictable. The purpose is to design an auditable forecasting experiment in which the cutoff date, target, features, model-selection rules, forecasts, and later evaluation are kept separate enough to expose look-ahead bias and overfitting.

## Research Question

The initial question is:

> **Using only information available through 31 August 2026, can a small set of signal-processing and time-series methods improve prospective market-risk forecasts relative to simple historical baselines?**

The first version is intentionally compact. I will define one primary forecasting target, establish simple baselines, add one principled signal-processing representation, validate chronologically, and preserve the prospective forecasts before the corresponding future periods are observed.

## Relationship to Quant AI Market Lab

The earlier project established a broader historical quantitative-research workflow covering validated ETF data, return and covariance analysis, PCA, market-condition models, Ridge and Random Forest risk forecasting, chronological evaluation, and portfolio experiments.

This repository changes the experimental question:

- **Quant AI Market Lab:** historical modelling, interpretation, validation, and portfolio analysis.
- **Quant Market Lab II:** signal extraction, fixed-cutoff forecasting, uncertainty, forecast preservation, and later realized-versus-forecast evaluation.

## Frozen Information Set

The initial research cutoff is:

**31 August 2026**

For the frozen prospective experiment, no observation after that date may be used to construct features, scale inputs, select hyperparameters, fit the frozen model, or revise the stored forecasts.

Because September 2026 is already partly observed during development, any September analysis must be labelled honestly as holdout or retrospective evaluation rather than as a forecast made before September began. Forecasts for later periods will be preserved with their Git history before those periods are evaluated.

## Initial Scope

### 1. Signal construction

I will begin with market series already motivated by the first project, including returns and volatility, and test one mathematically justified signal representation. Candidate methods include spectral analysis, causal filtering, or a state-space representation of latent risk. The first release does not need every method; the goal is to use only methods whose assumptions and limitations can be explained clearly.

### 2. Forecasting target

The first release will define one primary target before the frozen prospective model is finalized. Candidate targets include short- or medium-horizon realized volatility or another observable forward risk measure derived from future returns.

### 3. Baselines

The signal-based forecast must be compared with simple alternatives such as persistence, rolling historical volatility, or a constant historical estimate. Additional complexity is useful only if it improves a clearly defined out-of-sample metric or adds interpretable information.

### 4. Chronological validation

Model selection will use rolling or expanding historical validation. Future observations will not be shuffled into the training data. Any preprocessing that learns parameters from data must be fitted inside the corresponding training window.

### 5. Prospective forecast record

Frozen forecasts will be stored under `forecasts/` and committed before later evaluation. Original forecast files will not be silently rewritten after outcomes become known. Later model revisions will receive separate versioned outputs.

## Mathematical Focus

The project is designed to make the mathematics visible. The documentation will explain the relevant ideas behind discrete-time signals, frequency-domain representations where used, causal versus non-causal filtering, autocorrelation, state-space models where used, rolling-origin validation, forecast uncertainty, and computational complexity.

## Version Plan

### v0.1 — Prospective baseline

Freeze the research protocol, implement the first signal/forecasting pipeline, and preserve the first prospective forecasts.

### v1.0 — Signal processing & prospective forecasting

Complete the selected signal method, baselines, chronological validation, uncertainty analysis where appropriate, reproducible figures, mathematical notes, and limitations.

### Possible later extension

If the core forecasting study is complete, I may extend the repository to a separate cross-asset question: whether the same information set can support relative ETF return or risk-adjusted ranking. That would be a new research module, not a missing requirement for the first release.

## Research Standard

I want the repository to distinguish clearly between what was known when a forecast was created and what was learned afterward. Negative results are valid results. If a signal-processing method fails to outperform a simple baseline, I will report that rather than redesigning the historical forecast after seeing the outcome.

This project is a research and learning exercise, not investment advice and not evidence of future profitability.
