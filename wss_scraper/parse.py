# parse.py
from __future__ import annotations

import logging
from lxml import html
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ParseError(RuntimeError):
    """Raised when HTML parsing fails or extracted data is inconsistent."""


def parse_headers(page_html: str) -> list[str]:
    """
    Parse transaction table headers from the full transaction history HTML page.

    Returns normalized header keys (excluding the actions column).
    """
    tree = html.fromstring(page_html)

    ths = tree.xpath(".//div[@class='box-wrapper']//th")

    headers_raw = [th.text_content().strip() for th in ths if th.text_content().strip()]
    if not headers_raw:
        raise ParseError("Could not find transaction table headers (no <th> matched).")

    # Drop the actions column header if present
    first = headers_raw[0].strip().lower()
    if first in {"actions", "action"}:
        headers_raw = headers_raw[1:]

    headers = [h.strip().lower().replace(" ", "_") for h in headers_raw if h.strip()]

    if not headers:
        raise ParseError("Headers parsed but normalized to an empty list.")

    return headers


def parse_transactions(headers: List[str], html_fragment: str) -> List[Dict[str, Any]]:
    """
    Parse transaction rows from an HTML fragment containing <tr> elements.

    - Enforces that each row matches the header count (strict).
    - Removes the leading actions <td> when present (icons/links).
    """
    if not headers:
        raise ParseError("Header list is empty; cannot parse rows strictly.")

    doc = html.fromstring(f"<table>{html_fragment}</table>")

    transactions = []
    for i, tr in enumerate(doc.xpath(".//tr"), start=1):
        tds = tr.xpath("./td")
        if not tds:
            continue

        values = [" ".join(td.text_content().split()) for td in tds]

        # If the row includes an actions column, drop it.
        if tds and "actions" in ((tds[0].get("class") or "").lower()):
            values = values[1:]
        elif len(values) == len(headers) + 1:
            values = values[1:]

        if len(values) != len(headers):
            raise ParseError(
                f"Row {i}: expected {len(headers)} cells, got {len(values)}. "
                f"Headers={headers} Values={values}"
            )

        # Skip rows with empty cells instead of crashing the scrape
        empties = [headers[j] for j, v in enumerate(values) if v == ""]
        if empties:
            logger.warning("Row %d: empty values for columns %s - skipping row", i, empties)
            continue

        transactions.append(dict(zip(headers, values)))

    return transactions
