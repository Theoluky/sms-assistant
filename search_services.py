import os
import requests
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX      = os.getenv("GOOGLE_CX")

def get_search_summary(query):
    """Perform a Google CSE search and return a short SMS‐friendly summary."""
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return "Search is not configured."
    # Call the Google Custom Search API
    params = {
        "key": GOOGLE_API_KEY,
        "cx":  GOOGLE_CX,
        "q":   query,
    }
    resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=5)
    if resp.status_code != 200:
        return "⚠️ Search API error."
    data = resp.json()
    items = data.get("items")
    if not items:
        return f"No results for '{query}'."
    # Take the top result
    top = items[0]
    title   = top.get("title", "")
    snippet = top.get("snippet", "")
    link    = top.get("link", "")
    # Build a concise summary
    summary = f"🔍 {title}\n{snippet}"
    # If there's room, append link
    if len(summary) + len(link) + 5 < 160:
        summary += f"\n{link}"
    # Truncate to ~150 chars
    if len(summary) > 150:
        summary = summary[:147] + "..."
    return summary