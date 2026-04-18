"""
Shared Gemini API client using the new google.genai package.
"""

import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client() -> genai.Client:
    """Return a cached Gemini Client instance."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Make sure it is set in your .env file.")
        _client = genai.Client(api_key=api_key)
    return _client


def generate_text(prompt: str) -> str:
    """Send a prompt to Gemini and return the response text."""
    client = get_client()
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text
