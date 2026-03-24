"""
sheets_exporter.py — Google Sheets export module.

Pushes the scraped Leads DataFrame directly to a Google Sheet.
Supports two auth methods:
  1. OAuth (local) — opens browser, you log in with your Google account
  2. Service Account JSON (GitHub Actions) — via GOOGLE_CREDENTIALS_JSON env var
"""

import json
import logging
import os

import gspread
import pandas as pd

import config

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_client() -> gspread.Client:
    """
    Authenticate with Google.

    Priority:
      1. GOOGLE_CREDENTIALS_JSON env var (service account JSON string — for CI)
      2. OAuth with user account (opens browser first time, then caches token)
    """
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "")

    if creds_json:
        # Service account credentials passed as JSON string (GitHub Actions)
        from google.oauth2.service_account import Credentials
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        return gspread.authorize(creds)

    # OAuth flow — uses your personal Google account
    # First run opens a browser to authorize; token is cached afterwards
    return gspread.oauth(
        scopes=SCOPES,
        credentials_filename=config.GOOGLE_OAUTH_CREDENTIALS,
        authorized_user_filename=config.GOOGLE_OAUTH_TOKEN,
    )


def export_to_sheets(df: pd.DataFrame) -> bool:
    """
    Export the DataFrame to the configured Google Sheet.

    - Clears the first worksheet and writes fresh data.
    - Columns match config.CSV_COLUMNS.

    Returns True on success, False otherwise.
    """
    if not config.GOOGLE_SHEET_ID:
        logger.warning("GOOGLE_SHEET_ID not set. Skipping Google Sheets export.")
        return False

    try:
        client = _get_client()

        spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID)
        worksheet = spreadsheet.sheet1

        # Clear existing data and write fresh
        worksheet.clear()

        # Prepare data: header row + data rows
        header = list(df.columns)
        rows = df.fillna("").values.tolist()

        # Write all at once (header + rows)
        worksheet.update([header] + rows)

        logger.info(
            f"Successfully exported {len(rows)} leads to Google Sheet "
            f"'{spreadsheet.title}'"
        )
        return True

    except Exception as exc:
        logger.error(f"Failed to export to Google Sheets: {exc}")
        return False
