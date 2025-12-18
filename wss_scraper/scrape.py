# scrape.py
from __future__ import annotations

import argparse
import logging
import os
import time

import pandas as pd
from dotenv import load_dotenv

from wss_scraper.settings import (
    BASE_URL,
    HEADERS_ENDPOINT,
    TRANSACTION_ENDPOINT,
    REFERER_TRANSACTION_ENDPOINT,
    REFERER_HEADERS_ENDPOINT,
    PARQUET_FILENAME,
)
from wss_scraper.login import login_and_get_session_artifacts
from wss_scraper.fetch import create_session, fetch_headers, fetch_transactions
from wss_scraper.parse import parse_headers, parse_transactions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()


def get_dates(days_back: int = 180) -> tuple[str, str]:
    """
    Return (start_date, end_date) in the format required by WSS (MM-DD-YYYY).
    Defaults to the last 180 days.
    """
    seconds_in_day = 86400
    end_date = time.strftime("%m-%d-%Y")
    start_date = time.strftime(
        "%m-%d-%Y",
        time.localtime(time.time() - days_back * seconds_in_day),
    )
    return start_date, end_date


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="WallStreetSurvivor transaction history scraper")
    p.add_argument(
        "--out",
        default=PARQUET_FILENAME,
        help=f"Output Parquet file path (default: {PARQUET_FILENAME})",
    )
    p.add_argument(
        "--headless",
        action="store_true",
        help="Run browser headless (no UI).",
    )
    return p


def main() -> None:
    args = build_argparser().parse_args()

    email = os.getenv("WSS_USERNAME")
    password = os.getenv("WSS_PASSWORD")
    chrome_binary = os.getenv("CHROME_BINARY")

    if not email or not password:
        raise SystemExit("Missing WSS_USERNAME / WSS_PASSWORD (.env file required)")

    start_date, end_date = get_dates(days_back=180)

    # 1) Login (browser only once)
    cookies, user_agent = login_and_get_session_artifacts(
        base_url=BASE_URL,
        email=email,
        password=password,
        headless=args.headless,
        chrome_binary=chrome_binary,
    )

    # 2) Reuse authenticated HTTP session
    session = create_session(cookies, user_agent)

    # 3) Fetch headers from transaction history page (1 extra GET)
    headers_html = fetch_headers(
        session=session,
        base_url=BASE_URL,
        endpoint=HEADERS_ENDPOINT,  # e.g. "/account/transactionhistory"
        referer_path=REFERER_HEADERS_ENDPOINT,  # e.g ""/account/dashboardv2"
    )
    headers = parse_headers(headers_html)

    # 4) Fetch all pages
    all_rows = []
    page = 1

    while True:
        payload = fetch_transactions(
            session=session,
            base_url=BASE_URL,
            endpoint=TRANSACTION_ENDPOINT,  # "/account/gettransactions"
            referer_path=REFERER_TRANSACTION_ENDPOINT,  # "/account/transactionhistory"
            page_index=page,  # <-- IMPORTANT
            start_date=start_date,
            end_date=end_date,
        )

        rows = parse_transactions(headers, payload.get("Html", ""))
        all_rows.extend(rows)

        total_pages = int(payload.get("TotalPages") or 1)
        if page >= total_pages:
            break
        page += 1

    df = pd.DataFrame(all_rows)
    df.to_parquet(args.out, index=False)

    logger.info("Scraped %d transactions → %s", len(df), args.out)


if __name__ == "__main__":
    main()
