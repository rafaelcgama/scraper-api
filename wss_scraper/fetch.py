# fetch.py
from __future__ import annotations

import time
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FetchError(RuntimeError):
    pass


def create_session(cookies: Dict[str, str], user_agent: str) -> requests.Session:
    """
    Create an authenticated session that can be reused across all API calls.
    Put only "invariants" here: cookies + headers that don't change per request.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }
    )
    session.cookies.update(cookies)
    return session

def fetch_headers(
        session: requests.Session,
        base_url: str,
        endpoint: str,
        referer_path: str,
        *,
        retries: int = 3,
        timeout_s: int = 30,
) -> str:
    """
    Fetch the HTML page that contains the table headers.
    """
    url = f"{base_url}{endpoint}"

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": f"{base_url}{referer_path}",
    }

    last_exc: Optional[BaseException] = None
    for attempt in range(1, retries + 1):
        try:
            logger.info("Fetching transactionhistory HTML (attempt %d)", attempt)
            resp = session.get(url, headers=headers, timeout=timeout_s)

            if resp.status_code in (401, 403):
                raise FetchError("Auth expired/blocked while fetching transactionhistory HTML.")

            if resp.status_code >= 500:
                raise FetchError(f"Server error {resp.status_code} on {endpoint}")

            resp.raise_for_status()
            return resp.text

        except Exception as e:
            last_exc = e
            logger.warning("HTML fetch failed: %s", e)
            if attempt == retries:
                break
            time.sleep(1.0 * attempt)

    raise FetchError("Failed to fetch transactionhistory HTML") from last_exc

def fetch_transactions(
        session: requests.Session,
        base_url: str,
        endpoint: str,
        referer_path: str,
        *,
        page_index: int = 1,
        page_size: int = 12,
        start_date: str,
        end_date: str,
        sort_field: str = "CreateDate",
        sort_direction: str = "DESC",
        transaction_type: int = 1,
        retries: int = 3,
        timeout_s: int = 30,
) -> Dict[str, Any]:
    """
    Calls /account/gettransactions with the parameter set you observed:

      pageIndex, pageSize, startDate, endDate, sortField, sortDirection,
      transactionType, _

    Notes:
    - start_date / end_date must match the site format (you observed MM-DD-YYYY).
    - '_' is a cache-buster (ms timestamp) and should be generated per request.
    """

    url = f"{base_url.rstrip('/')}{endpoint}"

    params = {
        "pageIndex": page_index,
        "pageSize": page_size,
        "startDate": start_date,
        "endDate": end_date,
        "sortField": sort_field,
        "sortDirection": sort_direction,
        "transactionType": transaction_type,
        "_": int(time.time() * 1000),  # cache-buster like jQuery does
    }

    # Endpoint-specific headers belong here (not in create_session)
    headers = {
        "Referer": f"{base_url}{referer_path}",
    }

    last_exc: Optional[BaseException] = None

    for attempt in range(1, retries + 1):
        try:
            logger.info("Fetching transactions pageIndex=%s (attempt %s)", page_index, attempt)

            resp = session.get(url, params=params, headers=headers, timeout=timeout_s)

            if resp.status_code in (401, 403):
                raise FetchError("Auth expired/blocked (401/403). Re-login required.")

            if resp.status_code >= 500:
                raise FetchError(f"Server error {resp.status_code} on {endpoint}")

            resp.raise_for_status()

            ctype = resp.headers.get("Content-Type", "")
            if "application/json" not in ctype.lower():
                raise FetchError(f"Unexpected Content-Type: {ctype}")

            return resp.json()

        except Exception as e:
            last_exc = e
            logger.warning("Fetch failed (pageIndex=%s): %s", page_index, e)

            if attempt == retries:
                break

            # small backoff (keep it simple)
            time.sleep(1.0 * attempt)

    raise FetchError(f"Failed to fetch pageIndex={page_index} after {retries} attempts") from last_exc
