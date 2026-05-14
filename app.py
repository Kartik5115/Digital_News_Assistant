"""
Streamlit Dashboard — Financial News Sentiment Monitor
Shows today's scraped headlines and a sentiment distribution bar chart.
"""

import sys
import os
import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from datetime import datetime

# Allow importing pipeline scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from load import fetch_today, fetch_all, DB_PATH

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Financial News Sentiment",
    page_icon="📈",
    layout="wide",
)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("📈 Financial News Sentiment Monitor")
st.caption(f"Data sourced from Reuters, MarketWatch, Yahoo Finance • Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ── Sidebar controls ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")

    run_pipeline = st.button("🔄 Run ETL Pipeline", use_container_width=True)

    if run_pipeline:
        with st.spinner("Running Extract → Transform → Load…"):
            try:
                from pipeline import run_pipeline as _run
                result = _run()
                st.success(
                    f"Pipeline complete!\n\n"
                    f"• Extracted: **{result['extracted']}** headlines\n"
                    f"• Transformed: **{result['transformed']}** rows\n"
                    f"• Loaded: **{result['loaded']}** new rows"
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Pipeline error: {exc}")

    show_all = st.checkbox("Show all historical data", value=False)
    max_rows = st.slider("Max rows to display", 10, 500, 100, step=10)
    st.markdown("---")
    st.markdown("**DB path**")
    st.code(str(DB_PATH), language=None)

# ── Load data ─────────────────────────────────────────────────────────────────
if show_all:
    df = fetch_all(limit=max_rows)
    section_label = "All Stored Headlines"
else:
    df = fetch_today(limit=max_rows)
    section_label = "Today's Headlines"

# ── Pipeline prompt if DB is empty ───────────────────────────────────────────
if df.empty:
    st.info(
        "No data found in the database yet. "
        "Click **Run ETL Pipeline** in the sidebar to scrape and load today's headlines."
    )
    st.stop()

# ── KPI metrics row ───────────────────────────────────────────────────────────
total = len(df)
n_positive = (df["sentiment_label"] == "Positive").sum()
n_negative = (df["sentiment_label"] == "Negative").sum()
n_neutral  = (df["sentiment_label"] == "Neutral").sum()
avg_score  = df["sentiment_score"].mean()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Headlines", total)
col2.metric("Positive 🟢", n_positive)
col3.metric("Neutral  ⚪", n_neutral)
col4.metric("Negative 🔴", n_negative)
col5.metric("Avg Sentiment", f"{avg_score:+.3f}")

st.markdown("---")

# ── Sentiment distribution bar chart ─────────────────────────────────────────
st.subheader("Sentiment Distribution")

label_counts = (
    df["sentiment_label"]
    .value_counts()
    .reindex(["Positive", "Neutral", "Negative"], fill_value=0)
)

COLOR_MAP = {
    "Positive": "#2ecc71",
    "Neutral":  "#95a5a6",
    "Negative": "#e74c3c",
}
colors = [COLOR_MAP[lbl] for lbl in label_counts.index]

fig, ax = plt.subplots(figsize=(7, 3.5))
bars = ax.bar(label_counts.index, label_counts.values, color=colors, width=0.5, edgecolor="white")

for bar, val in zip(bars, label_counts.values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.3,
        str(val),
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
    )

ax.set_ylabel("Number of Headlines", fontsize=11)
ax.set_title("Sentiment Label Counts", fontsize=13, fontweight="bold")
ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
ax.spines[["top", "right"]].set_visible(False)
ax.set_facecolor("#f9f9f9")
fig.patch.set_facecolor("#f9f9f9")
plt.tight_layout()

st.pyplot(fig)

# ── Sentiment score histogram ─────────────────────────────────────────────────
with st.expander("Sentiment Score Distribution (histogram)"):
    fig2, ax2 = plt.subplots(figsize=(7, 3))
    ax2.hist(df["sentiment_score"], bins=20, color="#3498db", edgecolor="white", alpha=0.85)
    ax2.axvline(0, color="#e74c3c", linestyle="--", linewidth=1.2, label="Neutral (0)")
    ax2.set_xlabel("Polarity Score (−1 = very negative, +1 = very positive)", fontsize=10)
    ax2.set_ylabel("Count", fontsize=10)
    ax2.set_title("Polarity Score Histogram", fontsize=12)
    ax2.legend()
    ax2.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig2)

st.markdown("---")

# ── Headlines table ───────────────────────────────────────────────────────────
st.subheader(section_label)

sentiment_filter = st.multiselect(
    "Filter by sentiment",
    options=["Positive", "Neutral", "Negative"],
    default=["Positive", "Neutral", "Negative"],
)

display_df = df[df["sentiment_label"].isin(sentiment_filter)].copy()

def _score_color(val: float) -> str:
    if val > 0.05:
        return "color: #27ae60; font-weight: bold"
    elif val < -0.05:
        return "color: #c0392b; font-weight: bold"
    return "color: #7f8c8d"

table_cols = ["headline", "sentiment_score", "sentiment_label", "source", "published_at"]
available_cols = [c for c in table_cols if c in display_df.columns]

styled = (
    display_df[available_cols]
    .style.applymap(_score_color, subset=["sentiment_score"])
    .format({"sentiment_score": "{:+.4f}"})
)

st.dataframe(styled, use_container_width=True, height=420)

st.caption(f"Showing {len(display_df)} of {total} rows • Sentiment scored via TextBlob polarity")
