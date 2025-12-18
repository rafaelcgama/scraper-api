# wss_scraper/tests/test_scrape.py
from __future__ import annotations

import re
import unittest
from unittest.mock import MagicMock, patch

import wss_scraper.scrape as scrape

DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}$")


class TestGetDates(unittest.TestCase):
    def test_get_dates_format(self):
        start_date, end_date = scrape.get_dates(days_back=180)
        self.assertRegex(start_date, DATE_RE)
        self.assertRegex(end_date, DATE_RE)

    @patch("wss_scraper.scrape.time.time", return_value=0)
    @patch("wss_scraper.scrape.time.localtime")
    @patch("wss_scraper.scrape.time.strftime")
    def test_get_dates_calls_time_funcs(self, _strftime, _localtime, _time):
        # Just ensure it uses strftime/localtime/time in the expected shape.
        _strftime.side_effect = ["12-18-2025", "06-21-2025"]  # end_date, start_date
        start_date, end_date = scrape.get_dates(days_back=180)
        self.assertEqual(end_date, "12-18-2025")
        self.assertEqual(start_date, "06-21-2025")


class TestBuildArgParser(unittest.TestCase):
    def test_build_argparser_defaults(self):
        parser = scrape.build_argparser()
        args = parser.parse_args([])
        self.assertEqual(args.out, scrape.PARQUET_FILENAME)
        self.assertFalse(args.headless)

    def test_build_argparser_headless_flag(self):
        parser = scrape.build_argparser()
        args = parser.parse_args(["--headless"])
        self.assertTrue(args.headless)


class TestMain(unittest.TestCase):
    def setUp(self):
        # Avoid leaking argv changes across tests
        self._argv_patch = patch("wss_scraper.scrape.build_argparser")
        self.mock_build_argparser = self._argv_patch.start()
        self.addCleanup(self._argv_patch.stop)

    def _set_args(self, out="transactions.parquet", headless=False):
        args = MagicMock()
        args.out = out
        args.headless = headless
        parser = MagicMock()
        parser.parse_args.return_value = args
        self.mock_build_argparser.return_value = parser
        return args

    def test_main_missing_credentials_raises(self):
        self._set_args()

        with patch.dict("wss_scraper.scrape.os.environ", {}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                scrape.main()
            self.assertIn("Missing WSS_USERNAME / WSS_PASSWORD", str(ctx.exception))

    @patch("wss_scraper.scrape.pd.DataFrame")
    @patch("wss_scraper.scrape.parse_transactions")
    @patch("wss_scraper.scrape.fetch_transactions")
    @patch("wss_scraper.scrape.parse_headers")
    @patch("wss_scraper.scrape.fetch_headers")
    @patch("wss_scraper.scrape.create_session")
    @patch("wss_scraper.scrape.login_and_get_session_artifacts")
    def test_main_happy_path_single_page(
            self,
            mock_login,
            mock_create_session,
            mock_fetch_headers,
            mock_parse_headers,
            mock_fetch_transactions,
            mock_parse_transactions,
            mock_dataframe,
    ):
        self._set_args(out="out.parquet", headless=True)

        # env
        with patch.dict(
                "wss_scraper.scrape.os.environ",
                {"WSS_USERNAME": "u", "WSS_PASSWORD": "p", "CHROME_BINARY": "/bin/chrome"},
                clear=True,
        ):
            # login
            mock_login.return_value = ({"c": "v"}, "UA")

            # session
            session = MagicMock()
            mock_create_session.return_value = session

            # headers
            mock_fetch_headers.return_value = "<html>headers</html>"
            mock_parse_headers.return_value = ["transaction_type", "symbol"]

            # transactions payload (single page)
            mock_fetch_transactions.return_value = {"Html": "<tr>...</tr>", "TotalPages": 1}

            # parsed rows
            mock_parse_transactions.return_value = [
                {"transaction_type": "Buy", "symbol": "AAPL"}
            ]

            # dataframe mock
            df = MagicMock()
            mock_dataframe.return_value = df

            scrape.main()

        # headless flag should be passed to login
        mock_login.assert_called_once()
        _, kwargs = mock_login.call_args
        self.assertTrue(kwargs["headless"])
        self.assertEqual(kwargs["chrome_binary"], "/bin/chrome")

        # should fetch headers once and parse headers
        mock_fetch_headers.assert_called_once()
        mock_parse_headers.assert_called_once_with("<html>headers</html>")

        # should fetch transactions page 1 only
        mock_fetch_transactions.assert_called_once()
        _, tx_kwargs = mock_fetch_transactions.call_args
        self.assertEqual(tx_kwargs["page_index"], 1)

        # should write parquet to args.out
        df.to_parquet.assert_called_once_with("out.parquet", index=False)

    @patch("wss_scraper.scrape.pd.DataFrame")
    @patch("wss_scraper.scrape.parse_transactions")
    @patch("wss_scraper.scrape.fetch_transactions")
    @patch("wss_scraper.scrape.parse_headers")
    @patch("wss_scraper.scrape.fetch_headers")
    @patch("wss_scraper.scrape.create_session")
    @patch("wss_scraper.scrape.login_and_get_session_artifacts")
    def test_main_paginates_multiple_pages(
            self,
            mock_login,
            mock_create_session,
            mock_fetch_headers,
            mock_parse_headers,
            mock_fetch_transactions,
            mock_parse_transactions,
            mock_dataframe,
    ):
        self._set_args(out="out.parquet", headless=False)

        with patch.dict(
                "wss_scraper.scrape.os.environ",
                {"WSS_USERNAME": "u", "WSS_PASSWORD": "p"},
                clear=True,
        ):
            mock_login.return_value = ({"c": "v"}, "UA")
            mock_create_session.return_value = MagicMock()

            mock_fetch_headers.return_value = "<html>headers</html>"
            mock_parse_headers.return_value = ["transaction_type", "symbol"]

            # 2 pages returned
            mock_fetch_transactions.side_effect = [
                {"Html": "<tr>p1</tr>", "TotalPages": 2},
                {"Html": "<tr>p2</tr>", "TotalPages": 2},
            ]

            # parse each page into one row
            mock_parse_transactions.side_effect = [
                [{"transaction_type": "Buy", "symbol": "AAPL"}],
                [{"transaction_type": "Sell", "symbol": "MSFT"}],
            ]

            df = MagicMock()
            mock_dataframe.return_value = df

            scrape.main()

        # verify page_index went 1 then 2
        self.assertEqual(mock_fetch_transactions.call_count, 2)
        page_indexes = [call.kwargs["page_index"] for call in mock_fetch_transactions.call_args_list]
        self.assertEqual(page_indexes, [1, 2])

        # parquet called
        df.to_parquet.assert_called_once_with("out.parquet", index=False)

        # headless forwarded as False
        _, kwargs = mock_login.call_args
        self.assertFalse(kwargs["headless"])
