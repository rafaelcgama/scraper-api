from typing import Dict, Tuple
import logging

from seleniumbase import SB

logger = logging.getLogger(__name__)


def login_and_get_session_artifacts(
        base_url: str,
        email: str,
        password: str,
        headed: bool = False,
        chrome_binary: str | None = None
) -> Tuple[Dict[str, str], str]:
    """
    Logs in using SeleniumBase and returns cookies + user-agent.
    """

    sb_kwargs = {
        "uc": True,
        "headed": headed,
    }

    if chrome_binary:
        sb_kwargs["binary_location"] = chrome_binary

    with SB(**sb_kwargs) as sb:
        logger.info("Opening login page")
        sb.open(f"{base_url}/login")
        sb.wait_for_ready_state_complete()

        sb.type("//input[@id='tbLoginUserName']", email)
        sb.type("//input[@id='Password']", password)
        sb.click("//input[@type='submit']")

        sb.wait_for_ready_state_complete()
        sb.sleep(1)

        logger.info("Login successful, extracting session")

        user_agent = sb.driver.execute_script("return navigator.userAgent;")
        raw_cookies = sb.driver.get_cookies()

    cookies = {c["name"]: c["value"] for c in raw_cookies}
    logger.info("Extracted %d cookies", len(cookies))

    return cookies, user_agent