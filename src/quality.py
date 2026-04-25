"""Data quality gate: validates a transformed DataFrame before it hits the DB.
Raises QualityError on any failed check so the pipeline fails loudly.
"""
import logging
from dataclasses import dataclass
from typing import List

import pandas as pd

from config import config

logger = logging.getLogger(__name__)


class QualityError(Exception):
    """Raised when a data quality check fails."""


@dataclass
class QualityReport:
    passed: bool
    checks: List[str]
    errors: List[str]


def run_checks(df: pd.DataFrame) -> QualityReport:
    """Run all quality checks on a transformed DataFrame.

    Args:
        df: DataFrame output from transform.transform()

    Returns:
        QualityReport summarising pass/fail per check.

    Raises:
        QualityError: If any hard check fails.
    """
    checks: List[str] = []
    errors: List[str] = []

    # 1. Row count check
    if len(df) == 0:
        errors.append("FAIL: DataFrame is empty - no rows to load.")
    else:
        checks.append(f"PASS: row_count={len(df)}")

    # 2. Required columns present
    required = ["coin", "price_usd", "price_inr", "fetched_at"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        errors.append(f"FAIL: missing required columns: {missing_cols}")
    else:
        checks.append("PASS: all required columns present")

    # 3. Null rate check
    for col in ["price_usd", "price_inr"]:
        if col in df.columns:
            null_pct = df[col].isna().mean()
            if null_pct > config.max_null_pct:
                errors.append(f"FAIL: {col} null rate {null_pct:.1%} exceeds {config.max_null_pct:.1%}")
            else:
                checks.append(f"PASS: {col} null_rate={null_pct:.1%}")

    # 4. Price sanity: no negative prices
    if "price_usd" in df.columns:
        neg = (df["price_usd"] < 0).sum()
        if neg > 0:
            errors.append(f"FAIL: {neg} rows have negative price_usd")
        else:
            checks.append("PASS: no negative prices")

    # 5. Duplicate coin check
    dup_count = df["coin"].duplicated().sum() if "coin" in df.columns else 0
    if dup_count > 0:
        errors.append(f"FAIL: {dup_count} duplicate coin rows detected")
    else:
        checks.append("PASS: no duplicate coin rows")

    passed = len(errors) == 0
    report = QualityReport(passed=passed, checks=checks, errors=errors)

    for msg in checks:
        logger.info(msg)
    for msg in errors:
        logger.error(msg)

    if not passed:
        raise QualityError(f"Quality gate failed with {len(errors)} error(s). See logs.")

    logger.info("Quality gate PASSED (%d checks)", len(checks))
    return report
