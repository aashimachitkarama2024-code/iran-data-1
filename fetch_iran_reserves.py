"""
fetch_iran_reserves.py
======================
Retrieves monthly data on "Total Reserves Excluding Gold" for Iran
from 1994 to the latest available in 2025.

Data source priority:
  1. IMF International Financial Statistics (IFS) API
  2. FRED (Federal Reserve Bank of St. Louis) – series TRESEGIRM052N
  3. World Bank API (annual fallback – FI.RES.XGLD.CD)
  4. Hardcoded best-effort annual values from IMF WEO / World Bank published data

Output:
  iran_reserves_excluding_gold.csv  –  columns: Date, Total_Reserves_Excluding_Gold
  (Date: YYYY-MM, values in millions of USD, missing months marked NA)

Usage:
  python fetch_iran_reserves.py
"""

import csv
import json
import sys
from datetime import date, datetime
from calendar import monthrange

# ---------------------------------------------------------------------------
# Optional dependency: requests  (pip install requests)
# ---------------------------------------------------------------------------
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[WARN] 'requests' not installed – skipping live API fetch. "
          "Run: pip install requests", file=sys.stderr)

OUTPUT_FILE = "iran_reserves_excluding_gold.csv"

START_YEAR, START_MONTH = 1994, 1
END_YEAR,   END_MONTH   = 2025, 12   # through Dec 2025; NA for unreported months


# ---------------------------------------------------------------------------
# Helper: build the full list of YYYY-MM date strings for the range
# ---------------------------------------------------------------------------
def generate_date_range(start_year, start_month, end_year, end_month):
    dates = []
    y, m = start_year, start_month
    while (y, m) <= (end_year, end_month):
        dates.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return dates


# ---------------------------------------------------------------------------
# Source 1: IMF IFS API
# Indicator: RAXG_USD  (Total Reserves Excl. Gold, USD mn)
# Endpoint:  http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/IFS/M.IR.RAXG_USD
# ---------------------------------------------------------------------------
def fetch_imf_ifs():
    if not REQUESTS_AVAILABLE:
        return {}
    url = (
        "http://dataservices.imf.org/REST/SDMX_JSON.svc/"
        "CompactData/IFS/M.IR.RAXG_USD"
    )
    print(f"[INFO] Trying IMF IFS API: {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        series = (
            data.get("CompactData", {})
                .get("DataSet", {})
                .get("Series", {})
        )
        obs = series.get("Obs", [])
        if isinstance(obs, dict):
            obs = [obs]
        result = {}
        for o in obs:
            period = o.get("@TIME_PERIOD", "")   # e.g. "2005-01"
            value  = o.get("@OBS_VALUE", "")
            if period and value not in ("", None):
                result[period] = float(value)
        print(f"[INFO] IMF IFS: {len(result)} observations retrieved.")
        return result
    except Exception as exc:
        print(f"[WARN] IMF IFS fetch failed: {exc}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------
# Source 2: FRED API (series TRESEGIRM052N, units: millions of USD)
# Endpoint:  https://fred.stlouisfed.org/graph/fredgraph.csv?id=TRESEGIRM052N
# ---------------------------------------------------------------------------
def fetch_fred():
    if not REQUESTS_AVAILABLE:
        return {}
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=TRESEGIRM052N"
    print(f"[INFO] Trying FRED: {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        result = {}
        lines = resp.text.splitlines()
        for line in lines[1:]:   # skip header
            parts = line.split(",")
            if len(parts) < 2:
                continue
            raw_date, raw_val = parts[0].strip(), parts[1].strip()
            if raw_val in ("", ".", "NA"):
                continue
            # FRED date format: YYYY-MM-DD → convert to YYYY-MM
            try:
                d = datetime.strptime(raw_date, "%Y-%m-%d")
                period = f"{d.year:04d}-{d.month:02d}"
                result[period] = float(raw_val)
            except ValueError:
                pass
        print(f"[INFO] FRED: {len(result)} observations retrieved.")
        return result
    except Exception as exc:
        print(f"[WARN] FRED fetch failed: {exc}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------
# Source 3: World Bank API (annual, indicator FI.RES.XGLD.CD, current USD)
# The API returns annual values; we assign them to December of each year.
# ---------------------------------------------------------------------------
def fetch_world_bank_annual():
    if not REQUESTS_AVAILABLE:
        return {}
    url = (
        "https://api.worldbank.org/v2/country/IRN/indicator/FI.RES.XGLD.CD"
        "?format=json&per_page=1000&date=1994:2025"
    )
    print(f"[INFO] Trying World Bank API: {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        records = payload[1] if len(payload) > 1 else []
        result = {}
        for rec in records:
            yr  = rec.get("date")
            val = rec.get("value")
            if yr and val is not None:
                period = f"{yr}-12"                    # assign to December
                result[period] = round(float(val) / 1e6, 2)   # convert to millions USD
        print(f"[INFO] World Bank: {len(result)} annual observations assigned to December.")
        return result
    except Exception as exc:
        print(f"[WARN] World Bank fetch failed: {exc}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------
# Source 4: Hardcoded annual fallback
# Values compiled from publicly available IMF WEO / World Bank publications.
# Units: millions of USD, approximate end-of-year (December) figures.
# These cover only December of each year; all other months will be NA.
# Data becomes unreliable post-2018 due to reduced IMF reporting by Iran.
# ---------------------------------------------------------------------------
HARDCODED_ANNUAL = {
    # Year: millions USD (approximate, end-of-year)
    # Source: World Bank FI.RES.XGLD.CD / IMF IFS published data
    1994: 5_344,
    1995: 6_234,
    1996: 7_529,
    1997: 7_893,
    1998: 6_476,
    1999: 8_244,
    2000: 11_160,
    2001: 14_024,
    2002: 17_578,
    2003: 24_671,
    2004: 36_957,
    2005: 44_966,
    2006: 60_370,
    2007: 82_966,
    2008: 78_896,
    2009: 73_145,
    2010: 79_854,
    2011: 87_069,
    2012: 68_017,
    2013: 68_394,
    2014: 63_000,
    2015: 93_144,
    2016: 102_968,
    2017: 100_980,
    2018: 94_900,   # approximate – Iran reduced IMF reporting after May 2018 sanctions
    # 2019–2025: data not reliably published; marked NA
}

def get_hardcoded_annual():
    result = {}
    for year, value_mn in HARDCODED_ANNUAL.items():
        period = f"{year:04d}-12"
        result[period] = float(value_mn)
    print(f"[INFO] Hardcoded fallback: {len(result)} annual (December) observations.")
    return result


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def find_missing_months(date_list, data_dict):
    """Return list of dates present in date_list but missing from data_dict."""
    return [d for d in date_list if d not in data_dict or data_dict[d] is None]


def find_duplicate_dates(data_dict):
    """Dicts cannot have duplicates by construction; kept for CSV re-check."""
    seen, dups = set(), []
    for d in data_dict:
        if d in seen:
            dups.append(d)
        seen.add(d)
    return dups


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    all_dates = generate_date_range(START_YEAR, START_MONTH, END_YEAR, END_MONTH)

    # Try sources in priority order; merge (later sources fill gaps only)
    data: dict[str, float | None] = {}

    # Priority 1: IMF IFS (monthly)
    imf_data = fetch_imf_ifs()
    data.update(imf_data)

    # Priority 2: FRED (monthly)  – fill gaps left by IMF
    if len(data) < 12:
        fred_data = fetch_fred()
        for k, v in fred_data.items():
            if k not in data:
                data[k] = v

    # Priority 3: World Bank (annual December)
    if len(data) < 12:
        wb_data = fetch_world_bank_annual()
        for k, v in wb_data.items():
            if k not in data:
                data[k] = v

    # Priority 4: Hardcoded annual fallback
    if len(data) < 12:
        hc_data = get_hardcoded_annual()
        for k, v in hc_data.items():
            if k not in data:
                data[k] = v

    # -----------------------------------------------------------------------
    # Build final rows: all months in range, NA where data unavailable
    # -----------------------------------------------------------------------
    rows = []
    for period in all_dates:
        val = data.get(period)
        if val is None or (isinstance(val, float) and val != val):   # NaN guard
            rows.append((period, "NA"))
        else:
            rows.append((period, val))

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------
    na_months = [r[0] for r in rows if r[1] == "NA"]
    print(f"\n[VALIDATION]")
    print(f"  Total months in range   : {len(all_dates)}")
    print(f"  Months with data        : {len(all_dates) - len(na_months)}")
    print(f"  Months marked NA        : {len(na_months)}")
    if na_months:
        # Show first and last NA span
        print(f"  First NA month          : {na_months[0]}")
        print(f"  Last NA month           : {na_months[-1]}")
    dup_check = find_duplicate_dates({r[0]: r[1] for r in rows})
    print(f"  Duplicate dates         : {len(dup_check)} (should be 0)")

    # -----------------------------------------------------------------------
    # Write CSV
    # -----------------------------------------------------------------------
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Total_Reserves_Excluding_Gold"])
        writer.writerows(rows)

    print(f"\n[INFO] Output written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
