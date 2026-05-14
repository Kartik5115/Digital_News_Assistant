import logging
import re
import pandas as pd
from textblob import TextBlob
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import nltk
    for corpus in ("punkt", "punkt_tab", "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng"):
        nltk.download(corpus, quiet=True)
except Exception:
    pass

_DATE_FMTS = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S GMT",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
]


def _parse_date(raw: str) -> datetime:
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(raw.strip(), fmt).replace(tzinfo=None)
        except (ValueError, AttributeError):
            continue
    m = re.search(r"(\d{4}-\d{2}-\d{2})", str(raw))
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            pass
    return datetime.utcnow()


def _score(text: str) -> float:
    try:
        return round(TextBlob(str(text)).sentiment.polarity, 4)
    except Exception:
        return 0.0


def _label(score: float) -> str:
    if score > 0.05:
        return "Positive"
    if score < -0.05:
        return "Negative"
    return "Neutral"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        logger.warning("Empty DataFrame — nothing to transform")
        return df

    before = len(df)

    # Drop blank headlines and duplicates
    df = df[df["headline"].notna() & (df["headline"].str.strip() != "")]
    df["headline"] = df["headline"].str.strip()
    df = df.drop_duplicates(subset=["headline"], keep="first")

    # Handle missing values
    df["summary"] = df["summary"].fillna("")
    df["url"]     = df["url"].fillna("")
    df["source"]  = df["source"].fillna("Unknown")

    # Parse dates
    df["published_at"] = df["raw_date"].apply(_parse_date)

    # Sentiment on headline + summary for richer signal
    df["sentiment_score"] = (df["headline"] + ". " + df["summary"]).apply(_score)
    df["sentiment_label"] = df["sentiment_score"].apply(_label)

    df = df.drop(columns=["raw_date"], errors="ignore")
    df = df.reset_index(drop=True)

    logger.info(f"Transform complete — {before} → {len(df)} rows")
    return df
