# Checks for my first forecast record

I generated the record at 05:49:09 IST on September 30, 2026. I used 2,932 price rows from January 2, 2015 through August 31, 2026, with the eight original ETFs. I found no duplicate dates, nonnumeric prices, nonfinite prices, or nonpositive prices. No September observation is present. I did not independently establish the vendor's original data vintage.

## Implementation checks

- My three unit tests passed: explicit five-return target slices, forecast invariance when later observations change or are removed, and the distinction between RMS and demeaned standard deviation.
- I compared the reused feature and immediate-target functions against the original repository at commit `e41010ec71ca615188874f9bb501fe9dd518621b`. Features and targets matched. The immediate Ridge forecast differed by approximately 3.47e-18 because I use the SVD solver.
- I reconstructed all four stored Ridge predictions from the saved coefficients, training scales, and origin features within 1e-14.
- I checked every generated output hash against the manifest.
- One raw historical Ridge prediction was negative and was projected to zero by the documented rule. None of the four final raw Ridge predictions was negative.

## Historical monthly diagnostic

I report MAE in daily log-return decimal units. These are retrospective development checks, not fresh independent tests.

| Gap in sessions | Outcomes | Ridge MAE | Constant MAE | Rolling-20 RMS MAE |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 87 | 0.003354 | 0.004237 | 0.004229 |
| 21 | 86 | 0.004531 | 0.004605 | 0.005739 |
| 43 | 85 | 0.004909 | 0.004862 | 0.006269 |
| 63 | 84 | 0.004953 | 0.004827 | 0.006228 |

The constant baseline has slightly lower MAE than Ridge at the two longest gaps. I preserve both methods rather than changing my model after seeing these scores. The April 30 fixed-origin check has only one outcome per gap. Its detailed results are in the saved metric and prediction CSVs; four outcomes do not establish general forecasting skill.

## Frozen point predictions

I show percentages of daily return RMS below. These are point estimates of risk, not predicted gains or losses, and no calibrated prediction interval is included in this release.

| Five-session window | Ridge daily RMS | Constant baseline | Rolling-20 RMS baseline |
| --- | ---: | ---: | ---: |
| September 1-8 | 0.7560% | 0.8765% | 0.5780% |
| October 1-7 | 0.8118% | 0.8791% | 0.5780% |
| November 2-6 | 0.8418% | 0.8797% | 0.5780% |
| December 1-7 | 0.8701% | 0.8817% | 0.5780% |

September is retrospective. The other three windows require publication before their preceding-close boundaries to qualify as prospective. The immutable commit link is the publication evidence; the manifest alone establishes only the recorded generation time.
