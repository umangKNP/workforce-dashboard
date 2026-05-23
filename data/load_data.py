"""
Data loader — fetches ABS Labour Force data from World Bank API,
caches to SQLite, and returns clean DataFrames for the dashboard.
"""
import json
import sqlite3
import time
from pathlib import Path

import pandas as pd
import requests

DB_PATH = Path(__file__).parent / "workforce.db"
RAW_PATH = Path(__file__).parent / "raw"
RAW_PATH.mkdir(exist_ok=True)

# World Bank indicators for Australia
INDICATORS = {
    "SL.UEM.TOTL.ZS":   "Unemployment Rate (%)",
    "SL.EMP.TOTL.SP.ZS":"Employment-to-Population Ratio (%)",
    "SL.TLF.CACT.ZS":   "Labour Force Participation Rate (%)",
    "SL.TLF.CACT.FE.ZS":"Female Labour Force Participation (%)",
    "SL.TLF.CACT.MA.ZS":"Male Labour Force Participation (%)",
    "FP.CPI.TOTL.ZG":   "Inflation CPI (%)",
    "NY.GDP.PCAP.CD":   "GDP per Capita (USD)",
    "NY.GNP.PCAP.CD":   "GNI per Capita (USD)",
}


def _fetch_wb(indicator_id: str, country: str = "AU",
              start: int = 1991, end: int = 2024) -> list[dict]:
    """Fetch a World Bank indicator with simple retry."""
    url = (
        f"https://api.worldbank.org/v2/country/{country}"
        f"/indicator/{indicator_id}?format=json"
        f"&date={start}:{end}&per_page=100"
    )
    cache = RAW_PATH / f"{indicator_id.replace('.', '_')}.json"
    if cache.exists():
        return json.loads(cache.read_text())

    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            payload = resp.json()
            if isinstance(payload, list) and len(payload) > 1:
                data = payload[1] or []
                cache.write_text(json.dumps(data))
                return data
        except Exception:
            time.sleep(2 ** attempt)
    return []


def _build_db() -> None:
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            indicator_id   TEXT,
            indicator_name TEXT,
            year           INTEGER,
            value          REAL,
            PRIMARY KEY (indicator_id, year)
        )
    """)
    for ind_id, ind_name in INDICATORS.items():
        records = _fetch_wb(ind_id)
        rows = [
            (ind_id, ind_name, int(r["date"]), r["value"])
            for r in records
            if r.get("value") is not None
        ]
        con.executemany(
            "INSERT OR REPLACE INTO indicators VALUES (?,?,?,?)", rows
        )
    con.commit()
    con.close()


def get_dataframe() -> pd.DataFrame:
    """Return a wide-format DataFrame indexed by year with all indicators as columns."""
    if not DB_PATH.exists():
        _build_db()

    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM indicators", con)
    con.close()

    wide = df.pivot_table(
        index="year", columns="indicator_name", values="value"
    ).reset_index()
    wide = wide.sort_values("year").reset_index(drop=True)
    return wide


def get_long_dataframe() -> pd.DataFrame:
    """Return a long-format DataFrame — useful for multi-line charts."""
    if not DB_PATH.exists():
        _build_db()
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM indicators ORDER BY year", con)
    con.close()
    return df


def refresh_cache() -> None:
    """Delete cached raw JSON and DB to force a fresh pull."""
    for f in RAW_PATH.glob("*.json"):
        f.unlink()
    if DB_PATH.exists():
        DB_PATH.unlink()
    _build_db()
