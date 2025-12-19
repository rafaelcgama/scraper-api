import logging
from seleniumbase import SB
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


def login_and_get_session_artifacts(
        base_url: str,
        email: str,
        password: str,
        headless: bool = False,
        chrome_binary: Optional[str] = None
) -> Tuple[Dict[str, str], str]:
    """
    Authenticate via SeleniumBase and extract session cookies and user-agent.

    A real browser is required to pass Cloudflare protection. The returned
    cookies and user-agent can be reused for authenticated HTTP requests.
    """
    sb_kwargs = {
        "uc": True,
        "headless": headless,
    }

    if chrome_binary:
        sb_kwargs["binary_location"] = chrome_binary

    with SB(**sb_kwargs) as sb:
        logger.info("Opening login page")
        sb.open(f"{base_url}/login")
        sb.wait_for_ready_state_complete()

        sb.type("//input[@id='tbLoginUserName']", email)
        sb.type("//input[@id='Password']", password)
        sb.click("//input[@type='submit']") if chrome_binary else sb.js_click("//input[@type='submit']")

        # Wait until login completes (URL change or known element)
        sb.wait_for_ready_state_complete()
        sb.wait_for_element_not_present("//input[@id='tbLoginUserName']", timeout=10)

        current_url = sb.get_current_url()
        if "/login" in current_url.lower():
            raise RuntimeError("Login failed: still on login page")

        logger.info("Login successful, extracting session")

        user_agent = sb.driver.execute_script("return navigator.userAgent;")
        raw_cookies = sb.driver.get_cookies()

    cookies = {c["name"]: c["value"] for c in raw_cookies}
    logger.info("Extracted %d cookies", len(cookies))

    return cookies, user_agent
