# wss_api/models.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, Field



class Transaction(BaseModel):
    # We keep this flexible because your scraper headers are dynamic.
    # Keys will be exactly what parse_headers() produced (snake_case).
    data: Dict[str, Any] = Field(..., description="Transaction fields mapped by column name.")


class TransactionsResponse(BaseModel):
    count: int
    limit: int
    offset: int
    transactions: List[Transaction]
    source: Path