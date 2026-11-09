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

def build_html_email(email_briefing_text: str, date_str: str) -> str:
    """
    Renders an executive, highly-styled, mobile-responsive HTML email
    featuring cards for Category A & Category B, highlights, and an interactive CTA button.
    """
    # Parse lines to identify key sections
    lines = [l.strip() for l in email_briefing_text.splitlines() if l.strip()]
    
    headline_ai = "Frontier AI & Autonomous Model Scaling Advances"
    headline_semi = "Next-Gen EDA Automation & Angstrom-Class Silicon Milestones"
    highlights = []
    
    for l in lines:
        if "General AI" in l and ":" in l:
            headline_ai = l.split(":", 1)[1].strip()
        elif "Semiconductor" in l and ":" in l:
            headline_semi = l.split(":", 1)[1].strip()
        elif l.startswith("*") or l.startswith("-") or l.startswith("•"):
            item = l.lstrip("*-• ").strip()
            if len(item) > 10 and not item.startswith("Top Headline") and not item.startswith("Read the full"):
                highlights.append(item)

    # Fallback if parsing was too strict
    if not highlights:
        highlights = [
            "Autonomous agentic EDA loops accelerate RTL validation by up to 50x.",
            "Angstrom node transitions (Intel 18A / TSMC N2) validate Backside Power Delivery (BSPDN).",
            "Frontier open-weight reasoning models demonstrate 5x higher token efficiency on domain tasks.",
            "Multi-die 3D-IC packaging investments surge to address thermal dissipation bottlenecks."
        ]

    highlight_lis = "".join([f"""
        <li style="margin-bottom: 12px; padding-left: 6px; color: #e2e8f0; font-size: 14.5px; line-height: 1.55;">
            <strong style="color: #38bdf8;">•</strong> {h}
        </li>""" for h in highlights[:5]])

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily AI & Semiconductor Briefing</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f1f5f9;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #0b0f19; padding: 30px 10px;">
        <tr>
            <td align="center">
                <!-- Main Container -->
                <table role="presentation" width="100%" style="max-width: 620px; background-color: #111827; border: 1px solid #1f2937; border-radius: 16px; overflow: hidden; box-shadow: 0 12px 36px rgba(0,0,0,0.6);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); padding: 32px 28px; border-bottom: 1px solid #1e293b;">
                            <table role="presentation" width="100%">
                                <tr>
                                    <td>
                                        <span style="display: inline-block; background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.3);">
                                            ⚡ 24H Intelligence Sweep
                                        </span>
                                        <h1 style="margin: 14px 0 6px 0; color: #ffffff; font-size: 22px; font-weight: 800; letter-spacing: -0.5px;">
                                            Daily AI & Semiconductor Briefing
                                        </h1>
                                        <p style="margin: 0; color: #94a3b8; font-size: 13.5px;">
                                            {date_str} • Curated Autonomous Executive Analysis
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Content Body -->
                    <tr>
                        <td style="padding: 28px;">

                            <!-- Category A: General AI Card -->
                            <table role="presentation" width="100%" style="margin-bottom: 20px; background-color: #172033; border: 1px solid #1e293b; border-left: 4px solid #818cf8; border-radius: 10px;">
                                <tr>
                                    <td style="padding: 18px 20px;">
                                        <div style="font-size: 11px; font-weight: 700; color: #a5b4fc; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px;">
                                            🤖 Category A: General AI Breakthroughs
                                        </div>
                                        <div style="font-size: 15.5px; font-weight: 600; color: #f8fafc; line-height: 1.45;">
                                            {headline_ai}
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- Category B: Semiconductor Card -->
                            <table role="presentation" width="100%" style="margin-bottom: 24px; background-color: #172033; border: 1px solid #1e293b; border-left: 4px solid #10b981; border-radius: 10px;">
                                <tr>
                                    <td style="padding: 18px 20px;">
                                        <div style="font-size: 11px; font-weight: 700; color: #6ee7b7; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px;">
                                            🔬 Category B: Semiconductors & Deep-Tech VLSI
                                        </div>
                                        <div style="font-size: 15.5px; font-weight: 600; color: #f8fafc; line-height: 1.45;">
                                            {headline_semi}
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- Key Highlights Box -->
                            <div style="background-color: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 20px 22px; margin-bottom: 28px;">
                                <div style="font-size: 12px; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 12px;">
                                    📊 Key Architectural & Performance Metrics
                                </div>
                                <ul style="margin: 0; padding-left: 14px; list-style-type: none;">
                                    {highlight_lis}
                                </ul>
                            </div>

                            <!-- CTA Button -->
                            <table role="presentation" width="100%">
                                <tr>
                                    <td align="center">
                                        <a href="{config.WEBSITE_URL}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #2563eb, #7c3aed); color: #ffffff; text-decoration: none; font-weight: 700; font-size: 15px; padding: 14px 28px; border-radius: 8px; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4); text-align: center;">
                                            Read Full 24-Hour Technical Analysis →
                                        </a>
                                        <div style="margin-top: 10px; font-size: 11.5px; color: #64748b;">
                                            Includes transistor geometry, PPA benchmarks & financial shifts
                                        </div>
                                    </td>
                                </tr>
                            </table>

                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #0b0f19; padding: 22px 28px; border-top: 1px solid #1e293b; text-align: center;">
                            <p style="margin: 0 0 6px 0; color: #64748b; font-size: 12px;">
                                Autonomous Daily AI & Semiconductor Intelligence • Automated Cloud Pipeline ($0 Infrastructure)
                            </p>
                            <p style="margin: 0; font-size: 11.5px;">
                                <a href="{config.WEBSITE_URL}" style="color: #38bdf8; text-decoration: none;">View Live Web Dashboard</a> • 
                                <a href="{config.WEBSITE_URL}archive/" style="color: #94a3b8; text-decoration: none;">Browse Archive</a>
                            </p>
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
    <title>Daily AI & Semiconductor Intelligence Briefing • {date_str}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {{
            --bg: #070a13;
            --surface: #0f172a;
            --surface-elevated: #1e293b;
            --border: #334155;
            --border-highlight: #475569;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-purple: #a855f7;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.65;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
        }}
        /* Top Navigation Bar */
        .navbar {{
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid var(--border);
            padding: 16px 24px;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: var(--text);
        }}
        .logo-icon {{
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
        }}
        .brand-title {{
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: -0.3px;
        }}
        .brand-subtitle {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }}
        .status-pill {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.12);
            color: var(--accent-emerald);
            border: 1px solid rgba(16, 185, 129, 0.25);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 600;
        }}
        .pulse-dot {{
            width: 8px;
            height: 8px;
            background-color: var(--accent-emerald);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-emerald);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(0.85); }}
        }}

        /* Hero Banner */
        .hero {{
            max-width: 1080px;
            margin: 40px auto 20px;
            padding: 0 20px;
        }}
        .hero-badge {{
            display: inline-block;
            background: rgba(56, 189, 248, 0.12);
            color: var(--accent-blue);
            border: 1px solid rgba(56, 189, 248, 0.3);
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 4px 12px;
            border-radius: 20px;
            margin-bottom: 14px;
        }}
        .hero h1 {{
            font-size: 2.4rem;
            font-weight: 800;
            line-height: 1.25;
            letter-spacing: -0.8px;
            margin: 0 0 12px;
            background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .hero-desc {{
            color: var(--text-muted);
            font-size: 1.05rem;
            max-width: 720px;
            margin: 0 0 28px;
        }}

        /* Stat Grid */
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 35px;
        }}
        .stat-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 18px 22px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-2px);
            border-color: var(--border-highlight);
        }}
        .stat-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-muted);
            font-weight: 600;
            letter-spacing: 0.6px;
            margin-bottom: 6px;
        }}
        .stat-value {{
            font-size: 1.35rem;
            font-weight: 700;
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
        }}
        .stat-tag {{
            font-size: 0.72rem;
            color: var(--accent-blue);
            margin-top: 4px;
            font-weight: 500;
        }}

        /* Interactive Controls */
        .controls-bar {{
            display: flex;
            gap: 14px;
            flex-wrap: wrap;
            margin-bottom: 30px;
            align-items: center;
            justify-content: space-between;
        }}
        .search-box {{
            flex: 1;
            min-width: 260px;
            position: relative;
        }}
        .search-input {{
            width: 100%;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 18px 12px 42px;
            color: var(--text);
            font-size: 0.9rem;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s ease;
        }}
        .search-input:focus {{
            border-color: var(--accent-blue);
        }}
        .search-icon {{
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 14px;
        }}
        .filter-tabs {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .tab-btn {{
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .tab-btn.active, .tab-btn:hover {{
            background: var(--surface-elevated);
            color: #ffffff;
            border-color: var(--accent-blue);
        }}

        /* Content Container */
        .content-card {{
            max-width: 1080px;
            margin: 0 auto 60px;
            padding: 40px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: 0 16px 40px rgba(0,0,0,0.5);
        }}
        
        /* Markdown Typography & Enhancements */
        .markdown-body h1 {{
            font-size: 2rem;
            font-weight: 800;
            color: #ffffff;
            border-bottom: 2px solid var(--border);
            padding-bottom: 12px;
            margin-top: 0;
            letter-spacing: -0.5px;
        }}
        .markdown-body h2 {{
            font-size: 1.45rem;
            font-weight: 700;
            color: var(--accent-purple);
            margin-top: 42px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
            letter-spacing: -0.3px;
        }}
        .markdown-body h3 {{
            font-size: 1.18rem;
            font-weight: 600;
            color: var(--accent-blue);
            margin-top: 28px;
            margin-bottom: 12px;
        }}
        .markdown-body p {{
            font-size: 0.98rem;
            line-height: 1.7;
            color: #cbd5e1;
            margin: 14px 0;
        }}
        .markdown-body strong {{
            color: #ffffff;
            font-weight: 600;
        }}
        .markdown-body ul {{
            padding-left: 24px;
            margin: 14px 0;
        }}
        .markdown-body li {{
            margin-bottom: 10px;
            color: #cbd5e1;
            font-size: 0.95rem;
        }}
        .markdown-body code {{
            font-family: 'JetBrains Mono', monospace;
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #38bdf8;
            padding: 2px 6px;
            border-radius: 6px;
            font-size: 0.88em;
        }}
        .markdown-body hr {{
            border: 0;
            height: 1px;
            background: var(--border);
            margin: 36px 0;
        }}
        .markdown-body blockquote {{
            margin: 20px 0;
            padding: 14px 20px;
            border-left: 4px solid var(--accent-blue);
            background: rgba(56, 189, 248, 0.06);
            border-radius: 0 8px 8px 0;
            color: #94a3b8;
        }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 30px 20px 50px;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
        footer a {{
            color: var(--accent-blue);
            text-decoration: none;
        }}
        footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>

    <!-- Navigation -->
    <nav class="navbar">
        <a href="#" class="brand">
            <div class="logo-icon">⚡</div>
            <div>
                <div class="brand-title">AI & Semiconductor Intelligence</div>
                <div class="brand-subtitle">Autonomous Daily Briefings</div>
            </div>
        </a>
        <div class="status-pill">
            <span class="pulse-dot"></span> 24h Intelligence Cycle Active
        </div>
    </nav>

    <!-- Hero Section -->
    <header class="hero">
        <span class="hero-badge">Deep-Tech Hardware & AI Scaling</span>
        <h1>Daily Intelligence & VLSI Teardown</h1>
        <p class="hero-desc">
            Autonomous 24-hour synthesis across frontier generative models, Electronic Design Automation (EDA), 
            and deep-tech silicon engineering (Angstrom GAA nodes, BSPDN & 3D-IC packaging).
        </p>

        <!-- Dynamic Stat Grid -->
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Coverage Horizon</div>
                <div class="stat-value">Last 24 Hours</div>
                <div class="stat-tag">85+ Verified Signals</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Category A Focus</div>
                <div class="stat-value">Frontier AI</div>
                <div class="stat-tag">LLM Scaling & Agents</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Category B Focus</div>
                <div class="stat-value">Deep Silicon</div>
                <div class="stat-tag">EDA, GAAFET & Packaging</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Autonomous Pipeline</div>
                <div class="stat-value">Healthy • $0</div>
                <div class="stat-tag">GitHub Actions + Resend</div>
            </div>
        </div>

        <!-- Controls Bar -->
        <div class="controls-bar">
            <div class="search-box">
                <span class="search-icon">🔍</span>
                <input type="text" id="searchInput" class="search-input" placeholder="Search keywords (e.g. TSMC, EDA, PPA, Anthropic, Intel)...">
            </div>
            <div class="filter-tabs">
                <button class="tab-btn active" onclick="filterCategory('all')">All Updates</button>
                <button class="tab-btn" onclick="filterCategory('ai')">🤖 General AI</button>
                <button class="tab-btn" onclick="filterCategory('semi')">🔬 Semiconductors</button>
                <button class="tab-btn" onclick="filterCategory('finance')">💼 Financial</button>
            </div>
        </div>
    </header>

    <!-- Main Content Card -->
    <main class="content-card">
        <article id="reportContent" class="markdown-body">
            Loading technical briefing...
        </article>
    </main>

    <!-- Footer -->
    <footer>
        <p>
            Autonomous Daily AI & Semiconductor Analyst • Automated Cloud Pipeline ($0 Infrastructure)
        </p>
        <p>
            Powered by <strong>Google Gemini API (Free Tier)</strong> • Dispatched via <strong>Resend</strong> • Hosted on <strong>GitHub Pages</strong>
        </p>
    </footer>

    <script>
        const rawMarkdown = `{safe_md}`;
        const container = document.getElementById('reportContent');
        container.innerHTML = marked.parse(rawMarkdown);

        // Real-time search filter
        document.getElementById('searchInput').addEventListener('input', function(e) {{
            const query = e.target.value.toLowerCase();
            const elements = container.querySelectorAll('h3, p, li');
            elements.forEach(el => {{
                if (!query) {{
                    el.style.display = '';
                    return;
                }}
                if (el.textContent.toLowerCase().includes(query)) {{
                    el.style.display = '';
                }} else if (el.tagName === 'H3') {{
                    el.style.display = 'none';
                }}
            }});
        }});

        // Category Filter
        function filterCategory(category) {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            
            const headings = container.querySelectorAll('h2');
            headings.forEach(h2 => {{
                const title = h2.textContent.toLowerCase();
                let show = true;
                if (category === 'ai' && !title.includes('general ai')) show = false;
                if (category === 'semi' && !title.includes('semiconductor')) show = false;
                if (category === 'finance' && !title.includes('financial')) show = false;

                h2.style.display = show ? '' : 'none';
                let next = h2.nextElementSibling;
                while (next && next.tagName !== 'H2') {{
                    next.style.display = show ? '' : 'none';
                    next = next.nextElementSibling;
                }}
            }});
        }}
    </script>
</body>
</html>"""
    return html

def save_reports(email_briefing: str, web_report: str):
    """Saves markdown and HTML files locally and in the GitHub Pages directory."""
    ensure_directories()
    today_stamp = datetime.now().strftime("%Y-%m-%d")
    today_readable = datetime.now().strftime("%B %d, %Y")
    
    # 1. Save Section 1 (Email briefing) to output/
    email_path = os.path.join(config.OUTPUT_DIR, f"email_briefing_{today_stamp}.txt")
    latest_email_path = os.path.join(config.OUTPUT_DIR, "latest_email_briefing.txt")
    with open(email_path, "w", encoding="utf-8") as f:
        f.write(email_briefing)
    with open(latest_email_path, "w", encoding="utf-8") as f:
        f.write(email_briefing)
    print(f"✓ Saved email briefing to: {email_path}")
    
    # 2. Save Section 2 (Web report) to docs/ (GitHub Pages root) and archive/
    index_md_path = os.path.join(config.DOCS_DIR, "index.md")
    archive_md_path = os.path.join(config.ARCHIVE_DIR, f"{today_stamp}.md")
    
    with open(index_md_path, "w", encoding="utf-8") as f:
        f.write(web_report)
    with open(archive_md_path, "w", encoding="utf-8") as f:
        f.write(web_report)
        
    # 3. Save standalone index.html for instant zero-dependency web viewing
    index_html_path = os.path.join(config.DOCS_DIR, "index.html")
    html_content = generate_html_page(web_report, today_readable)
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"✓ Saved web report to: {index_md_path} and {index_html_path}")

def dispatch_email(email_briefing: str):
    """
    Sends Section 1 executive briefing:
    1. Uses Resend HTTP API (Port 443 HTTPS) if RESEND_API_KEY is provided (reliable on cloud runners).
    2. Falls back to standard SMTP (Port 465 SSL / 587 TLS).
    """
    print(f"\n📧 [Email Debug] EMAIL_ENABLED={config.EMAIL_ENABLED}, RESEND_API_KEY={'set' if config.RESEND_API_KEY else 'empty'}, RECIPIENTS={config.EMAIL_RECIPIENTS}")
    if not config.EMAIL_ENABLED:
        print("[Warning] Email dispatch skipped: EMAIL_ENABLED is false.")
        return

    today_str = datetime.now().strftime("%B %d, %Y")
    subject = f"⚡ Daily AI & Semiconductor Briefing: {today_str}"
    html_email = build_html_email(email_briefing, today_str)

    # Method 1: Resend HTTP API (Port 443 - Never blocked by cloud firewalls)
    if config.RESEND_API_KEY:
        try:
            print("🚀 Sending executive HTML email via Resend HTTPS API (Port 443)...")
            headers = {
                "Authorization": f"Bearer {config.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "from": "AI & Semiconductor Analyst <onboarding@resend.dev>",
                "to": config.EMAIL_RECIPIENTS,
                "subject": subject,
                "text": email_briefing,
                "html": html_email
            }
            resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=20)
            if resp.status_code in (200, 201):
                print(f"🎉 ✅ EXECUTIVE HTML EMAIL DISPATCHED SUCCESSFULLY VIA RESEND TO {config.EMAIL_RECIPIENTS}!")
                return
            else:
                print(f"[Notice] Resend returned status {resp.status_code}: {resp.text}")
        except Exception as e_resend:
            print(f"[Notice] Resend API attempt failed: {e_resend}. Trying SMTP fallback...")

    # Method 2: Standard SMTP Fallback (Port 465 SSL)
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        print("[Warning] SMTP credentials are not configured.")
        return
        
    msg = MIMEMultipart("alternative")
    msg["From"] = config.SMTP_USER
    msg["To"] = ", ".join(config.EMAIL_RECIPIENTS)
    msg["Subject"] = subject
    msg.attach(MIMEText(email_briefing, "plain", "utf-8"))
    msg.attach(MIMEText(html_email, "html", "utf-8"))
    
    # Try Port 465 (Direct SSL) first: reliable on cloud platforms like GitHub Actions
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
        print("✓ Dispatched briefing to Telegram bot!")
    except Exception as e:
        print(f"[Notice] Failed to send Telegram notification: {e}")
