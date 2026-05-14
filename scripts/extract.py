"""
Extract: Scrape financial news headlines from RSS feeds using BeautifulSoup.
Sources: Reuters Business News, MarketWatch Top Stories (with fallback sample data).
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RSS_SOURCES = [
    {
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
    },
    {
        "name": "MarketWatch Top Stories",
        "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
    },
    {
        "name": "Yahoo Finance",
        "url": "https://finance.yahoo.com/news/rssindex",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _parse_rss(xml_text: str, source_name: str) -> list[dict]:
    """Parse RSS/XML feed into a list of headline records."""
    soup = BeautifulSoup(xml_text, "lxml-xml")
    items = soup.find_all("item")
    records = []
    for item in items:
        title = item.find("title")
        pub_date = item.find("pubDate") or item.find("dc:date")
        link = item.find("link")
        description = item.find("description")

        headline = title.get_text(strip=True) if title else None
        if not headline:
            continue

        raw_date = pub_date.get_text(strip=True) if pub_date else ""
        url = link.get_text(strip=True) if link else ""
        summary = description.get_text(strip=True) if description else ""

        records.append(
            {
                "headline": headline,
                "summary": summary[:300] if summary else "",
                "url": url,
                "source": source_name,
                "raw_date": raw_date,
                "scraped_at": datetime.utcnow().isoformat(),
            }
        )
    return records


def _fetch_source(source: dict) -> list[dict]:
    """Attempt to fetch and parse a single RSS source."""
    try:
        logger.info(f"Fetching: {source['name']} — {source['url']}")
        resp = requests.get(source["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        records = _parse_rss(resp.text, source["name"])
        logger.info(f"  → {len(records)} headlines extracted")
        return records
    except Exception as exc:
        logger.warning(f"  → Failed ({source['name']}): {exc}")
        return []


def _fallback_sample() -> list[dict]:
    """Return a small set of realistic sample headlines for offline/demo use."""
    logger.warning("All live sources failed — using sample data.")
    now = datetime.utcnow().isoformat()
    samples = [
        ("Fed signals two rate cuts in 2025 as inflation cools", "Reuters Business"),
        ("S&P 500 hits record high driven by AI sector rally", "MarketWatch"),
        ("Oil prices slip on weak China demand outlook", "Yahoo Finance"),
        ("Apple reports record Q2 earnings beating analyst estimates", "Reuters Business"),
        ("Treasury yields rise ahead of jobs data release", "MarketWatch"),
        ("Bitcoin surges past $80k on ETF inflow surge", "Yahoo Finance"),
        ("Goldman Sachs raises US GDP forecast for 2025", "Reuters Business"),
        ("Euro weakens as ECB hints at further easing", "MarketWatch"),
        ("Nvidia stock climbs after strong data center guidance", "Yahoo Finance"),
        ("US jobless claims unexpectedly fall to 6-month low", "Reuters Business"),
        ("Amazon expands AWS infrastructure in Southeast Asia", "MarketWatch"),
        ("Tech layoffs continue as sector trims costs", "Yahoo Finance"),
        ("Dollar index falls after soft CPI print", "Reuters Business"),
        ("JPMorgan profit rises 12% on higher interest income", "MarketWatch"),
        ("Tesla cuts prices in Europe amid demand slowdown", "Yahoo Finance"),
    ]
    return [
        {
            "headline": h,
            "summary": "",
            "url": "",
            "source": src,
            "raw_date": now,
            "scraped_at": now,
        }
        for h, src in samples
    ]


def extract() -> pd.DataFrame:
    """
    Extract financial news headlines from configured RSS sources.
    Falls back to sample data if all live sources are unavailable.

    Returns:
        pd.DataFrame with columns:
            headline, summary, url, source, raw_date, scraped_at
    """
    all_records: list[dict] = []
    for source in RSS_SOURCES:
        all_records.extend(_fetch_source(source))

    if not all_records:
        all_records = _fallback_sample()

    df = pd.DataFrame(all_records)
    logger.info(f"Extraction complete: {len(df)} total records")
    return df


if __name__ == "__main__":
    df = extract()
    print(df.head())
