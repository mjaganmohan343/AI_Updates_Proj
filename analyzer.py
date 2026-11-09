"""
Analyzer module: Synthesizes raw 24-hour inputs into the dual-section report
using Google Gemini API (Free Tier).
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Tuple
import config

SYSTEM_PROMPT = """
You are an expert AI & Hardware Intelligence Analyst. Your goal is to synthesize and analyze the last 24 hours of breakthroughs, announcements, and research in Artificial Intelligence, specifically focusing on general AI advancements as well as deep-tech hardware (Semiconductors, VLSI, Chip Design, and Electronics).

You are given a raw list of articles, paper abstracts, and press releases discovered in the last 24 hours across:
- CATEGORY A: General AI Breakthroughs (NVIDIA, OpenAI, Anthropic, Open Source models, research benchmarks).
- CATEGORY B: Electronics & Hardware AI (VLSI design automation, EDA tools, Semiconductor fab updates, custom ASICs, Neuromorphic computing, Chiplet packaging, and electronic system design).

For EACH evaluated item, rigorously determine:
1. What was achieved / launched?
2. Technical performance details & metrics (benchmarks, clock speeds, efficiency gains, throughput, PPA).
3. Industry impact (How it affects electronics design, hardware manufacturing, or general AI ecosystem).
4. Commercial & Investment landscape (M&A, funding rounds, strategic partnerships).

You MUST output your response with EXACTLY the following structure, separated cleanly:

--- SECTION 1: EMAIL BRIEFING ---
Target Tone: Professional, direct, highly informative.

- Top Headline of the Day (General AI): [Title & one punchy sentence]
- Top Headline of the Day (Semiconductor/VLSI AI): [Title & one punchy sentence]
- Quick Highlights:
  * [Key metric 1]
  * [Key metric 2]
  * [Key metric 3]
  * [Key metric 4]
- [Call-to-Action Link]: "Read the full 24-hour detailed technical analysis here -> [INSERT_WEBSITE_URL]"

--- SECTION 2: WEB PAGE FULL REPORT ---

# Daily AI & Semiconductor Briefing: [TODAY'S DATE]

## Executive Overview
[Brief paragraph summarizing today's macro trends in AI & hardware.]

## 1. General AI & Open Source Developments
### [Headline 1]
- **Overview:** [Detailed description]
- **Performance & Benchmarks:** [Specific stats/numbers]
- **Future Impact:** [Analysis of how this shifts the landscape]

### [Headline 2]
- **Overview:** [Detailed description]
- **Performance & Benchmarks:** [Specific stats/numbers]
- **Future Impact:** [Analysis of how this shifts the landscape]

## 2. Semiconductors, VLSI & Hardware AI
### [Headline 1]
- **Overview:** [Detailed description of chip design, EDA, or fab update]
- **Technical Specs & VLSI Impact:** [Impact on physical design, power/performance/area (PPA), logic synthesis, or silicon fabrication]
- **Market & Investment Context:** [Funding, partnerships, or foundry capacity details]

### [Headline 2]
- **Overview:** [Detailed description of chip design, EDA, or fab update]
- **Technical Specs & VLSI Impact:** [Impact on physical design, power/performance/area (PPA), logic synthesis, or silicon fabrication]
- **Market & Investment Context:** [Funding, partnerships, or foundry capacity details]

## 3. Financial & Strategic Shifts
- [Summary of funding, investments, or mergers in the hardware/AI space over the last 24 hours]
"""

def call_gemini(prompt: str, api_key: str) -> str:
    """
    Calls Google Gemini API (Free Tier).
    Uses direct REST API to gemini-2.5-flash or gemini-1.5-flash for maximum portability.
    """
    models = ["gemini-2.5-flash", "gemini-1.5-flash"]
    
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": SYSTEM_PROMPT},
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "maxOutputTokens": 8192
            }
        }
        
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            else:
                print(f"[Notice] Model {model} returned status {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            print(f"[Notice] Failed calling {model}: {e}")
            
    raise RuntimeError("Failed to generate report from Gemini API. Please check your GEMINI_API_KEY.")

def generate_analyst_report(raw_data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Takes the raw categorized 24-hour items, triggers the AI synthesis,
    and returns (email_briefing, web_report).
    """
    today_str = datetime.now().strftime("%B %d, %Y")
    
    # Format the prompt context
    prompt = f"Today's Date: {today_str}\nWebsite URL placeholder to substitute: {config.WEBSITE_URL}\n\n"
    prompt += "=== RAW 24-HOUR DATA: CATEGORY A (GENERAL AI) ===\n"
    for idx, item in enumerate(raw_data.get("category_a", [])[:15], 1):
        prompt += f"[{idx}] {item['title']}\nSummary: {item['summary']}\nLink: {item['link']}\n\n"
        
    prompt += "=== RAW 24-HOUR DATA: CATEGORY B (SEMICONDUCTORS & VLSI) ===\n"
    for idx, item in enumerate(raw_data.get("category_b", [])[:15], 1):
        prompt += f"[{idx}] {item['title']}\nSummary: {item['summary']}\nLink: {item['link']}\n\n"
        
    print(f"🤖 Synthesizing intelligence with Gemini for {today_str}...")
    full_output = call_gemini(prompt, config.GEMINI_API_KEY)
    
    # Split into Section 1 and Section 2
    if "--- SECTION 2: WEB PAGE FULL REPORT ---" in full_output:
        parts = full_output.split("--- SECTION 2: WEB PAGE FULL REPORT ---")
        section_1 = parts[0].replace("--- SECTION 1: EMAIL BRIEFING ---", "").strip()
        section_2 = parts[1].strip()
    else:
        # Fallback if delimiter varies slightly
        section_1 = full_output[:1200]
        section_2 = full_output
        
    # Replace website URL placeholder
    section_1 = section_1.replace("[INSERT_WEBSITE_URL]", config.WEBSITE_URL)
    section_2 = section_2.replace("[INSERT_WEBSITE_URL]", config.WEBSITE_URL)
    
    return section_1, section_2
