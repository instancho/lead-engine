"""
enricher.py — Website email extraction.

Fetches a webpage and extracts email addresses from mailto: links
and visible text using regex.
"""

import re
import logging
import warnings

import requests
import urllib3
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)

# Matches most real-world email addresses
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# Common non-human emails to filter out
BLACKLISTED_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com",
    "googleapis.com", "w3.org", "schema.org",
    "wordpress.org", "yoursite.com",
}


def _is_valid_email(email: str) -> bool:
    """Return True if the email looks like a real contact address."""
    email = email.lower()
    domain = email.split("@")[-1]

    if domain in BLACKLISTED_DOMAINS:
        return False
    if email.endswith((".png", ".jpg", ".gif", ".svg", ".webp")):
        return False
    if len(email) > 254:
        return False

    return True


def extract_email(url: str) -> str:
    """
    Fetch *url* and return the first valid email found, or "".

    Looks at:
      1. mailto: href links
      2. Regex matches in page text / HTML
    """
    if not url:
        return ""

    # Normalise
    if not url.startswith("http"):
        url = f"https://{url}"

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
        # Fallback: retry without SSL verification (common on macOS Python)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
                resp = requests.get(
                    url, timeout=config.REQUEST_TIMEOUT,
                    headers=headers, allow_redirects=True, verify=False,
                )
                resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning(f"Failed to fetch {url} (SSL fallback): {exc}")
            return ""
    except requests.RequestException as exc:
        logger.warning(f"Failed to fetch {url}: {exc}")
        return ""

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")
    found_emails: list[str] = []

    # 1 — mailto: links (highest confidence)
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("mailto:"):
            email = href.replace("mailto:", "").split("?")[0].strip()
            if _is_valid_email(email):
                found_emails.append(email.lower())

    # 2 — Regex scan across entire HTML
    for match in EMAIL_REGEX.findall(html):
        if _is_valid_email(match):
            found_emails.append(match.lower())

    # Deduplicate while preserving order (mailto hits first)
    seen = set()
    unique: list[str] = []
    for em in found_emails:
        if em not in seen:
            seen.add(em)
            unique.append(em)

    if unique:
        logger.info(f"  Email found for {url}: {unique[0]}")
        return unique[0]

    logger.info(f"  No email found for {url}")
    return ""
