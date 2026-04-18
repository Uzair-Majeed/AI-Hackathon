"""
Shared OpenAI API client using GitHub Models inference endpoints.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client() -> OpenAI:
    """Return a cached OpenAI Client instance configured for GitHub Models."""
    global _client
    if _client is None:
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if not token:
            raise ValueError("GITHUB_TOKEN not found. Make sure it is set in your .env file.")
        
        endpoint = "https://models.github.ai/inference"
        
        _client = OpenAI(
            base_url=endpoint,
            api_key=token,
        )
    return _client

def generate_text(prompt: str) -> str:
    """Send a prompt to GPT-4o via GitHub Models API and return the response text."""
    client = get_client()
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=1.0,
        top_p=1.0,
        max_tokens=1000,
        model="openai/gpt-4o"
    )
    return response.choices[0].message.content
