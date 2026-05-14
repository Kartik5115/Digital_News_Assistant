"""
pipeline.py — Main ETL orchestrator.
Run with: python pipeline.py
Logs to:  logs/pipeline.log  +  stdout
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# ── Logging setup ─────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

_file_h   = logging.FileHandler(LOG_DIR / "pipeline.log")
_stream_h = logging.StreamHandler(sys.stdout)
for h in (_file_h, _stream_h):
    h.setFormatter(_fmt)

root = logging.getLogger()
root.setLevel(logging.INFO)
root.addHandler(_file_h)
root.addHandler(_stream_h)

logger = logging.getLogger("pipeline")

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from extract import extract
from transform import transform
from load import load


def run() -> dict:
    start = datetime.utcnow()

    logger.info("=" * 55)
    logger.info("  Financial News ETL Pipeline — starting")
    logger.info("=" * 55)

    # ── STEP 1: EXTRACT ───────────────────────────────────────────────────────
    logger.info("Step 1/3 — Scraping financial news sources...")
    raw = extract()
    logger.info(f"  ✔  {len(raw)} headlines collected from RSS feeds.")

    # ── STEP 2: TRANSFORM ─────────────────────────────────────────────────────
    logger.info("Step 2/3 — Cleaning data and calculating sentiment...")
    clean = transform(raw)
    logger.info(f"  ✔  Sentiment analysis complete — {len(clean)} records processed (100%).")

    # ── STEP 3: LOAD ──────────────────────────────────────────────────────────
    logger.info("Step 3/3 — Loading into SQLite database...")
    inserted = load(clean)
    skipped  = len(clean) - inserted
    logger.info(f"  ✔  {inserted} unique records added, {skipped} duplicates ignored.")

    elapsed = (datetime.utcnow() - start).seconds
    logger.info("=" * 55)
    logger.info(f"  Pipeline finished in {elapsed}s")
    logger.info("=" * 55)

    return {"extracted": len(raw), "transformed": len(clean), "loaded": inserted, "skipped": skipped}


if __name__ == "__main__":
    run()
