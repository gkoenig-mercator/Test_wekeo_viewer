# utils.py
from datetime import datetime
import argparse
from playwright.sync_api import Page


def log(msg: str):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def minutes_formatting_for_elapse_time(seconds: float) -> str:
    s = int(seconds)
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


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="WEkEO Session Timer - simulates a viewer session and measures disconnection time."
    )
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default=None,
    )
    parser.add_argument("--mouse-interval", type=int, default=None)
    parser.add_argument("--check-interval", type=int, default=None)
    parser.add_argument("--headless", action="store_true", default=None)

    return parser.parse_args(args)
