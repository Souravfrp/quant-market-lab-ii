# November 2026 SPY evaluation inputs

## What I saved
I saved the six SPY adjusted closing prices used in my provisional November calculation. October 30 is the anchor; November 2–6 supply five returns. I used displayed historical **Adj Close** values, rounded to US cents.

## Source and provenance
- Source website: Yahoo Finance SPY historical data, https://finance.yahoo.com/quote/SPY/history/
- Yahoo chart API used in the earlier October full-precision reconciliation: https://query1.finance.yahoo.com/v8/finance/chart/SPY
- Precision here: **two decimal places only**.
- These values come from the previously prepared Yahoo-displayed-price snapshot. I did **not** obtain a new raw Yahoo chart-API payload or independently archive a full-precision November response.
- The original retrieval timestamp, raw API payload, vendor snapshot hash and independent source-to-source verification are **not available** for this provisional dataset. I do not claim otherwise.
- Data may be revised by the vendor. This snapshot should not be silently substituted for the original October source vintage.

## How I calculated the result
I used r_t = ln(A_t/A_(t-1)) and RMS = sqrt(sum(r_t^2)/5). I did not subtract the mean or annualize the result. The observed SPY RMS from these displayed prices is **0.021649520303596678**, or **2.1649520304%**.

## Preservation
This folder is a new provisional evaluation. I did not change the original forecast archives or October results. Full-precision Yahoo reconciliation, an eight-ETF profile, source fingerprints and November-specific test suite are still outstanding.
