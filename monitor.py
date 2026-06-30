import math
import signal
import sys
import time

from playwright.sync_api import Page, Browser
from auth import is_session_alive
from config import Config
from utils import log, elapsed, screenshot


def keep_alive(page: Page, browser: Browser, config: Config, start_time: float):
    log(
        f"Starting mouse agitation every {config.mouse_interval}s, "
        f"session check every {config.check_interval}s."
    )
    log("Press Ctrl+C to stop.\n")

    def handle_sigint(sig, frame):
        log(f"\nStopped manually after {elapsed(start_time)}.")
        screenshot(page, "session_manual_stop")
        browser.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    mouse_x = 700
    direction = 1
    last_mouse = last_check = time.time()

    while True:
        now = time.time()

        if now - last_mouse >= config.mouse_interval:
            mouse_x += direction * 30
            if mouse_x > 1300 or mouse_x < 100:
                direction *= -1
            mouse_y = 400 + int(math.sin(now / 2) * 80)
            page.mouse.move(mouse_x, mouse_y)
            log(f"Mouse → ({mouse_x}, {mouse_y})  —  {elapsed(start_time)} elapsed")
            last_mouse = now

        if now - last_check >= config.check_interval:
            if not is_session_alive(page):
                log(f"\nSession expired after {elapsed(start_time)}!")
                log(f"Final URL: {page.url}")
                screenshot(page, "session_expired")
                browser.close()
                sys.exit(0)
            log(f"Session alive — {elapsed(start_time)} elapsed.")
            last_check = now

        time.sleep(1)
