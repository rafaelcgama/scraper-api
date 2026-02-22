# wss_api/settings.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    parquet_path: str = "data/transactions.parquet"
    default_limit: int = 200
    max_limit: int = 2000


SETTINGS = Settings()