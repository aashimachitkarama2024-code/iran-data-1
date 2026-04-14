# iran-data-1

Monthly data on **Total Reserves Excluding Gold** for Iran (Islamic Republic of Iran), 1994 – 2025.

## Files

| File | Description |
|------|-------------|
| `iran_reserves_excluding_gold.csv` | Clean CSV (`Date`, `Total_Reserves_Excluding_Gold` in millions USD). Monthly rows 1994-01 → 2025-12; months without data are `NA`. |
| `fetch_iran_reserves.py` | Python script that retrieves data from IMF IFS, FRED, and World Bank APIs and regenerates the CSV. Run with internet access for the most complete dataset. |
| `DATA_NOTES.md` | 3-line note on sources, gaps, and how to access full data. |

## Quick start

```bash
pip install requests pandas
python fetch_iran_reserves.py
```

The script tries data sources in this order:
1. **IMF IFS API** (`dataservices.imf.org`) – monthly, authoritative
2. **FRED** (series `TRESEGIRM052N`) – monthly mirror of IMF data
3. **World Bank API** (`FI.RES.XGLD.CD`) – annual fallback (assigned to December)
4. **Hardcoded annual values** – compiled from IMF WEO / World Bank publications

## Dataset summary

- **Variable:** Total Reserves Excluding Gold
- **Country:** Iran (ISO: IRN / IR)
- **Frequency:** Monthly (1994-01 to 2025-12)
- **Units:** Millions of USD
- **Missing values:** `NA`
- **Primary source:** IMF IFS (FRED series `TRESEGIRM052N`)

See `DATA_NOTES.md` for details on gaps and access limitations.
