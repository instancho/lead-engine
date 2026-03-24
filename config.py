"""
config.py — Central configuration for the lead generation system.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── OpenAI ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 120
OPENAI_TEMPERATURE = 0.7

# ─── Scraping ─────────────────────────────────────────────────────────────────
SCROLL_PAUSE_MIN = 2          # seconds – min pause between scrolls
SCROLL_PAUSE_MAX = 4          # seconds – max pause between scrolls
ACTION_DELAY_MIN = 2          # seconds – min delay between per-lead actions
ACTION_DELAY_MAX = 5          # seconds – max delay between per-lead actions
PAGE_LOAD_TIMEOUT = 15        # seconds – Selenium page-load timeout
MAPS_BASE_URL = "https://www.google.com/maps"

# ─── Website Analysis Thresholds ──────────────────────────────────────────────
THIN_CONTENT_THRESHOLD = 5000   # bytes – pages smaller than this are "thin"
REQUEST_TIMEOUT = 10             # seconds – timeout for requests.get()

# ─── Output ───────────────────────────────────────────────────────────────────
OUTPUT_FILENAME = "leads_output.csv"
CSV_COLUMNS = [
    "business_name",
    "website",
    "phone",
    "email",
    "location",
    "detected_issues",
    "personalization_line",
]

# ─── Webhook Integration ────────────────────────────────────────────────────────
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# ─── Google Sheets Integration ─────────────────────────────────────────────────
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_OAUTH_CREDENTIALS = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "credentials.json")
GOOGLE_OAUTH_TOKEN = os.getenv("GOOGLE_OAUTH_TOKEN", "authorized_user.json")
