"""I extend my five-day SPY RMS experiment to fixed, delayed target windows."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.validate_cutoff import CUTOFF, EXPECTED_ETFS, load_price_panel, validate_price_panel, sha256_file

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_COMMIT = "e41010ec71ca615188874f9bb501fe9dd518621b"
HORIZON = 5
ALPHA = 1.0
MIN_TRAIN = 504
# I count sessions after August 31 that precede each target window.
WINDOWS = (
    ("2026-09", 0, "2026-09-01", "2026-09-08", "2026-08-31"),
    ("2026-10", 21, "2026-10-01", "2026-10-07", "2026-09-30"),
    ("2026-11", 43, "2026-11-02", "2026-11-06", "2026-10-30"),
    ("2026-12", 63, "2026-12-01", "2026-12-07", "2026-11-30"),
)


def prepare_prices(path):
    frame = load_price_panel(path)
    validate_price_panel(frame)
    if frame.index.hasnans or not frame.index.equals(frame.index.normalize()):
        raise ValueError("I require nonmissing daily session dates.")
    if frame.columns.has_duplicates:
        raise ValueError("Duplicate ETF columns.")
    return frame.loc[:, list(EXPECTED_ETFS)].apply(pd.to_numeric, errors="raise")


def features_from_returns(returns):
    """I retain the original features, including sample standard deviations."""
    spy = returns["SPY"]
    return pd.DataFrame({
        "spy_return": spy,
        "spy_volatility_20d": spy.rolling(20, min_periods=20).std(ddof=1),
        "cross_asset_dispersion": returns.std(axis=1, ddof=1),
    }).dropna()


def delayed_target(spy, gap):
    """The label at t uses returns t+gap+1 through t+gap+5."""
    if isinstance(gap, bool) or not isinstance(gap, int) or gap < 0:
        raise ValueError("Gap must be a nonnegative integer.")
    squares = np.column_stack([spy.shift(-j).to_numpy() ** 2
                               for j in range(gap + 1, gap + HORIZON + 1)])
    target = pd.Series(np.sqrt(squares.mean(axis=1)), index=spy.index)
    end = pd.Series(spy.index, index=spy.index).shift(-(gap + HORIZON))
    return target, end


def fit_at_origin(returns, features, origin, gap):
    """I use only labels completed by the origin and fit scaling on those rows."""
    target, ends = delayed_target(returns["SPY"], gap)
    eligible = features.index[(ends.reindex(features.index) <= origin)
                              & target.reindex(features.index).notna()]
    if len(eligible) < MIN_TRAIN:
        raise ValueError("Insufficient completed training examples.")
    if not ends.loc[eligible].le(origin).all():
        raise AssertionError("A training label crossed the origin.")
    model = make_pipeline(StandardScaler(), Ridge(alpha=ALPHA, solver="svd"))
    model.fit(features.loc[eligible], target.loc[eligible])
    raw = float(model.predict(features.loc[[origin]])[0])
    # RMS cannot be negative. I retain the raw value so the projection is visible.
    prediction = max(0.0, raw)
    history = returns.loc[:origin, "SPY"].iloc[-20:]
    forecasts = {"ridge_expanding": prediction,
                 "constant": float(target.loc[eligible].mean()),
                 "rolling_20d_rms": float(np.sqrt(np.mean(history.to_numpy() ** 2)))}
    scaler = model.named_steps["standardscaler"]
    ridge = model.named_steps["ridge"]
    detail = {
        "gap_sessions": gap, "training_examples": len(eligible),
        "first_training_origin": str(eligible[0].date()),
        "last_training_origin": str(eligible[-1].date()),
        "last_training_target_end": str(ends.loc[eligible].max().date()),
        "feature_names": list(features.columns),
        "forecast_features": features.loc[origin].tolist(),
        "scaler_mean": scaler.mean_.tolist(), "scaler_scale": scaler.scale_.tolist(),
        "ridge_coefficients": ridge.coef_.tolist(), "ridge_intercept": float(ridge.intercept_),
        "raw_ridge_forecast": raw,
    }
    return forecasts, detail


def historical_check(returns, features):
    """I reuse monthly historical origins, with no tuning on their scores."""
    historical = returns.loc[:"2026-04-30"]
    origins = historical.groupby(historical.index.to_period("M")).tail(1).index
    origins = origins[origins >= pd.Timestamp("2019-01-01")]
    rows = []
    for origin in origins:
        pos = returns.index.get_loc(origin)
        for _, gap, _, _, _ in WINDOWS:
            end_pos = pos + gap + HORIZON
            if end_pos >= len(returns):
                continue
            end = returns.index[end_pos]
            # Pre-April completed labels form the historical check. April 30
            # separately supplies four frozen-origin May-August diagnostics.
            if end > pd.Timestamp("2026-04-30") and origin != pd.Timestamp("2026-04-30"):
                continue
            forecasts, detail = fit_at_origin(returns, features, origin, gap)
            actual = float(np.sqrt(np.mean(returns["SPY"].iloc[pos+gap+1:end_pos+1].to_numpy() ** 2)))
            for method, pred in forecasts.items():
                rows.append({"evaluation": "april_fixed_origin" if str(origin.date()) == "2026-04-30" else "historical_monthly",
                             "origin": str(origin.date()), "gap_sessions": gap,
                             "target_start": str(returns.index[pos+gap+1].date()),
                             "target_end": str(end.date()), "method": method,
                             "forecast": pred, "actual": actual,
                             "raw_ridge_forecast": detail["raw_ridge_forecast"] if method == "ridge_expanding" else None})
    result = pd.DataFrame(rows)
    summaries = []
    for (evaluation, gap, method), block in result.groupby(["evaluation", "gap_sessions", "method"]):
        error = block.forecast - block.actual
        summaries.append({"evaluation": evaluation, "gap_sessions": int(gap), "method": method,
                          "n": len(block), "mae": float(error.abs().mean()),
                          "rmse": float(np.sqrt(np.mean(error ** 2))),
                          "mean_error": float(error.mean())})
    return result, pd.DataFrame(summaries)


def source_fingerprints():
    paths = ["src/freeze_forecasts.py", "src/validate_cutoff.py", "docs/forecast_freeze_v0_1.md", "requirements-freeze.txt"]
    return {p: sha256_file(ROOT / p) for p in paths}


def generate(path, output):
    if output.exists():
        raise FileExistsError("I do not overwrite a forecast record. Choose a new output directory.")
    prices = prepare_prices(path)
    returns = np.log(prices / prices.shift(1)).iloc[1:]
    features = features_from_returns(returns)
    historical, metrics = historical_check(returns, features)
    now = datetime.now(timezone.utc)
    created = now.isoformat()
    records, models = [], []
    for month, gap, start, end, previous_close in WINDOWS:
        values, model = fit_at_origin(returns, features, CUTOFF, gap)
        models.append({"target_month": month, **model})
        boundary = datetime.fromisoformat(previous_close + "T16:00:00").replace(tzinfo=ZoneInfo("America/New_York"))
        status = "prospective" if month != "2026-09" and now < boundary else "retrospective"
        for method, value in values.items():
            records.append({"target_month": month, "asset": "SPY", "method": method,
                            "information_cutoff": "2026-08-31", "gap_sessions": gap,
                            "target_start": start, "target_end": end, "return_anchor_date": previous_close,
                            "horizon_sessions": HORIZON, "target": "five_day_daily_log_return_rms",
                            "forecast_decimal": value, "evaluation_status": status,
                            "created_at_utc": created})
    forecasts = pd.DataFrame(records)
    if not np.isfinite(forecasts.forecast_decimal).all():
        raise ValueError("Nonfinite forecast.")
    manifest = {"created_at_utc": created, "created_at_ist": now.astimezone(ZoneInfo("Asia/Kolkata")).isoformat(),
                "information_cutoff": "2026-08-31", "input_sha256": sha256_file(path),
                "price_rows": len(prices), "first_date": str(prices.index[0].date()),
                "last_date": str(prices.index[-1].date()), "assets": list(prices.columns),
                "original_repository": "https://github.com/Souravfrp/quant-ai-market-lab",
                "original_commit": ORIGINAL_COMMIT,
                "alpha": ALPHA, "solver": "svd", "training_window": "expanding",
                "selection": "Fixed before this run; no selection from new diagnostic scores",
                "ridge_nonnegative_projection": True, "source_sha256": source_fingerprints(),
                "versions": {"python": platform.python_version(), "numpy": np.__version__,
                             "pandas": pd.__version__, "scikit-learn": sklearn.__version__},
                "data_vintage": "User-supplied original-project snapshot; original download timestamp not independently verified",
                "september_outcomes_loaded": False,
                "scope": "First five scheduled sessions of each month, not whole-month risk or return direction",
                "publication_note": "Creation time is not publication proof; the GitHub commit establishes the external record."}
    output.mkdir(parents=True)
    forecasts.to_csv(output / "forecasts.csv", index=False, float_format="%.17g")
    historical.to_csv(output / "historical_predictions.csv", index=False, float_format="%.17g")
    metrics.to_csv(output / "historical_metrics.csv", index=False, float_format="%.17g")
    (output / "models.json").write_text(json.dumps(models, indent=2, allow_nan=False) + "\n")
    manifest["output_sha256"] = {p.name: sha256_file(p) for p in sorted(output.iterdir())}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    print(forecasts[["target_month", "method", "forecast_decimal", "evaluation_status"]].to_string(index=False))
    print("Saved:", output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/raw/adjusted_close.csv")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generate(args.data, args.output)


if __name__ == "__main__":
    main()
