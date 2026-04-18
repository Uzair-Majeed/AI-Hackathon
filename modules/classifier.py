"""
Email classifier — pure keyword/heuristic-based classification.
No API calls. Fast, reliable, works offline.
"""

import re

# Opportunity keywords (any of these → likely real)
OPPORTUNITY_KEYWORDS = [
    "scholarship", "internship", "fellowship", "competition", "grant",
    "admission", "research", "apply", "application", "deadline",
    "eligibility", "eligible", "stipend", "funding", "award",
    "programme", "program", "hiring", "opening", "opportunity",
    "call for", "registration", "hackathon", "conference", "bootcamp",
    "cohort", "fellowship", "collaborate", "paid", "unpaid role",
    "job opening", "position available", "cgpa", "gpa",
    "semester", "undergraduate", "graduate", "phd", "bs ", "ms ",
]

# Hard spam keywords — if these dominate, it's not an opportunity
SPAM_KEYWORDS = [
    "sale", "discount", "deal", "offer", "% off", "flash sale",
    "limited time", "buy now", "shop now", "click here", "unsubscribe",
    "promo", "coupon", "cashback", "free delivery", "order now",
    "newsletter", "subscription", "marketing", "advertisement",
    "daraz", "alibaba", "amazon", "flipkart",
]


def classify_email(email_text: str) -> dict:
    """
    Classify an email as an opportunity or not using keyword matching.

    Returns:
        { "is_opportunity": bool, "reason": str }
    """
    text_lower = email_text.lower()

    # Count hits
    opp_hits = [kw for kw in OPPORTUNITY_KEYWORDS if kw in text_lower]
    spam_hits = [kw for kw in SPAM_KEYWORDS if kw in text_lower]

    # Short-circuit: strong spam signal
    if len(spam_hits) >= 3 and len(opp_hits) <= 1:
        return {
            "is_opportunity": False,
            "reason": f"Spam/promotional content detected ({', '.join(spam_hits[:3])})",
        }

    # Any meaningful opportunity signal
    if len(opp_hits) >= 2:
        return {
            "is_opportunity": True,
            "reason": f"Opportunity keywords detected: {', '.join(opp_hits[:5])}",
        }

    # Single strong signal (like "scholarship" alone is enough)
    STRONG_KEYWORDS = {
        "scholarship", "internship", "fellowship", "hackathon",
        "grant", "admission", "call for applications", "funded",
    }
    strong_hits = [kw for kw in opp_hits if kw in STRONG_KEYWORDS]
    if strong_hits:
        return {
            "is_opportunity": True,
            "reason": f"Strong opportunity keyword: {strong_hits[0]}",
        }

    return {
        "is_opportunity": False,
        "reason": "No clear opportunity keywords found in this email",
    }
