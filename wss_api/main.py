# wss_api/main.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv

from wss_api.models import Transaction, TransactionsResponse
from wss_api.settings import SETTINGS
from wss_api.storage import StorageError, load_transactions

load_dotenv()

app = FastAPI(
    title="WallStreetSurvivor Transactions API",
    version="1.0.0",
)


@app.get("/transactions", response_model=TransactionsResponse)
def get_transactions(
        limit: int = Query(default=SETTINGS.default_limit, ge=0),
        offset: int = Query(default=0, ge=0),
):
    # enforce max limit to avoid dumping huge datasets in one request
    limit = min(limit, SETTINGS.max_limit)

    try:
        total, rows = load_transactions(
            SETTINGS.parquet_path,
            limit=limit,
            offset=offset,
        )
    except StorageError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read transactions: {e}")

    return TransactionsResponse(
        count=total,
        limit=limit,
        offset=offset,
        transactions=[Transaction(row) for row in rows],
        source=SETTINGS.parquet_path,
    )
