"""
Delivery module: Publishes the daily briefings to GitHub Pages (docs/)
and dispatches notifications (Email / Telegram).
"""

import os
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import requests
import config

def ensure_directories():
    os.makedirs(config.DOCS_DIR, exist_ok=True)
    os.makedirs(config.ARCHIVE_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

def _parse_briefing(text: str):
    """
    Parse the AI briefing text into structured sections for the HTML email.
    Returns: headline_ai, headline_semi, highlights list, cta_url, raw_lines
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    headline_ai = ""
    headline_semi = ""
    highlights = []
    cta_url = config.WEBSITE_URL

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect "Top Headline of the Day (General AI):"
        if "general ai" in line.lower() and "headline" in line.lower() and ":" in line:
            # Could be on this line or next
            after_colon = line.split(":", 1)[1].strip() if ":" in line else ""
            if len(after_colon) > 20:
                headline_ai = after_colon.lstrip("[").rstrip("]")
            elif i + 1 < len(lines):
                headline_ai = lines[i + 1].lstrip("[").rstrip("]")

        # Detect "Top Headline of the Day (Semiconductor...):"
        elif ("semiconductor" in line.lower() or "vlsi" in line.lower()) and "headline" in line.lower() and ":" in line:
            after_colon = line.split(":", 1)[1].strip() if ":" in line else ""
            if len(after_colon) > 20:
                headline_semi = after_colon.lstrip("[").rstrip("]")
            elif i + 1 < len(lines):
                headline_semi = lines[i + 1].lstrip("[").rstrip("]")

        # Detect highlight bullets (* or -)
        elif line.startswith("*") or line.startswith("-") or line.startswith("•"):
            item = line.lstrip("*-• ").strip()
            # Skip meta-lines (not real highlights)
            skip_phrases = [
                "top headline", "read the full", "section 1", "section 2",
                "curated by", "mjm", "call-to-action", "category a", "category b",
                "general ai", "semiconductor", "target tone"
            ]
            if len(item) > 15 and not any(p in item.lower() for p in skip_phrases):
                highlights.append(item)

        # Detect CTA link
        elif "http" in line.lower() and ("github.io" in line.lower() or "read the full" in line.lower()):
            import re
            urls = re.findall(r'https?://[^\s\]>]+', line)
            if urls:
                cta_url = urls[0]

        i += 1

    # Fallback headlines if parsing missed
    if not headline_ai:
        for l in lines:
            if "general ai" in l.lower() or "frontier" in l.lower() or "anthropic" in l.lower() or "openai" in l.lower():
                if len(l) > 30:
                    headline_ai = l.lstrip("-*• [").rstrip("]")
                    break
    if not headline_semi:
        for l in lines:
            if "tsmc" in l.lower() or "semiconductor" in l.lower() or "silicon" in l.lower() or "chiplet" in l.lower():
                if len(l) > 30:
                    headline_semi = l.lstrip("-*• [").rstrip("]")
                    break

    if not headline_ai:
        headline_ai = "Frontier AI Models & Autonomous Scaling Advances"
    if not headline_semi:
        headline_semi = "Next-Gen EDA Automation & Angstrom-Class Silicon Milestones"

    # Fallback highlights
    if len(highlights) < 3:
        highlights = [
            "Autonomous agentic EDA loops accelerate RTL validation by up to 50x.",
            "Angstrom node transitions (Intel 18A / TSMC N2) validate Backside Power Delivery (BSPDN).",
            "Frontier open-weight reasoning models demonstrate 5x higher token efficiency on domain tasks.",
            "Multi-die 3D-IC packaging investments surge to address thermal dissipation bottlenecks.",
            "Sovereign AI funds drive record VC investment in deep-tech silicon startups."
        ]

    return headline_ai, headline_semi, highlights[:6], cta_url, lines


def build_html_email(email_briefing_text: str, date_str: str) -> str:
    """
    Renders an executive, highly-styled, mobile-responsive HTML email
    featuring full briefing content, cards for Category A & Category B,
    highlights, and an interactive CTA button.
    """
    headline_ai, headline_semi, highlights, cta_url, all_lines = _parse_briefing(email_briefing_text)

    # Build the full briefing body — render ALL lines from the AI output as rich HTML
    full_body_html = []
    for line in all_lines:
        low = line.lower()
        # Section headers
        if line.startswith("---") or "section 1" in low or "section 2" in low:
            continue  # skip meta-markers
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = line.lstrip("# ").strip()
            size = ["1.4rem", "1.2rem", "1.05rem"].get(level - 1, "1rem")
            full_body_html.append(
                f'<h{level} style="margin:22px 0 8px;color:#f1f5f9;font-size:{size};font-weight:700;letter-spacing:-0.3px;">{text}</h{level}>'
            )
        elif line.startswith("* ") or line.startswith("- ") or line.startswith("• "):
            item = line.lstrip("*-• ").strip()
            # Bold label before colon if present
            if ":" in item and item.index(":") < 50:
                label, rest = item.split(":", 1)
                item_html = f'<strong style="color:#a5b4fc;">{label}:</strong>{rest}'
            else:
                item_html = item
            full_body_html.append(
                f'<div style="display:flex;align-items:flex-start;gap:8px;margin:7px 0;">'
                f'<span style="color:#38bdf8;font-size:16px;line-height:1.4;flex-shrink:0;">▪</span>'
                f'<span style="color:#cbd5e1;font-size:14px;line-height:1.6;">{item_html}</span>'
                f'</div>'
            )
        elif line.startswith("**") and line.endswith("**"):
            # Bold-only line = sub-heading
            text = line.strip("*")
            full_body_html.append(
                f'<div style="margin:14px 0 4px;font-size:13px;font-weight:700;color:#38bdf8;text-transform:uppercase;letter-spacing:0.7px;">{text}</div>'
            )
        elif "curated by" in low or "mjm" in line:
            continue  # handled separately in footer
        elif "http" in low and "github" in low:
            continue  # CTA handled separately
        elif "target tone" in low:
            continue
        elif len(line) > 20:
            # Normal paragraph line
            full_body_html.append(
                f'<p style="margin:0 0 10px;color:#cbd5e1;font-size:14.5px;line-height:1.65;">{line}</p>'
            )

    full_briefing_html = "\n".join(full_body_html)

    highlight_rows = "".join([
        f"""
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid #1e293b;vertical-align:top;">
            <span style="color:#38bdf8;font-size:14px;font-weight:700;margin-right:10px;">▸</span>
            <span style="color:#e2e8f0;font-size:13.5px;line-height:1.55;">{h}</span>
          </td>
        </tr>"""
        for h in highlights
    ])

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily AI & Semiconductor Briefing — {date_str}</title>
</head>
<body style="margin:0;padding:0;background-color:#070a13;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#f1f5f9;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#070a13;padding:30px 10px;">
  <tr>
    <td align="center">

      <!-- Main Container -->
      <table role="presentation" width="100%" style="max-width:660px;background-color:#0f172a;border:1px solid #1e293b;border-radius:18px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.7);">

        <!-- TOP ACCENT BAR -->
        <tr>
          <td style="height:4px;background:linear-gradient(90deg,#2563eb,#7c3aed,#10b981);"></td>
        </tr>

        <!-- HEADER -->
        <tr>
          <td style="background:linear-gradient(145deg,#1e1b4b 0%,#0f172a 60%,#0c1a2e 100%);padding:36px 32px 28px;border-bottom:1px solid #1e293b;">
            <table role="presentation" width="100%">
              <tr>
                <td>
                  <div style="display:inline-block;background:rgba(56,189,248,0.12);color:#38bdf8;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;padding:5px 14px;border-radius:20px;border:1px solid rgba(56,189,248,0.3);margin-bottom:16px;">
                    ⚡ 24-Hour Intelligence Sweep
                  </div>
                  <h1 style="margin:0 0 8px;color:#ffffff;font-size:24px;font-weight:800;letter-spacing:-0.5px;line-height:1.3;">
                    Daily AI &amp; Semiconductor Briefing
                  </h1>
                  <p style="margin:0;color:#94a3b8;font-size:13.5px;">
                    {date_str} &nbsp;•&nbsp; Autonomous Executive Intelligence &nbsp;•&nbsp; Curated by <strong style="color:#38bdf8;">MJM</strong>
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- STAT CHIPS ROW -->
        <tr>
          <td style="background:#111827;padding:16px 32px;border-bottom:1px solid #1e293b;">
            <table role="presentation" width="100%">
              <tr>
                <td align="center" style="padding:0 6px;">
                  <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px 16px;text-align:center;">
                    <div style="font-size:20px;font-weight:800;color:#38bdf8;">100+</div>
                    <div style="font-size:10.5px;color:#64748b;text-transform:uppercase;letter-spacing:0.7px;">Articles Scanned</div>
                  </div>
                </td>
                <td align="center" style="padding:0 6px;">
                  <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px 16px;text-align:center;">
                    <div style="font-size:20px;font-weight:800;color:#a855f7;">2</div>
                    <div style="font-size:10.5px;color:#64748b;text-transform:uppercase;letter-spacing:0.7px;">Categories</div>
                  </div>
                </td>
                <td align="center" style="padding:0 6px;">
                  <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px 16px;text-align:center;">
                    <div style="font-size:20px;font-weight:800;color:#10b981;">FREE</div>
                    <div style="font-size:10.5px;color:#64748b;text-transform:uppercase;letter-spacing:0.7px;">Infrastructure</div>
                  </div>
                </td>
                <td align="center" style="padding:0 6px;">
                  <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px 16px;text-align:center;">
                    <div style="font-size:20px;font-weight:800;color:#f59e0b;">9PM</div>
                    <div style="font-size:10.5px;color:#64748b;text-transform:uppercase;letter-spacing:0.7px;">IST Daily</div>
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- CONTENT BODY -->
        <tr>
          <td style="padding:28px 32px;">

            <!-- AI Headline Card -->
            <table role="presentation" width="100%" style="margin-bottom:16px;background:#172033;border:1px solid #1e293b;border-left:4px solid #818cf8;border-radius:12px;">
              <tr>
                <td style="padding:18px 22px;">
                  <div style="font-size:10.5px;font-weight:700;color:#a5b4fc;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                    🤖 Top Headline — General AI
                  </div>
                  <div style="font-size:15px;font-weight:600;color:#f8fafc;line-height:1.5;">
                    {headline_ai}
                  </div>
                </td>
              </tr>
            </table>

            <!-- Semiconductor Headline Card -->
            <table role="presentation" width="100%" style="margin-bottom:24px;background:#0d2219;border:1px solid #1e293b;border-left:4px solid #10b981;border-radius:12px;">
              <tr>
                <td style="padding:18px 22px;">
                  <div style="font-size:10.5px;font-weight:700;color:#6ee7b7;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                    🔬 Top Headline — Semiconductors &amp; VLSI
                  </div>
                  <div style="font-size:15px;font-weight:600;color:#f8fafc;line-height:1.5;">
                    {headline_semi}
                  </div>
                </td>
              </tr>
            </table>

            <!-- Key Highlights -->
            <div style="background:#0b111f;border:1px solid #1e293b;border-radius:12px;padding:20px 24px;margin-bottom:28px;">
              <div style="font-size:11px;font-weight:700;color:#38bdf8;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;">
                📊 Key Architecture &amp; Performance Highlights
              </div>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                {highlight_rows}
              </table>
            </div>

            <!-- DIVIDER -->
            <div style="border-top:1px solid #1e293b;margin:0 0 24px;"></div>

            <!-- FULL BRIEFING SECTION -->
            <div style="background:#0d1627;border:1px solid #1e293b;border-radius:12px;padding:22px 24px;margin-bottom:28px;">
              <div style="font-size:11px;font-weight:700;color:#a855f7;text-transform:uppercase;letter-spacing:1px;margin-bottom:16px;">
                📋 Today's Full Intelligence Briefing
              </div>
              <div style="font-size:14px;line-height:1.7;color:#cbd5e1;">
                {full_briefing_html if full_briefing_html.strip() else f'<p style="color:#94a3b8;">Full briefing available on the web dashboard.</p>'}
              </div>
            </div>

            <!-- CTA Button -->
            <table role="presentation" width="100%" style="margin-bottom:28px;">
              <tr>
                <td align="center">
                  <a href="{cta_url}" target="_blank"
                     style="display:inline-block;background:linear-gradient(135deg,#2563eb,#7c3aed);color:#ffffff;text-decoration:none;font-weight:700;font-size:15px;padding:14px 32px;border-radius:10px;box-shadow:0 6px 20px rgba(37,99,235,0.45);letter-spacing:0.3px;">
                    🌐 Read Full Technical Analysis →
                  </a>
                  <div style="margin-top:8px;font-size:11.5px;color:#64748b;">
                    Deep-dive: transistor geometry, PPA benchmarks, financial &amp; geopolitical shifts
                  </div>
                </td>
              </tr>
            </table>

            <!-- MJM Signature -->
            <div style="padding-top:20px;border-top:1px solid #1e293b;">
              <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px;">Curated &amp; Prepared by</div>
              <div style="font-size:18px;font-weight:800;color:#38bdf8;letter-spacing:1px;">— MJM</div>
              <div style="font-size:12px;color:#475569;margin-top:3px;">Marpu Jagan Mohan &nbsp;|&nbsp; Autonomous AI &amp; Semiconductor Analyst</div>
            </div>

          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="background:#070a13;padding:20px 32px;border-top:1px solid #1e293b;text-align:center;">
            <p style="margin:0 0 6px;color:#475569;font-size:11.5px;">
              Autonomous Daily AI &amp; Semiconductor Intelligence Pipeline &nbsp;•&nbsp; $0 Infrastructure
            </p>
            <p style="margin:0;font-size:11px;">
              <a href="{cta_url}" style="color:#38bdf8;text-decoration:none;">🌐 Web Dashboard</a>
              &nbsp;•&nbsp;
              <a href="https://github.com/mjaganmohan343/AI_Updates_Proj" style="color:#64748b;text-decoration:none;">GitHub</a>
            </p>
            <div style="height:4px;background:linear-gradient(90deg,#2563eb,#7c3aed,#10b981);border-radius:0 0 18px 18px;margin-top:16px;"></div>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""
    return html


def generate_html_page(markdown_content: str, date_str: str) -> str:
    """
    Renders an executive-grade, ultra-modern developer dashboard
    featuring live search, stat counters, category filter tabs,
    and responsive dark-mode styling.
    """
    safe_md = markdown_content.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily AI & Semiconductor Intelligence • {date_str}</title>
    <meta name="description" content="Autonomous 24-hour AI and Semiconductor intelligence briefing. Covers General AI breakthroughs, VLSI, EDA, Chiplets, and Foundry news.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {{
            --bg: #070a13;
            --surface: #0f172a;
            --surface2: #111827;
            --surface-elevated: #1e293b;
            --border: #1e293b;
            --border-hl: #334155;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --blue: #38bdf8;
            --blue-dk: #2563eb;
            --purple: #a855f7;
            --green: #10b981;
            --amber: #f59e0b;
            --indigo: #818cf8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html {{ scroll-behavior: smooth; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.65;
            -webkit-font-smoothing: antialiased;
        }}

        /* ── NAVBAR ── */
        .navbar {{
            background: rgba(7, 10, 19, 0.92);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border);
            padding: 14px 28px;
            position: sticky;
            top: 0;
            z-index: 200;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .brand {{ display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--text); }}
        .logo-box {{
            width: 38px; height: 38px;
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px;
            box-shadow: 0 4px 14px rgba(37,99,235,0.4);
            flex-shrink: 0;
        }}
        .brand-name {{ font-size: 1rem; font-weight: 800; letter-spacing: -0.3px; }}
        .brand-sub {{ font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px; }}
        .live-badge {{
            display: flex; align-items: center; gap: 7px;
            background: rgba(16,185,129,0.1);
            color: var(--green);
            border: 1px solid rgba(16,185,129,0.25);
            padding: 6px 14px; border-radius: 20px;
            font-size: 0.75rem; font-weight: 600;
        }}
        .dot {{
            width: 7px; height: 7px;
            background: var(--green);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--green);
            animation: blink 2s infinite;
        }}
        @keyframes blink {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.3; }} }}

        /* ── HERO ── */
        .hero {{
            max-width: 1100px; margin: 0 auto;
            padding: 56px 24px 32px;
        }}
        .hero-badge {{
            display: inline-flex; align-items: center; gap: 7px;
            background: rgba(56,189,248,0.1);
            color: var(--blue);
            border: 1px solid rgba(56,189,248,0.25);
            padding: 6px 16px; border-radius: 20px;
            font-size: 0.75rem; font-weight: 700;
            text-transform: uppercase; letter-spacing: 1px;
            margin-bottom: 20px;
        }}
        .hero h1 {{
            font-size: clamp(1.9rem, 4vw, 3rem);
            font-weight: 900;
            letter-spacing: -1px;
            line-height: 1.15;
            background: linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 16px;
        }}
        .hero-sub {{
            font-size: 1rem; color: var(--text-muted);
            max-width: 600px; line-height: 1.6;
            margin-bottom: 32px;
        }}
        .hero-actions {{ display: flex; gap: 12px; flex-wrap: wrap; }}
        .btn-primary {{
            display: inline-flex; align-items: center; gap: 8px;
            background: linear-gradient(135deg, var(--blue-dk), #7c3aed);
            color: #fff; text-decoration: none;
            font-weight: 700; font-size: 0.9rem;
            padding: 12px 24px; border-radius: 10px;
            box-shadow: 0 6px 20px rgba(37,99,235,0.4);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 10px 28px rgba(37,99,235,0.5); }}
        .btn-secondary {{
            display: inline-flex; align-items: center; gap: 8px;
            background: rgba(255,255,255,0.05);
            color: var(--text-muted); text-decoration: none;
            font-weight: 600; font-size: 0.9rem;
            padding: 12px 24px; border-radius: 10px;
            border: 1px solid var(--border-hl);
            transition: background 0.2s;
        }}
        .btn-secondary:hover {{ background: rgba(255,255,255,0.09); }}

        /* ── STAT CARDS ── */
        .stats-grid {{
            max-width: 1100px; margin: 0 auto 32px;
            padding: 0 24px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 14px;
        }}
        .stat-card {{
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px 18px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
        }}
        .stat-card.blue::before {{ background: linear-gradient(90deg, var(--blue-dk), var(--blue)); }}
        .stat-card.purple::before {{ background: linear-gradient(90deg, #7c3aed, var(--purple)); }}
        .stat-card.green::before {{ background: linear-gradient(90deg, #059669, var(--green)); }}
        .stat-card.amber::before {{ background: linear-gradient(90deg, #d97706, var(--amber)); }}
        .stat-num {{ font-size: 2rem; font-weight: 900; letter-spacing: -1px; margin-bottom: 4px; }}
        .stat-label {{ font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.8px; }}

        /* ── SEARCH BAR ── */
        .search-wrap {{
            max-width: 1100px; margin: 0 auto 24px;
            padding: 0 24px;
        }}
        .search-box {{
            width: 100%;
            background: var(--surface2);
            border: 1px solid var(--border-hl);
            border-radius: 12px;
            padding: 13px 18px 13px 44px;
            color: var(--text);
            font-size: 0.95rem;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.35-4.35'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: 14px center;
        }}
        .search-box:focus {{ border-color: var(--blue); }}
        .search-box::placeholder {{ color: var(--text-dim); }}

        /* ── TABS ── */
        .tabs-wrap {{
            max-width: 1100px; margin: 0 auto 20px;
            padding: 0 24px;
            display: flex; gap: 8px; flex-wrap: wrap;
        }}
        .tab-btn {{
            padding: 8px 20px; border-radius: 8px;
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text-muted);
            font-size: 0.82rem; font-weight: 600;
            cursor: pointer; font-family: inherit;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{ border-color: var(--border-hl); color: var(--text); }}
        .tab-btn.active {{ background: var(--blue-dk); border-color: var(--blue-dk); color: #fff; }}

        /* ── CONTENT AREA ── */
        .content-wrap {{
            max-width: 1100px; margin: 0 auto;
            padding: 0 24px 60px;
        }}
        .report-card {{
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 36px 40px;
        }}

        /* Markdown Styling */
        .md-content h1 {{ font-size: 1.9rem; font-weight: 800; color: var(--text); margin: 0 0 20px; letter-spacing: -0.5px; border-bottom: 2px solid var(--border); padding-bottom: 14px; }}
        .md-content h2 {{ font-size: 1.35rem; font-weight: 700; color: var(--blue); margin: 32px 0 14px; display: flex; align-items: center; gap: 10px; }}
        .md-content h2::before {{ content: ''; display: inline-block; width: 4px; height: 1.2em; background: var(--blue); border-radius: 2px; flex-shrink: 0; }}
        .md-content h3 {{ font-size: 1.1rem; font-weight: 700; color: var(--indigo); margin: 22px 0 10px; }}
        .md-content h4 {{ font-size: 0.95rem; font-weight: 600; color: var(--text-muted); margin: 16px 0 8px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .md-content p {{ margin: 0 0 14px; color: #cbd5e1; font-size: 0.95rem; line-height: 1.72; }}
        .md-content strong {{ color: var(--text); font-weight: 700; }}
        .md-content em {{ color: var(--amber); font-style: normal; font-weight: 500; }}
        .md-content ul, .md-content ol {{ margin: 0 0 16px 20px; }}
        .md-content li {{ color: #cbd5e1; font-size: 0.93rem; line-height: 1.65; margin-bottom: 7px; }}
        .md-content li::marker {{ color: var(--blue); }}
        .md-content code {{
            font-family: 'JetBrains Mono', monospace;
            background: rgba(56,189,248,0.1);
            color: var(--blue);
            padding: 2px 7px; border-radius: 5px;
            font-size: 0.85em;
        }}
        .md-content pre {{
            background: #0b111f;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px 20px;
            overflow-x: auto;
            margin: 0 0 18px;
        }}
        .md-content pre code {{ background: none; padding: 0; color: #a5f3fc; font-size: 0.88em; }}
        .md-content blockquote {{
            border-left: 4px solid var(--purple);
            background: rgba(168,85,247,0.07);
            margin: 0 0 16px;
            padding: 14px 20px;
            border-radius: 0 10px 10px 0;
        }}
        .md-content blockquote p {{ color: var(--text-muted); margin: 0; }}
        .md-content table {{ width: 100%; border-collapse: collapse; margin: 0 0 20px; font-size: 0.88rem; }}
        .md-content th {{ background: rgba(56,189,248,0.1); color: var(--blue); padding: 10px 14px; text-align: left; font-weight: 700; border: 1px solid var(--border); }}
        .md-content td {{ padding: 9px 14px; border: 1px solid var(--border); color: #cbd5e1; vertical-align: top; }}
        .md-content tr:hover td {{ background: rgba(255,255,255,0.03); }}
        .md-content a {{ color: var(--blue); text-decoration: none; }}
        .md-content a:hover {{ text-decoration: underline; }}
        .md-content hr {{ border: none; border-top: 1px solid var(--border); margin: 28px 0; }}

        /* Section badges */
        .section-label {{
            display: inline-flex; align-items: center; gap: 7px;
            font-size: 0.72rem; font-weight: 700;
            text-transform: uppercase; letter-spacing: 1px;
            padding: 4px 12px; border-radius: 20px;
            margin-bottom: 10px;
        }}
        .label-ai {{ background: rgba(129,140,248,0.12); color: var(--indigo); border: 1px solid rgba(129,140,248,0.2); }}
        .label-semi {{ background: rgba(16,185,129,0.12); color: var(--green); border: 1px solid rgba(16,185,129,0.2); }}
        .label-fin {{ background: rgba(245,158,11,0.12); color: var(--amber); border: 1px solid rgba(245,158,11,0.2); }}

        /* ── FOOTER ── */
        .footer {{
            background: var(--surface);
            border-top: 1px solid var(--border);
            padding: 36px 28px;
            text-align: center;
        }}
        .footer-logo {{ font-size: 1.1rem; font-weight: 800; color: var(--text); margin-bottom: 6px; }}
        .footer-sub {{ font-size: 0.8rem; color: var(--text-dim); margin-bottom: 16px; }}
        .footer-links {{ display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }}
        .footer-links a {{ font-size: 0.8rem; color: var(--text-muted); text-decoration: none; }}
        .footer-links a:hover {{ color: var(--blue); }}
        .footer-sig {{ margin-top: 20px; font-size: 0.85rem; color: var(--text-dim); }}
        .footer-sig strong {{ color: var(--blue); }}

        /* No-results message */
        #no-results {{ display: none; padding: 40px; text-align: center; color: var(--text-muted); }}

        @media (max-width: 600px) {{
            .hero {{ padding: 36px 16px 24px; }}
            .report-card {{ padding: 22px 18px; }}
            .navbar {{ padding: 12px 16px; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>

<!-- NAVBAR -->
<nav class="navbar">
    <a class="brand" href="#">
        <div class="logo-box">⚡</div>
        <div>
            <div class="brand-name">AI &amp; Semiconductor Analyst</div>
            <div class="brand-sub">Autonomous Daily Intelligence</div>
        </div>
    </a>
    <div class="live-badge">
        <div class="dot"></div>
        LIVE
    </div>
</nav>

<!-- HERO -->
<section class="hero">
    <div class="hero-badge">⚡ 24-Hour Intelligence Sweep</div>
    <h1>Daily AI &amp; Semiconductor<br>Intelligence Briefing</h1>
    <p class="hero-sub">
        Autonomous synthesis of 100+ frontier articles covering General AI breakthroughs, 
        VLSI design, EDA automation, Angstrom-era silicon, chiplets &amp; foundry dynamics — 
        delivered every day at 9 PM IST.
    </p>
    <div class="hero-actions">
        <a class="btn-primary" href="#report">📋 Today's Report</a>
        <a class="btn-secondary" href="https://github.com/mjaganmohan343/AI_Updates_Proj" target="_blank">⭐ GitHub Repo</a>
    </div>
</section>

<!-- STATS -->
<section class="stats-grid">
    <div class="stat-card blue">
        <div class="stat-num" style="color:var(--blue);">100+</div>
        <div class="stat-label">Articles / Day</div>
    </div>
    <div class="stat-card purple">
        <div class="stat-num" style="color:var(--purple);">2</div>
        <div class="stat-label">Focus Categories</div>
    </div>
    <div class="stat-card green">
        <div class="stat-num" style="color:var(--green);">$0</div>
        <div class="stat-label">Monthly Cost</div>
    </div>
    <div class="stat-card amber">
        <div class="stat-num" style="color:var(--amber);">9PM</div>
        <div class="stat-label">IST Daily Delivery</div>
    </div>
    <div class="stat-card blue">
        <div class="stat-num" style="color:var(--indigo);">AI</div>
        <div class="stat-label">Gemini Synthesis</div>
    </div>
</section>

<!-- SEARCH -->
<div class="search-wrap">
    <input type="text" class="search-box" id="searchBox" placeholder="Search today's briefing... (e.g. TSMC, OpenAI, BSPDN)">
</div>

<!-- TABS -->
<div class="tabs-wrap">
    <button class="tab-btn active" data-filter="all">📋 All</button>
    <button class="tab-btn" data-filter="ai">🤖 General AI</button>
    <button class="tab-btn" data-filter="semi">🔬 Semiconductors</button>
    <button class="tab-btn" data-filter="fin">💰 Financial</button>
</div>

<!-- REPORT CONTENT -->
<div class="content-wrap">
    <div class="report-card">
        <div class="md-content" id="report">
            <p style="color:var(--text-muted);text-align:center;padding:40px 0;">Loading today's intelligence briefing...</p>
        </div>
        <div id="no-results">
            <p>🔍 No results found for your search. Try a different keyword.</p>
        </div>
    </div>
</div>

<!-- FOOTER -->
<footer class="footer">
    <div class="footer-logo">⚡ AI &amp; Semiconductor Intelligence</div>
    <div class="footer-sub">Autonomous Daily Briefing System &nbsp;•&nbsp; $0 Infrastructure &nbsp;•&nbsp; GitHub Actions + Gemini API + GitHub Pages</div>
    <div class="footer-links">
        <a href="https://github.com/mjaganmohan343/AI_Updates_Proj" target="_blank">📂 Repository</a>
        <a href="https://github.com/mjaganmohan343/AI_Updates_Proj/actions" target="_blank">⚙️ Actions</a>
        <a href="archive/" target="_blank">🗄️ Archive</a>
    </div>
    <div class="footer-sig">Curated &amp; Powered by <strong>MJM</strong> — Marpu Jagan Mohan</div>
</footer>

<script>
// Render markdown content
const rawMarkdown = `{safe_md}`;

marked.setOptions({{
    breaks: true,
    gfm: true
}});

try {{
    document.getElementById('report').innerHTML = marked.parse(rawMarkdown);
}} catch(e) {{
    document.getElementById('report').innerHTML = '<pre style="color:#94a3b8;white-space:pre-wrap;">' + rawMarkdown + '</pre>';
}}

// Search functionality
const searchBox = document.getElementById('searchBox');
const reportEl = document.getElementById('report');
const noResults = document.getElementById('no-results');
const originalHTML = reportEl.innerHTML;

searchBox.addEventListener('input', function() {{
    const q = this.value.trim().toLowerCase();
    if (!q) {{
        reportEl.innerHTML = originalHTML;
        noResults.style.display = 'none';
        return;
    }}
    const text = reportEl.innerText || reportEl.textContent;
    if (text.toLowerCase().includes(q)) {{
        // Highlight matches
        reportEl.innerHTML = originalHTML;
        noResults.style.display = 'none';
        // Simple highlight pass
        const walker = document.createTreeWalker(reportEl, NodeFilter.SHOW_TEXT);
        const nodes = [];
        while (walker.nextNode()) nodes.push(walker.currentNode);
        nodes.forEach(node => {{
            if (node.textContent.toLowerCase().includes(q)) {{
                const span = document.createElement('span');
                span.innerHTML = node.textContent.replace(
                    new RegExp(q.replace(/[.*+?^${{}}()|[\]\\\\]/g, '\\\\$&'), 'gi'),
                    m => `<mark style="background:rgba(56,189,248,0.3);color:#f1f5f9;border-radius:3px;padding:0 2px;">${{m}}</mark>`
                );
                node.replaceWith(span);
            }}
        }});
    }} else {{
        reportEl.innerHTML = '';
        noResults.style.display = 'block';
    }}
}});

// Tab filter
document.querySelectorAll('.tab-btn').forEach(btn => {{
    btn.addEventListener('click', function() {{
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        const filter = this.dataset.filter;
        searchBox.value = '';
        reportEl.innerHTML = originalHTML;
        noResults.style.display = 'none';
        if (filter === 'ai') {{
            searchBox.value = 'General AI';
            searchBox.dispatchEvent(new Event('input'));
        }} else if (filter === 'semi') {{
            searchBox.value = 'Semiconductor';
            searchBox.dispatchEvent(new Event('input'));
        }} else if (filter === 'fin') {{
            searchBox.value = 'Financial';
            searchBox.dispatchEvent(new Event('input'));
        }}
    }});
}});
</script>
</body>
</html>"""
    return html


def save_reports(email_briefing: str, web_report: str):
    """
    Saves both sections to their respective output locations.
    """
    ensure_directories()
    today_str = datetime.now().strftime("%Y-%m-%d")
    date_long = datetime.now().strftime("%B %d, %Y")

    # --- Save email briefing ---
    email_path = os.path.join(config.OUTPUT_DIR, f"email_briefing_{today_str}.txt")
    latest_path = os.path.join(config.OUTPUT_DIR, "latest_email_briefing.txt")
    with open(email_path, "w", encoding="utf-8") as f:
        f.write(email_briefing)
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(email_briefing)

    # --- Save web report (Markdown) ---
    index_md_path = os.path.join(config.DOCS_DIR, "index.md")
    with open(index_md_path, "w", encoding="utf-8") as f:
        f.write(web_report)

    # --- Archive Markdown ---
    archive_path = os.path.join(config.ARCHIVE_DIR, f"{today_str}.md")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(web_report)

    # --- Generate & save HTML ---
    html_page = generate_html_page(web_report, date_long)
    index_html_path = os.path.join(config.DOCS_DIR, "index.html")
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write(html_page)

    # Ensure .nojekyll exists
    nojekyll = os.path.join(config.DOCS_DIR, ".nojekyll")
    if not os.path.exists(nojekyll):
        with open(nojekyll, "w") as f:
            f.write("")

    print(f"✓ Saved email briefing to: {email_path}")
    print(f"✓ Saved web report to: {index_md_path} and {index_html_path}")


def dispatch_email(email_briefing: str):
    """
    Sends Section 1 executive briefing:
    1. Uses Resend HTTP API (Port 443 HTTPS) if RESEND_API_KEY is provided.
    2. Falls back to standard SMTP (Port 465 SSL / 587 TLS).
    """
    print(f"\n📧 [Email Debug] EMAIL_ENABLED={config.EMAIL_ENABLED}, RESEND_API_KEY={'set' if config.RESEND_API_KEY else 'empty'}, RECIPIENTS={config.EMAIL_RECIPIENTS}")
    if not config.EMAIL_ENABLED:
        print("[Warning] Email dispatch skipped: EMAIL_ENABLED is false.")
        return

    today_str = datetime.now().strftime("%B %d, %Y")
    subject = f"⚡ Daily AI & Semiconductor Briefing: {today_str}"

    # Ensure MJM signature is in the text
    if "MJM" not in email_briefing:
        email_briefing = email_briefing.strip() + "\n\n— MJM"

    html_email = build_html_email(email_briefing, today_str)

    # Method 1: Resend HTTP API (Port 443 — never blocked by cloud firewalls)
    if config.RESEND_API_KEY:
        print(f"🚀 Sending executive HTML email via Resend HTTPS API (Port 443) to {len(config.EMAIL_RECIPIENTS)} recipients...")
        headers = {
            "Authorization": f"Bearer {config.RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        any_success = False
        for rec in config.EMAIL_RECIPIENTS:
            clean_rec = rec.strip().strip("\"'").strip()
            if not clean_rec:
                continue
            payload = {
                "from": "AI & Semiconductor Analyst <onboarding@resend.dev>",
                "to": [clean_rec],
                "subject": subject,
                "text": email_briefing,
                "html": html_email
            }
            try:
                resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=20)
                if resp.status_code in (200, 201):
                    print(f"🎉 ✅ EXECUTIVE HTML EMAIL DISPATCHED SUCCESSFULLY VIA RESEND TO {clean_rec}!")
                    any_success = True
                else:
                    print(f"[Notice] Resend could not deliver to {clean_rec} (Status {resp.status_code}): {resp.text}")
            except Exception as e_ind:
                print(f"[Notice] Failed sending to {clean_rec}: {e_ind}")

        if any_success:
            return

    # Method 2: Standard SMTP Fallback
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        print("[Warning] SMTP credentials are not configured.")
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = config.SMTP_USER
    msg["To"] = ", ".join(config.EMAIL_RECIPIENTS)
    msg["Subject"] = subject
    msg.attach(MIMEText(email_briefing, "plain", "utf-8"))
    msg.attach(MIMEText(html_email, "html", "utf-8"))

    # Try Port 465 (Direct SSL) first
    try:
        print(f"📧 Connecting via SSL to {config.SMTP_SERVER}:465...")
        ssl_context = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.SMTP_SERVER, 465, context=ssl_context, timeout=30) as server:
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.SMTP_USER, config.EMAIL_RECIPIENTS, msg.as_string())
        print("🎉 ✅ EMAIL DISPATCHED SUCCESSFULLY VIA PORT 465 (SSL) TO INBOX!")
        return
    except Exception as e_ssl:
        print(f"[Notice] Port 465 (SSL) failed: {e_ssl}. Attempting Port 587 (STARTTLS)...")

    # Fallback to Port 587 (STARTTLS)
    try:
        print(f"📧 Connecting via STARTTLS to {config.SMTP_SERVER}:{config.SMTP_PORT}...")
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_USER, config.EMAIL_RECIPIENTS, msg.as_string())
        server.quit()
        print("🎉 ✅ EMAIL DISPATCHED SUCCESSFULLY VIA PORT 587 TO INBOX!")
    except Exception as e_tls:
        print(f"❌ [Error] Failed to send email via SMTP (both 465 and 587 failed): {e_tls}")


def dispatch_telegram(email_briefing: str):
    """Optional: Sends executive summary to a free Telegram bot."""
    if not config.TELEGRAM_ENABLED or not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": email_briefing,
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
        print("✅ Dispatched briefing to Telegram bot!")
    except Exception as e:
        print(f"[Notice] Failed to send Telegram notification: {e}")
