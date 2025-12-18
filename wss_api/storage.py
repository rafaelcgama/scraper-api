# wss_api/storage.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import pandas as pd


class StorageError(RuntimeError):
    """Raised when the Parquet file cannot be read or is invalid."""


def load_transactions(
        parquet_path: str,
        *,
        limit: int,
        offset: int,
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Load persisted transactions from Parquet.

    Returns:
      (total_count, rows_as_dicts)
    """
    if not os.path.exists(parquet_path):
        raise StorageError(f"Parquet file not found: {parquet_path}")

    df = pd.read_parquet(parquet_path)

    total = int(len(df))

    # Simple pagination
    if offset < 0:
        offset = 0
    if limit < 0:
        limit = 0

    page = df.iloc[offset: offset + limit]
    rows = page.to_dict(orient="records")
    return total, rows
