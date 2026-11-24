"""
Ticket classification using keyword heuristics + optional Gemini.
Falls back to keyword matching when Gemini is unavailable.
"""
import re
from typing import Optional

from app.models.models import TicketCategory


# Keyword sets for each category
CATEGORY_KEYWORDS: dict[TicketCategory, list[str]] = {
    TicketCategory.billing: [
        "bill", "billing", "invoice", "charge", "payment", "refund",
        "credit card", "subscription fee", "overcharged", "receipt",
    ],
    TicketCategory.account: [
        "account", "login", "password", "sign in", "access", "profile",
        "username", "email", "register", "authentication", "locked",
    ],
    TicketCategory.technical: [
        "error", "bug", "crash", "not working", "broken", "fail",
        "issue", "problem", "glitch", "exception", "timeout", "slow",
        "performance", "installation", "setup", "configure",
    ],
    TicketCategory.cancellation: [
        "cancel", "cancellation", "terminate", "unsubscribe", "close account",
        "end subscription", "stop service",
    ],
    TicketCategory.feature: [
        "feature", "request", "suggestion", "enhance", "improvement",
        "add", "support for", "would like", "wish", "missing",
    ],
    TicketCategory.security: [
        "security", "hack", "breach", "phishing", "suspicious", "malware",
        "virus", "unauthorized", "data leak", "vulnerability", "2fa", "mfa",
    ],
}


def classify_ticket_keywords(title: str, description: str) -> tuple[TicketCategory, float]:
    """
    Simple keyword-based classifier.
    Returns (category, confidence_score).
    """
    combined = (title + " " + description).lower()

    scores: dict[TicketCategory, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in combined)
        if count:
            scores[category] = count

    if not scores:
        return TicketCategory.uncategorized, 0.0

    best_cat = max(scores, key=lambda c: scores[c])
    total_matches = sum(scores.values())
    confidence = scores[best_cat] / total_matches if total_matches else 0.0
    return best_cat, round(min(confidence, 1.0), 3)


async def classify_ticket_gemini(
    title: str,
    description: str,
    gemini_client,
    model_name: str,
) -> tuple[TicketCategory, float]:
    """
    Classify using Gemini. Returns (category, confidence).
    Falls back to keyword classifier on failure.
    """
    categories = [c.value for c in TicketCategory if c != TicketCategory.uncategorized]
    prompt = (
        f"Classify this support ticket into exactly one of these categories: "
        f"{', '.join(categories)}.\n\n"
        f"Title: {title}\nDescription: {description}\n\n"
        f"Reply with ONLY the category name, nothing else."
    )

    try:
        response = await gemini_client.generate_content_async(prompt)
        raw = response.text.strip().lower()
        for cat in TicketCategory:
            if cat.value == raw:
                return cat, 0.90
        # If response doesn't match, fall back
        return classify_ticket_keywords(title, description)
    except Exception:
        return classify_ticket_keywords(title, description)
