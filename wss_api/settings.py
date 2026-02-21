# wss_api/settings.py
from __future__ import annotations

from dataclasses import dataclass
from wss_scraper.settings import PARQUET_FILENAME


@dataclass(frozen=True)
class Settings:
    parquet_path: str = PARQUET_FILENAME
    default_limit: int = 200
    max_limit: int = 2000


SETTINGS = Settings()