"""
Utility helpers for the pipeline.
"""

import os
import re
import json
from datetime import datetime
from typing import List, Optional

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    path = os.path.join(PROMPTS_DIR, f"{name}.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_emails(raw_text: str) -> List[str]:
    """
    Split a pasted multi-email blob into individual emails.
    Separator: a line containing only '---'
    """
    # Normalize line endings
    raw_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # Split on lines that are exactly '---'
    parts = re.split(r'\n---\n', raw_text)
    emails = [e.strip() for e in parts if e.strip()]
    return emails


def parse_json_response(text: str) -> dict:
    """
    Robustly parse JSON from a Gemini response.
    Handles markdown code blocks, extra whitespace, etc.
    """
    # Remove markdown code fences
    text = re.sub(r'```(?:json)?\s*', '', text).strip()
    text = text.replace('```', '').strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find a JSON object in the text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {}


def days_until(deadline: Optional[datetime]) -> Optional[int]:
    """Return number of days from now until the deadline."""
    if deadline is None:
        return None
    now = datetime.now()
    delta = deadline - now
    return delta.days


def urgency_label(days: Optional[int]) -> str:
    """Return a human-readable urgency label."""
    if days is None:
        return "No deadline"
    if days < 0:
        return "Expired"
    if days <= 7:
        return f"🔴 CRITICAL — {days} day{'s' if days != 1 else ''} left"
    if days <= 30:
        return f"🔶 URGENT — {days} days left"
    if days <= 90:
        return f"🟡 SOON — {days} days left"
    return f"🟢 {days} days left"


def urgency_color_class(days: Optional[int]) -> str:
    """Return a CSS class name for urgency coloring."""
    if days is None:
        return "urgency-none"
    if days < 0:
        return "urgency-expired"
    if days <= 7:
        return "urgency-critical"
    if days <= 30:
        return "urgency-urgent"
    if days <= 90:
        return "urgency-soon"
    return "urgency-ok"
