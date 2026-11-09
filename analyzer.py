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

SYSTEM_PROMPT = """You are an elite Lead AI & Hardware Intelligence Analyst producing an authoritative, high-density daily intelligence report. Your audience comprises hardware architects, silicon design executives, AI researchers, and deep-tech venture investors.

CRITICAL INSTRUCTIONS:
- Deliver HIGH TECHNICAL DEPTH. Include quantitative metrics, benchmark scores, clock speeds, TOPS/W, PPA (Power/Performance/Area) gains, memory bandwidth, transistor geometry, and wafer pricing.
- Do NOT output preamble, thoughts, outlines, or conversational filler.
- Begin IMMEDIATELY with '--- SECTION 1: EMAIL BRIEFING ---'.
- Follow the EXACT structure below:

--- SECTION 1: EMAIL BRIEFING ---
Target Tone: Crisp, executive, highly informative.

- Top Headline of the Day (General AI): [Specific title & 2-sentence punchy analysis]
- Top Headline of the Day (Semiconductor/VLSI AI): [Specific title & 2-sentence punchy analysis]
- Key Performance & Architecture Highlights:
  * [Highlight 1: Model/Software metric, e.g. SWE-bench, context window, token efficiency]
  * [Highlight 2: Hardware/PPA metric, e.g. GAAFET, BSPDN, TOPS/Watt, frequency delta]
  * [Highlight 3: Packaging & Interconnect metric, e.g. HBM3e/4 bandwidth, TB/s, CoWoS pitch]
  * [Highlight 4: Infrastructure & Capital metric, e.g. funding, power MW, cluster size]
  * [Highlight 5: Strategic/Geopolitical shift, e.g. foundry allocation, export restrictions]
- [Call-to-Action Link]: "Read the full 24-hour detailed technical analysis here -> [INSERT_WEBSITE_URL]"

Curated by: MJM

--- SECTION 2: WEB PAGE FULL REPORT ---

# Daily AI & Semiconductor Briefing: [TODAY'S DATE]

## Executive Overview
[3-4 rich paragraphs analyzing today's macro currents at the intersection of AI algorithmic advances and deep-tech silicon engineering. Detail how compute scaling, foundry node shifts, and packaging bottlenecks are shaping the industry.]

## 1. General AI & Open Source Developments

### [Headline 1: Frontier Models & Reasoning]
- **Overview:** [Deep technical analysis of the launch, weights, or paper]
- **Performance & Benchmarks:** [Hard numbers: MMLU-Pro, SWE-bench, GSM8k, throughput (tokens/sec), parameter efficiency]
- **Future Impact:** [Architectural and industry significance for developer ecosystems]

### [Headline 2: Agentic Frameworks & Test-Time Compute]
- **Overview:** [Detailed technical explanation of multi-step agents, code synthesis, or test-time compute loops]
- **Performance & Benchmarks:** [Latency, cost-per-task reduction, benchmark gains]
- **Future Impact:** [How this transforms autonomous software and hardware engineering]

### [Headline 3: Open Weights & Efficiency Innovations]
- **Overview:** [Quantization (FP8/FP4/INT4), distillation, or novel architecture breakthrough]
- **Performance & Benchmarks:** [VRAM footprint, memory bandwidth utilization, speedup factors]
- **Future Impact:** [Local workstation deployment and private enterprise adoption]

## 2. Semiconductors, VLSI & Hardware AI

### [Headline 1: EDA & Autonomous Physical Design]
- **Overview:** [Detailed coverage of AI-driven EDA tools (Synopsys, Cadence, Siemens) for floorplanning, routing, or verification]
- **Technical Specs & VLSI Impact:** [Impact on PPA (Power/Performance/Area), timing closure, DRC violations, and logic synthesis turnaround time]
- **Market & Foundry Context:** [Adoption by hyperscalers, foundries, and fabless designers]

### [Headline 2: Angstrom Nodes & Advanced Transistor Architecture]
- **Overview:** [Foundry developments (TSMC N2/A16, Intel 18A/14A, Samsung SF2) regarding GAAFET, RibbonFET, and Backside Power Delivery (BSPDN/PowerVia)]
- **Technical Specs & VLSI Impact:** [Standard cell height, IR drop reduction, frequency gain at iso-power, interconnect density]
- **Market & Foundry Context:** [Tape-out schedules, wafer pricing, and capacity commitments]

### [Headline 3: Advanced Packaging & Custom Accelerators]
- **Overview:** [Developments in chiplet packaging (CoWoS, EMIB, 3D-IC, UCIe) and custom ASICs/TPUs/accelerators]
- **Technical Specs & VLSI Impact:** [Interconnect bandwidth (TB/s), bump pitch, thermal dissipation / TDP, HBM3e/HBM4 integration]
- **Market & Foundry Context:** [Hyperscaler capex, supply chain constraints, and packaging lead times]

## 3. Financial, Strategic & Geopolitical Shifts
- **Strategic M&A & Joint Ventures:** [Details of recent deals, joint development agreements, and foundry commitments]
- **Venture Capital & Sovereign Funding:** [Details on funding rounds, European Chips Act, US CHIPS grants, and sovereign AI funds]
- **Supply Chain & Geopolitical Dynamics:** [Export restrictions, equipment sales (ASML, Tokyo Electron), and fab construction updates]
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
    for idx, item in enumerate(raw_data.get("category_a", [])[:25], 1):
        prompt += f"[{idx}] {item['title']}\nSummary: {item['summary']}\nLink: {item['link']}\n\n"
        
    prompt += "=== RAW 24-HOUR DATA: CATEGORY B (SEMICONDUCTORS & VLSI) ===\n"
    for idx, item in enumerate(raw_data.get("category_b", [])[:25], 1):
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
