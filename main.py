"""
Main Orchestration Pipeline for Autonomous Daily AI & Semiconductor Analyst.
Coordinates sourcing, synthesis, publishing, and alerts.
"""

import sys
import os
from datetime import datetime
import config
from sources import collect_daily_sources
from analyzer import generate_analyst_report
from delivery import save_reports, dispatch_email, dispatch_telegram

def run_pipeline():
    print("=" * 65)
    print("🚀 STARTING AUTONOMOUS AI & SEMICONDUCTOR INTELLIGENCE PIPELINE")
    print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    
    # 1. Verification of Free API Key
    if not config.GEMINI_API_KEY:
        print("\n❌ Error: GEMINI_API_KEY is not set.")
        print("Please obtain a 100% free Gemini API key from https://aistudio.google.com/")
        print("and set it in your .env file or GitHub Actions Secrets as GEMINI_API_KEY.\n")
        sys.exit(1)
        
    # 2. Collect 24h fresh intelligence across Category A and Category B
    raw_data = collect_daily_sources()
    total_items = len(raw_data.get("category_a", [])) + len(raw_data.get("category_b", []))
    
    if total_items == 0:
        print("[Warning] No feed entries were retrieved. Check network or feed URLs.")
        sys.exit(0)
        
    # 3. Synthesize report via Gemini (Section 1 + Section 2)
    email_briefing, web_report = generate_analyst_report(raw_data)
    
    # 4. Save and Publish (GitHub Pages + Archive)
    save_reports(email_briefing, web_report)
    
    # 5. Optional Dispatches (Email & Telegram)
    dispatch_email(email_briefing)
    dispatch_telegram(email_briefing)
    
    print("\n" + "=" * 65)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 65)
    print("\n--- PREVIEW OF SECTION 1 (EMAIL BRIEFING) ---\n")
    print(email_briefing)
    print("\n" + "=" * 65)

if __name__ == "__main__":
    run_pipeline()
