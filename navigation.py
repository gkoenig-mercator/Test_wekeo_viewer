from playwright.sync_api import Page, TimeoutError as PWTimeout
from config import Config
from utils import log, screenshot


def search_dataset(page: Page, config: Config):
    log(f"Searching for dataset: {config.dataset_hint}")
    search_box = page.get_by_role("textbox", name="Free-text")
    search_box.wait_for(state="visible", timeout=15000)
    search_box.click()
    search_box.fill(config.dataset_hint)
    page.wait_for_load_state("networkidle")
    screenshot(page, "debug_catalogue")


def open_dataset(page: Page):
    log("Clicking 'Select layers'…")
    page.wait_for_timeout(2000)
    screenshot(page, "debug_before_use_dataset")

    buttons = page.get_by_role("button").all()
    log(f"Found {len(buttons)} buttons:")
    for btn in buttons:
        txt = btn.text_content() or ""
        log(f"  button: '{txt.strip()}'")

    page.get_by_role("button", name="Select layers").first.click(force=True)


def select_layer(page: Page, config: Config):
    log(f"Selecting layer: {config.layer_hint}")
    try:
        page.get_by_text(config.layer_hint).first.click(timeout=15000)
        page.wait_for_load_state("networkidle")
    except PWTimeout:
        screenshot(page, "debug_layer_not_found")
        raise RuntimeError(f"Layer '{config.layer_hint}' not found on page.")


def click_dataset_action(page: Page):
    log("Clicking dataset action button…")
    page.locator(
        "li:nth-child(8) > .jsx-ef4f6a8dd706a6be.buttons-wrapper > .jsx-ef4f6a8dd706a6be"
    ).click()
    page.wait_for_load_state("networkidle")
    log("Dataset opened.")


def navigate_to_dataset(page: Page, config: Config):
    """Full navigation sequence from catalogue to open dataset."""
    if "catalogue" not in page.url:
        page.goto(config.catalogue_url, wait_until="networkidle")

    search_dataset(page, config)
    open_dataset(page)
    select_layer(page, config)
    click_dataset_action(page)
