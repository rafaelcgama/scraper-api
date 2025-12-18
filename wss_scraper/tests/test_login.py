import unittest
from unittest.mock import MagicMock, patch, call

# Adjust this import to match your actual package/module path.
# If login.py is at wss_scraper/login.py, use:
from wss_scraper.login import login_and_get_session_artifacts


class TestLogin(unittest.TestCase):
    @patch("wss_scraper.login.SB")
    def test_login_returns_cookies_and_user_agent(self, SB_mock):
        # Arrange: mock SB context manager -> sb instance
        sb_instance = MagicMock()
        SB_mock.return_value.__enter__.return_value = sb_instance

        # Mock driver behaviors
        sb_instance.driver.execute_script.return_value = "UA_TEST"
        sb_instance.driver.get_cookies.return_value = [
            {"name": "cookie_a", "value": "A"},
            {"name": "cookie_b", "value": "B"},
        ]

        base_url = "https://app.wallstreetsurvivor.com"
        email = "user@example.com"
        password = "secret"

        # Act
        cookies, ua = login_and_get_session_artifacts(
            base_url=base_url,
            email=email,
            password=password,
            headless=False,
            chrome_binary=None,
        )

        # Assert: return values
        self.assertEqual(ua, "UA_TEST")
        self.assertEqual(cookies, {"cookie_a": "A", "cookie_b": "B"})

        # Assert: SB called with expected kwargs
        SB_mock.assert_called_once_with(uc=True, headless=False)

        # Assert: basic login flow called
        sb_instance.open.assert_called_once_with(f"{base_url}/login")
        sb_instance.wait_for_ready_state_complete.assert_called()

        sb_instance.type.assert_has_calls(
            [
                call("//input[@id='tbLoginUserName']", email),
                call("//input[@id='Password']", password),
            ],
            any_order=False,
        )
        sb_instance.click.assert_called_once_with("//input[@type='submit']")

        sb_instance.driver.execute_script.assert_called_once_with("return navigator.userAgent;")
        sb_instance.driver.get_cookies.assert_called_once()

    @patch("wss_scraper.login.SB")
    def test_login_passes_chrome_binary_location_when_provided(self, SB_mock):
        sb_instance = MagicMock()
        SB_mock.return_value.__enter__.return_value = sb_instance

        sb_instance.driver.execute_script.return_value = "UA_TEST"
        sb_instance.driver.get_cookies.return_value = []

        base_url = "https://app.wallstreetsurvivor.com"
        chrome_bin = "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

        login_and_get_session_artifacts(
            base_url=base_url,
            email="user@example.com",
            password="secret",
            headless=True,
            chrome_binary=chrome_bin,
        )

        # SB should receive binary_location when provided
        SB_mock.assert_called_once_with(uc=True, headless=True, binary_location=chrome_bin)

    @patch("wss_scraper.login.SB")
    def test_cookie_extraction_ignores_unrelated_fields(self, SB_mock):
        sb_instance = MagicMock()
        SB_mock.return_value.__enter__.return_value = sb_instance

        sb_instance.driver.execute_script.return_value = "UA_TEST"
        sb_instance.driver.get_cookies.return_value = [
            {"name": "sid", "value": "123", "domain": ".wallstreetsurvivor.com", "httpOnly": True},
            {"name": "x", "value": "y", "path": "/", "secure": True},
        ]

        cookies, ua = login_and_get_session_artifacts(
            base_url="https://app.wallstreetsurvivor.com",
            email="u",
            password="p",
        )

        self.assertEqual(ua, "UA_TEST")
        self.assertEqual(cookies, {"sid": "123", "x": "y"})


if __name__ == "__main__":
    unittest.main()