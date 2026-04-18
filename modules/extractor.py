"""
Structured extractor — pure regex/heuristic field extraction from email text.
No API calls. Fast, reliable, works offline.
"""

import re
from datetime import datetime

# ─────────────────────────────────────────────────────
# Opportunity type keywords
# ─────────────────────────────────────────────────────
TYPE_KEYWORDS = {
    "scholarship": ["scholarship", "need-based", "merit-based", "tuition waiver", "financial aid", "stipend fund"],
    "internship":  ["intern", "internship", "summer placement", "industrial training"],
    "fellowship":  ["fellowship", "fellow", "research fellow", "postdoc"],
    "competition": ["competition", "hackathon", "contest", "challenge", "olympiad", "tournament", "softec"],
    "admission":   ["admission", "apply for", "enroll", "enrollment", "phd position", "ms admission"],
    "research":    ["research", "research assistant", "ra position", "research program", "publication"],
    "grant":       ["grant", "funding", "research grant", "seed grant"],
}

# ─────────────────────────────────────────────────────
# Month patterns for date parsing
# ─────────────────────────────────────────────────────
MONTH_MAP = {
    "january": 1, "jan": 1, "february": 2, "feb": 2,
    "march": 3, "mar": 3, "april": 4, "apr": 4,
    "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

DATE_PATTERNS = [
    # April 30, 2026 or April 30 2026
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{1,2})[,\s]+(\d{4})\b",
    # 30 April 2026
    r"\b(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)[,\s]+(\d{4})\b",
    # 2026-04-30 or 30/04/2026 or 30-04-2026
    r"\b(\d{4})[/-](\d{2})[/-](\d{2})\b",
    r"\b(\d{2})[/-](\d{2})[/-](\d{4})\b",
]

DEADLINE_TRIGGERS = [
    "deadline", "last date", "apply by", "applications close",
    "closing date", "submit by", "due date", "last day",
    "before", "ends on", "closes on", "valid till",
]


def extract_opportunity(email_text: str) -> dict:
    """
    Extract structured fields from an opportunity email using pure regex/heuristics.
    Returns a dict matching the extractor output schema.
    """
    lines = email_text.strip().split("\n")
    text_lower = email_text.lower()

    return {
        "title":               _extract_title(email_text, lines),
        "type":                _extract_type(text_lower),
        "deadline":            _extract_deadline(email_text, text_lower),
        "eligibility":         _extract_eligibility(email_text, text_lower),
        "required_documents":  _extract_documents(text_lower),
        "location":            _extract_location(text_lower),
        "link":                _extract_link(email_text),
        "contact":             _extract_contact(email_text, text_lower),
        "organization":        _extract_org(email_text, lines),
        "stipend_or_amount":   _extract_stipend(email_text, text_lower),
    }


# ─────────────────────────────────────────────────────
# Field extractors
# ─────────────────────────────────────────────────────

def _extract_title(text: str, lines: list) -> str:
    """Extract from Subject: line."""
    for line in lines:
        if line.lower().startswith("subject:"):
            return line[8:].strip()
    # Fallback: first non-empty line
    for line in lines:
        if line.strip():
            return line.strip()[:100]
    return "Untitled Opportunity"


def _extract_type(text_lower: str) -> str:
    """Match the best opportunity type by keyword count."""
    scores = {}
    for opp_type, keywords in TYPE_KEYWORDS.items():
        scores[opp_type] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


def _extract_deadline(text: str, text_lower: str) -> str | None:
    """Find dates near deadline-trigger words first, then any date."""
    # 1. Search in sentences near deadline keywords
    sentences = re.split(r"[.\n]", text_lower)
    deadline_sentences = [s for s in sentences if any(t in s for t in DEADLINE_TRIGGERS)]
    search_text = " ".join(deadline_sentences) if deadline_sentences else text_lower

    date_str = _find_date_in_text(search_text)
    if date_str:
        return date_str

    # 2. Fall back to any date in full email
    return _find_date_in_text(text_lower)


def _find_date_in_text(text: str) -> str | None:
    """Try all date regex patterns and return ISO date string or None."""
    # Pattern: Month day, year (e.g. April 30, 2026)
    m = re.search(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{1,2})[,\s]+(\d{4})\b",
        text, re.IGNORECASE
    )
    if m:
        month = MONTH_MAP.get(m.group(1).lower())
        if month:
            return f"{m.group(3)}-{month:02d}-{int(m.group(2)):02d}"

    # Pattern: day Month year (e.g. 30 April 2026)
    m = re.search(
        r"\b(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|"
        r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s*[,]?\s*(\d{4})\b",
        text, re.IGNORECASE
    )
    if m:
        month = MONTH_MAP.get(m.group(2).lower())
        if month:
            return f"{m.group(3)}-{month:02d}-{int(m.group(1)):02d}"

    # Pattern: YYYY-MM-DD
    m = re.search(r"\b(202[4-9])[/-](\d{2})[/-](\d{2})\b", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # Pattern: DD/MM/YYYY
    m = re.search(r"\b(\d{2})[/-](\d{2})[/-](202[4-9])\b", text)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    return None


def _extract_eligibility(text: str, text_lower: str) -> list:
    """Find lines/phrases that describe eligibility criteria."""
    eligibility = []
    lines = text.split("\n")

    # CGPA / GPA requirement
    cgpa_match = re.search(r"(cgpa|gpa)[:\s]*[≥>=of]*\s*(\d+\.?\d*)", text_lower)
    if cgpa_match:
        eligibility.append(f"Minimum CGPA: {cgpa_match.group(2)}")

    # Degree mentions
    degree_patterns = ["bs ", "ms ", "phd", "bachelor", "master", "undergraduate", "graduate"]
    for dp in degree_patterns:
        if dp in text_lower:
            # Find the sentence context
            for line in lines:
                if dp in line.lower() and len(line.strip()) < 200:
                    clean = line.strip().lstrip("-•*").strip()
                    if clean and clean not in eligibility:
                        eligibility.append(clean)
                    break

    # Semester mentions
    sem_match = re.search(r"semester[s]?\s*(\d[\d\s\-,andor]+)", text_lower)
    if sem_match:
        eligibility.append(f"Semester: {sem_match.group(0).strip()[:60]}")

    # Lines with eligibility keywords
    elig_triggers = ["eligible", "eligibility", "must be", "requirement", "citizen", "national"]
    for line in lines:
        line_low = line.lower()
        if any(t in line_low for t in elig_triggers) and 5 < len(line.strip()) < 200:
            clean = line.strip().lstrip("-•*").strip()
            if clean and clean not in eligibility:
                eligibility.append(clean)

    return eligibility[:6]  # cap at 6


def _extract_documents(text_lower: str) -> list:
    """Find required documents mentioned in the email."""
    doc_keywords = {
        "transcript": "Transcript",
        "cnic": "CNIC / National ID",
        "cv": "CV / Resume",
        "resume": "CV / Resume",
        "passport": "Passport",
        "photograph": "Photograph",
        "photo": "Photograph",
        "recommendation letter": "Recommendation Letter",
        "reference letter": "Reference Letter",
        "statement of purpose": "Statement of Purpose",
        "sop": "Statement of Purpose",
        "cover letter": "Cover Letter",
        "income certificate": "Income Certificate",
        "bank statement": "Bank Statement",
        "degree certificate": "Degree Certificate",
        "marksheet": "Marksheet",
        "domicile": "Domicile Certificate",
    }
    found = []
    seen = set()
    for kw, label in doc_keywords.items():
        if kw in text_lower and label not in seen:
            found.append(label)
            seen.add(label)
    return found


def _extract_location(text_lower: str) -> str:
    """Extract location from the email."""
    location_keywords = [
        ("remote", "Remote"),
        ("online", "Online / Remote"),
        ("pakistan", "Pakistan"),
        ("lahore", "Lahore, Pakistan"),
        ("karachi", "Karachi, Pakistan"),
        ("islamabad", "Islamabad, Pakistan"),
        ("usa", "United States"),
        ("united states", "United States"),
        ("uk", "United Kingdom"),
        ("united kingdom", "United Kingdom"),
        ("europe", "Europe"),
        ("canada", "Canada"),
        ("australia", "Australia"),
        ("dubai", "Dubai, UAE"),
        ("uae", "UAE"),
    ]
    for kw, label in location_keywords:
        if kw in text_lower:
            return label
    return ""


def _extract_link(text: str) -> str:
    """Find the first meaningful URL in the email."""
    urls = re.findall(r"https?://[^\s\)\]\"'<>]+", text)
    # Prefer apply/register/form URLs
    for url in urls:
        if any(x in url.lower() for x in ["apply", "register", "form", "apply", "portal", "submit"]):
            return url.rstrip(".,;)")
    # Return first URL found
    return urls[0].rstrip(".,;)") if urls else ""


def _extract_contact(text: str, text_lower: str) -> str:
    """Extract email address for contact."""
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    # Skip the From: address (usually first), return contact email
    if len(emails) > 1:
        return emails[1]
    return emails[0] if emails else ""


def _extract_org(text: str, lines: list) -> str:
    """Extract organization from From: line."""
    for line in lines:
        if line.lower().startswith("from:"):
            # From: Name <email> or From: email
            name_match = re.match(r"from:\s*(.+?)(?:\s*<|$)", line, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
                if "@" not in name and len(name) > 2:
                    return name
        if line.lower().startswith("organization:") or line.lower().startswith("org:"):
            return line.split(":", 1)[1].strip()

    # Try domain from first email address
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+)", text)
    if emails:
        domain = emails[0]
        # Strip common TLDs for cleaner display
        parts = domain.replace(".org", "").replace(".com", "").replace(".pk", "").split(".")
        return parts[-1].upper() if parts else domain
    return ""


def _extract_stipend(text: str, text_lower: str) -> str:
    """Extract stipend or award value."""
    # PKR
    pkr = re.search(r"pkr\s*[\d,]+(?:\s*(?:per|/)\s*\w+)?", text_lower)
    if pkr:
        return pkr.group(0).upper()
    # USD $
    usd = re.search(r"\$\s*[\d,]+(?:\s*(?:per|/)\s*\w+)?", text)
    if usd:
        return usd.group(0)
    # Generic amount
    amount = re.search(r"rs\.?\s*[\d,]+", text_lower)
    if amount:
        return amount.group(0).upper()
    # "fully funded"
    if "fully funded" in text_lower:
        return "Fully Funded"
    if "fully-funded" in text_lower:
        return "Fully Funded"
    return ""
