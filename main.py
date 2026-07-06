# main.py
from playwright.sync_api import sync_playwright

from session import Session
from storage import Storage
from config import Config
from browser import create_browser, create_context
from auth import accept_cookies, login
from navigation import navigate_to_dataset
from monitor import keep_alive
from utils import parse_args


def main():
    args = parse_args()
    config = Config.from_env_and_args(args)
    config.validate()

    session = Session(config)
    storage = Storage(session)

    storage.log(f"Run started: {session.run_id}")
    storage.log(f"Browser: {config.browser} | Headless: {config.headless}")

    with sync_playwright() as p:
        browser = create_browser(p, config)
        context, page = create_context(browser)
        page.goto(config.catalogue_url, wait_until="domcontentloaded")

        try:
            accept_cookies(page)
            login(page, config)
            navigate_to_dataset(page, config)
        except Exception as e:
            storage.log(f"Error: {e}")
            storage.save_screenshot(page, "error")
            storage.save_result(
                duration_seconds=int(session.elapsed()), disconnect_reason="error"
            )
            context.close()
            browser.close()
            return

        keep_alive(page, browser, config, storage, session._start_time)


if __name__ == "__main__":
    main()
