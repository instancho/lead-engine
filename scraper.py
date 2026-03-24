"""
scraper.py — Google Maps lead scraper using Selenium.

Searches Google Maps via direct URL, scrolls to load results, and extracts
lead data (business name, website, phone, location) for each listing.
"""

import time
import random
import logging
from urllib.parse import urlparse, quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import config

logger = logging.getLogger(__name__)


def _random_delay(low=None, high=None):
    """Sleep for a random duration within the configured range."""
    low = low or config.ACTION_DELAY_MIN
    high = high or config.ACTION_DELAY_MAX
    time.sleep(random.uniform(low, high))


def _normalise_domain(url: str) -> str:
    """Return a clean domain from a URL for deduplication."""
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc.lower().replace("www.", "")
        return domain
    except Exception:
        return url.lower()


def _build_driver() -> webdriver.Chrome:
    """Create and return a headless Chrome WebDriver."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=en-US")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    )
    opts.page_load_strategy = "normal"

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)
    return driver


def _scroll_results_panel(driver, panel, max_results: int, pause_min=None, pause_max=None):
    """
    Scroll the Google Maps results panel until we have enough listings
    or no new results load.
    """
    pause_min = pause_min or config.SCROLL_PAUSE_MIN
    pause_max = pause_max or config.SCROLL_PAUSE_MAX

    last_count = 0
    stale_rounds = 0

    while stale_rounds < 5:
        # Scroll the panel down
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", panel)
        time.sleep(random.uniform(pause_min, pause_max))

        # Check if "end of list" marker appeared
        try:
            end_markers = driver.find_elements(By.CSS_SELECTOR, "span.HlvSq")
            if end_markers:
                logger.info("Reached end of Google Maps listing results.")
                break
        except Exception:
            pass

        # Count current listings
        listings = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
        current_count = len(listings)

        if current_count >= max_results:
            logger.info(f"Collected {current_count} listings (target: {max_results}).")
            break

        if current_count == last_count:
            stale_rounds += 1
        else:
            stale_rounds = 0

        last_count = current_count
        logger.info(f"Scrolling… {current_count} listings loaded so far.")


def _extract_listing_data(driver, listing) -> dict | None:
    """Click a listing and extract its detail data. Returns dict or None."""
    try:
        listing.click()
        _random_delay(2, 4)

        data = {
            "business_name": "",
            "website": "",
            "phone": "",
            "location": "",
        }

        # ── Business name ─────────────────────────────────────────────────
        try:
            name_el = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf")
            data["business_name"] = name_el.text.strip()
        except Exception:
            try:
                name_el = driver.find_element(By.CSS_SELECTOR, "h1.fontHeadlineLarge")
                data["business_name"] = name_el.text.strip()
            except Exception:
                pass

        # ── Website ───────────────────────────────────────────────────────
        try:
            website_el = driver.find_element(
                By.CSS_SELECTOR, "a[data-item-id='authority']"
            )
            data["website"] = website_el.get_attribute("href") or ""
        except Exception:
            try:
                website_els = driver.find_elements(
                    By.CSS_SELECTOR, "a[aria-label*='Website']"
                )
                if website_els:
                    data["website"] = website_els[0].get_attribute("href") or ""
            except Exception:
                pass

        # ── Phone ─────────────────────────────────────────────────────────
        try:
            phone_el = driver.find_element(
                By.CSS_SELECTOR, "button[data-item-id^='phone']"
            )
            phone_text = phone_el.get_attribute("aria-label") or phone_el.text
            data["phone"] = phone_text.replace("Phone:", "").strip()
        except Exception:
            try:
                phone_els = driver.find_elements(
                    By.CSS_SELECTOR, "button[aria-label*='Phone']"
                )
                if phone_els:
                    phone_text = phone_els[0].get_attribute("aria-label") or phone_els[0].text
                    data["phone"] = phone_text.replace("Phone:", "").strip()
            except Exception:
                pass

        # ── Location / address ────────────────────────────────────────────
        try:
            addr_el = driver.find_element(
                By.CSS_SELECTOR, "button[data-item-id='address']"
            )
            data["location"] = (
                addr_el.get_attribute("aria-label") or addr_el.text
            ).replace("Address:", "").strip()
        except Exception:
            try:
                addr_els = driver.find_elements(
                    By.CSS_SELECTOR, "button[aria-label*='Address']"
                )
                if addr_els:
                    data["location"] = (
                        addr_els[0].get_attribute("aria-label") or addr_els[0].text
                    ).replace("Address:", "").strip()
            except Exception:
                pass

        # Only return if we at least have a name
        if data["business_name"]:
            return data

    except Exception as exc:
        logger.warning(f"Error extracting listing: {exc}")

    return None


def scrape_leads(search_query: str, max_results: int = 100) -> list[dict]:
    """
    Scrape Google Maps for leads matching *search_query*.

    Returns a list of dicts with keys:
        business_name, website, phone, location
    Deduplicates by domain.
    """
    logger.info(f"Starting Google Maps scrape: '{search_query}' (max {max_results})")
    driver = _build_driver()
    leads: list[dict] = []
    seen_domains: set[str] = set()

    try:
        # 1 — Navigate directly to search results via URL
        search_url = f"{config.MAPS_BASE_URL}/search/{quote_plus(search_query)}"
        logger.info(f"Navigating to: {search_url}")
        driver.get(search_url)
        time.sleep(8)  # Let Maps fully render
        logger.info(f"Page title: {driver.title}")

        # 2 — Locate the scrollable results panel
        panels = driver.find_elements(By.CSS_SELECTOR, "div[role='feed']")
        if not panels:
            panels = driver.find_elements(By.CSS_SELECTOR, "div.m6QErb.DxyBCb")
        if not panels:
            logger.error("Could not find results panel. Google Maps layout may have changed.")
            return leads

        results_panel = panels[0]
        logger.info("Found results panel.")

        # 3 — Scroll to load listings
        _scroll_results_panel(driver, results_panel, max_results)

        # 4 — Re-fetch listing elements and iterate
        listing_elements = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")[:max_results]
        logger.info(f"Processing {len(listing_elements)} listings…")

        for idx, el in enumerate(listing_elements, 1):
            try:
                # Scroll element into view first
                driver.execute_script("arguments[0].scrollIntoView(true);", el)
                _random_delay(1, 2)

                data = _extract_listing_data(driver, el)
                if data is None:
                    continue

                # Dedup by domain
                if data["website"]:
                    domain = _normalise_domain(data["website"])
                    if domain in seen_domains:
                        logger.info(f"  [{idx}] Skipping duplicate domain: {domain}")
                        continue
                    seen_domains.add(domain)
                else:
                    # Skip entries without a website
                    logger.info(f"  [{idx}] Skipping '{data['business_name']}' — no website")
                    continue

                leads.append(data)
                logger.info(f"  [{idx}] ✔ {data['business_name']}")

            except Exception as exc:
                logger.warning(f"  [{idx}] Error: {exc}")
                continue

    except Exception as exc:
        logger.error(f"Fatal scraper error: {exc}")

    finally:
        driver.quit()

    logger.info(f"Scraping complete. {len(leads)} unique leads collected.")
    return leads
