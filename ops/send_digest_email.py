"""Email the analytics digest via Resend.

The daily sweep's output used to live only in the Actions Step Summary —
a dashboard nobody opens. This step pushes it to the inbox instead:
data that doesn't reach a human isn't a feedback loop.

Env: RESEND_API_KEY (required), EMAIL_FROM (required),
     DIGEST_TO (optional, defaults to the operator's address).
Usage: python ops/send_digest_email.py digest.md
"""
import html
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

TO_DEFAULT = "m17551076169@gmail.com"


def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        sys.exit("usage: send_digest_email.py <digest.md>")
    md = open(sys.argv[1], encoding="utf-8").read()

    api_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("EMAIL_FROM")
    if not api_key or not sender:
        sys.exit("RESEND_API_KEY / EMAIL_FROM not set")
    to = os.environ.get("DIGEST_TO", TO_DEFAULT)

    # Beijing date for the subject (runner is UTC; 01:00 UTC = 09:00 CST)
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    # Surface the conversion-event count in the subject so a glance tells you
    # whether the funnel moved without even opening the mail.
    conv = md.count("🎯 **")
    subject = f"📊 数据日报 {today} · {conv} 个转化事件在动"

    body = f"""<div style="font-family:system-ui,-apple-system,sans-serif;max-width:720px">
<pre style="font-family:ui-monospace,Menlo,monospace;font-size:13px;line-height:1.55;white-space:pre-wrap">{html.escape(md)}</pre>
<p style="font-size:12px;color:#888">AgentSkillsHub · Analytics Daily Sweep ·
原始 JSON 在 GitHub Actions artifact(留 30 天)</p>
</div>"""

    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"from": sender, "to": [to], "subject": subject, "html": body},
        timeout=30,
    )
    if r.status_code >= 300:
        sys.exit(f"Resend {r.status_code}: {r.text[:300]}")
    print(f"✓ digest emailed to {to} ({subject})")


if __name__ == "__main__":
    main()
