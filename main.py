import sys
import time
from playwright.sync_api import sync_playwright

from config import Config
from browser import create_browser, create_context
from auth import accept_cookies, login
from navigation import navigate_to_dataset
from monitor import keep_alive
from utils import log, parse_args


def run(config: Config):
    config.validate()

    with sync_playwright() as p:
        browser = create_browser(p, config)
        _, page = create_context(browser)

        try:
            log("Navigating to WEkEO catalogue…")
            page.goto(config.catalogue_url, wait_until="networkidle")
            accept_cookies(page)
            log(f"Current URL: {page.url}")

            login(page, config)
            navigate_to_dataset(page, config)

        except (RuntimeError, ValueError) as e:
            log(f"Fatal: {e}")
            browser.close()
            sys.exit(1)

        keep_alive(page, browser, config, start_time=time.time())


def main():
    args = parse_args()
    config = Config.from_env_and_args(args)
    run(config)


if __name__ == "__main__":
    main()
