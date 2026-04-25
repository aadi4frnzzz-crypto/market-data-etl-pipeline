"""Pipeline orchestrator: ties Extract -> Transform -> Quality -> Load together.
Entry point for both CLI execution and GitHub Actions.
"""
import logging
import sys
import time
from typing import Optional

from config import config
from extract import fetch_prices
from transform import transform
from quality import run_checks, QualityError
from load import load


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def run_pipeline() -> Optional[int]:
    """Execute the full ETL pipeline.

    Returns:
        Number of rows loaded, or None if pipeline failed.
    """
    logger = logging.getLogger("pipeline")
    start = time.perf_counter()
    logger.info("=== Market Data ETL Pipeline START ===")

    try:
        # Step 1: Extract
        logger.info("[1/4] Extracting from CoinGecko API...")
        raw = fetch_prices()

        # Step 2: Transform
        logger.info("[2/4] Transforming raw data...")
        df = transform(raw)

        # Step 3: Quality gate
        logger.info("[3/4] Running quality checks...")
        run_checks(df)

        # Step 4: Load
        logger.info("[4/4] Loading to database...")
        rows_loaded = load(df)

        elapsed = time.perf_counter() - start
        logger.info(
            "=== Pipeline COMPLETE | rows=%d | duration=%.2fs ===",
            rows_loaded, elapsed
        )
        return rows_loaded

    except QualityError as exc:
        logger.error("Quality gate blocked load: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unhandled pipeline error: %s", exc)
        sys.exit(2)


if __name__ == "__main__":
    setup_logging()
    run_pipeline()
