"""Email the analytics digest via Resend.

The daily sweep's output used to live only in the Actions Step Summary —
a dashboard nobody opens. This step pushes it to the inbox instead:
data that doesn't reach a human isn't a feedback loop.

The optional second file is the private lead list from ops/new_leads.py. It
goes first in the body and into the subject, and nowhere else: unlike the
digest it never reaches the public Step Summary.

Env: RESEND_API_KEY (required), EMAIL_FROM (required),
     DIGEST_TO (optional, defaults to the operator's address).
Usage: python ops/send_digest_email.py digest.md [leads.md]
"""
import html
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

TO_DEFAULT = "m17551076169@gmail.com"
# The heading ops/new_leads.py opens its file with: new leads, or a failed check.
LEADS_FLAG = re.compile(r"## (🔔 新留资 \d+ 条|⚠️ 新留资没查成)")
# new_leads.py always writes its file (empty when there are no leads), so a
# missing one means it died before writing, e.g. on an import error.
LEADS_MISSING = "## ⚠️ 新留资没查成(见 Actions 日志)\n"


def read_leads(path):
    """The lead list; "" when the check found none, a warning when it never ran."""
    if not path:
        return ""
    if not os.path.exists(path):
        return LEADS_MISSING
    return open(path, encoding="utf-8").read()


def subject_for(md, leads, today):
    # Surface the conversion-event count in the subject so a glance tells you
    # whether the funnel moved without even opening the mail. If a source fetch
    # failed (banner present), a "0" would be a lie — flag the outage instead
    # of reporting a false all-clear (07-12 GA-token-expiry scar).
    if "⚠️ **数据源未出数" in md:
        subject = f"📊 数据日报 {today} · ⚠️ 数据源故障(见正文)"
    else:
        conv = md.count("🎯 **")
        subject = f"📊 数据日报 {today} · {conv} 个转化事件在动"
    # A lead waiting for a reply outranks everything else in the mail.
    flag = LEADS_FLAG.match(leads)
    return f"{flag.group(1)} · {subject}" if flag else subject


def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        sys.exit("usage: send_digest_email.py <digest.md> [leads.md]")
    md = open(sys.argv[1], encoding="utf-8").read()
    leads = read_leads(sys.argv[2] if len(sys.argv) > 2 else "")

    api_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("EMAIL_FROM")
    if not api_key or not sender:
        sys.exit("RESEND_API_KEY / EMAIL_FROM not set")
    to = os.environ.get("DIGEST_TO", TO_DEFAULT)

    # Beijing date for the subject (runner is UTC; 01:00 UTC = 09:00 CST)
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    subject = subject_for(md, leads, today)
    text = f"{leads}\n{md}" if leads else md

    # lang="zh" stops Gmail's "this email appears to be in English" banner
    body = f"""<div lang="zh" style="font-family:system-ui,-apple-system,sans-serif;max-width:720px">
<pre style="font-family:ui-monospace,Menlo,monospace;font-size:13px;line-height:1.55;white-space:pre-wrap">{html.escape(text)}</pre>
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
    # Log Resend's email id so a lost message can be traced in their dashboard
    rid = ""
    try:
        rid = r.json().get("id", "")
    except ValueError:
        pass
    print(f"✓ digest emailed to {to} ({subject}) resend_id={rid}")


if __name__ == "__main__":
    main()
