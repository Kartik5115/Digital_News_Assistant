"""
Pipeline: Orchestrates the full Extract → Transform → Load cycle.
Run directly:
    python scripts/pipeline.py
"""

import logging
import sys
import os

# Allow importing sibling modules whether run from root or scripts/
sys.path.insert(0, os.path.dirname(__file__))

from extract import extract
from transform import transform
from load import load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_pipeline() -> dict:
    """
    Run the complete ETL pipeline.

    Returns:
        dict with keys: extracted, transformed, loaded
    """
    logger.info("=" * 55)
    logger.info("  Financial News ETL Pipeline — starting")
    logger.info("=" * 55)

    # EXTRACT
    logger.info("Step 1/3 — EXTRACT")
    raw_df = extract()

    # TRANSFORM
    logger.info("Step 2/3 — TRANSFORM")
    clean_df = transform(raw_df)

    # LOAD
    logger.info("Step 3/3 — LOAD")
    rows_inserted = load(clean_df)

    summary = {
        "extracted": len(raw_df),
        "transformed": len(clean_df),
        "loaded": rows_inserted,
    }

    logger.info("=" * 55)
    logger.info(
        f"  Pipeline complete: "
        f"{summary['extracted']} extracted, "
        f"{summary['transformed']} transformed, "
        f"{summary['loaded']} loaded"
    )
    logger.info("=" * 55)
    return summary


if __name__ == "__main__":
    result = run_pipeline()
    sys.exit(0)
