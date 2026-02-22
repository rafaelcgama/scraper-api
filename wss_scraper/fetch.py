# fetch.py
from __future__ import annotations

import logging
import requests
from typing import Dict, Any, Optional
from time import sleep, time

logger = logging.getLogger(__name__)


class FetchError(RuntimeError):
    """Raised when an HTTP fetch fails in a non-recoverable way."""


def create_session(cookies: Dict[str, str], user_agent: str) -> requests.Session:
    """
    Create an authenticated requests.Session for reuse across all API calls.

    Stores only request invariants (cookies + stable headers).
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


def _get_with_retry(
        session: requests.Session,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        retries: int = 3,
        timeout_s: int = 30,
        context: str = "Request",
        return_json: bool = False,
) -> Any:
    """
    Helper function to perform an HTTP GET request with exponential backoff and error handling.
    """
    for attempt in range(1, retries + 1):
        try:
            logger.info("%s (attempt %d)", context, attempt)
            resp = session.get(url, params=params, headers=headers, timeout=timeout_s)

            if resp.status_code in (401, 403):
                raise FetchError(f"Auth expired/blocked while: {context}")

            if resp.status_code >= 500:
                raise FetchError(
                    f"Server error {resp.status_code} on {url}: {resp.text[:300]}"
                )

            resp.raise_for_status()

            if return_json:
                ctype = resp.headers.get("Content-Type", "")
                if "application/json" not in ctype.lower():
                    raise FetchError(f"Unexpected Content-Type: {ctype}")
                try:
                    return resp.json()
                except Exception as e:
                    raise FetchError(f"Invalid JSON response: {e}") from e

            return resp.text

        except Exception as e:
            logger.warning("%s failed: %s", context, e)
            if attempt == retries:
                raise FetchError(f"Failed to complete: {context} after {attempt} attempts") from e
            sleep(min(attempt, 3))

    raise FetchError(f"Failed to complete: {context} after {retries} attempts")


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
    Fetch the HTML page that contains the transaction table headers.

    Returns the raw HTML text for parsing in parse.py.
    """
    url = f"{base_url}{endpoint}"

    req_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": f"{base_url}{referer_path}",
    }

    return _get_with_retry(
        session=session,
        url=url,
        headers=req_headers,
        retries=retries,
        timeout_s=timeout_s,
        context="Fetching headers HTML",
    )


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
    Fetch one transactions page from the /account/gettransactions endpoint.

    Notes:
    - start_date / end_date must match site format (MM-DD-YYYY).
    - '_' is a cache-buster (ms timestamp) generated per request.
    """
    url = f"{base_url}{endpoint}"

    params = {
        "pageIndex": page_index,
        "pageSize": page_size,
        "startDate": start_date,
        "endDate": end_date,
        "sortField": sort_field,
        "sortDirection": sort_direction,
        "transactionType": transaction_type,
        "_": int(time() * 1000),
    }

    req_headers = {"Referer": f"{base_url}{referer_path}"}

    return _get_with_retry(
        session=session,
        url=url,
        headers=req_headers,
        params=params,
        retries=retries,
        timeout_s=timeout_s,
        context=f"Fetching transactions pageIndex={page_index}",
        return_json=True,
    )
