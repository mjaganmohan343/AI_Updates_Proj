"""
Delivery module: Publishes the daily briefings to GitHub Pages (docs/)
and dispatches notifications (Email / Telegram).
"""

import os
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

def generate_html_page(markdown_content: str, date_str: str) -> str:
    """
    Renders a sleek, mobile-friendly, dark-themed HTML webpage 
    for GitHub Pages using Marked.js on CDN (zero build step needed).
    """
    # Escape backticks for JS template literal
    safe_md = markdown_content.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily AI & Semiconductor Intelligence Briefing - {date_str}</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {{
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-main: #c9d1d9;
            --text-heading: #58a6ff;
            --accent-green: #3fb950;
            --accent-purple: #bc8cff;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            line-height: 1.6;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 35px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        }}
        .badge {{
            display: inline-block;
            background: linear-gradient(135deg, #1f6feb, #8957e5);
            color: white;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 20px;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        h1, h2, h3 {{
            color: var(--text-heading);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }}
        h1 {{ font-size: 2rem; color: #f0f6fc; }}
        h2 {{ font-size: 1.4rem; margin-top: 30px; color: var(--accent-purple); }}
        h3 {{ font-size: 1.15rem; color: var(--text-heading); border: none; }}
        strong {{ color: #f0f6fc; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
        a {{ color: #58a6ff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        footer {{
            text-align: center;
            margin-top: 30px;
            font-size: 0.85rem;
            color: #8b949e;
        }}
    </style>
</head>
<body>
    <div class="container">
        <span class="badge">Autonomous Intelligence Briefing</span>
        <div id="content">Loading briefing...</div>
        <footer>
            Autonomous Daily AI & Semiconductor Analyst • Generated with \$0 Cloud Pipeline
        </footer>
    </div>
    <script>
        const markdown = `{safe_md}`;
        document.getElementById('content').innerHTML = marked.parse(markdown);
    </script>
</body>
</html>
"""
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
    """Sends Section 1 executive briefing via standard SMTP (Gmail)."""
    if not config.EMAIL_ENABLED or not config.SMTP_USER or not config.SMTP_PASSWORD:
        print("[Info] Email dispatch is disabled or credentials are not configured.")
        return
        
    today_str = datetime.now().strftime("%B %d, %Y")
    subject = f"⚡ Daily AI & Semiconductor Briefing: {today_str}"
    
    msg = MIMEMultipart()
    msg["From"] = config.SMTP_USER
    msg["To"] = ", ".join(config.EMAIL_RECIPIENTS)
    msg["Subject"] = subject
    msg.attach(MIMEText(email_briefing, "plain", "utf-8"))
    
    try:
        print(f"📧 Sending email to {len(config.EMAIL_RECIPIENTS)} recipients...")
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_USER, config.EMAIL_RECIPIENTS, msg.as_string())
        server.quit()
        print("✓ Email dispatched successfully!")
    except Exception as e:
        print(f"[Error] Failed to send email: {e}")

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
