# wss_api/tests/test_main.py
import unittest
from unittest.mock import patch
import pandas as pd
from fastapi.testclient import TestClient

from wss_api.main import app


class TestGetTransactions(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("wss_api.main._df", new_callable=lambda: pd.DataFrame(
        [
            {"type": "BUY", "symbol": "AAPL", "quantity": "1"},
            {"type": "SELL", "symbol": "MSFT", "quantity": "2"},
            {"type": "BUY", "symbol": "TSLA", "quantity": "3"},
        ]
    ))
    def test_get_transactions_success(self, _df):
        r = self.client.get("/transactions?limit=2&offset=0")
        self.assertEqual(r.status_code, 200)

        body = r.json()
        self.assertEqual(body["count"], 3)
        self.assertEqual(body["limit"], 2)
        self.assertEqual(body["offset"], 0)
        self.assertIsInstance(body["transactions"], list)
        self.assertEqual(len(body["transactions"]), 2)

        # Transaction model wraps row dict under "data"
        self.assertEqual(body["transactions"][0]["symbol"], "AAPL")

        # Pydantic will serialize Path to string (if your model uses str)
        self.assertIn("source", body)

    @patch("wss_api.main._df", None)
    def test_get_transactions_returns_503_if_data_not_loaded(self):
        r = self.client.get("/transactions")
        self.assertEqual(r.status_code, 503)
        self.assertIn("Transaction data is currently unavailable", r.json()["detail"])

    @patch("wss_api.main.filter_and_paginate_transactions", side_effect=Exception("boom"))
    @patch("wss_api.main._df", new_callable=lambda: pd.DataFrame([{"a": 1}]))
    def test_get_transactions_unexpected_error_returns_500(self, _, _mock_filter):
        r = self.client.get("/transactions")
        self.assertEqual(r.status_code, 500)
        self.assertIn("Failed to process transactions: boom", r.json()["detail"])

    @patch("wss_api.main.SETTINGS")
    @patch("wss_api.main._df", new_callable=lambda: pd.DataFrame())
    @patch("wss_api.main.filter_and_paginate_transactions", return_value=(0, []))
    def test_limit_is_capped_by_max_limit(self, _filter, _, _settings):
        _settings.default_limit = 200
        _settings.max_limit = 10
        _settings.parquet_path = "data/transactions.parquet"

        r = self.client.get("/transactions?limit=999&offset=0")
        self.assertEqual(r.status_code, 200)

        body = r.json()
        self.assertEqual(body["limit"], 10)  # capped
        _filter.assert_called_once()
        _, kwargs = _filter.call_args
        self.assertEqual(kwargs["limit"], 10)
        self.assertEqual(kwargs["offset"], 0)

    def test_query_validation_rejects_negative_values(self):
        # Query(...) has ge=0 so FastAPI should reject before hitting handler
        r = self.client.get("/transactions?limit=-1&offset=0")
        self.assertEqual(r.status_code, 422)

        r2 = self.client.get("/transactions?limit=1&offset=-5")
        self.assertEqual(r2.status_code, 422)


if __name__ == "__main__":
    unittest.main()
