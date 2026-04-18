"""
Normalizer — cleans and standardizes raw extracted data into an Opportunity object.
"""

from datetime import datetime
from typing import Optional
from models.schemas import Opportunity


# Canonical opportunity type mappings
TYPE_ALIASES = {
    "intern": "internship",
    "internship": "internship",
    "job": "internship",
    "scholarship": "scholarship",
    "funding": "scholarship",
    "stipend": "scholarship",
    "financial aid": "scholarship",
    "grant": "grant",
    "research grant": "grant",
    "funding grant": "grant",
    "fellowship": "fellowship",
    "mentor": "fellowship",
    "mentorship": "fellowship",
    "competition": "competition",
    "contest": "competition",
    "hackathon": "competition",
    "olympiad": "competition",
    "admission": "admission",
    "admissions": "admission",
    "program admission": "admission",
    "research": "research",
    "research internship": "research",
    "research position": "research",
    "other": "other",
}

# Common date formats Gemini might use despite being asked for YYYY-MM-DD
EXTRA_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d %B %Y",
    "%B %d, %Y",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%B %Y",
]


def normalize_type(raw_type: str) -> str:
    """Normalize opportunity type string to a canonical value."""
    if not raw_type:
        return "other"
    key = raw_type.strip().lower()
    # Direct lookup
    if key in TYPE_ALIASES:
        return TYPE_ALIASES[key]
    # Partial match
    for alias, canonical in TYPE_ALIASES.items():
        if alias in key:
            return canonical
    return "other"


def normalize_deadline(raw_deadline) -> Optional[datetime]:
    """Parse deadline string into a datetime object."""
    if not raw_deadline or raw_deadline == "null":
        return None
    if isinstance(raw_deadline, datetime):
        return raw_deadline

    raw = str(raw_deadline).strip()

    for fmt in EXTRA_DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    return None


def normalize_skills_list(items: list) -> list:
    """Deduplicate and lowercase a list of strings."""
    seen = set()
    result = []
    for item in items:
        clean = str(item).strip()
        lower = clean.lower()
        if lower and lower not in seen:
            seen.add(lower)
            result.append(clean)
    return result


def normalize_opportunity(raw: dict, email_text: str, email_index: int) -> Opportunity:
    """
    Convert a raw extraction dict into a normalized Opportunity dataclass.
    """
    opp = Opportunity(
        email_index=email_index,
        raw_email=email_text,
    )

    opp.title = str(raw.get("title") or "Untitled Opportunity").strip()
    opp.opp_type = normalize_type(str(raw.get("type") or "other"))
    opp.deadline_raw = str(raw.get("deadline") or "").strip()
    opp.deadline = normalize_deadline(raw.get("deadline"))
    opp.eligibility = normalize_skills_list(raw.get("eligibility") or [])
    opp.required_documents = normalize_skills_list(raw.get("required_documents") or [])
    opp.location = str(raw.get("location") or "").strip()
    opp.link = str(raw.get("link") or "").strip()
    opp.contact = str(raw.get("contact") or "").strip()
    opp.organization = str(raw.get("organization") or "").strip()
    opp.stipend_or_amount = str(raw.get("stipend_or_amount") or "").strip()

    return opp
