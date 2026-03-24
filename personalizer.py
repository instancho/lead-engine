"""
personalizer.py — AI-powered personalization using OpenAI.

Generates short, natural cold-email openers based on a business's name
and any detected website issues.
"""

import logging

from openai import OpenAI

import config

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> OpenAI:
    """Lazy-initialise the OpenAI client."""
    global _client
    if _client is None:
        if not config.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set — personalization will be skipped.")
            return None  # type: ignore
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = (
    "You are a cold-email copywriter for a freelance web design agency. "
    "Given a business name and a list of website issues, write a 1–2 sentence "
    "personalised opener for a cold email. The tone must be:\n"
    "  • Natural and conversational\n"
    "  • Observational, not salesy or pushy\n"
    "  • Specific to the business — never generic\n"
    "Do NOT include a subject line. Do NOT start with 'Hi' or 'Hey'. "
    "Just the opener paragraph."
)


def generate_personalization(business_name: str, issues: str) -> str:
    """
    Return a 1–2 sentence personalised cold-email opener for *business_name*
    based on *issues*. Returns "" on failure or missing API key.
    """
    client = _get_client()
    if client is None:
        return ""

    if not business_name:
        return ""

    user_msg = f"Business: {business_name}\nDetected website issues: {issues or 'None detected'}"

    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=config.OPENAI_MAX_TOKENS,
            temperature=config.OPENAI_TEMPERATURE,
        )
        result = response.choices[0].message.content.strip()
        logger.info(f"  Personalization generated for '{business_name}'")
        return result

    except Exception as exc:
        logger.warning(f"  OpenAI error for '{business_name}': {exc}")
        return ""
