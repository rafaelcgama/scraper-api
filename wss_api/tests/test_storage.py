# wss_api/tests/test_storage.py
import unittest
import pandas as pd
import numpy as np

from wss_api.storage import filter_and_paginate_transactions


class TestFilterAndPaginateTransactions(unittest.TestCase):
    def test_paginate_returns_total_and_rows(self):
        df = pd.DataFrame(
            [
                {"a": 1, "b": "x"},
                {"a": 2, "b": "y"},
                {"a": 3, "b": "z"},
            ]
        )

        total, rows = filter_and_paginate_transactions(df, limit=2, offset=0)

        self.assertEqual(total, 3)
        self.assertEqual(rows, [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])

    def test_pagination_offset_applied(self):
        df = pd.DataFrame([{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}])

        total, rows = filter_and_paginate_transactions(df, limit=2, offset=2)

        self.assertEqual(total, 4)
        self.assertEqual(rows, [{"id": 3}, {"id": 4}])

    def test_offset_beyond_end_returns_empty(self):
        df = pd.DataFrame([{"id": 1}, {"id": 2}])

        total, rows = filter_and_paginate_transactions(df, limit=10, offset=999)

        self.assertEqual(total, 2)
        self.assertEqual(rows, [])

    def test_negative_offset_is_clamped_to_zero(self):
        df = pd.DataFrame([{"id": 1}, {"id": 2}, {"id": 3}])

        total, rows = filter_and_paginate_transactions(df, limit=2, offset=-5)

        self.assertEqual(total, 3)
        self.assertEqual(rows, [{"id": 1}, {"id": 2}])

    def test_negative_limit_is_clamped_to_zero(self):
        df = pd.DataFrame([{"id": 1}, {"id": 2}, {"id": 3}])

        total, rows = filter_and_paginate_transactions(df, limit=-1, offset=0)

        self.assertEqual(total, 3)
        self.assertEqual(rows, [])

    def test_replaces_nan_with_empty_string(self):
        df = pd.DataFrame(
            [
                {"a": 1, "b": "x"},
                {"a": np.nan, "b": np.nan},
            ]
        )

        total, rows = filter_and_paginate_transactions(df, limit=2, offset=0)

        self.assertEqual(total, 2)
        self.assertEqual(rows[1]["a"], "")
        self.assertEqual(rows[1]["b"], "")


if __name__ == "__main__":
    unittest.main()
