# wss_api/models.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, RootModel


class Transaction(RootModel[Dict[str, Any]]):
    """Transaction fields mapped by column name (snake_case)."""
    pass


class TransactionsResponse(BaseModel):
    count: int
    limit: int
    offset: int
    transactions: List[Transaction]
    source: Path
