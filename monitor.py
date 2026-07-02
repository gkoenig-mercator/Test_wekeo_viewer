# monitor.py
import math
import signal
import sys
import time

from playwright.sync_api import Page, Browser
from auth import is_session_alive
from config import Config
from storage import Storage
from utils import minutes_formatting_for_elapse_time


def keep_alive(page: Page, browser: Browser, config: Config, storage: Storage, start_time: float):
    storage.log(
        f"Starting mouse agitation every {config.mouse_interval}s, "
        f"session check every {config.check_interval}s."
    )
    storage.log("Press Ctrl+C to stop.\n")

    def handle_sigint(sig, frame):
        storage.log(f"\nStopped manually after {minutes_formatting_for_elapse_time(storage.session.elapsed())}.")
        storage.save_screenshot(page, "session_manual_stop")
        storage.save_result(
            duration_seconds=session.elapsed(),
            disconnect_reason="manual_stop",
            config=config
        )
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
            storage.log(f"Mouse → ({mouse_x}, {mouse_y})  —  {minutes_formatting_for_elapse_time(storage.session.elapsed())} elapsed")
            last_mouse = now

        if now - last_check >= config.check_interval:
            if not is_session_alive(page):
                storage.log(f"\nSession expired after {minutes_formatting_for_elapse_time(session.elapsed())}!")
                storage.log(f"Final URL: {page.url}")
                storage.save_screenshot(page, "session_expired")
                storage.save_result(
                    duration_seconds= storage.session.elapsed(),
                    disconnect_reason="session_expired"
                )
                browser.close()
                sys.exit(0)
            storage.log(f"Session alive — {minutes_formatting_for_elapse_time(storage.session.elapsed())} elapsed.")
            last_check = now

        time.sleep(1)
