"""
pipeline.py — Main ETL orchestrator.
Run with: python pipeline.py
Logs to:  logs/pipeline.log
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# ── Logging setup ─────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "pipeline.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("pipeline")

# ── Add scripts/ to path ──────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from extract import extract
from transform import transform
from load import load


def run() -> dict:
    start = datetime.utcnow()
    logger.info("=" * 50)
    logger.info("Pipeline started")
    logger.info("=" * 50)

    try:
        logger.info("EXTRACT")
        raw = extract()

        logger.info("TRANSFORM")
        clean = transform(raw)

        logger.info("LOAD")
        n = load(clean)

        elapsed = (datetime.utcnow() - start).seconds
        result = {"extracted": len(raw), "transformed": len(clean), "loaded": n, "elapsed_s": elapsed}
        logger.info(f"Pipeline SUCCESS — {result}")
        return result

    except Exception as exc:
        logger.error(f"Pipeline FAILED: {exc}", exc_info=True)
        raise


if __name__ == "__main__":
    run()
