# Automated Financial News ETL Pipeline

A production-ready data engineering pipeline that automatically scrapes financial news headlines, performs AI-powered sentiment analysis, stores the results in a structured SQLite database, and surfaces insights through an interactive Streamlit monitoring dashboard.

---

## Architecture

```
Extract  ──▶  Transform  ──▶  Load  ──▶  Dashboard
```

### Extract — `scripts/extract.py`

Scrapes the latest financial headlines from multiple RSS feeds using `requests` and `BeautifulSoup`. Sources include **MarketWatch**, **Yahoo Finance**, and **Reuters Business News**. Network timeouts and source failures are handled gracefully with `try-except` blocks, and a realistic fallback dataset is used if all live sources are unavailable.

### Transform — `scripts/transform.py`

Cleans and enriches the raw headline data using `pandas`:

- Removes blank and duplicate headlines
- Handles missing values across all fields
- Normalises publication dates across multiple RFC 822 and ISO 8601 formats
- Assigns a **Sentiment Score** (−1.0 to +1.0) to each headline using `TextBlob` polarity analysis applied to the combined `headline + summary` text for a richer signal
- Adds a **Sentiment Label**: `Positive`, `Neutral`, or `Negative`

### Load — `scripts/load.py`

Persists transformed data to `data/warehouse.db` using `SQLAlchemy`:

- Creates the `market_analysis` table automatically on first run
- Enforces a **UNIQUE constraint** on the `headline` column to prevent duplicate entries across daily pipeline runs
- Upsert logic skips existing headlines and logs the count of new vs. ignored records

---

## Project Structure

```
├── pipeline.py              # Main ETL orchestrator
├── scripts/
│   ├── extract.py           # BeautifulSoup RSS scraper
│   ├── transform.py         # Pandas + TextBlob processing
│   └── load.py              # SQLAlchemy database loader
├── app/
│   └── dashboard.py         # Streamlit monitoring dashboard
├── data/
│   └── warehouse.db         # SQLite database (auto-created)
├── logs/
│   └── pipeline.log         # Run-by-run log file
├── cron_config.md           # Scheduling instructions
├── requirements.txt         # Python dependencies
└── .streamlit/
    └── config.toml          # Server and theme configuration
```

---

## Tools & Technologies

| Layer        | Technology                                  |
|--------------|---------------------------------------------|
| Language     | Python 3.11                                 |
| Scraping     | `requests` + `BeautifulSoup4` (lxml-xml)    |
| Processing   | `pandas`                                    |
| Sentiment AI | `TextBlob` (NLTK polarity scoring)          |
| Database     | SQLite via `SQLAlchemy`                     |
| Dashboard    | `Streamlit` + `Plotly`                      |
| Logging      | Python `logging` → `logs/pipeline.log`      |

---

## Dashboard Features

The Streamlit dashboard (`app/dashboard.py`) provides:

- **KPI Metric Bar** — Total articles scraped, overall market mood (Bullish / Neutral / Bearish), and time since last update
- **7-Day Sentiment Trend** — Interactive Plotly line chart showing how average news sentiment shifts day by day
- **Sentiment Breakdown** — Interactive donut chart (Positive / Neutral / Negative split) and a top-sources bar chart
- **News Explorer** — Full-text keyword search + sentiment filter over the complete headline database, with a sortable results table

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the pipeline

```bash
python pipeline.py
```

You will see step-by-step terminal output:

```
11:00:01 [INFO] Step 1/3 — Scraping financial news sources...
11:00:02 [INFO]   ✔  52 headlines collected from RSS feeds.
11:00:02 [INFO] Step 2/3 — Cleaning data and calculating sentiment...
11:00:02 [INFO]   ✔  Sentiment analysis complete — 52 records processed (100%).
11:00:03 [INFO] Step 3/3 — Loading into SQLite database...
11:00:03 [INFO]   ✔  15 unique records added, 37 duplicates ignored.
```

### 3. Launch the dashboard

```bash
streamlit run app/dashboard.py --server.port 5000
```

---

## Automation

The pipeline is designed to run on a **daily cron schedule**, keeping the database fresh without manual intervention. See [`cron_config.md`](cron_config.md) for full setup instructions.

**Quick example — run every day at 7:00 AM:**

```bash
crontab -e
# Add this line:
0 7 * * * /usr/bin/python3 /path/to/project/pipeline.py >> /path/to/project/logs/cron.log 2>&1
```

Every run appends a timestamped entry to `logs/pipeline.log`, so you always have a clear audit trail of what was scraped, processed, and loaded.

---

## Schema

```sql
CREATE TABLE market_analysis (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    headline        TEXT    NOT NULL UNIQUE,
    sentiment_score REAL,
    sentiment_label TEXT,
    source          TEXT,
    published_at    TEXT,
    scraped_at      TEXT,
    summary         TEXT,
    url             TEXT,
    inserted_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## License

MIT
