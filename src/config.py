"""Central configuration for the ETL pipeline.
All env vars and constants live here — never hardcoded elsewhere.
"""
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    # CoinGecko API
    api_base_url: str = "https://api.coingecko.com/api/v3"
    api_timeout: int = 15
    api_retry_attempts: int = 3
    api_retry_backoff: float = 2.0

    # Target assets
    coins: List[str] = field(default_factory=lambda: [
        "bitcoin", "ethereum", "solana",
        "binancecoin", "ripple", "cardano",
        "polkadot", "avalanche-2"
    ])
    vs_currencies: str = "usd,inr"

    # Database
    db_path: str = os.getenv("DB_PATH", "data/crypto_prices.db")

    # Output
    export_csv_path: str = "data/latest_prices.csv"

    # Quality thresholds
    max_null_pct: float = 0.1          # fail if >10% nulls
    max_price_change_pct: float = 50.0  # alert if >50% change in one run

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
