from playwright.sync_api import Page, TimeoutError as PWTimeout
from config import Config
from utils import log, screenshot

LOGIN_BANNER_SELECTOR = 'a[href*="identity.prod.wekeo2.eu/oauth2/authorize"]'
# ^ reuse the exact selector _click_login_link already trusts and waits on successfully


def is_session_alive(page: Page, timeout: int = 8000) -> bool:
    """
    We detect the login banner (the one containing the OAuth login link).
    Its presence means "not logged in"; its absence means "logged in".
    We actively wait (poll) rather than snapshot, so we don't mistake
    "banner hasn't rendered yet" for "banner will never appear".
    """
    if any(
        k in page.url for k in ("login", "signin", "auth", "identity.prod.wekeo2.eu")
    ):
        return False

    try:
        page.locator(LOGIN_BANNER_SELECTOR).first.wait_for(
            state="visible", timeout=timeout
        )
        # Banner showed up within the window -> not authenticated
        return False
    except PWTimeout:
        # Banner never appeared in time -> assume authenticated
        return True


def accept_cookies(page: Page, timeout: int = 5000):
    try:
        page.locator(
            'button:has-text("Accept"), button:has-text("accept"), #onetrust-accept-btn-handler'
        ).first.click(timeout=timeout)
        log("Accepted cookie banner.")
    except PWTimeout:
        pass


def _click_login_link(page: Page):
    log("Looking for login link…")
    try:
        link = page.locator(LOGIN_BANNER_SELECTOR).first
        link.wait_for(timeout=10000)
        link.click()
        page.wait_for_load_state("networkidle")
        log(f"On login page: {page.url}")
    except PWTimeout:
        screenshot(page, "debug_no_login_link")
        raise RuntimeError("Could not find login link in banner.")


def _handle_wso2_warnings(page: Page):
    try:
        btn = page.locator('button:has-text("Start over"), a:has-text("Start over")')
        btn.wait_for(timeout=4000)
        log("WSO2 session timeout warning — clicking 'Start over'…")
        btn.click()
        page.wait_for_load_state("networkidle")
    except PWTimeout:
        pass

    try:
        page.locator('button:has-text("Got it")').click(timeout=4000)
        log("Accepted WSO2 cookie notice.")
    except PWTimeout:
        pass


def _fill_credentials(page: Page, config: Config):
    try:
        page.locator('input[name="usernameUserInput"]').wait_for(
            state="visible", timeout=10000
        )
    except PWTimeout:
        screenshot(page, "debug_no_username_field")
        raise RuntimeError(f"Username field not found at {page.url}")

    screenshot(page, "debug_login_page")
    page.locator('input[name="usernameUserInput"]').fill(config.username)
    page.locator('input[name="password"]').fill(config.password)

    log("Submitting credentials…")
    with page.expect_navigation(timeout=30000):
        page.locator('button[type="submit"], input[type="submit"]').first.click()
    page.wait_for_load_state("networkidle")
    log(f"After login submit: {page.url}")


def _check_login_error(page: Page):
    error_el = page.query_selector(
        ".alert-danger, #error-msg, .login-error, "
        'span:has-text("Invalid credentials"), span:has-text("incorrect")'
    )
    if error_el:
        screenshot(page, "debug_login_error")
        raise RuntimeError(f"Login error: {error_el.text_content()}")


def _confirm_returned_to_wekeo(page: Page):
    try:
        page.wait_for_url(lambda url: "wekeo.copernicus.eu" in url, timeout=30000)
        page.wait_for_load_state("networkidle")
    except PWTimeout:
        screenshot(page, "debug_post_login")
        raise RuntimeError(f"Did not return to wekeo.copernicus.eu — at {page.url}")


def login(page: Page, config: Config):
    if is_session_alive(page):
        log("Already logged in via existing session, skipping login.")
        return

    try:
        _click_login_link(page)
    except RuntimeError:
        # Re-check: maybe we WERE logged in and the ambiguous state fooled us
        if is_session_alive(page):
            log("Session turned out to be alive after all — skipping login.")
            return
        raise

    _handle_wso2_warnings(page)
    _fill_credentials(page, config)
    _check_login_error(page)
    _confirm_returned_to_wekeo(page)

    if not is_session_alive(page):
        screenshot(page, "debug_session_check")
        raise RuntimeError("Login failed or session not established.")

    log("Logged in successfully.")
