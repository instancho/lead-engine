"""
analyzer.py — Lightweight website quality analysis.

Checks pages for common issues that indicate a weak online presence,
which are useful talking points for cold outreach.
"""

import logging
import warnings

import requests
import urllib3
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)


def analyze_website(url: str) -> str:
    """
    Fetch *url* and return a comma-separated string of detected issues.

    Checks:
      - Page loads at all
      - Page size (thin content)
      - Viewport meta tag (mobile optimisation)
      - <title> tag presence
      - Meta description presence

    Returns "" if no issues detected.
    """
    if not url:
        return "No website"

    if not url.startswith("http"):
        url = f"https://{url}"

    issues: list[str] = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(
            url, timeout=config.REQUEST_TIMEOUT,
            headers=headers, allow_redirects=True,
        )
        resp.raise_for_status()
    except requests.exceptions.SSLError:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
                resp = requests.get(
                    url, timeout=config.REQUEST_TIMEOUT,
                    headers=headers, allow_redirects=True, verify=False,
                )
                resp.raise_for_status()
        except requests.RequestException:
            return "Website not loading"
    except requests.RequestException:
        return "Website not loading"

    html = resp.text
    page_size = len(resp.content)
    soup = BeautifulSoup(html, "html.parser")

    # ── Thin content ──────────────────────────────────────────────────────
    if page_size < config.THIN_CONTENT_THRESHOLD:
        issues.append("Thin content")

    # ── Mobile optimisation ───────────────────────────────────────────────
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport:
        issues.append("Not mobile optimized")

    # ── Title tag ─────────────────────────────────────────────────────────
    title_tag = soup.find("title")
    if not title_tag or not title_tag.get_text(strip=True):
        issues.append("Missing title tag")

    # ── Meta description ──────────────────────────────────────────────────
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if not meta_desc or not meta_desc.get("content", "").strip():
        issues.append("Missing meta description")

    result = ", ".join(issues)
    if result:
        logger.info(f"  Issues for {url}: {result}")
    else:
        logger.info(f"  No issues detected for {url}")

    return result
