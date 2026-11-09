"""
Sources module: Ingests 24-hour breakthroughs from free RSS feeds
for Category A (General AI) and Category B (Semiconductors / VLSI).
"""

import time
import feedparser
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import config

# Headers to prevent bot-blocking
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*"
}

def is_within_24_hours(entry: Dict[str, Any], hours: int = 30) -> bool:
    """
    Checks if a feed entry was published within the target window (default 30h to handle timezones).
    If no date is parsed, defaults to True to avoid missing breaking news.
    """
    time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if not time_struct:
        return True  # Fallback for feeds with non-standard date formats
    
    published_dt = datetime.fromtimestamp(time.mktime(time_struct), tz=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return published_dt >= cutoff

def fetch_feed_entries(url: str, max_items: int = 25) -> List[Dict[str, str]]:
    """Fetches and parses a single RSS feed with custom headers and timeout."""
    items = []
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=12)
        if response.status_code != 200:
            return items
        
        parsed = feedparser.parse(response.content)
        for entry in parsed.entries[:max_items]:
            if is_within_24_hours(entry):
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "") or entry.get("description", "")
                link = entry.get("link", "")
                
                # Clean up simple HTML tags if present in summary
                cleaned_summary = " ".join(summary.replace("<p>", " ").replace("</p>", " ").replace("<br>", " ").split())
                if len(cleaned_summary) > 400:
                    cleaned_summary = cleaned_summary[:400] + "..."
                
                if title:
                    items.append({
                        "title": title,
                        "summary": cleaned_summary,
                        "link": link
                    })
    except Exception as e:
        print(f"[Warning] Failed to fetch feed {url[:60]}...: {e}")
    
    return items

def collect_daily_sources() -> Dict[str, List[Dict[str, str]]]:
    """
    Aggregates all 24-hour items across Category A and Category B.
    Deduplicates entries by title.
    """
    results = {
        "category_a": [],
        "category_b": []
    }
    
    print("⏳ Collecting Category A (General AI) updates from the last 24 hours...")
    seen_titles_a = set()
    for feed_url in config.FEEDS["Category_A_General_AI"]:
        entries = fetch_feed_entries(feed_url)
        for item in entries:
            norm_title = item["title"].lower()
            if norm_title not in seen_titles_a:
                seen_titles_a.add(norm_title)
                results["category_a"].append(item)
                
    print(f"✓ Found {len(results['category_a'])} fresh items for Category A.")

    print("⏳ Collecting Category B (Semiconductors & VLSI) updates from the last 24 hours...")
    seen_titles_b = set()
    for feed_url in config.FEEDS["Category_B_Semiconductors_VLSI"]:
        entries = fetch_feed_entries(feed_url)
        for item in entries:
            norm_title = item["title"].lower()
            if norm_title not in seen_titles_b:
                seen_titles_b.add(norm_title)
                results["category_b"].append(item)
                
    print(f"✓ Found {len(results['category_b'])} fresh items for Category B.")

    return results

if __name__ == "__main__":
    data = collect_daily_sources()
    print(f"\nTotal collected: A={len(data['category_a'])}, B={len(data['category_b'])}")
