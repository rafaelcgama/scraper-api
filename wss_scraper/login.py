import logging
import time
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
    """
    sb_kwargs = {
        "uc": True,
        "headless": headless,
    }

    if chrome_binary:
        sb_kwargs["binary_location"] = chrome_binary

    with SB(**sb_kwargs) as sb:
        logger.info("Opening login page: %s/login", base_url)
        sb.open(f"{base_url}/login")
        sb.wait_for_ready_state_complete()

        sb.type("//input[@id='tbLoginUserName']", email)
        sb.type("//input[@id='Password']", password)
        
        # Small sleep helps headless browsers register the typed text before clicking
        time.sleep(1)
        
        # Use JS click if headless for maximum reliability in Docker/Challenges
        sb.js_click("//input[@type='submit']") if headless else sb.click("//input[@type='submit']")

        # Wait until login completes (URL change or known element)
        sb.wait_for_ready_state_complete()
        
        # Increase timeout to 20s for slower environments like Docker
        sb.wait_for_element_not_present("//input[@id='tbLoginUserName']", timeout=20)

        current_url = sb.get_current_url()
        if "/login" in current_url.lower():
            raise RuntimeError(f"Login failed: still on {current_url}")

        logger.info("Login successful")
        user_agent = sb.driver.execute_script("return navigator.userAgent;")
        raw_cookies = sb.driver.get_cookies()

    cookies = {c["name"]: c["value"] for c in raw_cookies}
    return cookies, user_agent
