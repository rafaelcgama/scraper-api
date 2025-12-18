# wss_api/tests/test_storage.py
import unittest
from unittest.mock import patch

import pandas as pd

from wss_api.storage import StorageError, load_transactions


class TestLoadTransactions(unittest.TestCase):
    @patch("wss_api.storage.os.path.exists", return_value=False)
    def test_missing_parquet_raises(self, _exists):
        with self.assertRaises(StorageError) as ctx:
            load_transactions("data/missing.parquet", limit=10, offset=0)
        self.assertIn("Parquet file not found", str(ctx.exception))

    @patch("wss_api.storage.os.path.exists", return_value=True)
    @patch("wss_api.storage.pd.read_parquet")
    def test_load_transactions_returns_total_and_rows(self, _read_parquet, _exists):
        df = pd.DataFrame(
            [
                {"a": 1, "b": "x"},
                {"a": 2, "b": "y"},
                {"a": 3, "b": "z"},
            ]
        )
        _read_parquet.return_value = df

        total, rows = load_transactions("data/transactions.parquet", limit=2, offset=0)

        self.assertEqual(total, 3)
        self.assertEqual(rows, [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
        _read_parquet.assert_called_once_with("data/transactions.parquet")

    @patch("wss_api.storage.os.path.exists", return_value=True)
    @patch("wss_api.storage.pd.read_parquet")
    def test_pagination_offset_applied(self, _read_parquet, _exists):
        df = pd.DataFrame(
            [
                {"id": 1},
                {"id": 2},
                {"id": 3},
                {"id": 4},
            ]
        )
        _read_parquet.return_value = df

        total, rows = load_transactions("data/transactions.parquet", limit=2, offset=2)

        self.assertEqual(total, 4)
        self.assertEqual(rows, [{"id": 3}, {"id": 4}])

    @patch("wss_api.storage.os.path.exists", return_value=True)
    @patch("wss_api.storage.pd.read_parquet")
    def test_offset_beyond_end_returns_empty(self, _read_parquet, _exists):
        df = pd.DataFrame([{"id": 1}, {"id": 2}])
        _read_parquet.return_value = df

        total, rows = load_transactions("data/transactions.parquet", limit=10, offset=999)

        self.assertEqual(total, 2)
        self.assertEqual(rows, [])

    @patch("wss_api.storage.os.path.exists", return_value=True)
    @patch("wss_api.storage.pd.read_parquet")
    def test_negative_offset_is_clamped_to_zero(self, _read_parquet, _exists):
        df = pd.DataFrame([{"id": 1}, {"id": 2}, {"id": 3}])
        _read_parquet.return_value = df

        total, rows = load_transactions("data/transactions.parquet", limit=2, offset=-5)

        self.assertEqual(total, 3)
        self.assertEqual(rows, [{"id": 1}, {"id": 2}])

    @patch("wss_api.storage.os.path.exists", return_value=True)
    @patch("wss_api.storage.pd.read_parquet")
    def test_negative_limit_is_clamped_to_zero(self, _read_parquet, _exists):
        df = pd.DataFrame([{"id": 1}, {"id": 2}, {"id": 3}])
        _read_parquet.return_value = df

        total, rows = load_transactions("data/transactions.parquet", limit=-1, offset=0)

        self.assertEqual(total, 3)
        self.assertEqual(rows, [])

    @patch("wss_api.storage.os.path.exists", return_value=True)
    @patch("wss_api.storage.pd.read_parquet", side_effect=Exception("bad parquet"))
    def test_read_parquet_failure_bubbles_by_default(self, _read_parquet, _exists):
        # Current storage.py does not wrap read_parquet exceptions into StorageError.
        # This test documents the current behavior. If you later choose to wrap,
        # update this test accordingly.
        with self.assertRaises(Exception) as ctx:
            load_transactions("data/transactions.parquet", limit=10, offset=0)
        self.assertIn("bad parquet", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()