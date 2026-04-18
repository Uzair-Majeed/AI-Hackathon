"""
Summarizer for the Opportunity Inbox Copilot.
Generates an AI-driven insight summary using the GPT-4o API (via GitHub Models).
"""

from utils.github_openai_client import generate_text

def get_ai_summary(opportunity_data: dict) -> str:
    """
    Returns an AI summary based on the opportunity details by querying GPT-4o.
    """
    title = opportunity_data.get('title', 'this opportunity')
    org = opportunity_data.get('organization', 'the organization')
    score = int(opportunity_data.get('final_score', 0) * 10)
    why = opportunity_data.get('why', '')
    
    prompt = f"""
You are an AI assistant helping a student overview opportunities.
Write a strategic summary for the following opportunity using AT LEAST 5 bullet points.
Title: {title}
Organization: {org}
Match Score: {score}%
Logic match explanation: {why}

Keep the tone encouraging, professional, and highlight key actionable insights. Format the output STRICTLY as bullet points (-).
"""
    try:
        return generate_text(prompt)
    except Exception as e:
        return f"This **{title}** by **{org}** is ranked as a top match. *(AI Summary fetch failed: {str(e)})*"
