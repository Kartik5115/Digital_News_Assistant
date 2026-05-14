# Financial News ETL Pipeline

An automated system that extracts financial news, cleans and normalises data, scores sentiment, stores it in SQLite, and displays a monitoring dashboard.

## Run & Operate

- **Dashboard**: `streamlit run app/dashboard.py --server.port 5000`
- **Run pipeline**: `python pipeline.py`
- **Run individual steps**:
  - `python scripts/extract.py`
  - `python scripts/transform.py`
  - `python scripts/load.py`

## Project Structure

```
scripts/
  extract.py      — BeautifulSoup RSS scraper (MarketWatch, Yahoo Finance, Reuters)
  transform.py    — Pandas dedup + TextBlob sentiment scoring
  load.py         — SQLAlchemy upsert into data/warehouse.db → market_analysis table
app/
  dashboard.py    — Streamlit dark-theme monitoring dashboard
pipeline.py       — Main orchestrator (Extract → Transform → Load)
data/
  warehouse.db    — SQLite database (auto-created on first run)
logs/
  pipeline.log    — Pipeline run log (success/error per run)
cron_config.md    — Instructions for scheduling pipeline.py with cron
requirements.txt  — Python dependencies
.streamlit/
  config.toml     — Server config (port 5000) + dark theme
```

## Stack

- **Scraping**: `requests` + `BeautifulSoup4` (lxml-xml parser on RSS feeds)
- **Transform**: `pandas` + `TextBlob` (polarity −1.0 to +1.0)
- **Storage**: SQLite via `SQLAlchemy` — `data/warehouse.db` → `market_analysis`
- **Dashboard**: `Streamlit` + `matplotlib`

## Architecture Decisions

- RSS feeds parsed as XML — more reliable than scraping rendered HTML
- UNIQUE constraint on `headline` + upsert logic prevents duplicates across repeated runs
- TextBlob scored on `headline + summary` concatenation for richer signal
- Logging writes to both stdout and `logs/pipeline.log` on every run
- Dark professional theme configured via `.streamlit/config.toml`

## Gotchas

- NLTK corpora are auto-downloaded on first `transform.py` import
- Reuters RSS may be blocked in the sandbox — MarketWatch + Yahoo Finance are the reliable sources
- DB path is resolved from `scripts/load.py` location so it works from any CWD

## User Preferences

_Populate as you build — explicit user instructions worth remembering across sessions._
