"""
WEkEO Session Timer - Playwright (Python)

Credentials via environment variables:
    WEKEO_USER=your@email.com WEKEO_PASS=yourpassword python wekeo_session_timer.py

Optional env vars:
    WEKEO_DATASET   - partial name of dataset to search (default: EO:ESA:DAT:SENTINEL-2)
    WEKEO_LAYER     - layer name to select (default: True color)
    MOUSE_INTERVAL  - seconds between mouse moves (default: 5)
    CHECK_INTERVAL  - seconds between session checks (default: 10)
    HEADLESS        - set to "true" to run headless (default: false)
"""

import os
import math
import time
import signal
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PWTimeout

# ── Config ────────────────────────────────────────────────────────────────────
USERNAME       = os.environ.get("WEKEO_USER", "gkoenig")
PASSWORD       = os.environ.get("WEKEO_PASS", "")
DATASET_HINT   = os.environ.get("WEKEO_DATASET", "EO:ESA:DAT:SENTINEL-2")
LAYER_HINT     = os.environ.get("WEKEO_LAYER", "True color")
MOUSE_INTERVAL = int(os.environ.get("MOUSE_INTERVAL", "5"))
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "10"))
HEADLESS       = os.environ.get("HEADLESS", "false").lower() == "true"

CATALOGUE_URL  = "https://wekeo.copernicus.eu/data?view=catalogue"


# ── Utilities ─────────────────────────────────────────────────────────────────
def log(msg: str):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)

def elapsed(start: float) -> str:
    s = int(time.time() - start)
    return f"{s // 60}m {s % 60}s"

def screenshot(page: Page, name: str):
    path = f"{name}.png"
    page.screenshot(path=path)
    log(f"Screenshot saved: {path}")

def dump_visible_text(page: Page, limit: int = 50):
    log("Visible text on page:")
    for t in page.locator("*:visible").all_text_contents()[:limit]:
        t = t.strip()
        if t:
            print(f"  '{t}'")


# ── Session ───────────────────────────────────────────────────────────────────
def is_session_alive(page: Page) -> bool:
    if any(k in page.url for k in ("login", "signin", "auth")):
        return False
    return page.query_selector(
        'a[href*="login"], button:has-text("Log in"), button:has-text("Sign in")'
    ) is None


# ── Login flow ────────────────────────────────────────────────────────────────
def accept_cookies(page: Page, timeout: int = 5000):
    try:
        page.locator(
            'button:has-text("Accept"), button:has-text("accept"), #onetrust-accept-btn-handler'
        ).first.click(timeout=timeout)
        log("Accepted cookie banner.")
    except PWTimeout:
        pass

def click_login_link(page: Page):
    log("Looking for login link…")
    try:
        link = page.locator('a[href*="identity.prod.wekeo2.eu/oauth2/authorize"]').first
        link.wait_for(timeout=10000)
        link.click()
        page.wait_for_load_state("networkidle")
        log(f"On login page: {page.url}")
    except PWTimeout:
        screenshot(page, "debug_no_login_link")
        raise RuntimeError("Could not find login link in banner.")

def handle_wso2_warnings(page: Page):
    # "Start over" session timeout warning
    try:
        btn = page.locator('button:has-text("Start over"), a:has-text("Start over")')
        btn.wait_for(timeout=4000)
        log("WSO2 session timeout warning — clicking 'Start over'…")
        btn.click()
        page.wait_for_load_state("networkidle")
    except PWTimeout:
        pass

    # Cookie notice
    try:
        page.locator('button:has-text("Got it")').click(timeout=4000)
        log("Accepted WSO2 cookie notice.")
    except PWTimeout:
        pass

def fill_credentials(page: Page):
    try:
        page.locator('input[name="usernameUserInput"]').wait_for(state="visible", timeout=10000)
    except PWTimeout:
        screenshot(page, "debug_no_username_field")
        raise RuntimeError(f"Username field not found at {page.url}")

    screenshot(page, "debug_login_page")
    page.locator('input[name="usernameUserInput"]').fill(USERNAME)
    page.locator('input[name="password"]').fill(PASSWORD)

    log("Submitting credentials…")
    with page.expect_navigation(timeout=30000):
        page.locator('button[type="submit"], input[type="submit"]').first.click()
    page.wait_for_load_state("networkidle")
    log(f"After login submit: {page.url}")

def check_login_error(page: Page):
    error_el = page.query_selector(
        '.alert-danger, #error-msg, .login-error, '
        'span:has-text("Invalid credentials"), span:has-text("incorrect")'
    )
    if error_el:
        screenshot(page, "debug_login_error")
        raise RuntimeError(f"Login error: {error_el.text_content()}")

def confirm_returned_to_wekeo(page: Page):
    try:
        page.wait_for_url("**/wekeo.copernicus.eu/**", timeout=30000)
        page.wait_for_load_state("networkidle")
    except PWTimeout:
        screenshot(page, "debug_post_login")
        raise RuntimeError(f"Did not return to wekeo.copernicus.eu — at {page.url}")

def login(page: Page):
    if is_session_alive(page):
        log("Already logged in via existing session, skipping login.")
        return

    click_login_link(page)
    handle_wso2_warnings(page)
    fill_credentials(page)
    check_login_error(page)
    confirm_returned_to_wekeo(page)

    if not is_session_alive(page):
        screenshot(page, "debug_session_check")
        raise RuntimeError("Login failed or session not established.")

    log("Logged in successfully.")


# ── Dataset / layer selection ─────────────────────────────────────────────────
def search_dataset(page: Page):
    log(f"Searching for dataset: {DATASET_HINT}")
    search_box = page.get_by_role("textbox", name="Free-text")
    search_box.wait_for(state="visible", timeout=15000)
    search_box.click()
    search_box.fill(DATASET_HINT)
    page.wait_for_load_state("networkidle")
    screenshot(page, "debug_catalogue")

def open_dataset(page: Page):
    log("Clicking 'Use Dataset'…")
    page.wait_for_timeout(1000)  # let React settle after search
    page.get_by_role("button", name="Use Dataset").first.click(force=True)
    page.wait_for_load_state("networkidle")
    screenshot(page, "after_use_dataset")
    log(f"URL after Use Dataset: {page.url}")
    dump_visible_text(page)

def select_layer(page: Page):
    log(f"Selecting layer: {LAYER_HINT}")
    try:
        page.get_by_text(LAYER_HINT).first.click(timeout=15000)
        page.wait_for_load_state("networkidle")
    except PWTimeout:
        screenshot(page, "debug_layer_not_found")
        raise RuntimeError(f"Layer '{LAYER_HINT}' not found on page.")

def click_dataset_action(page: Page):
    log("Clicking dataset action button…")
    page.locator(
        "li:nth-child(8) > .jsx-ef4f6a8dd706a6be.buttons-wrapper > .jsx-ef4f6a8dd706a6be"
    ).click()
    page.wait_for_load_state("networkidle")
    log("Dataset opened.")


# ── Keep-alive loop ───────────────────────────────────────────────────────────
def keep_alive(page: Page, browser: Browser, start_time: float):
    log(f"Starting mouse agitation every {MOUSE_INTERVAL}s, "
        f"session check every {CHECK_INTERVAL}s.")
    log("Press Ctrl+C to stop.\n")

    def handle_sigint(sig, frame):
        log(f"\nStopped manually after {elapsed(start_time)}.")
        screenshot(page, "session_manual_stop")
        browser.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    mouse_x   = 700
    direction = 1
    last_mouse = last_check = time.time()

    while True:
        now = time.time()

        if now - last_mouse >= MOUSE_INTERVAL:
            mouse_x += direction * 30
            if mouse_x > 1300 or mouse_x < 100:
                direction *= -1
            mouse_y = 400 + int(math.sin(now / 2) * 80)
            page.mouse.move(mouse_x, mouse_y)
            log(f"Mouse → ({mouse_x}, {mouse_y})  —  {elapsed(start_time)} elapsed")
            last_mouse = now

        if now - last_check >= CHECK_INTERVAL:
            if not is_session_alive(page):
                log(f"\nSession expired after {elapsed(start_time)}!")
                log(f"Final URL: {page.url}")
                screenshot(page, "session_expired")
                browser.close()
                sys.exit(0)
            log(f"Session alive — {elapsed(start_time)} elapsed.")
            last_check = now

        time.sleep(1)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    if not USERNAME or not PASSWORD:
        print("Please set WEKEO_USER and WEKEO_PASS environment variables.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=50)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page    = context.new_page()

        try:
            log("Navigating to WEkEO catalogue…")
            page.goto(CATALOGUE_URL, wait_until="networkidle")
            accept_cookies(page)
            log(f"Current URL: {page.url}")

            login(page)

            if "catalogue" not in page.url:
                page.goto(CATALOGUE_URL, wait_until="networkidle")

            search_dataset(page)
            open_dataset(page)
            select_layer(page)
            click_dataset_action(page)

        except RuntimeError as e:
            log(f"Fatal: {e}")
            browser.close()
            sys.exit(1)

        keep_alive(page, browser, start_time=time.time())


if __name__ == "__main__":
    main()

