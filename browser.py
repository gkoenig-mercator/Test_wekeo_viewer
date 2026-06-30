from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from config import Config


def create_browser(playwright, config: Config) -> Browser:
    return playwright.chromium.launch(
        headless=config.headless,
        slow_mo=50,
    )


def create_context(browser: Browser) -> tuple[BrowserContext, Page]:
    context = browser.new_context(viewport={"width": 1400, "height": 900})
    page = context.new_page()
    return context, page
