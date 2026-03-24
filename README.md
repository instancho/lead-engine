# Lead Generation & Outreach Preparation System

A Python-based system that scrapes Google Maps for service businesses, enriches leads with email addresses and website analysis, generates AI-powered personalized cold-email openers, and exports everything to a clean CSV.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Run the pipeline
```bash
# Basic usage
python main.py --query "roofing company in Dallas" --max_results 20

# Skip AI personalization (no API key needed)
python main.py --query "plumber in Austin" --max_results 10 --skip-personalization

# Custom output file
python main.py --query "dentist in Houston" --max_results 50 --output my_leads.csv
```

## Output

Generates a CSV (`leads_output.csv`) with columns:

| Column | Description |
|--------|-------------|
| `business_name` | Name from Google Maps |
| `website` | Business website URL |
| `phone` | Phone number |
| `email` | Extracted from website |
| `location` | Address / city / state |
| `detected_issues` | Website quality issues |
| `personalization_line` | AI-generated cold-email opener |

## Architecture

```
main.py          → Orchestrator (CLI + pipeline)
├── scraper.py   → Google Maps Selenium scraper
├── enricher.py  → Email extraction (requests + BeautifulSoup)
├── analyzer.py  → Website quality heuristics
├── personalizer.py → OpenAI cold-email personalization
└── config.py    → Central configuration
```

## Requirements

- Python 3.10+
- Google Chrome browser installed
- OpenAI API key (for personalization; optional with `--skip-personalization`)
