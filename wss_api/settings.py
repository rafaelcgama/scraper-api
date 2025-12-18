# wss_api/settings.py
from __future__ import annotations

import os
from dataclasses import dataclass
from wss_scraper.settings import PARQUET_FILENAME


@dataclass(frozen=True)
class Settings:
    parquet_path: str = os.getenv("WSS_PARQUET_PATH", PARQUET_FILENAME)
    default_limit: int = int(os.getenv("WSS_API_DEFAULT_LIMIT", "200"))
    max_limit: int = int(os.getenv("WSS_API_MAX_LIMIT", "2000"))


SETTINGS = Settings()