"""Mail a radar report (markdown) through Resend, the project's mail provider.

  python ops/radar/notify.py <report.md> <subject>

Env: RESEND_API_KEY and EMAIL_FROM (the newsletter's own), RADAR_EMAIL_TO (who reads the
radar; comma-separated for several). Without RADAR_EMAIL_TO it prints why and exits 0:
a missing recipient must not fail the run that produced the report.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import markdown

STYLE = ("<style>body{font:14px/1.6 -apple-system,'PingFang SC',sans-serif;color:#1f2328;max-width:900px}"
         "table{border-collapse:collapse;margin:8px 0}th,td{border:1px solid #d0d7de;padding:4px 8px;"
         "font-size:13px;vertical-align:top}th{background:#f6f8fa}h2{font-size:18px}h3{font-size:15px;"
         "margin-top:22px}</style>")


def html(md_text: str) -> str:
    return STYLE + markdown.markdown(md_text, extensions=["tables"])


def send(subject: str, md_text: str) -> str:
    to = [a.strip() for a in os.environ.get("RADAR_EMAIL_TO", "").split(",") if a.strip()]
    if not to:
        return "skipped: RADAR_EMAIL_TO not set"
    body = json.dumps({"from": os.environ["EMAIL_FROM"], "to": to, "subject": subject,
                       "html": html(md_text)}).encode()
    # Resend sits behind Cloudflare, which answers Python's default User-Agent with 403
    # "error code: 1010": every radar mail failed that way until 2026-10-06.
    req = urllib.request.Request("https://api.resend.com/emails", data=body, method="POST", headers={
        "Authorization": f"Bearer {os.environ['RESEND_API_KEY']}", "Content-Type": "application/json",
        "User-Agent": "agentskillshub-radar/1.0 (+https://agentskillshub.top)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return f"sent ({res.status})"
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Resend {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}") from exc


def main() -> int:
    report, subject = Path(sys.argv[1]), sys.argv[2]
    print(send(subject, report.read_text()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
