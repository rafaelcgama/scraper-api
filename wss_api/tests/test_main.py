# wss_api/tests/test_main.py
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from wss_api.main import app
from wss_api.storage import StorageError


class TestGetTransactions(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("wss_api.main.load_transactions")
    def test_get_transactions_success(self, _load):
        _load.return_value = (
            3,
            [
                {"type": "BUY", "symbol": "AAPL", "quantity": "1"},
                {"type": "SELL", "symbol": "MSFT", "quantity": "2"},
            ],
        )

        r = self.client.get("/transactions?limit=2&offset=0")
        self.assertEqual(r.status_code, 200)

        body = r.json()
        self.assertEqual(body["count"], 3)
        self.assertEqual(body["limit"], 2)
        self.assertEqual(body["offset"], 0)
        self.assertIsInstance(body["transactions"], list)
        self.assertEqual(len(body["transactions"]), 2)

        # Transaction model wraps row dict under "data"
        self.assertEqual(body["transactions"][0]["data"]["symbol"], "AAPL")

        # Pydantic will serialize Path to string (if your model uses str)
        self.assertIn("source", body)

        _load.assert_called_once()
        _, kwargs = _load.call_args
        self.assertEqual(kwargs["limit"], 2)
        self.assertEqual(kwargs["offset"], 0)

    @patch("wss_api.main.load_transactions", side_effect=StorageError("Parquet file not found: data/x.parquet"))
    def test_get_transactions_storage_error_returns_404(self, _load):
        r = self.client.get("/transactions")
        self.assertEqual(r.status_code, 404)
        self.assertIn("Parquet file not found", r.json()["detail"])

    @patch("wss_api.main.load_transactions", side_effect=Exception("boom"))
    def test_get_transactions_unexpected_error_returns_500(self, _load):
        r = self.client.get("/transactions")
        self.assertEqual(r.status_code, 500)
        self.assertIn("Failed to read transactions", r.json()["detail"])

    @patch("wss_api.main.load_transactions")
    @patch("wss_api.main.SETTINGS")
    def test_limit_is_capped_by_max_limit(self, _settings, _load):
        _settings.default_limit = 200
        _settings.max_limit = 10
        _settings.parquet_path = "data/transactions.parquet"

        _load.return_value = (0, [])

        r = self.client.get("/transactions?limit=999&offset=0")
        self.assertEqual(r.status_code, 200)

        body = r.json()
        self.assertEqual(body["limit"], 10)  # capped
        _load.assert_called_once_with(
            "data/transactions.parquet",
            limit=10,
            offset=0,
        )

    def test_query_validation_rejects_negative_values(self):
        # Query(...) has ge=0 so FastAPI should reject before hitting handler
        r = self.client.get("/transactions?limit=-1&offset=0")
        self.assertEqual(r.status_code, 422)

        r2 = self.client.get("/transactions?limit=1&offset=-5")
        self.assertEqual(r2.status_code, 422)


if __name__ == "__main__":
    unittest.main()