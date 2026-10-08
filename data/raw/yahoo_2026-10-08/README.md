# Yahoo snapshot retrieved 8 October 2026

I saved the complete adjusted-close series for all eight ETFs, starting 2 January 2015. The August file ends 31 August (2,932 rows); the October file ends 7 October (2,958 rows). Dates match the exchange_calendars 4.13.2 XNYS schedule; the 2026 holidays were checked against the NYSE published schedule. All prices are positive, finite and complete.

The August CSV hash differs from the original frozen snapshot. This is a reconstruction, not a recovered original file. A hash difference does not establish a price difference: serialization, provider revisions or later dividend adjustments may contribute. I cannot compare individual original prices without that file. I keep the original forecasts unchanged.

The two provenance JSON files record source fields, per-ticker retrieval times and raw-response hashes. responses.tar.gz preserves the exact eight API responses. Reproduce the CSVs by extracting those responses into a new directory and running src.download_ewma_inputs with --assemble-existing-responses. Fetching again is a new data vintage and may produce different adjusted prices.

References: https://www.nyse.com/trade/hours-calendars and https://github.com/gerrymanoim/exchange_calendars .
