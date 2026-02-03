#!/usr/bin/env python3
"""
Fetch the most-discussed Hacker News articles and send them to Instapaper.

Usage:
    python hn_to_instapaper.py

Configuration:
    Set the following environment variables:
    - ICLOUD_EMAIL: Your iCloud email address
    - ICLOUD_APP_PASSWORD: An app-specific password (not your main password)
    - INSTAPAPER_EMAIL: Your Instapaper save-by-email address
"""

import os
import smtplib
import requests
from email.mime.text import MIMEText

# Configuration
ICLOUD_EMAIL = os.environ.get("ICLOUD_EMAIL")
ICLOUD_APP_PASSWORD = os.environ.get("ICLOUD_APP_PASSWORD")
INSTAPAPER_EMAIL = os.environ.get("INSTAPAPER_EMAIL")

# HN API endpoints
HN_TOP_STORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# Settings
STORIES_TO_FETCH = 20
STORIES_TO_SEND = 5


def fetch_top_stories(n: int) -> list[int]:
    """Fetch the top N story IDs from Hacker News."""
    response = requests.get(HN_TOP_STORIES, timeout=10)
    response.raise_for_status()
    return response.json()[:n]


def fetch_story(story_id: int) -> dict | None:
    """Fetch story details. Returns None if the request fails."""
    try:
        response = requests.get(HN_ITEM.format(story_id), timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def has_external_url(story: dict) -> bool:
    """Check if a story has an external URL (not a self-post)."""
    return story.get("url") is not None


def get_top_commented_stories(stories: list[dict], n: int) -> list[dict]:
    """Sort stories by comment count and return top N."""
    sorted_stories = sorted(
        stories,
        key=lambda s: s.get("descendants", 0),
        reverse=True
    )
    return sorted_stories[:n]


def send_to_instapaper(url: str, title: str) -> None:
    """Send a URL to Instapaper via email."""
    msg = MIMEText(url)
    msg["Subject"] = title
    msg["From"] = ICLOUD_EMAIL
    msg["To"] = INSTAPAPER_EMAIL

    with smtplib.SMTP("smtp.mail.me.com", 587) as server:
        server.starttls()
        server.login(ICLOUD_EMAIL, ICLOUD_APP_PASSWORD)
        server.send_message(msg)


def main():
    # Validate configuration
    missing = []
    if not ICLOUD_EMAIL:
        missing.append("ICLOUD_EMAIL")
    if not ICLOUD_APP_PASSWORD:
        missing.append("ICLOUD_APP_PASSWORD")
    if not INSTAPAPER_EMAIL:
        missing.append("INSTAPAPER_EMAIL")
    
    if missing:
        print("Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nSee script header for configuration instructions.")
        return

    print(f"Fetching top {STORIES_TO_FETCH} stories from Hacker News...")
    story_ids = fetch_top_stories(STORIES_TO_FETCH)

    print("Fetching story details...")
    stories = []
    for story_id in story_ids:
        story = fetch_story(story_id)
        if story and has_external_url(story):
            stories.append(story)

    print(f"Found {len(stories)} stories with external URLs.")

    top_stories = get_top_commented_stories(stories, STORIES_TO_SEND)

    print(f"\nSending top {len(top_stories)} most-discussed articles to Instapaper:\n")
    
    for i, story in enumerate(top_stories, 1):
        title = story.get("title", "Untitled")
        url = story["url"]
        comments = story.get("descendants", 0)
        
        print(f"{i}. {title}")
        print(f"   {url}")
        print(f"   ({comments} comments)")
        
        try:
            send_to_instapaper(url, title)
            print("   ✓ Sent to Instapaper\n")
        except Exception as e:
            print(f"   ✗ Failed to send: {e}\n")

    print("Done!")


if __name__ == "__main__":
    main()
