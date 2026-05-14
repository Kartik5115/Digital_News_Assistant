# Financial News ETL Pipeline

A Python ETL pipeline that scrapes financial news headlines, scores sentiment, stores them in SQLite, and displays a live Streamlit dashboard.

## Run & Operate

- **Dashboard**: `streamlit run app.py --server.port 5000`
- **Run pipeline manually**: `python scripts/pipeline.py`
- **Run individual steps**:
  - `python scripts/extract.py` — scrape headlines only
  - `python scripts/transform.py` — extract + transform
  - `python scripts/load.py` — full ETL to SQLite

## Stack

- Python 3.x
- **Scraping**: `requests` + `BeautifulSoup4` (lxml-xml parser) — RSS feeds
- **Transform**: `pandas` + `TextBlob` (polarity sentiment scoring)
- **Storage**: SQLite via `sqlite3` — file at `data/market_data.db`
- **Dashboard**: `Streamlit` + `matplotlib`

## Where things live

```
scripts/
  extract.py     — BeautifulSoup RSS scraper (Reuters, MarketWatch, Yahoo Finance)
  transform.py   — Pandas dedup + TextBlob sentiment scoring
  load.py        — SQLite read/write helpers
  pipeline.py    — Orchestrates Extract → Transform → Load
data/
  market_data.db — SQLite database (auto-created on first run)
app.py           — Streamlit dashboard
.streamlit/
  config.toml    — Server config (port 5000, headless)
```

## Architecture decisions

- RSS feeds are parsed as XML with BeautifulSoup's `lxml-xml` parser — more reliable than scraping rendered HTML.
- Duplicate detection runs at two levels: Pandas `drop_duplicates` during transform, and a same-day headline check on load to safely support repeated pipeline runs.
- TextBlob polarity is applied to `headline + summary` concatenation for a richer sentiment signal than headline-only scoring.
- The dashboard's "Run ETL Pipeline" button calls `pipeline.py` inline — no separate scheduler needed for demos.

## Product

- Scrapes financial headlines from MarketWatch and Yahoo Finance RSS feeds (Reuters as tertiary).
- Cleans and deduplicates data, then scores each headline with a sentiment polarity (−1.0 to +1.0).
- Stores everything in `data/market_data.db` → `news_logs` table with auto-incrementing ID.
- Streamlit dashboard shows KPI metrics, a sentiment bar chart, a polarity histogram, and a filterable headlines table.

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- NLTK corpora (`punkt`, `averaged_perceptron_tagger`) must be downloaded before first TextBlob use — `transform.py` does this automatically on import.
- Reuters RSS (`feeds.reuters.com`) may be blocked in the Replit sandbox — MarketWatch + Yahoo Finance are the reliable sources.
- SQLite DB path is resolved relative to `scripts/load.py` location (`../data/market_data.db`) so it works from any CWD.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
