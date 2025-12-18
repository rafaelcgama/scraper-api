#!/usr/bin/env bash
set -e

echo "Starting Intelligent Audit pipeline..."

echo "Running scraper..."
python -m wss_scraper.scrape --headless --out data/transactions.parquet

echo "Scrape completed."

echo "Starting API server..."
exec uvicorn wss_api.main:app --host 0.0.0.0 --port 8000