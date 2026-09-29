"""Validate the frozen market-data snapshot before I use it for forecasting.

I use this script as a hard gate between raw price data and the prospective
forecasting pipeline.  It checks that the dataset contains exactly my intended
ETF universe, ends on the 31 August 2026 cutoff, contains no later observation,
and has a clean chronological price panel.  I also print a SHA-256 fingerprint
so I can identify the exact input file used by later experiments.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


CUTOFF = pd.Timestamp("2026-08-31")
EXPECTED_ETFS = ("SPY", "QQQ", "IWM", "TLT", "GLD", "USO", "EEM", "VNQ")
DEFAULT_DATA_PATH = Path("data/raw/adjusted_close.csv")


class DataValidationError(ValueError):
    """Raised when the frozen dataset violates one of my research rules."""


def sha256_file(path: Path) -> str:
    """Return the SHA-256 fingerprint of the exact data file I validate."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_price_panel(path: Path) -> pd.DataFrame:
    """Load the adjusted-close panel and put trading dates on the index."""

    if not path.exists():
        raise FileNotFoundError(f"Data file does not exist: {path}")

    frame = pd.read_csv(path)
    if "Date" not in frame.columns:
        raise DataValidationError(
            "I expect a 'Date' column followed by the eight ETF price columns."
        )

    try:
        dates = pd.to_datetime(frame.pop("Date"), errors="raise")
    except (TypeError, ValueError) as exc:
        raise DataValidationError("I could not parse every value in the Date column.") from exc

    frame.index = pd.DatetimeIndex(dates, name="Date")
    return frame


def validate_price_panel(frame: pd.DataFrame) -> dict[str, object]:
    """Apply the cutoff, universe, ordering, missingness, and price checks."""

    if frame.empty:
        raise DataValidationError("The price panel is empty.")

    if frame.index.has_duplicates:
        duplicate_dates = frame.index[frame.index.duplicated()].unique()
        preview = ", ".join(date.strftime("%Y-%m-%d") for date in duplicate_dates[:5])
        raise DataValidationError(f"I found duplicate trading dates: {preview}")

    if not frame.index.is_monotonic_increasing:
        raise DataValidationError("Trading dates are not strictly chronological.")

    observed_columns = tuple(frame.columns)
    missing = sorted(set(EXPECTED_ETFS) - set(observed_columns))
    extra = sorted(set(observed_columns) - set(EXPECTED_ETFS))
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing={missing}")
        if extra:
            details.append(f"unexpected={extra}")
        raise DataValidationError(
            "The ETF universe does not match my frozen eight-asset universe: "
            + "; ".join(details)
        )

    # I keep the column order fixed so every downstream matrix uses the same
    # asset ordering rather than depending on how a CSV happened to be saved.
    frame = frame.loc[:, list(EXPECTED_ETFS)].apply(pd.to_numeric, errors="coerce")

    if frame.isna().any().any():
        bad = frame.isna().sum()
        bad = bad[bad > 0].to_dict()
        raise DataValidationError(f"I found missing or non-numeric prices: {bad}")

    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise DataValidationError("I found non-finite price values.")

    if (values <= 0).any():
        raise DataValidationError("I found zero or negative adjusted prices.")

    first_date = frame.index.min().normalize()
    last_date = frame.index.max().normalize()

    post_cutoff = frame.index[frame.index.normalize() > CUTOFF]
    if len(post_cutoff) > 0:
        first_bad = post_cutoff.min().strftime("%Y-%m-%d")
        raise DataValidationError(
            f"I found data after my 2026-08-31 cutoff; first violating date: {first_bad}."
        )

    if last_date != CUTOFF:
        raise DataValidationError(
            "My frozen snapshot must end exactly on 2026-08-31; "
            f"this file ends on {last_date.strftime('%Y-%m-%d')}."
        )

    return {
        "rows": int(len(frame)),
        "start_date": first_date.strftime("%Y-%m-%d"),
        "end_date": last_date.strftime("%Y-%m-%d"),
        "assets": list(EXPECTED_ETFS),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the frozen August 2026 adjusted-close snapshot."
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help=f"CSV to validate (default: {DEFAULT_DATA_PATH})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = load_price_panel(args.path)
    summary = validate_price_panel(frame)
    fingerprint = sha256_file(args.path)

    print("Frozen data validation: PASS")
    print(f"Path: {args.path}")
    print(f"Rows: {summary['rows']}")
    print(f"Date range: {summary['start_date']} to {summary['end_date']}")
    print(f"Assets: {', '.join(summary['assets'])}")
    print(f"Cutoff: {CUTOFF.strftime('%Y-%m-%d')}")
    print(f"SHA-256: {fingerprint}")


if __name__ == "__main__":
    main()
