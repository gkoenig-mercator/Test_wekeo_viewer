"""
WEkEO Session Timer - Playwright (Python)

Usage:
    pip install playwright
    playwright install chromium
    python wekeo_session_timer.py

Credentials via environment variables:
    WEKEO_USER=your@email.com WEKEO_PASS=yourpassword python wekeo_session_timer.py

Optional env vars:
    WEKEO_DATASET   - partial name of dataset to click (default: first result)
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
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ── Config ────────────────────────────────────────────────────────────────────
USERNAME       = os.environ.get("WEKEO_USER", "")
PASSWORD       = os.environ.get("WEKEO_PASS", "")
DATASET_HINT   = os.environ.get("WEKEO_DATASET", "EO:ESA:DAT:SENTINEL-2")
MOUSE_INTERVAL = int(os.environ.get("MOUSE_INTERVAL", "5"))
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "10"))
HEADLESS       = os.environ.get("HEADLESS", "false").lower() == "true"

CATALOGUE_URL  = "https://wekeo.copernicus.eu/data?view=catalogue"

# ── Helpers ───────────────────────────────────────────────────────────────────
def elapsed(start: float) -> str:
    s = int(time.time() - start)
    return f"{s // 60}m {s % 60}s"

def log(msg: str):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)

def is_session_alive(page) -> bool:
    url = page.url
    if any(k in url for k in ("login", "signin", "auth")):
        return False
    login_btn = page.query_selector(
        'a[href*="login"], button:has-text("Log in"), button:has-text("Sign in")'
    )
    return login_btn is None


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if not USERNAME or not PASSWORD:
        print("❌  Please set WEKEO_USER and WEKEO_PASS environment variables.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=50)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page    = context.new_page()

        start_time = None  # set after successful login

        # Ctrl+C handler
        def handle_sigint(sig, frame):
            log(f"\n🛑  Stopped manually after {elapsed(start_time)}.")
            page.screenshot(path="session_manual_stop.png")
            log("Screenshot saved to session_manual_stop.png")
            browser.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_sigint)

        # ── Step 1: Navigate to catalogue ─────────────────────────────────────
        log("Navigating to WEkEO catalogue…")
        page.goto(CATALOGUE_URL, wait_until="networkidle")

         # ── Step 2: Accept cookies ────────────────────────────────────────────
        try:
            page.locator(
                'button:has-text("Accept"), button:has-text("accept"), #onetrust-accept-btn-handler'
            ).first.click(timeout=5000)
            log("Accepted cookie banner.")
        except PWTimeout:
            pass

        # ── Step 3: Click the "log in" link in the banner ─────────────────────
        log(f"Current URL: {page.url}")

        # Check if we're already logged in (e.g. valid session cookie exists)
        if is_session_alive(page):
            log("✅  Already logged in via existing session, skipping login.")
        else:
            log("Looking for login link in banner…")
            try:
                # The banner contains "Register or log in" — target the "log in" anchor
                login_link = page.locator(
                    'a[href*="identity.prod.wekeo2.eu/oauth2/authorize"]'
                ).first
                login_link.wait_for(timeout=10000)
                log("Found login link, clicking…")
                login_link.click()
                page.wait_for_load_state("networkidle")
                log(f"After clicking login link: {page.url}")
            except PWTimeout:
                log("❌  Could not find login link in banner.")
                page.screenshot(path="debug_no_login_link.png")
                log("Screenshot saved to debug_no_login_link.png")
                browser.close()
                sys.exit(1)

            # ── Handle WSO2 "session timeout" warning if it appears ───────────
            try:
                start_over_btn = page.locator('button:has-text("Start over"), a:has-text("Start over")')
                start_over_btn.wait_for(timeout=4000)
                log("⚠️  WSO2 session timeout warning detected — clicking 'Start over'…")
                start_over_btn.click()
                page.wait_for_load_state("networkidle")
                log(f"After 'Start over': {page.url}")
            except PWTimeout:
                pass  # No timeout warning, proceed normally

            # ── Accept WSO2 cookie banner if present ──────────────────────────
            try:
                page.locator('button:has-text("Got it")').click(timeout=4000)
                log("Accepted WSO2 cookie notice.")
            except PWTimeout:
                pass
            # ── Wait for username field to actually be present ────────────────
            try:
                page.locator('input[name="usernameUserInput"]').wait_for(state="visible", timeout=10000)
            except PWTimeout:
                log(f"❌  Username field not found. URL: {page.url}")
                page.screenshot(path="debug_no_username_field.png")
                browser.close()
                sys.exit(1)

            # ── Fill credentials ──────────────────────────────────────────────────────
            log(f"On login page: {page.url}")
            page.screenshot(path="debug_login_page.png")
            log("Screenshot saved to debug_login_page.png — check what the page looks like")

            page.locator('input[name="usernameUserInput"]').fill(USERNAME)
            page.locator('input[name="password"]').fill(PASSWORD)
            page.screenshot(path="debug_before_submit.png")
            log("Submitting credentials…")
            with page.expect_navigation(timeout=30000):
                page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_load_state("networkidle")
            log(f"After login submit: {page.url}")

            # ── Detect login failure ──────────────────────────────────────────
            error_el = page.query_selector(
                '.alert-danger, #error-msg, .login-error, '
                'span:has-text("Invalid credentials"), '
                'span:has-text("incorrect")'
            )
            if error_el:
                log(f"❌  Login error detected: {error_el.text_content()}")
                page.screenshot(path="debug_login_error.png")
                browser.close()
                sys.exit(1)

            # ── Confirm we're back on WEkEO ───────────────────────────────────
            try:
                page.wait_for_url("**/wekeo.copernicus.eu/**", timeout=30000)
                page.wait_for_load_state("networkidle")
            except PWTimeout:
                log(f"❌  Did not return to wekeo.copernicus.eu. Current URL: {page.url}")
                page.screenshot(path="debug_post_login.png")
                browser.close()
                sys.exit(1)

            if not is_session_alive(page):
                log("❌  Login failed or session not established. Check credentials.")
                page.screenshot(path="debug_session_check.png")
                browser.close()
                sys.exit(1)

            log("✅  Logged in successfully.")

        start_time = time.time()
        # ── Step 4: Go to catalogue and pick a dataset ────────────────────────
        if "catalogue" not in page.url:
            page.goto(CATALOGUE_URL, wait_until="networkidle")

        log("Selecting a dataset…")
        dataset_selector = ", ".join([
            "app-dataset-card",
            ".dataset-card",
            ".dataset-item",
            "mat-card",
            ".result-item",
        ])
        page.wait_for_selector(dataset_selector, timeout=20000)

        if DATASET_HINT:
            dataset_el = page.locator(dataset_selector).filter(has_text=DATASET_HINT).first
        else:
            dataset_el = page.locator(dataset_selector).first

        dataset_name = (dataset_el.text_content() or "(unknown)").strip()[:80]
        log(f'Clicking dataset: "{dataset_name}…"')
        dataset_el.click()
        page.wait_for_load_state("networkidle")
        log("Dataset opened.")

        # ── Step 5: Mouse agitation + session timer loop ──────────────────────
        log(f"Starting mouse agitation every {MOUSE_INTERVAL}s, "
            f"session check every {CHECK_INTERVAL}s.")
        log("Press Ctrl+C to stop manually.\n")

        mouse_x    = 700
        direction  = 1
        last_mouse = time.time()
        last_check = time.time()

        while True:
            now = time.time()

            # Mouse move
            if now - last_mouse >= MOUSE_INTERVAL:
                mouse_x += direction * 30
                if mouse_x > 1300 or mouse_x < 100:
                    direction *= -1
                mouse_y = 400 + int(math.sin(now / 2) * 80)
                page.mouse.move(mouse_x, mouse_y)
                log(f"🖱  Mouse → ({mouse_x}, {mouse_y})  —  {elapsed(start_time)} elapsed")
                last_mouse = now

            # Session check
            if now - last_check >= CHECK_INTERVAL:
                if not is_session_alive(page):
                    duration = elapsed(start_time)
                    log(f"\n⚠️  Session expired after {duration}!")
                    log(f"Final URL: {page.url}")
                    page.screenshot(path="session_expired.png")
                    log("Screenshot saved to session_expired.png")
                    browser.close()
                    sys.exit(0)
                else:
                    log(f"✔  Session alive — {elapsed(start_time)} elapsed.")
                last_check = now

            time.sleep(1)


if __name__ == "__main__":
    main()
