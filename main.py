#!/usr/bin/env python3
"""
main.py — Lead Generation System

Orchestrates the full pipeline:
  1. Scrape leads from Google Maps
  2. Enrich each lead with email extraction
  3. Analyse each website for issues
  4. Export to CSV / Google Sheets
"""

import argparse
import logging
import time

import pandas as pd

import config
from scraper import scrape_leads
from enricher import extract_email
from analyzer import analyze_website
from webhook_exporter import export_to_webhook
from sheets_exporter import export_to_sheets

# ─── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Lead generation system for freelance web design outreach."
    )
    parser.add_argument(
        "--query",
        type=str,
        default="roofing company in Dallas",
        help="Google Maps search query (default: 'roofing company in Dallas')",
    )
    parser.add_argument(
        "--max_results",
        type=int,
        default=100,
        help="Maximum number of leads to collect (default: 100)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=config.OUTPUT_FILENAME,
        help=f"Output CSV filename (default: {config.OUTPUT_FILENAME})",
    )
    parser.add_argument(
        "--skip-webhook",
        action="store_true",
        help="Skip exporting to Webhook even if configured.",
    )
    parser.add_argument(
        "--skip-sheets",
        action="store_true",
        help="Skip exporting to Google Sheets even if configured.",
    )
    return parser.parse_args()


def run_pipeline(query: str, max_results: int, output_file: str, skip_webhook: bool = False, skip_sheets: bool = False):
    """Run the full lead-generation pipeline."""

    logger.info("=" * 60)
    logger.info("  LEAD GENERATION SYSTEM")
    logger.info(f"  Query:       {query}")
    logger.info(f"  Max results: {max_results}")
    logger.info(f"  Output:      {output_file}")
    logger.info("=" * 60)

    # ── Step 1: Scrape Google Maps ────────────────────────────────────────
    logger.info("\n📍  STEP 1 / 3 — Scraping Google Maps …")
    raw_leads = scrape_leads(query, max_results)

    if not raw_leads:
        logger.warning("No leads scraped. Exiting.")
        return

    logger.info(f"   → {len(raw_leads)} leads scraped.\n")

    # ── Step 2: Enrich with email ─────────────────────────────────────────
    logger.info("📧  STEP 2 / 3 — Extracting emails …")
    for idx, lead in enumerate(raw_leads, 1):
        logger.info(f"  [{idx}/{len(raw_leads)}] {lead['business_name']}")
        lead["email"] = extract_email(lead.get("website", ""))
        time.sleep(1)  # polite delay

    # ── Step 3: Analyse websites ──────────────────────────────────────────
    logger.info("\n🔍  STEP 3 / 3 — Analysing websites …")
    for idx, lead in enumerate(raw_leads, 1):
        logger.info(f"  [{idx}/{len(raw_leads)}] {lead['business_name']}")
        lead["detected_issues"] = analyze_website(lead.get("website", ""))
        time.sleep(1)

    # ── Build DataFrame & export ──────────────────────────────────────────
    df = pd.DataFrame(raw_leads, columns=config.CSV_COLUMNS)

    # Fill NaN / None with empty strings
    df.fillna("", inplace=True)

    # Final dedup by domain (belt-and-suspenders)
    df.drop_duplicates(subset=["website"], keep="first", inplace=True)

    # 1. Export locally
    df.to_csv(output_file, index=False)
    
    # 2. Export to Webhook
    webhook_status = "Skipped (--skip-webhook)"
    if skip_webhook:
        logger.info("\n📊  STEP 5 / 6 — Webhook Export SKIPPED")
    elif config.WEBHOOK_URL:
        logger.info("\n📊  STEP 5 / 6 — Exporting to Webhook...")
        success = export_to_webhook(df)
        webhook_status = "Success" if success else "Failed"
    else:
        webhook_status = "Not configured (.env)"
        logger.info("\n📊  STEP 5 / 6 — Webhook Export SKIPPED (No URL configured)")

    # 3. Export to Google Sheets
    sheets_status = "Skipped (--skip-sheets)"
    if skip_sheets:
        logger.info("\n📊  STEP 6 / 6 — Google Sheets Export SKIPPED")
    elif config.GOOGLE_SHEET_ID:
        logger.info("\n📊  STEP 6 / 6 — Exporting to Google Sheets...")
        success = export_to_sheets(df)
        sheets_status = "Success" if success else "Failed"
    else:
        sheets_status = "Not configured (.env)"
        logger.info("\n📊  STEP 6 / 6 — Google Sheets Export SKIPPED (No Sheet ID configured)")

    logger.info("\n" + "=" * 60)
    logger.info("  ✅  PIPELINE COMPLETE")
    logger.info(f"  Leads exported: {len(df)}")
    logger.info(f"  Local File:     {output_file}")
    logger.info(f"  Webhook Export: {webhook_status}")
    logger.info(f"  Google Sheets:  {sheets_status}")
    logger.info("=" * 60)

    # Quick summary
    with_email = (df["email"] != "").sum()
    with_issues = (df["detected_issues"] != "").sum()

    logger.info(f"\n  📊  Summary:")
    logger.info(f"      Leads with email:           {with_email}/{len(df)}")
    logger.info(f"      Leads with detected issues:  {with_issues}/{len(df)}")

    return df


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        query=args.query,
        max_results=args.max_results,
        output_file=args.output,
        skip_webhook=args.skip_webhook,
        skip_sheets=args.skip_sheets,
    )
