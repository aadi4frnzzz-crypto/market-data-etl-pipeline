"""Extraction layer: pulls raw price data from CoinGecko REST API.
Includes retry logic with exponential backoff.
"""
import logging
import time
from typing import Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import config

logger = logging.getLogger(__name__)


def _build_session() -> requests.Session:
    """Create a session with automatic retry on transient errors."""
    session = requests.Session()
    retry = Retry(
        total=config.api_retry_attempts,
        backoff_factor=config.api_retry_backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


def fetch_prices() -> Dict[str, Any]:
    """Fetch current prices + metadata for configured coins.

    Returns:
        Raw JSON dict from CoinGecko: {coin_id: {usd: ..., inr: ..., ...}}

    Raises:
        requests.HTTPError: On 4xx/5xx after all retries exhausted.
    """
    session = _build_session()
    endpoint = f"{config.api_base_url}/simple/price"
    params = {
        "ids": ",".join(config.coins),
        "vs_currencies": config.vs_currencies,
        "include_24hr_change": "true",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
    }

    logger.info("Fetching prices for %d coins from CoinGecko...", len(config.coins))
    start = time.perf_counter()

    response = session.get(endpoint, params=params, timeout=config.api_timeout)
    response.raise_for_status()

    elapsed = time.perf_counter() - start
    data = response.json()
    logger.info("Fetched %d coins in %.2fs", len(data), elapsed)
    return data
