# Data Notes – Iran Total Reserves Excluding Gold

**Source:** IMF International Financial Statistics (IFS), mirrored on FRED (series `TRESEGIRM052N`). Full monthly time-series for 1994–2025 requires a live connection to the IMF IFS API (`dataservices.imf.org`) or FRED. Run `fetch_iran_reserves.py` with internet access to automatically retrieve and populate all available months.

**Current dataset:** Only end-of-year (December) figures are included, compiled from IMF WEO / World Bank annual publications (`FI.RES.XGLD.CD`); all other months are marked `NA`. Values are in **millions of USD**.

**Gaps & limitations:** Iran substantially reduced its IMF data reporting after the re-imposition of US sanctions in May 2018; post-2018 values are approximate and post-2019 are entirely absent from open sources. For complete monthly coverage, an IMF IFS subscription or access to CEIC/Haver Analytics is required.
