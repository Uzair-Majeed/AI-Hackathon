"""
Ranking engine — deterministic scoring of opportunities against a student profile.

Scoring Dimensions (0–10 each, weighted):
  Profile Match   → 30%
  Urgency         → 25%
  Preference Match → 20%
  Completeness    → 10%
  Opportunity Value → 15%
"""

from datetime import datetime
from typing import List
from models.schemas import Opportunity, StudentProfile
from utils.helpers import days_until


# ──────────────────────────────────────────
# Static value map — higher = more impactful
# ──────────────────────────────────────────
OPPORTUNITY_VALUE = {
    "scholarship": 10,
    "grant": 9,
    "fellowship": 9,
    "research": 8,
    "internship": 7,
    "admission": 6,
    "competition": 6,
    "other": 3,
}

# Weights (must sum to 1.0)
WEIGHTS = {
    "profile_match": 0.30,
    "urgency": 0.25,
    "preference": 0.20,
    "completeness": 0.10,
    "value": 0.15,
}


# ──────────────────────────────────────────
# Individual scoring functions
# ──────────────────────────────────────────

def _score_profile_match(opp: Opportunity, profile: StudentProfile) -> float:
    """
    Score how well the opportunity matches the student's profile.
    Considers: degree/program in eligibility, skill overlap, experience relevance.
    """
    score = 0.0

    # ── Eligibility text matching (up to 4 points) ──
    eligibility_text = " ".join(opp.eligibility).lower()
    if eligibility_text:
        # Degree/program match
        degree_terms = [profile.degree.lower(), profile.program.lower()]
        for term in degree_terms:
            if term and term in eligibility_text:
                score += 2.0
                break

        # CGPA check: if the eligibility mentions a CGPA, check if student meets it
        import re
        cgpa_match = re.search(r'(?:cgpa|gpa)\s*(?:of\s*)?(\d+\.?\d*)', eligibility_text)
        if cgpa_match:
            required_cgpa = float(cgpa_match.group(1))
            if profile.cgpa >= required_cgpa:
                score += 2.0
            else:
                score -= 1.0  # Penalty for not meeting CGPA
        else:
            score += 1.0  # No CGPA requirement = neutral positive
    else:
        score += 2.0  # No eligibility info = assume eligible

    # ── Skill overlap (up to 4 points) ──
    if profile.skills:
        student_skills = {s.lower().strip() for s in profile.skills}
        # Check skill overlap with eligibility + email text
        opp_text = (eligibility_text + " " + opp.raw_email.lower())
        matches = sum(1 for skill in student_skills if skill in opp_text)
        skill_ratio = min(matches / max(len(student_skills), 1), 1.0)
        score += skill_ratio * 4.0

    # ── Experience relevance (up to 2 points) ──
    if profile.past_experience:
        exp_terms = profile.past_experience.lower().split()
        opp_text = opp.raw_email.lower()
        exp_matches = sum(1 for t in exp_terms if len(t) > 3 and t in opp_text)
        score += min(exp_matches * 0.5, 2.0)

    return max(0.0, min(10.0, score))


def _score_urgency(opp: Opportunity) -> float:
    """
    Score urgency based on deadline proximity.
    Closer deadline = higher urgency = higher score.
    """
    days = days_until(opp.deadline)
    if days is None:
        return 2.0       # No deadline = low urgency but not zero
    if days < 0:
        return 0.5       # Expired — still show it but low priority
    if days <= 3:
        return 10.0
    if days <= 7:
        return 9.0
    if days <= 14:
        return 8.0
    if days <= 30:
        return 7.0
    if days <= 60:
        return 5.0
    if days <= 90:
        return 4.0
    return 2.0


def _score_preference(opp: Opportunity, profile: StudentProfile) -> float:
    """
    Score based on whether the opportunity type matches student's preferences.
    """
    if not profile.preferred_types:
        return 5.0  # No preferences = neutral

    student_prefs = {t.lower().strip() for t in profile.preferred_types}

    if opp.opp_type.lower() in student_prefs:
        return 10.0

    # Partial credit for related types
    related = {
        "internship": {"research", "fellowship"},
        "scholarship": {"grant", "fellowship"},
        "research": {"internship", "fellowship", "grant"},
        "fellowship": {"internship", "scholarship", "research"},
        "grant": {"scholarship", "research"},
        "competition": {"hackathon"},
    }
    related_types = related.get(opp.opp_type.lower(), set())
    if student_prefs & related_types:
        return 6.0

    return 2.0


def _score_completeness(opp: Opportunity) -> float:
    """
    Score based on how many fields were successfully extracted.
    More info = more reliable opportunity.
    """
    fields = [
        opp.title and opp.title != "Untitled Opportunity",
        opp.opp_type and opp.opp_type != "other",
        opp.deadline is not None,
        len(opp.eligibility) > 0,
        len(opp.required_documents) > 0,
        bool(opp.location),
        bool(opp.link),
        bool(opp.contact),
        bool(opp.organization),
        bool(opp.stipend_or_amount),
    ]
    filled = sum(1 for f in fields if f)
    return (filled / len(fields)) * 10.0


def _score_value(opp: Opportunity) -> float:
    """
    Score the intrinsic value / impact of the opportunity type.
    """
    return float(OPPORTUNITY_VALUE.get(opp.opp_type.lower(), 3))


# ──────────────────────────────────────────
# Main scoring & ranking
# ──────────────────────────────────────────

def score_opportunity(opp: Opportunity, profile: StudentProfile) -> Opportunity:
    """
    Compute all scoring dimensions and the weighted final score (0–10).
    Mutates and returns the same Opportunity object.
    """
    opp.profile_match_score = round(_score_profile_match(opp, profile), 2)
    opp.urgency_score = round(_score_urgency(opp), 2)
    opp.preference_score = round(_score_preference(opp, profile), 2)
    opp.completeness_score = round(_score_completeness(opp), 2)
    opp.value_score = round(_score_value(opp), 2)

    opp.final_score = round(
        opp.profile_match_score * WEIGHTS["profile_match"]
        + opp.urgency_score * WEIGHTS["urgency"]
        + opp.preference_score * WEIGHTS["preference"]
        + opp.completeness_score * WEIGHTS["completeness"]
        + opp.value_score * WEIGHTS["value"],
        2
    )

    return opp


def rank_opportunities(
    opportunities: List[Opportunity], profile: StudentProfile
) -> List[Opportunity]:
    """
    Score all opportunities, sort by final score descending, and assign ranks.
    """
    for opp in opportunities:
        score_opportunity(opp, profile)

    # Sort descending by score, with title as tiebreaker
    opportunities.sort(key=lambda o: (-o.final_score, o.title))

    for i, opp in enumerate(opportunities):
        opp.rank = i + 1

    return opportunities
