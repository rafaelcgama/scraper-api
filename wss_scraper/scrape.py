import argparse
import logging
import os
import time

import pandas as pd
from dotenv import load_dotenv

from wss_scraper.settings import (
    BASE_URL,
    TRANSACTION_ENDPOINT,
    REFERER_TRANSACTION_ENDPOINT,
    REFERER_HEADERS_ENDPOINT,
    PARQUET_FILENAME,
)
from wss_scraper.login import login_and_get_session_artifacts
from wss_scraper.fetch import create_session, fetch_headers, fetch_transactions
from wss_scraper.parse import parse_transactions, parse_headers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser("WallStreetSurvivor scraper")
    parser.add_argument("--out", default=PARQUET_FILENAME)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    email = os.getenv("WSS_USERNAME")
    password = os.getenv("WSS_PASSWORD")
    chrome_binary = os.getenv("CHROME_BINARY")

    if not email or not password:
        raise SystemExit("Missing WSS_USERNAME / WSS_PASSWORD (.env file required)")

    cookies, user_agent = login_and_get_session_artifacts(
        BASE_URL, email, password, headless=True, chrome_binary=chrome_binary #args.headed
    )

    session = create_session(cookies, user_agent)

    all_rows = []
    page = 1

    SECONDS_IN_DAY = 86400
    end_date = time.strftime("%m-%d-%Y")
    start_date = time.strftime(
        "%m-%d-%Y",
        time.localtime(time.time() - 180 * SECONDS_IN_DAY)
    )
    payload_headers = fetch_headers(
        session,
        BASE_URL,
        REFERER_TRANSACTION_ENDPOINT,
        REFERER_HEADERS_ENDPOINT,
    )
    
    headers = parse_headers(payload_headers)
    
    while True:
        payload_transactions = fetch_transactions(
            session,
            BASE_URL,
            TRANSACTION_ENDPOINT,
            REFERER_TRANSACTION_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
        )

        rows = parse_transactions(headers, payload_transactions.get("Html", ""))
        all_rows.extend(rows)

        if page >= payload_transactions.get("TotalPages", 1):
            break

        page += 1

    df = pd.DataFrame(all_rows)
    df.to_parquet(args.out, index=False)

    logger.info("Scraped %d transactions → %s", len(df), args.out)


if __name__ == "__main__":
    main()