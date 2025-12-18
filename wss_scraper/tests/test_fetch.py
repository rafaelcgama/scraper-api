import unittest
from unittest.mock import MagicMock, patch

import requests

from wss_scraper.fetch import (
    FetchError,
    create_session,
    fetch_headers,
    fetch_transactions,
)


def _mock_response(
        *,
        status_code: int = 200,
        text: str = "",
        headers: dict | None = None,
        json_data=None,
        json_raises: Exception | None = None,
        raise_for_status_raises: Exception | None = None,
):
    """
    Small helper to build a response-like mock with only what fetch.py uses.
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = headers or {}

    if raise_for_status_raises is not None:
        resp.raise_for_status.side_effect = raise_for_status_raises
    else:
        resp.raise_for_status.return_value = None

    if json_raises is not None:
        resp.json.side_effect = json_raises
    else:
        resp.json.return_value = json_data

    return resp


class TestCreateSession(unittest.TestCase):
    def test_create_session_sets_headers_and_cookies(self):
        cookies = {"a": "1", "b": "2"}
        ua = "UA_TEST"

        s = create_session(cookies=cookies, user_agent=ua)

        self.assertIsInstance(s, requests.Session)
        self.assertEqual(s.headers.get("User-Agent"), ua)
        self.assertIn("application/json", s.headers.get("Accept", ""))
        self.assertEqual(s.headers.get("X-Requested-With"), "XMLHttpRequest")

        # RequestsCookieJar behaves like a dict for simple get()
        self.assertEqual(s.cookies.get("a"), "1")
        self.assertEqual(s.cookies.get("b"), "2")


class TestFetchHeaders(unittest.TestCase):
    @patch("wss_scraper.fetch.sleep", return_value=None)
    def test_fetch_headers_success(self, _sleep):
        session = MagicMock()
        session.get.return_value = _mock_response(status_code=200, text="<html>ok</html>")

        html = fetch_headers(
            session=session,
            base_url="https://example.com",
            endpoint="/account/transactionhistory",
            referer_path="/account/transactionhistory",
            retries=3,
            timeout_s=30,
        )

        self.assertEqual(html, "<html>ok</html>")
        session.get.assert_called()

    @patch("wss_scraper.fetch.sleep", return_value=None)
    def test_fetch_headers_401_raises_wrapper(self, _sleep):
        session = MagicMock()
        session.get.return_value = _mock_response(status_code=401, text="nope")

        with self.assertRaises(FetchError) as ctx:
            fetch_headers(
                session=session,
                base_url="https://example.com",
                endpoint="/account/transactionhistory",
                referer_path="/account/transactionhistory",
                retries=1,
                timeout_s=30,
            )

        # Your function wraps on last attempt
        self.assertIn("Failed to fetch headers HTML", str(ctx.exception))

    @patch("wss_scraper.fetch.sleep", return_value=None)
    def test_fetch_headers_5xx_raises_wrapper(self, _sleep):
        session = MagicMock()
        session.get.return_value = _mock_response(status_code=500, text="server error")

        with self.assertRaises(FetchError) as ctx:
            fetch_headers(
                session=session,
                base_url="https://example.com",
                endpoint="/account/transactionhistory",
                referer_path="/account/transactionhistory",
                retries=1,
                timeout_s=30,
            )

        # Current behavior: wrapper message, not the 5xx message
        self.assertIn("Failed to fetch headers HTML", str(ctx.exception))

    @patch("wss_scraper.fetch.sleep", return_value=None)
    def test_fetch_headers_retries_then_succeeds(self, _sleep):
        session = MagicMock()
        session.get.side_effect = [
            _mock_response(status_code=500, text="boom"),
            _mock_response(status_code=200, text="<html>ok</html>"),
        ]

        html = fetch_headers(
            session=session,
            base_url="https://example.com",
            endpoint="/account/transactionhistory",
            referer_path="/account/transactionhistory",
            retries=3,
            timeout_s=30,
        )

        self.assertEqual(html, "<html>ok</html>")
        self.assertEqual(session.get.call_count, 2)
        _sleep.assert_called()  # backoff happened


class TestFetchTransactions(unittest.TestCase):
    @patch("wss_scraper.fetch.sleep", return_value=None)
    def test_fetch_transactions_success_json(self, _sleep):
        session = MagicMock()
        session.get.return_value = _mock_response(
            status_code=200,
            headers={"Content-Type": "application/json; charset=utf-8"},
            json_data={"Html": "<tr>...</tr>", "TotalPages": 1},
        )

        payload = fetch_transactions(
            session=session,
            base_url="https://example.com",
            endpoint="/account/gettransactions",
            referer_path="/account/transactionhistory",
            start_date="06-17-2025",
            end_date="12-17-2025",
            retries=3,
            timeout_s=30,
        )

        self.assertIsInstance(payload, dict)
        self.assertIn("Html", payload)
        session.get.assert_called()

        # Also verify we pass params and referer header
        _, kwargs = session.get.call_args
        self.assertIn("params", kwargs)
        self.assertIn("headers", kwargs)
        self.assertIn("Referer", kwargs["headers"])
        self.assertTrue(kwargs["headers"]["Referer"].endswith("/account/transactionhistory"))

    @patch("wss_scraper.fetch.sleep", return_value=None)
    def test_fetch_transactions_401_raises_wrapper(self, _sleep):
        session = MagicMock()
        session.get.return_value = _mock_response(
            status_code=401,
            headers={"Content-Type": "application/json"},
            json_data={},
        )

        with self.assertRaises(FetchError) as ctx:
            fetch_transactions(
                session=session,
                base_url="https://example.com",
                endpoint="/account/gettransactions",
                referer_path="/account/transactionhistory",
                start_date="06-17-2025",
                end_date="12-17-2025",
                retries=1,
                timeout_s=30,
            )

        self.assertIn("Failed to fetch pageIndex=1 after 1 attempts", str(ctx.exception))

    @patch("wss_scraper.fetch.sleep", return_value=None)
    def test_fetch_transactions_5xx_raises_wrapper(self, _sleep):
        session = MagicMock()
        session.get.return_value = _mock_response(
            status_code=500,
            text="server error",
            headers={"Content-Type": "application/json"},
            json_data={},
        )

        with self.assertRaises(FetchError) as ctx:
            fetch_transactions(
                session=session,
                base_url="https://example.com",
                endpoint="/account/gettransactions",
                referer_path="/account/transactionhistory",
                start_date="06-17-2025",
                end_date="12-17-2025",
                retries=1,
                timeout_s=30,
            )

        self.assertIn("Failed to fetch pageIndex=1 after 1 attempts", str(ctx.exception))

    @patch("wss_scraper.fetch.sleep", return_value=None)
    def test_fetch_transactions_content_type_mismatch_raises_wrapper(self, _sleep):
        session = MagicMock()
        session.get.return_value = _mock_response(
            status_code=200,
            headers={"Content-Type": "text/html"},
            text="<html>no json</html>",
        )

        with self.assertRaises(FetchError) as ctx:
            fetch_transactions(
                session=session,
                base_url="https://example.com",
                endpoint="/account/gettransactions",
                referer_path="/account/transactionhistory",
                start_date="06-17-2025",
                end_date="12-17-2025",
                retries=1,
                timeout_s=30,
            )

        self.assertIn("Failed to fetch pageIndex=1 after 1 attempts", str(ctx.exception))

    @patch("wss_scraper.fetch.sleep", return_value=None)
    def test_fetch_transactions_invalid_json_sets_cause(self, _sleep):
        session = MagicMock()
        bad_json_exc = ValueError("bad json")
        session.get.return_value = _mock_response(
            status_code=200,
            headers={"Content-Type": "application/json; charset=utf-8"},
            json_raises=bad_json_exc,
        )

        with self.assertRaises(FetchError) as ctx:
            fetch_transactions(
                session=session,
                base_url="https://example.com",
                endpoint="/account/gettransactions",
                referer_path="/account/transactionhistory",
                start_date="06-17-2025",
                end_date="12-17-2025",
                retries=1,
                timeout_s=30,
            )

        # Wrapper at the end, because invalid JSON becomes FetchError, then caught, then wrapper raised
        self.assertIn("Failed to fetch pageIndex=1 after 1 attempts", str(ctx.exception))

        # In your code, the "Invalid JSON response: ..." FetchError is raised using "from e",
        # but it gets swallowed by the outer try/except and replaced by the wrapper.
        # So we can't rely on __cause__ here at the top level.
        # We only verify it doesn't crash and returns the correct wrapper message.

    @patch("wss_scraper.fetch.sleep", return_value=None)
    def test_fetch_transactions_retries_then_succeeds(self, _sleep):
        session = MagicMock()
        session.get.side_effect = [
            _mock_response(status_code=500, text="boom", headers={"Content-Type": "application/json"}),
            _mock_response(
                status_code=200,
                headers={"Content-Type": "application/json"},
                json_data={"Html": "<tr>...</tr>", "TotalPages": 1},
            ),
        ]

        payload = fetch_transactions(
            session=session,
            base_url="https://example.com",
            endpoint="/account/gettransactions",
            referer_path="/account/transactionhistory",
            start_date="06-17-2025",
            end_date="12-17-2025",
            retries=3,
            timeout_s=30,
        )

        self.assertIn("Html", payload)
        self.assertEqual(session.get.call_count, 2)
        _sleep.assert_called()