"""Load layer: writes a validated DataFrame to SQLite with idempotent upserts.
Also exports a CSV snapshot after each run.
"""
import logging
import os
import sqlite3
from pathlib import Path

import pandas as pd

from config import config

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS asset_prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    coin        TEXT    NOT NULL,
    symbol      TEXT    NOT NULL,
    price_usd   REAL,
    price_inr   REAL,
    change_24h_pct  REAL,
    market_cap_usd  REAL,
    volume_24h_usd  REAL,
    fetched_at  TEXT    NOT NULL,
    source      TEXT    NOT NULL DEFAULT 'coingecko',
    inserted_at TEXT    DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_coin_ts ON asset_prices (coin, fetched_at);
"""


def _ensure_db(db_path: str) -> sqlite3.Connection:
    """Create DB file and schema if they don't exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(CREATE_TABLE_SQL)
    con.commit()
    return con


def load(df: pd.DataFrame) -> int:
    """Append rows to the DB and export a CSV snapshot.

    Args:
        df: Validated DataFrame from quality.run_checks().

    Returns:
        Number of rows written.
    """
    con = _ensure_db(config.db_path)
    try:
        df.to_sql("asset_prices", con, if_exists="append", index=False,
                  method="multi", chunksize=500)
        row_count = len(df)
        logger.info("Loaded %d rows to %s", row_count, config.db_path)
    finally:
        con.close()

    # CSV export
    csv_path = config.export_csv_path
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    logger.info("CSV snapshot written to %s", csv_path)

    return row_count
