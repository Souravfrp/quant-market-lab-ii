# My local reproduction check

On September 30, 2026, I reproduced the frozen forecasts on my MacBook Air in my existing `quant-ai` conda environment. I checked out commit `d25b13a24f4c6ce3c75cfba2aa5aff20c3ef40ac`. This note records the terminal results I shared during the check; it does not claim an independent remote inspection of my Mac.

## Data check

I ran:

```bash
python -m src.validate_cutoff "$HOME/Documents/quant-ai-market-lab/data/raw/adjusted_close.csv"
```

The validator passed with 2,932 rows from January 2, 2015 through August 31, 2026 and all eight expected ETFs. The SHA-256 matched the frozen input exactly:

```text
637fdeb14b482a12b37abef1fce77f5f94b161c3a92ab28b28948dd3736a4c59
```

## Timing tests

I ran `python -m unittest discover -s tests -v`. All three tests passed in the reported 0.086 seconds:

- Explicit target slices and unavailable trailing labels.
- Forecast invariance to changing or removing observations after the origin, with completed training labels.
- RMS rather than demeaned standard deviation.

## Forecast reproduction

I ran the existing forecasting module against my original CSV and wrote the rerun into a temporary directory. I compared the rerun with `forecasts/2026-09-30-v0.1/forecasts.csv`, aligning both tables by target month and method.

I checked that the indexes matched and compared all 12 numerical predictions with `numpy.testing.assert_allclose`, using relative tolerance `1e-10` and absolute tolerance `1e-12`. The terminal reported:

```text
PASS: All 12 predictions match the frozen record.
```

This confirms numerical reproduction within those tolerances, not byte-for-byte equality of the output files. Rerun timestamps differ by design. I did not capture a separate local dependency-version report or compare every metadata field in this check.

I left the original forecasts and their publication commit unchanged. This check establishes reproducibility and the tested timing properties; it does not establish predictive accuracy. September outcomes were not part of this reproduction check.
