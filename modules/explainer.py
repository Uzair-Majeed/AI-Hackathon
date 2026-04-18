"""
Explanation generator — builds human-readable evidence for each ranked opportunity.

Uses Gemini ONLY for the final 'why' summary paragraph (1 call per opportunity).
Everything else is pure Python: requirements and checklist are template-based.
"""

from typing import List
from models.schemas import Opportunity, StudentProfile
from utils.helpers import days_until, urgency_label


def generate_explanation(opp: Opportunity, profile: StudentProfile) -> Opportunity:
    """
    Populate explanation fields on an Opportunity object.
    Mutates and returns the same Opportunity object.
    """
    opp.why = _build_why_with_ai(opp, profile)
    opp.requirements_summary = _build_requirements(opp)
    opp.checklist = _build_checklist(opp)
    return opp


def _build_why_with_ai(opp: Opportunity, profile: StudentProfile) -> str:
    """Try Gemini for a personalized 'why' paragraph; fall back to template."""
    try:
        from utils.gemini_client import generate_text
        prompt = f"""You are an academic advisor. Write 2-3 sentences explaining why this opportunity 
is a good fit for this student. Be specific, concise, and evidence-backed.

Opportunity: {opp.title} ({opp.opp_type}) by {opp.organization}
Stipend/Value: {opp.stipend_or_amount or 'Not specified'}
Deadline: {opp.deadline.strftime('%B %d, %Y') if opp.deadline else 'Not specified'}

Student: {profile.degree} {profile.program}, Semester {profile.semester}, CGPA {profile.cgpa}
Skills: {', '.join(profile.skills[:4])}
Interests: {', '.join(profile.interests[:3])}
Financial Need: {'Yes' if profile.financial_need else 'No'}

Give ONLY the 2-3 sentence explanation. No bullet points, no headers."""
        result = generate_text(prompt)
        if result and len(result.strip()) > 20:
            return result.strip()
    except Exception:
        pass  # Silently fall back to template

    return _build_why_template(opp, profile)


# ──────────────────────────────────────────
# WHY section — evidence-backed reasoning
# ──────────────────────────────────────────

def _build_why_template(opp: Opportunity, profile: StudentProfile) -> str:
    reasons = []

    # ── Urgency ──
    days = days_until(opp.deadline)
    if days is not None:
        if days <= 7:
            reasons.append(f"⏰ **Deadline is critically close** — only {days} day{'s' if days != 1 else ''} remaining!")
        elif days <= 30:
            reasons.append(f"⏰ **Deadline approaching** — {days} days left to apply.")
        elif days < 0:
            reasons.append("⚠️ Deadline has already passed — may still be worth checking.")
    else:
        reasons.append("📅 No specific deadline mentioned — apply at your convenience.")

    # ── Profile match signals ──
    if profile.skills:
        student_skills = {s.lower().strip() for s in profile.skills}
        opp_text = opp.raw_email.lower()
        matched = [s for s in profile.skills if s.lower().strip() in opp_text]
        if matched:
            reasons.append(f"🎯 **Matches your skills**: {', '.join(matched[:5])}")

    if profile.program:
        if profile.program.lower() in " ".join(opp.eligibility).lower():
            reasons.append(f"🎓 Your program ({profile.program}) is listed as eligible.")

    # ── Preference match ──
    if profile.preferred_types:
        prefs = {t.lower().strip() for t in profile.preferred_types}
        if opp.opp_type.lower() in prefs:
            reasons.append(f"✅ This is a **{opp.opp_type}** — one of your preferred opportunity types.")

    # ── Financial need ──
    if profile.financial_need and opp.opp_type in ("scholarship", "grant", "fellowship"):
        reasons.append("💰 Offers financial support — relevant to your indicated financial need.")

    # ── Stipend/value ──
    if opp.stipend_or_amount:
        reasons.append(f"💵 Value: **{opp.stipend_or_amount}**")

    # ── Location ──
    if opp.location and profile.location_preference:
        if profile.location_preference.lower() in opp.location.lower() or opp.location.lower() == "remote":
            reasons.append(f"📍 Location matches your preference: {opp.location}")

    if not reasons:
        reasons.append("This opportunity has been automatically ranked based on available information.")

    return "\n\n".join(reasons)


# ──────────────────────────────────────────
# REQUIREMENTS section
# ──────────────────────────────────────────

def _build_requirements(opp: Opportunity) -> str:
    parts = []

    if opp.eligibility:
        parts.append("**Eligibility Criteria:**")
        for item in opp.eligibility:
            parts.append(f"  • {item}")

    if opp.required_documents:
        parts.append("\n**Required Documents:**")
        for doc in opp.required_documents:
            parts.append(f"  • {doc}")

    if not parts:
        parts.append("No specific requirements listed in the email.")

    return "\n".join(parts)


# ──────────────────────────────────────────
# CHECKLIST — actionable steps
# ──────────────────────────────────────────

def _build_checklist(opp: Opportunity) -> List[str]:
    steps = []

    # Step 1: Read & understand
    steps.append("Read the full opportunity details carefully")

    # Step 2: Check eligibility
    if opp.eligibility:
        steps.append("Verify you meet all eligibility criteria")

    # Step 3: Prepare documents
    if opp.required_documents:
        doc_list = ", ".join(opp.required_documents[:4])
        suffix = f" (+ {len(opp.required_documents) - 4} more)" if len(opp.required_documents) > 4 else ""
        steps.append(f"Gather required documents: {doc_list}{suffix}")

    # Common application prep
    steps.append("Update your CV/Resume")

    # Type-specific steps
    if opp.opp_type in ("scholarship", "fellowship", "admission"):
        steps.append("Draft a compelling Statement of Purpose / motivation letter")
    if opp.opp_type == "research":
        steps.append("Prepare a research statement or outline of interests")
    if opp.opp_type == "competition":
        steps.append("Form your team and register")
    if opp.opp_type == "grant":
        steps.append("Prepare a research/project proposal following the template")

    # Apply
    if opp.link:
        steps.append(f"Apply online at: {opp.link}")
    elif opp.contact:
        steps.append(f"Contact for application: {opp.contact}")
    else:
        steps.append("Find the application link or contact the organization to apply")

    # Deadline reminder
    days = days_until(opp.deadline)
    if days is not None and days > 0:
        steps.append(f"Set a calendar reminder — deadline: {opp.deadline_raw or opp.deadline.strftime('%B %d, %Y')}")

    return steps
