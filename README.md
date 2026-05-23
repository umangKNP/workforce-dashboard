# workforce-dashboard

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.18-3F4F75?logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

**Interactive workforce analytics dashboard for Australian labour market data (1991–2024).**  
Built with Streamlit + Plotly. Data sourced from World Bank Open Data API — no API key, no CSV uploads.

---

## Dashboard

**Live:** `streamlit run app.py`

### What you get

| Component | Description |
|-----------|-------------|
| **KPI Cards** | Unemployment rate, LFP rate, employment ratio, GDP per capita — with YoY delta |
| **Unemployment Trend** | Line chart with recession bands (GFC 2008, COVID 2020) |
| **Gender LFP Gap** | Male vs Female labour force participation, 1991–2024 |
| **GDP per Capita** | Bar + 5-year rolling average overlay |
| **Correlation Scatter** | GDP vs Unemployment coloured by year — inverse relationship visible |
| **Normalised Index** | All indicators indexed to base year = 100 for comparison |
| **Year Range Slider** | Filter all charts to any subset of years |

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Data is fetched from the World Bank API on first run and cached locally in `data/workforce.db`. Subsequent runs load from cache instantly.

To force a data refresh:
```python
from data.load_data import refresh_cache
refresh_cache()
```

---

## Architecture

```
app.py                    ← Streamlit UI + Plotly charts
data/
  load_data.py            ← World Bank API client + SQLite cache
  workforce.db            ← Local cache (git-ignored)
  raw/*.json              ← Raw API responses (git-ignored)
.streamlit/
  config.toml             ← Dark theme matching portfolio
```

---

## Indicators

| Indicator | Code |
|-----------|------|
| Unemployment Rate | `SL.UEM.TOTL.ZS` |
| Employment-to-Population | `SL.EMP.TOTL.SP.ZS` |
| Labour Force Participation (Total) | `SL.TLF.CACT.ZS` |
| Labour Force Participation (Female) | `SL.TLF.CACT.FE.ZS` |
| Labour Force Participation (Male) | `SL.TLF.CACT.MA.ZS` |
| Inflation CPI | `FP.CPI.TOTL.ZG` |
| GDP per Capita | `NY.GDP.PCAP.CD` |
| GNI per Capita | `NY.GNP.PCAP.CD` |

---

## Power BI Portability

This project was designed to be portable to Power BI. The DAX equivalents for key measures:

```dax
-- Unemployment Rate YoY Change (DAX equivalent)
Unemployment YoY =
VAR CurrentYear = MAX('indicators'[year])
VAR CurrentVal  = CALCULATE(SUM('indicators'[value]),
                             'indicators'[indicator_name] = "Unemployment Rate (%)",
                             'indicators'[year] = CurrentYear)
VAR PriorVal    = CALCULATE(SUM('indicators'[value]),
                             'indicators'[indicator_name] = "Unemployment Rate (%)",
                             'indicators'[year] = CurrentYear - 1)
RETURN CurrentVal - PriorVal

-- 5-Year Rolling Average (DAX equivalent)
GDP 5yr Rolling Avg =
CALCULATE(
    AVERAGEX(
        FILTER(ALL('indicators'),
               'indicators'[year] <= MAX('indicators'[year]) &&
               'indicators'[year] >= MAX('indicators'[year]) - 4),
        'indicators'[value]
    ),
    'indicators'[indicator_name] = "GDP per Capita (USD)"
)
```

---

*Data: [World Bank Open Data](https://data.worldbank.org/) (free, no key required)*
