import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    UniqueConstraint, text
)
from sqlalchemy.orm import declarative_base, Session

logger = logging.getLogger(__name__)

DB_DIR  = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "warehouse.db"
DB_URL  = f"sqlite:///{DB_PATH}"

Base = declarative_base()


class MarketAnalysis(Base):
    __tablename__ = "market_analysis"
    __table_args__ = (UniqueConstraint("headline", name="uq_headline"),)

    id              = Column(Integer, primary_key=True, autoincrement=True)
    headline        = Column(String,  nullable=False)
    sentiment_score = Column(Float)
    sentiment_label = Column(String)
    source          = Column(String)
    published_at    = Column(String)
    scraped_at      = Column(String)
    summary         = Column(String)
    url             = Column(String)
    inserted_at     = Column(DateTime, default=datetime.utcnow)


def _engine():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(DB_URL, echo=False)
    Base.metadata.create_all(engine)
    return engine


def load(df: pd.DataFrame) -> int:
    if df.empty:
        logger.warning("Empty DataFrame — nothing to load")
        return 0

    engine = _engine()
    inserted = 0

    with Session(engine) as session:
        for _, row in df.iterrows():
            exists = session.execute(
                text("SELECT 1 FROM market_analysis WHERE headline = :h"),
                {"h": row["headline"]},
            ).fetchone()
            if exists:
                continue

            session.add(MarketAnalysis(
                headline        = row["headline"],
                sentiment_score = row.get("sentiment_score"),
                sentiment_label = row.get("sentiment_label"),
                source          = row.get("source"),
                published_at    = str(row.get("published_at", "")),
                scraped_at      = str(row.get("scraped_at", "")),
                summary         = row.get("summary", ""),
                url             = row.get("url", ""),
            ))
            inserted += 1

        session.commit()

    logger.info(f"Load complete — {inserted} new rows inserted into market_analysis")
    return inserted


def fetch_all(limit: int = 1000) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    engine = _engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(f"SELECT * FROM market_analysis ORDER BY inserted_at DESC LIMIT {limit}"),
            conn,
        )


def fetch_today() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    engine = _engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text("SELECT * FROM market_analysis WHERE date(inserted_at) = date('now') ORDER BY inserted_at DESC"),
            conn,
        )


def total_records() -> int:
    if not DB_PATH.exists():
        return 0
    engine = _engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM market_analysis"))
        return result.scalar() or 0
