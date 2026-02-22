# wss_api/storage.py
from __future__ import annotations

import pandas as pd
from typing import Any, Dict, List, Tuple


def filter_and_paginate_transactions(
        df: pd.DataFrame,
        *,
        limit: int,
        offset: int,
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Apply pagination to an already-loaded Pandas DataFrame of transactions.

    Returns:
      (total_count, rows_as_dicts)
    """
    total = int(len(df))

    # Simple pagination bounds
    if offset < 0:
        offset = 0
    if limit < 0:
        limit = 0

    page = df.iloc[offset: offset + limit].copy()
    
    # JSON cannot handle NaN or NaT values cleanly, 
    # so we replace missing data with empty strings.
    page = page.fillna("")
    
    rows = page.to_dict(orient="records")
    return total, rows
