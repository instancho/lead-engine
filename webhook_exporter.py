"""
webhook_exporter.py — Webhook export module.

Pushes the scraped Leads DataFrame to a Webhook URL (e.g. Make.com or Zapier)
which can then easily add it to Google Sheets or CRMs.
"""

import logging
import requests
import pandas as pd

import config

logger = logging.getLogger(__name__)

def export_to_webhook(df: pd.DataFrame) -> bool:
    """
    Export the pandas DataFrame *df* to the configured Webhook URL.
    Returns True on success, False otherwise.
    """
    if not config.WEBHOOK_URL:
        logger.warning("WEBHOOK_URL not set. Skipping webhook export.")
        return False

    try:
        # Convert DataFrame to a list of dictionaries (easy for Zapier/Make to parse)
        leads_list = df.to_dict(orient="records")

        # Basic validation
        if not leads_list:
            logger.warning("No leads to export to webhook.")
            return False

        logger.info(f"Sending {len(leads_list)} leads to webhook...")
        
        response = requests.post(
            config.WEBHOOK_URL,
            json={"leads": leads_list},
            timeout=15,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()

        logger.info("Successfully exported leads to webhook!")
        return True

    except Exception as exc:
        logger.error(f"Failed to export to webhook: {exc}")
        return False
