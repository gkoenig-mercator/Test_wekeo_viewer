from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from config import Config

BROWSER_MAP = {
    "chromium": lambda pw: pw.chromium,
    "firefox":  lambda pw: pw.firefox,
    "webkit":   lambda pw: pw.webkit,
}

def create_browser(playwright, config: Config) -> Browser:
    launcher = BROWSER_MAP.get(config.browser)
    if launcher is None:
        raise ValueError(f"Unsupported browser: '{config.browser}'. Choose from: {list(BROWSER_MAP)}")

    return launcher(playwright).launch(
        headless=config.headless,
        slow_mo=50,
    )


def create_context(browser: Browser) -> tuple[BrowserContext, Page]:
    context = browser.new_context(viewport={"width": 1400, "height": 900})
    page = context.new_page()
    return context, page
