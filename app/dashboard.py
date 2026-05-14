import sys
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from load import fetch_all, total_records

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Sentiment Monitor",
    page_icon="📈",
    layout="wide",
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def time_ago(dt) -> str:
    if pd.isnull(dt):
        return "—"
    diff = datetime.utcnow() - pd.to_datetime(dt).to_pydatetime().replace(tzinfo=None)
    s = int(diff.total_seconds())
    if s < 60:
        return f"{s} seconds ago"
    if s < 3600:
        return f"{s // 60} minutes ago"
    if s < 86400:
        return f"{s // 3600} hours ago"
    return f"{s // 86400} days ago"


def sentiment_label(score: float) -> str:
    if score > 0.15:
        return "Bullish 📈"
    if score < -0.15:
        return "Bearish 📉"
    return "Neutral ➡️"


def run_pipeline_inline():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from pipeline import run
    return run()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Controls")
    if st.button("▶  Run Pipeline Now", use_container_width=True):
        log_placeholder = st.empty()
        with st.spinner("Running…"):
            try:
                result = run_pipeline_inline()
                st.success(
                    f"**Complete!**\n\n"
                    f"- Scraped: **{result['extracted']}** headlines\n"
                    f"- Processed: **{result['transformed']}** records\n"
                    f"- Added: **{result['loaded']}** new | "
                    f"Skipped: **{result['skipped']}** duplicates"
                )
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("### 📋 Pipeline Log")
    log_path = Path(__file__).resolve().parent.parent / "logs" / "pipeline.log"
    if log_path.exists():
        lines = log_path.read_text().strip().splitlines()
        log_text = "\n".join(lines[-25:])
        st.code(log_text, language=None)
    else:
        st.caption("No log yet — run the pipeline first.")


# ── Load data ─────────────────────────────────────────────────────────────────
df = fetch_all(limit=5000)

if df.empty:
    st.title("📈 Market Sentiment Monitor")
    st.info("No data yet. Click **▶ Run Pipeline Now** in the sidebar to get started.")
    st.stop()

df["inserted_at"] = pd.to_datetime(df["inserted_at"], errors="coerce")
df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")

last_update_ts = df["inserted_at"].max()
avg_score      = df["sentiment_score"].mean()
total          = total_records()

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("📈 Market Sentiment Monitor")
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — METRIC BAR
# ─────────────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

c1.metric(
    label="Total Articles Scraped",
    value=f"{total:,}",
)

c2.metric(
    label="Average Market Sentiment",
    value=f"{avg_score:+.2f}",
    delta=sentiment_label(avg_score),
)

c3.metric(
    label="Last Update",
    value=time_ago(last_update_ts),
)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — 7-DAY SENTIMENT TREND
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Sentiment Trend — Last 7 Days")

cutoff = datetime.utcnow() - timedelta(days=7)
trend_df = df[df["inserted_at"] >= cutoff].copy()
trend_df["date"] = trend_df["inserted_at"].dt.date

daily = (
    trend_df.groupby("date")
    .agg(avg_sentiment=("sentiment_score", "mean"), count=("headline", "count"))
    .reset_index()
    .sort_values("date")
)

fig, ax = plt.subplots(figsize=(11, 3.2))
fig.patch.set_facecolor("#0e1117")
ax.set_facecolor("#0e1117")

if len(daily) > 0:
    dates  = daily["date"].tolist()
    scores = daily["avg_sentiment"].tolist()

    ax.plot(dates, scores, color="#00d4aa", linewidth=2.5,
            marker="o", markersize=7, markerfacecolor="#ffffff", zorder=3)
    ax.fill_between(dates, scores, 0,
                    where=[s >= 0 for s in scores], alpha=0.18, color="#00d4aa")
    ax.fill_between(dates, scores, 0,
                    where=[s < 0  for s in scores], alpha=0.18, color="#ff4b4b")

    # Annotate each point
    for d, s in zip(dates, scores):
        ax.annotate(f"{s:+.2f}", (d, s),
                    textcoords="offset points", xytext=(0, 10),
                    color="#e0e0e0", fontsize=8, ha="center")

ax.axhline(0, color="#444", linewidth=1, linestyle="--")
ax.set_ylim(-1, 1)
ax.set_ylabel("Avg Sentiment", color="#aaaaaa", fontsize=10)
ax.tick_params(colors="#aaaaaa", labelsize=9)
for spine in ax.spines.values():
    spine.set_edgecolor("#333")
if len(daily) == 1:
    ax.set_title(
        "Only 1 day of data so far — run the pipeline daily to build a trend.",
        color="#888", fontsize=9, loc="left"
    )
plt.tight_layout()
st.pyplot(fig)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — DATA EXPLORER
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Data Explorer")

keyword = st.text_input("🔍 Search by keyword", placeholder='e.g. "Apple", "Fed", "oil"…')

display = df.copy()
if keyword.strip():
    display = display[display["headline"].str.contains(keyword.strip(), case=False, na=False)]

table = display[["headline", "source", "sentiment_label", "sentiment_score", "published_at"]].copy()
table.columns = ["Headline", "Source", "Sentiment", "Score", "Published"]
table["Score"] = table["Score"].map(lambda x: f"{x:+.3f}")
table["Published"] = pd.to_datetime(table["Published"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M")

st.dataframe(table.reset_index(drop=True), use_container_width=True, height=400)
st.caption(f"Showing {len(table):,} of {total:,} total records")
