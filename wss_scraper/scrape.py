import argparse
import logging
import os

import pandas as pd
from dotenv import load_dotenv

from wss_scraper.settings import (
    BASE_URL,
    TRANSACTION_ENDPOINT,
    DEFAULT_PAGE_SIZE,
    DEFAULT_OUTPUT_FILE,
)
from wss_scraper.login import login_and_get_session_artifacts
from wss_scraper.fetch import create_session, fetch_transaction_page
from wss_scraper.parse import parse_transactions


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser("WallStreetSurvivor scraper")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    email = os.getenv("WSS_USERNAME")
    password = os.getenv("WSS_PASSWORD")
    chrome_binary = os.getenv("CHROME_BINARY")

    if not email or not password:
        raise SystemExit("Missing WSS_USERNAME / WSS_PASSWORD (.env file required)")

    cookies, user_agent = login_and_get_session_artifacts(
        BASE_URL, email, password, headed=True, chrome_binary=chrome_binary #args.headed
    )

    session = create_session(cookies, user_agent)

    all_rows = []
    page = 1

    while True:
        payload = fetch_transaction_page(
            session,
            BASE_URL,
            TRANSACTION_ENDPOINT,
            page,
            DEFAULT_PAGE_SIZE,
        )

        rows = parse_transactions(payload.get("Html", ""))
        all_rows.extend(rows)

        if page >= payload.get("TotalPages", 1):
            break

        page += 1

    df = pd.DataFrame(all_rows)
    df.to_parquet(args.out, index=False)

    logger.info("Scraped %d transactions → %s", len(df), args.out)


if __name__ == "__main__":
    main()