import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from load import fetch_all, total_records

st.set_page_config(page_title="Market Intelligence", page_icon="📊", layout="wide")

# ── Run pipeline helper ───────────────────────────────────────────────────────
def run_pipeline():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from pipeline import run
    return run()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Controls")
    if st.button("▶  Run Pipeline", use_container_width=True):
        with st.spinner("Running ETL…"):
            try:
                r = run_pipeline()
                st.success(f"Done — {r['loaded']} new rows loaded")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.markdown("---")
    keyword = st.text_input("🔍 Search headlines", placeholder="e.g. Fed, Apple, oil…")
    show_all = st.checkbox("Show all history", value=False)

# ── Load data ─────────────────────────────────────────────────────────────────
df = fetch_all(limit=2000)

if df.empty:
    st.info("No data yet — click **Run Pipeline** in the sidebar.")
    st.stop()

df["inserted_at"] = pd.to_datetime(df["inserted_at"], errors="coerce")
df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")

# Apply keyword filter
if keyword:
    mask = df["headline"].str.contains(keyword, case=False, na=False)
    filtered = df[mask]
else:
    filtered = df

if not show_all:
    today = datetime.utcnow().date()
    filtered = filtered[filtered["inserted_at"].dt.date == today]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📊 Market Intelligence Dashboard")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")

# ── KPI cards ─────────────────────────────────────────────────────────────────
total   = total_records()
pos     = (filtered["sentiment_label"] == "Positive").sum()
neg     = (filtered["sentiment_label"] == "Negative").sum()
avg_pol = filtered["sentiment_score"].mean() if not filtered.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Records Processed", f"{total:,}")
c2.metric("Positive 🟢", int(pos))
c3.metric("Negative 🔴", int(neg))
c4.metric("Avg Polarity", f"{avg_pol:+.3f}")

st.markdown("---")

# ── Daily Sentiment Trend ─────────────────────────────────────────────────────
st.subheader("Daily Sentiment Trend")

trend = (
    df.dropna(subset=["inserted_at"])
    .assign(date=df["inserted_at"].dt.date)
    .groupby("date")["sentiment_score"]
    .mean()
    .reset_index()
    .sort_values("date")
)

if len(trend) >= 1:
    fig, ax = plt.subplots(figsize=(10, 3))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    ax.plot(
        trend["date"], trend["sentiment_score"],
        color="#00d4aa", linewidth=2.5, marker="o", markersize=6, markerfacecolor="#ffffff"
    )
    ax.axhline(0, color="#444", linewidth=1, linestyle="--")
    ax.fill_between(trend["date"], trend["sentiment_score"], 0,
                    where=(trend["sentiment_score"] >= 0),
                    alpha=0.15, color="#00d4aa")
    ax.fill_between(trend["date"], trend["sentiment_score"], 0,
                    where=(trend["sentiment_score"] < 0),
                    alpha=0.15, color="#ff4b4b")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.tick_params(colors="#aaaaaa", labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    ax.set_ylabel("Avg Polarity", color="#aaaaaa", fontsize=10)
    ax.set_ylim(-1, 1)
    plt.tight_layout()
    st.pyplot(fig)
else:
    st.info("Not enough data for a trend yet — run the pipeline a few times.")

st.markdown("---")

# ── Sentiment distribution ────────────────────────────────────────────────────
st.subheader("Sentiment Distribution")
if not filtered.empty:
    counts = (
        filtered["sentiment_label"]
        .value_counts()
        .reindex(["Positive", "Neutral", "Negative"], fill_value=0)
    )
    fig2, ax2 = plt.subplots(figsize=(5, 2.5))
    fig2.patch.set_facecolor("#0e1117")
    ax2.set_facecolor("#0e1117")
    colors = ["#00d4aa", "#888888", "#ff4b4b"]
    bars = ax2.bar(counts.index, counts.values, color=colors, width=0.5)
    for bar, v in zip(bars, counts.values):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                 str(v), ha="center", fontsize=11, color="#ffffff", fontweight="bold")
    ax2.tick_params(colors="#aaaaaa")
    for spine in ax2.spines.values():
        spine.set_edgecolor("#333")
    ax2.set_facecolor("#0e1117")
    plt.tight_layout()
    st.pyplot(fig2)

st.markdown("---")

# ── Headlines table ───────────────────────────────────────────────────────────
st.subheader(f"Headlines {'(filtered)' if keyword else ''}")

if filtered.empty:
    st.warning("No headlines match your search.")
else:
    cols = ["headline", "sentiment_score", "sentiment_label", "source", "published_at"]
    available = [c for c in cols if c in filtered.columns]
    display = filtered[available].copy()
    display["sentiment_score"] = display["sentiment_score"].map(lambda x: f"{x:+.3f}")
    st.dataframe(display, use_container_width=True, height=380)
    st.caption(f"{len(filtered)} headlines shown")
