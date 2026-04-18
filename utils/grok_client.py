"""
Shared Grok API (xAI) client using standard HTTP requests.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def generate_text(prompt: str) -> str:
    """Send a prompt to Grok API and return the response text."""
    api_key = os.getenv("XAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("XAI_API_KEY not found. Make sure it is set in your .env file.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "grok-4.20-reasoning",
        "input": prompt
    }
    
    resp = requests.post("https://api.x.ai/v1/responses", headers=headers, json=payload)
    
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        error_msg = resp.json().get('error', resp.text)
        raise ValueError(f"Grok API Error: {error_msg}")
    
    data = resp.json()
    
    if "response" in data:
        return data["response"]
    elif "text" in data:
        return data["text"]
    elif "output" in data:
        return data["output"]
    elif "message" in data:
        if isinstance(data["message"], dict) and "content" in data["message"]:
            return data["message"]["content"]
        return str(data["message"])
    elif "choices" in data:
        return data["choices"][0]["message"]["content"]
    else:
        return str(data)
