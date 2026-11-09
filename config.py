"""
Configuration module for Daily AI & Semiconductor Analyst.
Loads environment variables and defines curated free feeds.
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# API Keys & URLs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
WEBSITE_URL = os.getenv("WEBSITE_URL", "").strip() or "https://github.com/your-username/AI_Updates_Proj"

# Delivery Configurations
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").strip().lower().strip("\"'") in ("true", "1", "yes")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
SMTP_SERVER = os.getenv("SMTP_SERVER", "").strip() or "smtp.gmail.com"

# Safely parse port even if passed as empty string
smtp_port_raw = os.getenv("SMTP_PORT", "").strip()
SMTP_PORT = int(smtp_port_raw) if smtp_port_raw.isdigit() else 587

SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
EMAIL_RECIPIENTS = [
    r.strip().strip("\"'").strip()
    for r in os.getenv("EMAIL_RECIPIENTS", "").replace(";", ",").split(",")
    if r.strip().strip("\"'").strip()
]

TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() in ("true", "1", "yes")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Directory Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
ARCHIVE_DIR = os.path.join(DOCS_DIR, "archive")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Curated Zero-Cost Data Feeds (Last 24 Hours / 1 Day filter)
FEEDS = {
    "Category_A_General_AI": [
        # Google News RSS with 24h freshness filter (when:1d)
        "https://news.google.com/rss/search?q=(OpenAI+OR+Anthropic+OR+DeepMind+OR+Meta+AI+OR+LLM+OR+%22open+source+model%22+OR+%22reasoning+model%22)+when:1d&hl=en-US&gl=US&ceid=US:en",
        # arXiv cs.AI and cs.LG (Artificial Intelligence & Machine Learning)
        "https://rss.arxiv.org/rss/cs.AI",
        "https://rss.arxiv.org/rss/cs.LG",
        # VentureBeat AI
        "https://venturebeat.com/category/ai/feed/",
        # TechCrunch AI
        "https://techcrunch.com/category/artificial-intelligence/feed/",
    ],
    "Category_B_Semiconductors_VLSI": [
        # Google News RSS with 24h freshness filter for VLSI, EDA, Semiconductor
        "https://news.google.com/rss/search?q=(VLSI+OR+semiconductor+OR+%22chip+design%22+OR+TSMC+OR+%22EDA+tools%22+OR+Synopsys+OR+Cadence+OR+ASIC+OR+chiplet+OR+neuromorphic+OR+RibbonFET+OR+CoWoS)+when:1d&hl=en-US&gl=US&ceid=US:en",
        # arXiv cs.AR (Hardware Architecture & VLSI)
        "https://rss.arxiv.org/rss/cs.AR",
        # Semiconductor Engineering & Hardware Feeds
        "https://semiengineering.com/feed/",
        "https://www.servethehome.com/feed/",
        "https://www.tomshardware.com/feeds/all",
        "https://www.eetimes.com/feed/",
    ]
}
