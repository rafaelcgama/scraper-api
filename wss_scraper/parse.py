from typing import List, Dict, Any
from lxml import html


class ParseError(RuntimeError):
    pass


def parse_headers(page_html: str) -> list[str]:
    tree = html.fromstring(page_html)

    # Try the normal case: a <thead> with <th>
    cols = tree.xpath('.//div[@class="box-wrapper"]//th')
    headers = [col.text_content().strip() for col in cols if col.text_content().strip()]
    if headers and headers[0] in ("actions", "action", ""):
        headers = headers[1:]

    if not headers:
        raise ParseError("Could not find transaction table headers using scoped XPath")

    # Normalize
    norm = [h.lower().replace(" ", "_") for h in headers]
    return norm


def parse_transactions(headers: List[str], html_fragment: str) -> List[Dict[str, Any]]:
    """
    headers: normalized header names for the data columns (excluding the 'actions' column)
             e.g. ["type","symbol","quantity","instrument","status","price","fee","timestamp"]
    html_fragment: string containing <tr>...</tr> rows (and possibly scripts)

    Returns: list[dict] where each dict maps header -> cell text.
    """
    number_cols = len(headers)
    if number_cols == 0:
        raise ParseError("Header list is empty; cannot parse rows strictly.")

    # Wrap fragment so lxml can parse multiple <tr> nodes
    wrapped = f"<table>{html_fragment}</table>"
    doc = html.fromstring(wrapped)


    transactions = []
    for i, tr in enumerate(doc.xpath(".//tr"), start=1):
        tds = tr.xpath("./td")

        # Drop the first "actions" cell (icons/links) if present
        if tds and ("actions" in (tds[0].get("class") or "").lower()):
            tds = tds[1:]

        values = [" ".join(td.text_content().split()) for td in tds]  # keep position, normalize whitespace

        if len(values) != len(headers):
            raise ParseError(
                f"Row {i}: expected {len(headers)} cells, got {len(values)}. "
                f"Headers={headers} Values={values}"
            )

        # If you truly require non-empty values for every column:
        empties = [headers[j] for j, v in enumerate(values) if v == ""]
        if empties:
            raise ParseError(f"Row {i}: empty values for columns: {empties}")

        transactions.append(dict(zip(headers, values)))

    return transactions
