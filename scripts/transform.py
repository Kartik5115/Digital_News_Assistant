"""
Transform: Clean the extracted data using Pandas and add Sentiment Score via TextBlob.
Steps:
  1. Remove duplicate headlines
  2. Parse and normalise published dates
  3. Strip whitespace / empty rows
  4. Add 'sentiment_score' column (TextBlob polarity: -1.0 to +1.0)
  5. Add 'sentiment_label' column (Positive / Neutral / Negative)
"""

import pandas as pd
from textblob import TextBlob
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

# Attempt to download required NLTK corpora silently on first run
try:
    import nltk
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
    nltk.download("averaged_perceptron_tagger", quiet=True)
    nltk.download("averaged_perceptron_tagger_eng", quiet=True)
except Exception:
    pass


_DATE_PATTERNS = [
    "%a, %d %b %Y %H:%M:%S %z",   # RFC 822: Mon, 01 Jan 2024 12:00:00 +0000
    "%a, %d %b %Y %H:%M:%S GMT",
    "%Y-%m-%dT%H:%M:%SZ",          # ISO 8601
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
]


def _parse_date(raw: str) -> datetime:
    """Try several common date formats; fall back to today's date."""
    if not raw:
        return datetime.utcnow()
    raw = raw.strip()
    for fmt in _DATE_PATTERNS:
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=None)
        except ValueError:
            continue
    # Last-resort: extract YYYY-MM-DD with regex
    m = re.search(r"(\d{4}-\d{2}-\d{2})", raw)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            pass
    return datetime.utcnow()


def _sentiment_score(text: str) -> float:
    """Return TextBlob polarity score for the given text (-1.0 to +1.0)."""
    try:
        return round(TextBlob(str(text)).sentiment.polarity, 4)
    except Exception:
        return 0.0


def _sentiment_label(score: float) -> str:
    if score > 0.05:
        return "Positive"
    elif score < -0.05:
        return "Negative"
    return "Neutral"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and enrich a raw headlines DataFrame.

    Args:
        df: Raw DataFrame from extract()

    Returns:
        Cleaned DataFrame with additional columns:
            published_at (datetime), sentiment_score (float), sentiment_label (str)
    """
    if df.empty:
        logger.warning("Received empty DataFrame — nothing to transform.")
        return df

    original_count = len(df)

    # 1. Drop rows with missing or blank headlines
    df = df[df["headline"].notna() & (df["headline"].str.strip() != "")]

    # 2. Strip extra whitespace from text columns
    for col in ["headline", "summary", "source"]:
        if col in df.columns:
            df[col] = df[col].str.strip()

    # 3. Remove duplicate headlines (keep first occurrence)
    df = df.drop_duplicates(subset=["headline"], keep="first")

    # 4. Parse publication date
    df["published_at"] = df["raw_date"].apply(_parse_date)

    # 5. Add sentiment columns (applied to headline + summary for richer signal)
    df["text_for_sentiment"] = (
        df["headline"] + ". " + df["summary"].fillna("")
    )
    df["sentiment_score"] = df["text_for_sentiment"].apply(_sentiment_score)
    df["sentiment_label"] = df["sentiment_score"].apply(_sentiment_label)

    # 6. Drop helper / raw columns
    df = df.drop(columns=["raw_date", "text_for_sentiment"], errors="ignore")

    # 7. Reorder columns
    columns = [
        "headline",
        "sentiment_score",
        "sentiment_label",
        "source",
        "published_at",
        "scraped_at",
        "summary",
        "url",
    ]
    df = df[[c for c in columns if c in df.columns]]
    df = df.reset_index(drop=True)

    logger.info(
        f"Transform complete: {original_count} → {len(df)} rows "
        f"(removed {original_count - len(df)} duplicates/blanks)"
    )
    return df


if __name__ == "__main__":
    from extract import extract
    raw = extract()
    clean = transform(raw)
    print(clean[["headline", "sentiment_score", "sentiment_label"]].to_string())
