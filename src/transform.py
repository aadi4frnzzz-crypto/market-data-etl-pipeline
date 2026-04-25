"""Transformation layer: normalises raw CoinGecko JSON into a clean DataFrame."""
import logging
from datetime import datetime, timezone
from typing import Any, Dict

import pandas as pd

from config import config

logger = logging.getLogger(__name__)

SCHEMA = {
    "coin": str,
    "symbol": str,
    "price_usd": float,
    "price_inr": float,
    "change_24h_pct": float,
    "market_cap_usd": float,
    "volume_24h_usd": float,
    "fetched_at": str,
    "source": str,
}

COIN_SYMBOLS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "cardano": "ADA",
    "polkadot": "DOT",
    "avalanche-2": "AVAX",
}


def transform(raw: Dict[str, Any]) -> pd.DataFrame:
    """Convert raw API dict -> normalised DataFrame.

    Args:
        raw: Dict keyed by coin ID from CoinGecko simple/price endpoint.

    Returns:
        pd.DataFrame with columns matching SCHEMA.
    """
    now = datetime.now(timezone.utc).isoformat()
    rows = []

    for coin_id, data in raw.items():
        rows.append({
            "coin": coin_id,
            "symbol": COIN_SYMBOLS.get(coin_id, coin_id.upper()[:5]),
            "price_usd": data.get("usd"),
            "price_inr": data.get("inr"),
            "change_24h_pct": data.get("usd_24h_change"),
            "market_cap_usd": data.get("usd_market_cap"),
            "volume_24h_usd": data.get("usd_24h_vol"),
            "fetched_at": now,
            "source": "coingecko",
        })

    df = pd.DataFrame(rows)

    # Cast types
    for col, dtype in SCHEMA.items():
        if col in df.columns and dtype in (float, int):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Round float columns to 6 decimal places
    float_cols = [c for c, t in SCHEMA.items() if t == float and c in df.columns]
    df[float_cols] = df[float_cols].round(6)

    logger.info("Transformed %d rows | cols: %s", len(df), list(df.columns))
    return df
