import sys
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from load import fetch_all, total_records

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Sentiment",
    page_icon="📈",
    layout="wide",
)

PLOTLY_THEME = "plotly_dark"


# ── Helpers ───────────────────────────────────────────────────────────────────
def time_ago(dt) -> str:
    if pd.isnull(dt):
        return "—"
    diff = datetime.utcnow() - pd.to_datetime(dt).to_pydatetime().replace(tzinfo=None)
    s = int(diff.total_seconds())
    if s < 60:   return f"{s}s ago"
    if s < 3600: return f"{s // 60}m ago"
    if s < 86400:return f"{s // 3600}h ago"
    return f"{s // 86400}d ago"


def market_mood(score: float) -> str:
    if score >  0.15: return "🟢 Bullish"
    if score < -0.15: return "🔴 Bearish"
    return "⚪ Neutral"


def run_etl():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from pipeline import run
    return run()


# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    return fetch_all(limit=5000)

df = load_data()

# ── Header row ────────────────────────────────────────────────────────────────
header_col, btn_col = st.columns([5, 1])
with header_col:
    st.title("📈 Market Sentiment Monitor")
with btn_col:
    st.write("")
    if st.button("🔄 Refresh Data", use_container_width=False):
        st.cache_data.clear()
        st.rerun()

# ── Run pipeline banner ───────────────────────────────────────────────────────
with st.expander("▶  Run ETL Pipeline", expanded=False):
    if st.button("Run Now", use_container_width=False, type="primary"):
        with st.spinner("Scraping → Cleaning → Loading…"):
            try:
                r = run_etl()
                st.success(
                    f"✅ Done — **{r['extracted']}** scraped · "
                    f"**{r['loaded']}** new · **{r['skipped']}** duplicates skipped"
                )
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Pipeline error: {e}")

st.divider()

# ── Empty state ───────────────────────────────────────────────────────────────
if df.empty:
    st.info("No data yet — expand **Run ETL Pipeline** above and click **Run Now**.")
    st.stop()

df["inserted_at"]  = pd.to_datetime(df["inserted_at"],  errors="coerce")
df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")

# ── KPI metrics ───────────────────────────────────────────────────────────────
total   = total_records()
avg_sc  = df["sentiment_score"].mean()
last_ts = df["inserted_at"].max()

k1, k2, k3 = st.columns(3)
k1.metric("📰 Total Articles",    f"{total:,}")
k2.metric("📊 Market Mood",       market_mood(avg_sc), f"avg polarity {avg_sc:+.3f}")
k3.metric("🕒 Last Updated",      time_ago(last_ts))

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# CHART 1 — Sentiment trend (interactive)
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Sentiment Trend — Last 7 Days")

cutoff = datetime.utcnow() - timedelta(days=7)
trend = (
    df[df["inserted_at"] >= cutoff]
    .assign(date=df["inserted_at"].dt.date)
    .groupby("date")
    .agg(avg=("sentiment_score", "mean"), count=("headline", "count"))
    .reset_index()
    .sort_values("date")
)

fig_trend = go.Figure()

# Shaded fill under curve
fig_trend.add_trace(go.Scatter(
    x=trend["date"], y=trend["avg"],
    mode="lines+markers+text",
    line=dict(color="#00d4aa", width=3),
    marker=dict(size=9, color="#ffffff", line=dict(color="#00d4aa", width=2)),
    text=[f"{v:+.2f}" for v in trend["avg"]],
    textposition="top center",
    textfont=dict(size=11),
    fill="tozeroy",
    fillcolor="rgba(0,212,170,0.12)",
    hovertemplate="<b>%{x}</b><br>Avg Sentiment: %{y:+.3f}<br>Articles: %{customdata}<extra></extra>",
    customdata=trend["count"],
    name="Avg Sentiment",
))

fig_trend.add_hline(y=0, line_dash="dash", line_color="#555", line_width=1)

fig_trend.update_layout(
    template=PLOTLY_THEME,
    height=280,
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(title="", showgrid=False),
    yaxis=dict(title="Polarity", range=[-1, 1], zeroline=False, gridcolor="#222"),
    showlegend=False,
    plot_bgcolor="#0e1117",
    paper_bgcolor="#0e1117",
)

st.plotly_chart(fig_trend, width="stretch")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 2 — Sentiment breakdown (interactive donut)
# ─────────────────────────────────────────────────────────────────────────────
col_donut, col_bar = st.columns(2)

with col_donut:
    st.subheader("Sentiment Split")
    counts = (
        df["sentiment_label"]
        .value_counts()
        .reindex(["Positive", "Neutral", "Negative"], fill_value=0)
    )
    fig_donut = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.55,
        marker_colors=["#00d4aa", "#888888", "#ff4b4b"],
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value} articles<br>%{percent}<extra></extra>",
    ))
    fig_donut.update_layout(
        template=PLOTLY_THEME,
        height=260,
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        paper_bgcolor="#0e1117",
    )
    st.plotly_chart(fig_donut, width="stretch")

with col_bar:
    st.subheader("Top Sources")
    src_counts = df["source"].value_counts().head(6).reset_index()
    src_counts.columns = ["Source", "Count"]
    fig_bar = px.bar(
        src_counts, x="Count", y="Source", orientation="h",
        color="Count",
        color_continuous_scale=[[0, "#1a3a3a"], [1, "#00d4aa"]],
        template=PLOTLY_THEME,
    )
    fig_bar.update_layout(
        height=260,
        margin=dict(l=0, r=10, t=10, b=10),
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
    )
    st.plotly_chart(fig_bar, width="stretch")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# DATA EXPLORER
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("🔍 News Explorer")

scol1, scol2 = st.columns([3, 1])
with scol1:
    keyword = st.text_input("Search headlines", placeholder='e.g. Apple · Fed · oil · Nvidia…', label_visibility="collapsed")
with scol2:
    sent_filter = st.selectbox("Sentiment", ["All", "Positive", "Neutral", "Negative"], label_visibility="collapsed")

view = df.copy()
if keyword.strip():
    view = view[view["headline"].str.contains(keyword.strip(), case=False, na=False)]
if sent_filter != "All":
    view = view[view["sentiment_label"] == sent_filter]

table = view[["headline", "source", "sentiment_label", "sentiment_score", "published_at"]].copy()
table.columns = ["Headline", "Source", "Sentiment", "Score", "Published"]
table["Score"]     = table["Score"].map(lambda x: f"{x:+.3f}")
table["Published"] = pd.to_datetime(table["Published"], errors="coerce").dt.strftime("%b %d, %H:%M")

st.dataframe(table.reset_index(drop=True), width="stretch", height=360)
st.caption(f"Showing **{len(table):,}** of **{total:,}** total records")
