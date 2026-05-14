"""
Load: Append transformed news data into a SQLite database.
Database : data/market_data.db
Table    : news_logs
"""

import sqlite3
import pandas as pd
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "market_data.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS news_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    headline        TEXT    NOT NULL,
    sentiment_score REAL,
    sentiment_label TEXT,
    source          TEXT,
    published_at    TEXT,
    scraped_at      TEXT,
    summary         TEXT,
    url             TEXT,
    inserted_at     TEXT    DEFAULT (datetime('now'))
);
"""


def _ensure_db() -> sqlite3.Connection:
    """Create DB directory and table if they don't exist; return connection."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


def load(df: pd.DataFrame) -> int:
    """
    Append transformed rows into the news_logs table.
    Skips rows whose headline already exists for today to avoid duplicates
    across repeated pipeline runs.

    Args:
        df: Cleaned DataFrame from transform()

    Returns:
        Number of rows actually inserted.
    """
    if df.empty:
        logger.warning("Empty DataFrame — nothing to load.")
        return 0

    conn = _ensure_db()

    # Fetch today's existing headlines to avoid re-inserting on repeated runs
    existing = pd.read_sql_query(
        "SELECT headline FROM news_logs WHERE date(inserted_at) = date('now')",
        conn,
    )
    existing_set = set(existing["headline"].str.strip().tolist())

    new_rows = df[~df["headline"].isin(existing_set)].copy()

    if new_rows.empty:
        logger.info("No new headlines to insert (all already in DB for today).")
        conn.close()
        return 0

    # Convert datetime columns to ISO string for SQLite
    for col in ["published_at", "scraped_at"]:
        if col in new_rows.columns:
            new_rows[col] = new_rows[col].astype(str)

    new_rows.to_sql("news_logs", conn, if_exists="append", index=False)
    conn.commit()
    row_count = len(new_rows)
    logger.info(f"Load complete: {row_count} rows inserted into news_logs ({DB_PATH})")
    conn.close()
    return row_count


def fetch_today(limit: int = 500) -> pd.DataFrame:
    """
    Read today's news_logs rows from the database.

    Args:
        limit: Maximum rows to return.

    Returns:
        pd.DataFrame sorted by published_at descending.
    """
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql_query(
        f"""
        SELECT headline, sentiment_score, sentiment_label, source,
               published_at, scraped_at, summary, url
        FROM   news_logs
        WHERE  date(inserted_at) = date('now')
        ORDER  BY inserted_at DESC
        LIMIT  {int(limit)}
        """,
        conn,
    )
    conn.close()
    return df


def fetch_all(limit: int = 1000) -> pd.DataFrame:
    """Read all rows from news_logs (most recent first)."""
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql_query(
        f"""
        SELECT headline, sentiment_score, sentiment_label, source,
               published_at, scraped_at, summary, url, inserted_at
        FROM   news_logs
        ORDER  BY inserted_at DESC
        LIMIT  {int(limit)}
        """,
        conn,
    )
    conn.close()
    return df


if __name__ == "__main__":
    from extract import extract
    from transform import transform
    raw = extract()
    clean = transform(raw)
    n = load(clean)
    print(f"Inserted {n} rows. DB at: {DB_PATH}")
