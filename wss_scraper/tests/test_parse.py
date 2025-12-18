# wss_scraper/tests/test_parse.py
import unittest

from wss_scraper.parse import ParseError, parse_headers, parse_transactions


class TestParseHeaders(unittest.TestCase):
    def test_parse_headers_success_drops_actions_and_normalizes(self):
        page_html = """
        <html>
          <body>
            <div class="box-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Actions</th>
                    <th>Transaction Type</th>
                    <th>Symbol</th>
                    <th>Trade Date</th>
                  </tr>
                </thead>
              </table>
            </div>
          </body>
        </html>
        """
        headers = parse_headers(page_html)
        self.assertEqual(headers, ["transaction_type", "symbol", "trade_date"])

    def test_parse_headers_success_without_actions(self):
        page_html = """
        <html>
          <body>
            <div class="box-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Symbol</th>
                    <th>Quantity</th>
                  </tr>
                </thead>
              </table>
            </div>
          </body>
        </html>
        """
        headers = parse_headers(page_html)
        self.assertEqual(headers, ["type", "symbol", "quantity"])

    def test_parse_headers_raises_when_no_th_found(self):
        page_html = "<html><body><div class='box-wrapper'></div></body></html>"
        with self.assertRaises(ParseError) as ctx:
            parse_headers(page_html)
        self.assertIn("no <th> matched", str(ctx.exception).lower())

    def test_parse_headers_raises_when_normalized_empty(self):
        # Only whitespace headers -> raw has nothing after strip()
        page_html = """
        <html>
          <body>
            <div class="box-wrapper">
              <table>
                <thead><tr><th>   </th></tr></thead>
              </table>
            </div>
          </body>
        </html>
        """
        with self.assertRaises(ParseError) as ctx:
            parse_headers(page_html)
        # In your code, this triggers the earlier "no <th> matched" check
        self.assertTrue(
            ("no <th> matched" in str(ctx.exception).lower())
            or ("normalized to an empty list" in str(ctx.exception).lower())
        )


class TestParseTransactions(unittest.TestCase):
    def test_parse_transactions_raises_when_headers_empty(self):
        with self.assertRaises(ParseError) as ctx:
            parse_transactions([], "<tr><td>A</td></tr>")
        self.assertIn("header list is empty", str(ctx.exception).lower())

    def test_parse_transactions_drops_actions_by_class(self):
        headers = ["transaction_type", "symbol", "quantity"]
        html_fragment = """
          <tr>
            <td class="actions"><a href="#">X</a></td>
            <td>Market - Buy</td>
            <td>AAPL</td>
            <td>50</td>
          </tr>
        """
        rows = parse_transactions(headers, html_fragment)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["transaction_type"], "Market - Buy")
        self.assertEqual(rows[0]["symbol"], "AAPL")
        self.assertEqual(rows[0]["quantity"], "50")

    def test_parse_transactions_drops_actions_by_count_fallback(self):
        headers = ["transaction_type", "symbol", "quantity"]
        html_fragment = """
          <tr>
            <td><a href="#">X</a></td> <!-- no class="actions", but it's extra cell -->
            <td>Market - Buy</td>
            <td>AAPL</td>
            <td>50</td>
          </tr>
        """
        rows = parse_transactions(headers, html_fragment)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], {
            "transaction_type": "Market - Buy",
            "symbol": "AAPL",
            "quantity": "50",
        })

    def test_parse_transactions_strict_count_raises(self):
        headers = ["a", "b", "c"]
        html_fragment = """
          <tr>
            <td class="actions">X</td>
            <td>1</td>
            <td>2</td>
            <!-- missing third value -->
          </tr>
        """
        with self.assertRaises(ParseError) as ctx:
            parse_transactions(headers, html_fragment)
        self.assertIn("expected 3 cells", str(ctx.exception).lower())

    def test_parse_transactions_empties_raise(self):
        headers = ["a", "b"]
        html_fragment = """
          <tr>
            <td>1</td>
            <td>   </td>
          </tr>
        """
        with self.assertRaises(ParseError) as ctx:
            parse_transactions(headers, html_fragment)
        self.assertIn("empty values", str(ctx.exception).lower())

    def test_parse_transactions_ignores_non_td_rows(self):
        headers = ["a"]
        html_fragment = """
          <tr><th>Header-ish</th></tr>
          <tr><td>1</td></tr>
        """
        rows = parse_transactions(headers, html_fragment)
        self.assertEqual(rows, [{"a": "1"}])

    def test_parse_transactions_whitespace_normalization(self):
        headers = ["a", "b"]
        html_fragment = """
          <tr>
            <td>  hello   world </td>
            <td>\n  AAPL\t </td>
          </tr>
        """
        rows = parse_transactions(headers, html_fragment)
        self.assertEqual(rows[0]["a"], "hello world")
        self.assertEqual(rows[0]["b"], "AAPL")


if __name__ == "__main__":
    unittest.main()
