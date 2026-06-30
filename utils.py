import time
from datetime import datetime
from playwright.sync_api import Page


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
