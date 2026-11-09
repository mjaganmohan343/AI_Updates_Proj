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

SYSTEM_PROMPT = """You are an expert AI & Hardware Intelligence Analyst. Your goal is to synthesize the last 24 hours of breakthroughs in Artificial Intelligence (General AI) and Deep-Tech Hardware (Semiconductors, VLSI, EDA tools, and Electronics).

CRITICAL FORMATTING INSTRUCTIONS:
- Do NOT output your thought process, outline, reasoning, or preliminary notes.
- Do NOT repeat the prompt instructions.
- Start your response IMMEDIATELY with '--- SECTION 1: EMAIL BRIEFING ---'.
- Follow the EXACT structure below:

--- SECTION 1: EMAIL BRIEFING ---
Target Tone: Professional, direct, highly informative.

- Top Headline of the Day (General AI): [Specific title & one punchy summary sentence]
- Top Headline of the Day (Semiconductor/VLSI AI): [Specific title & one punchy summary sentence]
- Quick Highlights:
  * [Key breakthrough 1 with hard metrics]
  * [Key breakthrough 2 with hard metrics]
  * [Key breakthrough 3 with hard metrics]
  * [Key breakthrough 4 with hard metrics]
- [Call-to-Action Link]: "Read the full 24-hour detailed technical analysis here -> [INSERT_WEBSITE_URL]"

--- SECTION 2: WEB PAGE FULL REPORT ---

# Daily AI & Semiconductor Briefing: [TODAY'S DATE]

## Executive Overview
[2-3 paragraph executive summary of macro trends across AI algorithms, silicon scaling, and hardware co-design.]

## 1. General AI & Open Source Developments
### [Headline 1]
- **Overview:** [Detailed technical explanation of the launch or paper]
- **Performance & Benchmarks:** [Hard numbers, throughput, latency, benchmark improvements]
- **Future Impact:** [Architectural and industry significance]

### [Headline 2]
- **Overview:** [Detailed technical explanation of the launch or paper]
- **Performance & Benchmarks:** [Hard numbers, throughput, latency, benchmark improvements]
- **Future Impact:** [Architectural and industry significance]

## 2. Semiconductors, VLSI & Hardware AI
### [Headline 1: Chip Design / EDA / Foundry Update]
- **Overview:** [Detailed explanation of EDA tool, packaging, or fab milestone]
- **Technical Specs & VLSI Impact:** [Impact on PPA (Power/Performance/Area), transistor density, routing, or packaging]
- **Market & Investment Context:** [Supply chain, foundry allocations, or partnerships]

### [Headline 2: Hardware Architecture / Acceleration]
- **Overview:** [Detailed explanation of new silicon architecture or accelerator]
- **Technical Specs & VLSI Impact:** [Bandwidth, TOPS/W, GAA/BSPDN details]
- **Market & Investment Context:** [Commercial deployment context]

## 3. Financial & Strategic Shifts
- [Bullet points of major funding rounds, M&A, and investments from the last 24 hours]
"""

def get_available_models(api_key: str) -> list:
    """Dynamically fetches models that support generateContent for this API key."""
    candidates = []
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for m in data.get("models", []):
                supported = m.get("supportedGenerationMethods", [])
                if "generateContent" in supported:
                    # Strip 'models/' prefix if present
                    name = m["name"].replace("models/", "")
                    candidates.append(name)
    except Exception as e:
        print(f"[Notice] Could not dynamically list models: {e}")
        
    # Prioritize flash models, then pro models
    priority = ["gemini-2.0-flash", "gemini-2.0-flash-exp", "gemini-1.5-flash-latest", "gemini-1.5-flash-002", "gemini-1.5-flash-001", "gemini-1.5-pro", "gemini-pro"]
    sorted_models = []
    for p in priority:
        if p in candidates:
            sorted_models.append(p)
            
    # Add any remaining candidates
    for c in candidates:
        if c not in sorted_models:
            sorted_models.append(c)
            
    return sorted_models if sorted_models else priority

def call_gemini(prompt: str, api_key: str) -> str:
    """
    Calls Google Gemini API (Free Tier).
    Automatically queries valid active models on the key.
    """
    models = get_available_models(api_key)
    print(f"🔍 Discovered available Gemini models: {models[:4]}")
    
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_PROMPT}\n\nTask Input:\n{prompt}"}
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
            print(f"🤖 Calling model: {model}...")
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"✓ Model {model} responded successfully!")
                return text
            else:
                print(f"[Notice] Model {model} returned status {resp.status_code}: {resp.text[:140]}")
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
