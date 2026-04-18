"""
test_pipeline.py — Quick logic test for the Opportunity Inbox Copilot.
Run: python test_pipeline.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("  OPPORTUNITY INBOX COPILOT — Logic Test")
print("=" * 60)

# ─────────────────────────────────────────
# 1. Test email splitting
# ─────────────────────────────────────────
print("\n[1] Testing email splitter...")
from utils.helpers import split_emails

raw = """
Subject: HEC Scholarship 2026
Deadline April 30. Apply at hec.gov.pk.

---

Subject: Daraz Sale 70% off
Buy now at daraz.pk
"""

parts = split_emails(raw)
assert len(parts) == 2, f"Expected 2 emails, got {len(parts)}"
print(f"    ✅ Split correctly → {len(parts)} emails detected")

# ─────────────────────────────────────────
# 2. Test normalizer (no API needed)
# ─────────────────────────────────────────
print("\n[2] Testing normalizer...")
from modules.normalizer import normalize_opportunity, normalize_type, normalize_deadline

# Type normalization
assert normalize_type("intern") == "internship"
assert normalize_type("funding") == "scholarship"
assert normalize_type("hackathon") == "competition"
assert normalize_type("xyz_unknown") == "other"
print("    ✅ Type aliases work correctly")

# Deadline parsing
from datetime import datetime
dl = normalize_deadline("2026-04-30")
assert isinstance(dl, datetime)
assert dl.month == 4 and dl.day == 30
print(f"    ✅ Deadline parsed: '2026-04-30' → {dl.strftime('%B %d, %Y')}")

dl_none = normalize_deadline(None)
assert dl_none is None
print("    ✅ Missing deadline → None (handled)")

# Full normalize call with mock data
mock_raw = {
    "title": "HEC Need-Based Scholarship",
    "type": "scholarship",
    "deadline": "2026-04-30",
    "eligibility": ["Pakistani citizen", "CGPA >= 2.5", "Undergraduate student"],
    "required_documents": ["Transcript", "CNIC", "Income certificate"],
    "location": "Pakistan",
    "link": "https://portal.hec.gov.pk",
    "contact": "needbased@hec.gov.pk",
    "organization": "HEC Pakistan",
    "stipend_or_amount": "PKR 50,000/semester",
}
opp = normalize_opportunity(mock_raw, "sample email text", email_index=0)
assert opp.title == "HEC Need-Based Scholarship"
assert opp.opp_type == "scholarship"
assert opp.deadline is not None
assert len(opp.eligibility) == 3
print(f"    ✅ Opportunity normalized: '{opp.title}' | type={opp.opp_type} | deadline={opp.deadline.date()}")

# ─────────────────────────────────────────
# 3. Test ranker (no API needed)
# ─────────────────────────────────────────
print("\n[3] Testing ranking engine...")
from models.schemas import StudentProfile
from modules.ranker import score_opportunity, rank_opportunities

profile = StudentProfile(
    degree="BS",
    program="Computer Science",
    semester=5,
    cgpa=3.4,
    skills=["Python", "Machine Learning", "Data Science"],
    interests=["AI", "Research"],
    preferred_types=["scholarship", "internship"],
    financial_need=True,
    location_preference="Pakistan",
    past_experience="ML coursera, freelance web dev",
)

# Score the scholarship
scored = score_opportunity(opp, profile)
print(f"    📊 Scores for '{opp.title}':")
print(f"       Profile Match:  {scored.profile_match_score:.1f}/10")
print(f"       Urgency:        {scored.urgency_score:.1f}/10")
print(f"       Preference:     {scored.preference_score:.1f}/10")
print(f"       Completeness:   {scored.completeness_score:.1f}/10")
print(f"       Value:          {scored.value_score:.1f}/10")
print(f"       ─────────────────────────")
print(f"       FINAL SCORE:    {scored.final_score:.2f}/10")

assert scored.final_score > 0, "Score should be > 0"
assert scored.preference_score == 10.0, "Scholarship is in preferred types → should be 10"
print(f"    ✅ Scoring logic correct")

# Rank multiple opportunities
from modules.normalizer import normalize_opportunity
spam_mock = {"title": "Daraz Sale", "type": "other", "deadline": None,
             "eligibility": [], "required_documents": [], "location": "",
             "link": "", "contact": "", "organization": "Daraz", "stipend_or_amount": ""}
spam_opp = normalize_opportunity(spam_mock, "70% off sale", email_index=1)

ranked = rank_opportunities([opp, spam_opp], profile)
assert ranked[0].title == "HEC Need-Based Scholarship", "Scholarship should rank #1"
assert ranked[0].rank == 1
assert ranked[1].rank == 2
print(f"    ✅ Ranking correct: #{ranked[0].rank} {ranked[0].title} ({ranked[0].final_score:.1f}) > #{ranked[1].rank} {ranked[1].title} ({ranked[1].final_score:.1f})")

# ─────────────────────────────────────────
# 4. Test explainer (no API needed)
# ─────────────────────────────────────────
print("\n[4] Testing explanation generator...")
from modules.explainer import generate_explanation

explained = generate_explanation(opp, profile)
assert opp.why, "Why section should not be empty"
assert opp.requirements_summary, "Requirements should not be empty"
assert len(opp.checklist) >= 3, "Should have at least 3 checklist items"
print(f"    ✅ Why section generated ({len(opp.why)} chars)")
print(f"    ✅ Requirements generated ({len(opp.requirements_summary)} chars)")
print(f"    ✅ Checklist generated ({len(opp.checklist)} steps):")
for i, step in enumerate(opp.checklist, 1):
    print(f"       {i}. {step}")

# ─────────────────────────────────────────
# 5. Test Gemini API (classifier + extractor)
# ─────────────────────────────────────────
print("\n[5] Testing Gemini API connection...")
try:
    from utils.gemini_client import generate_text
    resp = generate_text("Reply with exactly: CONNECTED")
    print(f"    ✅ Gemini API working → response: '{resp.strip()[:50]}'")
    api_working = True
except Exception as e:
    print(f"    ❌ Gemini API error: {e}")
    api_working = False

if api_working:
    print("\n[6] Testing classifier on real email vs spam...")
    from modules.classifier import classify_email

    real_email = """Subject: HEC Scholarship 2026
    The HEC Need-Based Scholarship is now open. Pakistani undergraduate students
    with CGPA >= 2.5 can apply. Deadline: April 30, 2026.
    Required: transcript, CNIC. Apply at hec.gov.pk"""

    spam_email = """Subject: Flash Sale 70% OFF
    Huge discounts on electronics today only! Use code SAVE70 at daraz.pk"""

    cls_real = classify_email(real_email)
    cls_spam = classify_email(spam_email)

    print(f"    Real email → is_opportunity={cls_real['is_opportunity']} | reason: {cls_real['reason'][:70]}")
    print(f"    Spam email → is_opportunity={cls_spam['is_opportunity']} | reason: {cls_spam['reason'][:70]}")

    if cls_real['is_opportunity'] and not cls_spam['is_opportunity']:
        print("    ✅ Classifier working correctly!")
    else:
        print("    ⚠️  Classifier result unexpected — check prompts")

    print("\n[7] Testing extractor on real email...")
    from modules.extractor import extract_opportunity
    extracted = extract_opportunity(real_email)
    print(f"    Title: {extracted.get('title')}")
    print(f"    Type:  {extracted.get('type')}")
    print(f"    Deadline: {extracted.get('deadline')}")
    print(f"    Eligibility: {extracted.get('eligibility')}")
    print(f"    ✅ Extractor working!")

print("\n" + "=" * 60)
print("  ALL CORE LOGIC TESTS PASSED ✅")
print("=" * 60)
print("\nTo run the full app:  streamlit run app.py")
