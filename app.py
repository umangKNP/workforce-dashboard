"""
Workforce Analytics Dashboard — Australian Labour Market (1991–2024)
Streamlit app powered by World Bank Open Data.

Run:
    streamlit run app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data.load_data import get_dataframe, get_long_dataframe

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AU Workforce Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme overrides ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stMetric { background: #0d1117; border: 1px solid #21262d;
                border-radius: 8px; padding: 1rem; }
    .stMetric label { color: #8b949e !important; font-size: 0.75rem !important;
                      text-transform: uppercase; letter-spacing: 0.08em; }
    .stMetric [data-testid="stMetricValue"] { font-size: 1.8rem !important;
                                              font-weight: 700 !important; }
    h1, h2, h3 { letter-spacing: -0.02em; }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

ACCENT  = "#818cf8"
GREEN   = "#4ade80"
AMBER   = "#f59e0b"
PINK    = "#f472b6"
BG      = "#0d1117"
GRID    = "#21262d"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=BG, plot_bgcolor=BG,
    font=dict(color="#c9d1d9", family="Inter, sans-serif", size=12),
    xaxis=dict(gridcolor=GRID, showline=False, tickcolor="#8b949e"),
    yaxis=dict(gridcolor=GRID, showline=False, tickcolor="#8b949e"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID),
)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Fetching World Bank data…")
def load_wide():
    return get_dataframe()

@st.cache_data(ttl=3600, show_spinner=False)
def load_long():
    return get_long_dataframe()

wide = load_wide()
long = load_long()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 AU Workforce Analytics")
    st.markdown("*Australian labour market data, 1991–2024*")
    st.divider()

    yr_col = "year"
    min_yr = int(wide[yr_col].min())
    max_yr = int(wide[yr_col].max())
    year_range = st.slider(
        "Year Range", min_value=min_yr, max_value=max_yr,
        value=(min_yr, max_yr), step=1,
    )

    st.divider()
    st.markdown("**Data source:** [World Bank Open Data](https://data.worldbank.org/)")
    st.markdown("**Coverage:** Australia (AUS), annual")

df = wide[(wide[yr_col] >= year_range[0]) & (wide[yr_col] <= year_range[1])]
df_long = long[(long["year"] >= year_range[0]) & (long["year"] <= year_range[1])]

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.markdown("# 🇦🇺 Australian Labour Market Dashboard")
st.caption(f"Data range: {year_range[0]} – {year_range[1]}  ·  Source: World Bank Open Data")
st.divider()

col1, col2, col3, col4 = st.columns(4)

unemp_col  = "Unemployment Rate (%)"
lfp_col    = "Labour Force Participation Rate (%)"
emp_col    = "Employment-to-Population Ratio (%)"
gdp_col    = "GDP per Capita (USD)"

def latest(col: str) -> float | None:
    s = df[[yr_col, col]].dropna()
    return s[col].iloc[-1] if len(s) > 0 else None

def delta(col: str) -> float | None:
    s = df[[yr_col, col]].dropna()
    if len(s) < 2:
        return None
    return s[col].iloc[-1] - s[col].iloc[-2]

with col1:
    v = latest(unemp_col)
    d = delta(unemp_col)
    st.metric("Unemployment Rate", f"{v:.1f}%" if v else "N/A",
              delta=f"{d:+.1f}pp" if d else None,
              delta_color="inverse")

with col2:
    v = latest(lfp_col)
    d = delta(lfp_col)
    st.metric("Labour Force Participation", f"{v:.1f}%" if v else "N/A",
              delta=f"{d:+.1f}pp" if d else None)

with col3:
    v = latest(emp_col)
    d = delta(emp_col)
    st.metric("Employment-to-Population", f"{v:.1f}%" if v else "N/A",
              delta=f"{d:+.1f}pp" if d else None)

with col4:
    v = latest(gdp_col)
    d = delta(gdp_col)
    st.metric("GDP per Capita", f"${v:,.0f}" if v else "N/A",
              delta=f"${d:+,.0f}" if d else None)

st.divider()

# ── Row 1: Unemployment + Labour Force Trend ──────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Unemployment Rate Over Time")
    u = df[[yr_col, unemp_col]].dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=u[yr_col], y=u[unemp_col],
        mode="lines+markers",
        line=dict(color=ACCENT, width=2.5),
        marker=dict(size=4, color=ACCENT),
        fill="tozeroy",
        fillcolor=f"rgba(129,140,248,0.08)",
        name="Unemployment %",
    ))
    # Recession bands (approx)
    for start, end, label in [(2008, 2010, "GFC"), (2020, 2021, "COVID")]:
        if start >= year_range[0] and end <= year_range[1]:
            fig.add_vrect(x0=start, x1=end,
                          fillcolor="rgba(244,114,182,0.06)",
                          line_width=0, annotation_text=label,
                          annotation_position="top left",
                          annotation_font_color=PINK)
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_ticksuffix="%",
                      yaxis_title="Unemployment Rate (%)")
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Labour Force Participation — Male vs Female")
    f_col = "Female Labour Force Participation (%)"
    m_col = "Male Labour Force Participation (%)"
    lfp_data = df[[yr_col, f_col, m_col]].dropna()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=lfp_data[yr_col], y=lfp_data[m_col],
                              name="Male", line=dict(color=ACCENT, width=2),
                              mode="lines"))
    fig2.add_trace(go.Scatter(x=lfp_data[yr_col], y=lfp_data[f_col],
                              name="Female", line=dict(color=PINK, width=2),
                              mode="lines"))
    fig2.update_layout(**PLOTLY_LAYOUT, yaxis_ticksuffix="%",
                       yaxis_title="Participation Rate (%)")
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: GDP per Capita + Correlation scatter ───────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("GDP per Capita (USD)")
    g = df[[yr_col, gdp_col]].dropna()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=g[yr_col], y=g[gdp_col],
        marker_color=GREEN, marker_line_width=0,
        opacity=0.8,
    ))
    fig3.add_trace(go.Scatter(
        x=g[yr_col], y=g[gdp_col].rolling(5).mean(),
        mode="lines", name="5yr MA",
        line=dict(color=AMBER, width=2, dash="dot"),
    ))
    fig3.update_layout(**PLOTLY_LAYOUT,
                       yaxis_tickprefix="$",
                       yaxis_tickformat=",.0f")
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.subheader("Unemployment vs GDP per Capita")
    scatter_df = df[[yr_col, unemp_col, gdp_col]].dropna()
    fig4 = px.scatter(
        scatter_df, x=gdp_col, y=unemp_col,
        color=yr_col, color_continuous_scale="Viridis",
        text=yr_col,
        labels={gdp_col: "GDP per Capita (USD)", unemp_col: "Unemployment (%)"},
    )
    fig4.update_traces(textposition="top center", textfont_size=8, marker_size=8)
    fig4.update_layout(**PLOTLY_LAYOUT,
                       coloraxis_colorbar=dict(title="Year", tickfont_size=10),
                       xaxis_tickprefix="$", xaxis_tickformat=",.0f",
                       yaxis_ticksuffix="%")
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: All indicators normalised ─────────────────────────────────────────
st.subheader("All Labour Market Indicators — Normalised (Base = First Year = 100)")
norm_cols = [c for c in [unemp_col, lfp_col, emp_col] if c in df.columns]
norm_df = df[[yr_col] + norm_cols].dropna()
colours = [ACCENT, GREEN, AMBER, PINK]
fig5 = go.Figure()
for i, col in enumerate(norm_cols):
    base = norm_df[col].iloc[0]
    if base and base != 0:
        indexed = norm_df[col] / base * 100
        fig5.add_trace(go.Scatter(
            x=norm_df[yr_col], y=indexed,
            name=col, mode="lines",
            line=dict(color=colours[i % len(colours)], width=2),
        ))
fig5.add_hline(y=100, line_dash="dot", line_color="#8b949e", opacity=0.5)
fig5.update_layout(**PLOTLY_LAYOUT, yaxis_title="Index (Base Year = 100)",
                   height=350)
st.plotly_chart(fig5, use_container_width=True)

# ── Raw data table ────────────────────────────────────────────────────────────
with st.expander("View raw data"):
    st.dataframe(df.set_index(yr_col).style.format("{:.2f}"),
                 use_container_width=True)

st.divider()
st.caption(
    "Built by [Umang Kochar](https://umangk.dev) · "
    "Data: [World Bank Open Data](https://data.worldbank.org/) · "
    "Source: [GitHub](https://github.com/umangKNP)"
)
