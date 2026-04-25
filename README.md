# market-data-etl-pipeline

![Python](https://img.shields.io/badge/Python-3.11-blue) ![SQLite](https://img.shields.io/badge/Database-SQLite-green) ![GitHub Actions](https://img.shields.io/badge/CI-GitHub_Actions-orange) ![License](https://img.shields.io/badge/License-MIT-yellow)

A **production-grade ETL pipeline** that extracts live cryptocurrency market data from the CoinGecko API, validates and transforms it, and loads it into a SQLite database — running automatically every 6 hours via GitHub Actions.

## Architecture

```
CoinGecko API
     |
     v
[src/extract.py]  <-- HTTP session with retry + exponential backoff
     |
     v
[src/transform.py] <-- Schema normalisation, type casting, symbol mapping
     |
     v
[src/quality.py]  <-- 5 data quality checks (fail loudly on bad data)
     |
     v
[src/load.py]     <-- SQLite append + CSV snapshot export
     |
     v
data/crypto_prices.db  +  data/latest_prices.csv
```

## Project Structure

```
market-data-etl-pipeline/
|-- src/
|   |-- config.py       # Centralised config via env vars
|   |-- extract.py      # API client with retry logic
|   |-- transform.py    # Data normalisation layer
|   |-- quality.py      # Quality gate (5 checks)
|   |-- load.py         # SQLite + CSV output
|   |-- main.py         # Pipeline orchestrator
|-- .github/
|   |-- workflows/
|       |-- pipeline.yml  # Scheduled GitHub Actions runner
|-- data/               # Auto-generated (gitignored)
|-- requirements.txt
|-- README.md
```

## Setup & Run

```bash
# 1. Clone
git clone https://github.com/aadi4frnzzz-crypto/market-data-etl-pipeline.git
cd market-data-etl-pipeline

# 2. Install
pip install -r requirements.txt

# 3. Run pipeline
cd src
python main.py
```

## Configuration

| Env Var | Default | Description |
|---|---|---|
| `DB_PATH` | `data/crypto_prices.db` | SQLite database path |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Database Schema

```sql
CREATE TABLE asset_prices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    coin            TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    price_usd       REAL,
    price_inr       REAL,
    change_24h_pct  REAL,
    market_cap_usd  REAL,
    volume_24h_usd  REAL,
    fetched_at      TEXT NOT NULL,
    source          TEXT NOT NULL DEFAULT 'coingecko',
    inserted_at     TEXT DEFAULT (datetime('now'))
);
```

## Pipeline Stages

| Stage | File | What it does |
|---|---|---|
| Extract | `extract.py` | CoinGecko API call with retry/backoff |
| Transform | `transform.py` | Normalise schema, cast types, map symbols |
| Quality | `quality.py` | 5 checks: row count, nulls, negatives, duplicates, columns |
| Load | `load.py` | Append to SQLite, write CSV snapshot |
| Orchestrate | `main.py` | Ties all stages, structured logging, clean exit codes |

## Automation

GitHub Actions runs the pipeline:
- Every 6 hours automatically
- On every push to `main` that touches `src/`
- On manual trigger (workflow_dispatch)

Output CSVs are uploaded as build artifacts (retained 30 days).

## Design Decisions

- **No Airflow/Kafka** — overkill for this scale; GitHub Actions is the right tool
- **SQLite first** — swap to Postgres by changing `load.py` connection string only
- **Quality gate fails loudly** — pipeline exits with code 1 on bad data, not silently
- **Idempotent runs** — duplicate runs append new timestamped rows; no row corruption

## Coins Tracked

BTC, ETH, SOL, BNB, XRP, ADA, DOT, AVAX

## License

MIT
