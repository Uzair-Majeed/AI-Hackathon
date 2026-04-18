"""
Data models / schemas for the Opportunity Inbox Copilot.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class StudentProfile:
    degree: str                          # e.g. "BS"
    program: str                         # e.g. "Computer Science"
    semester: int                        # 1-8
    cgpa: float                          # 0.0 - 4.0
    skills: List[str]                    # ["Python", "Machine Learning", ...]
    interests: List[str]                 # ["AI", "Web Dev", ...]
    preferred_types: List[str]           # ["scholarship", "internship", ...]
    financial_need: bool                 # True/False
    location_preference: str             # "Pakistan", "Remote", "Any", etc.
    past_experience: str                 # Free text summary


@dataclass
class Opportunity:
    email_index: int                     # Index in the original email list
    raw_email: str                       # Original email text

    # Extracted fields
    title: str = "Untitled Opportunity"
    opp_type: str = "other"             # internship|scholarship|competition|fellowship|admission|research|grant|other
    deadline: Optional[datetime] = None
    deadline_raw: str = ""
    eligibility: List[str] = field(default_factory=list)
    required_documents: List[str] = field(default_factory=list)
    location: str = ""
    link: str = ""
    contact: str = ""
    organization: str = ""
    stipend_or_amount: str = ""

    # Scoring dimensions (0–10 each)
    profile_match_score: float = 0.0
    urgency_score: float = 0.0
    preference_score: float = 0.0
    completeness_score: float = 0.0
    value_score: float = 0.0
    final_score: float = 0.0
    rank: int = 0

    # Explanation outputs
    why: str = ""
    requirements_summary: str = ""
    checklist: List[str] = field(default_factory=list)

    # Classification metadata
    classification_reason: str = ""
