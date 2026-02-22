# wss_api/main.py
from __future__ import annotations

import logging
import pandas as pd
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query

from wss_api.models import Transaction, TransactionsResponse
from wss_api.settings import SETTINGS
from wss_api.storage import filter_and_paginate_transactions

load_dotenv()
logger = logging.getLogger(__name__)

# This global variable will hold our Parquet data in memory (RAM)
_df: Optional[pd.DataFrame] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This runs exactly ONCE when the API server boots up.
    We load the Parquet file from the hard drive into RAM here.
    """
    global _df
    try:
        _df = pd.read_parquet(SETTINGS.parquet_path)
        logger.info(f"Loaded {len(_df)} transactions into memory.")
    except Exception as e:
        logger.warning(f"Failed to load dataset on startup. Error: {e}")
        # We don't crash. We leave `_df` as None, so the API knows data isn't ready.
    
    yield  # The API runs...
    
    # This runs exactly ONCE when the API shuts down
    _df = None


app = FastAPI(
    title="API Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def read_root():
    """
    Root endpoint that provides a welcoming entry point and basic API discovery.
    """
    return {
        "message": "Welcome to the Transaction Scraper API!",
        "status": "online",
        "endpoints": {
            "transactions": "/transactions",
            "documentation": "/docs",
            "health": "/health"
        },
        "links": {
            "github": "https://github.com/rafaelcgama/scraper-api"
        }
    }


@app.get("/transactions", response_model=TransactionsResponse)
def get_transactions(
        limit: int = Query(default=SETTINGS.default_limit, ge=0),
        offset: int = Query(default=0, ge=0),
):
    # Enforce max limit to avoid dumping huge datasets in one request
    limit = min(limit, SETTINGS.max_limit)

    # If _df is None, it means the API booted up but the scraper hasn't finished (or run at all).
    if _df is None:
        raise HTTPException(
            status_code=503, 
            detail="Transaction data is currently unavailable. Waiting for scraper to populate the file."
        )

    try:
        # Instead of reading from the hard drive, we just pass the memory cache!
        total, rows = filter_and_paginate_transactions(
            df=_df,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process transactions: {e}")

    return TransactionsResponse(
        count=total,
        limit=limit,
        offset=offset,
        transactions=[Transaction(row) for row in rows],
        source=SETTINGS.parquet_path,
    )
