"""
Pipeline controller — orchestrates the full email-to-ranking pipeline.
"""

from typing import List, Tuple
from models.schemas import Opportunity, StudentProfile
from modules.classifier import classify_email
from modules.extractor import extract_opportunity
from modules.normalizer import normalize_opportunity
from modules.ranker import rank_opportunities
from modules.explainer import generate_explanation
from database.db import init_db, save_run


def run_pipeline(
    emails: List[str],
    profile: StudentProfile,
    progress_callback=None,
) -> Tuple[List[Opportunity], List[dict]]:
    """
    Run the full pipeline:
      1. Classify each email (opportunity or not)
      2. Extract structured data from opportunities
      3. Normalize extracted data
      4. Score and rank all opportunities
      5. Generate explanations
      6. Persist to SQLite

    Args:
        emails: list of individual email texts
        profile: the student's profile
        progress_callback: optional callable(step_text, progress_fraction)

    Returns:
        (ranked_opportunities, discarded_emails)
        discarded_emails is a list of {"email_index": int, "reason": str}
    """
    init_db()

    total_steps = len(emails) * 2 + 3  # classify + extract per email, then rank + explain + save
    current_step = 0

    def _progress(msg: str):
        nonlocal current_step
        current_step += 1
        if progress_callback:
            progress_callback(msg, current_step / total_steps)

    opportunities: List[Opportunity] = []
    discarded: List[dict] = []

    # ── Step 1 + 2: Classify → Extract for each email ──
    for i, email_text in enumerate(emails):
        # Classify
        _progress(f"Classifying email {i + 1}/{len(emails)}...")
        cls_result = classify_email(email_text)

        if not cls_result["is_opportunity"]:
            discarded.append({
                "email_index": i,
                "email_snippet": email_text[:120].replace("\n", " ") + "...",
                "reason": cls_result["reason"],
            })
            _progress(f"Email {i + 1} discarded — not an opportunity")
            continue

        # Extract
        _progress(f"Extracting details from email {i + 1}...")
        raw_data = extract_opportunity(email_text)

        # Normalize
        opp = normalize_opportunity(raw_data, email_text, email_index=i)
        opp.classification_reason = cls_result["reason"]
        opportunities.append(opp)

    # ── Step 3: Rank ──
    _progress("Scoring and ranking opportunities...")
    if opportunities:
        opportunities = rank_opportunities(opportunities, profile)

    # ── Filter by Match Score Threshold (50%+) ──
    final_opps = []
    for opp in opportunities:
        if opp.final_score >= 5.0:
            final_opps.append(opp)
        else:
            discarded.append({
                "email_index": opp.email_index,
                "email_snippet": opp.raw_email[:120].replace("\n", " ") + "...",
                "reason": f"Match score too low ({int(opp.final_score * 10)}%). Requires at least a 50% match.",
            })
            _progress(f"Email {opp.email_index + 1} discarded — below 50% match requirement.")
    opportunities = final_opps

    # ── Step 4: Explain ──
    _progress("Generating explanations and checklists...")
    for opp in opportunities:
        generate_explanation(opp, profile)

    # ── Step 5: Persist ──
    _progress("Saving results...")
    if opportunities:
        save_run(profile, opportunities, total_emails=len(emails))

    return opportunities, discarded
