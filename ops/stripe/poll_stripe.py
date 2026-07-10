#!/usr/bin/env python3
"""Poll Stripe for new paid checkout sessions → email alert + GitHub delivery issue.

Runs on GitHub Actions cron (every 30 min). Idempotent: dedupes against
existing GitHub issues labeled `order` that contain the session id.

Env:
  STRIPE_RESTRICTED_KEY  restricted key, read-only on Checkout Sessions (rk_live_...)
  RESEND_API_KEY / EMAIL_FROM  notification email
  GITHUB_TOKEN / GITHUB_REPOSITORY  issue creation (provided by Actions)
  ALERT_EMAIL  where to send the alert (default owner's gmail)

Privacy: customer email goes ONLY into the private alert email, never into
the public GitHub issue (repo is public).
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

STRIPE_KEY = os.environ.get("STRIPE_RESTRICTED_KEY", "")
RESEND_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "m17551076169@gmail.com")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO = os.environ.get("GITHUB_REPOSITORY", "zhuyansen/agent-skills-hub")
LOOKBACK_SECONDS = 3 * 3600  # overlap window; dedupe makes re-reads harmless


def http_json(url: str, headers: dict, data: bytes | None = None, method: str = "GET"):
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def stripe_sessions() -> list[dict]:
    since = int(time.time()) - LOOKBACK_SECONDS
    url = (
        "https://api.stripe.com/v1/checkout/sessions?limit=20&status=complete"
        f"&created[gte]={since}"
    )
    out = http_json(url, {"Authorization": f"Bearer {STRIPE_KEY}"})
    return [s for s in out.get("data", []) if s.get("payment_status") == "paid"]


def existing_order_ids() -> set[str]:
    url = (
        f"https://api.github.com/repos/{GH_REPO}/issues"
        "?labels=order&state=all&per_page=100"
    )
    issues = http_json(
        url,
        {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"},
    )
    ids: set[str] = set()
    for issue in issues:
        body = issue.get("body") or ""
        for token in body.split():
            if token.startswith("cs_"):
                ids.add(token.strip("`"))
    return ids


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "(none)"
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


def decode_repo(client_reference_id: str | None) -> str:
    if not client_reference_id:
        return "(not provided)"
    return client_reference_id.replace("--", "/")


def create_issue(session: dict, repo_slug: str) -> str:
    amount = (session.get("amount_total") or 0) / 100
    currency = (session.get("currency") or "usd").upper()
    body = (
        f"New paid deep-audit order.\n\n"
        f"- **Target repo**: `{repo_slug}`\n"
        f"- **Amount**: {amount:.2f} {currency}\n"
        f"- **Customer**: {mask_email((session.get('customer_details') or {}).get('email', ''))}"
        f" (full details in the alert email / Stripe dashboard)\n"
        f"- **Session**: `{session['id']}`\n\n"
        f"Delivery checklist:\n"
        f"- [ ] Run deep audit on `{repo_slug}`\n"
        f"- [ ] Write report\n"
        f"- [ ] Send report to customer\n"
        f"- [ ] Close this issue\n"
    )
    payload = json.dumps(
        {
            "title": f"💰 Deep Audit order — {repo_slug}",
            "body": body,
            "labels": ["order"],
        }
    ).encode()
    out = http_json(
        f"https://api.github.com/repos/{GH_REPO}/issues",
        {
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
        data=payload,
        method="POST",
    )
    return out.get("html_url", "")


def send_alert(session: dict, repo_slug: str, issue_url: str) -> None:
    if not (RESEND_KEY and EMAIL_FROM):
        return
    amount = (session.get("amount_total") or 0) / 100
    email = (session.get("customer_details") or {}).get("email", "(none)")
    html = (
        f'<div lang="zh"><h2>💰 有人付款了!${amount:.2f}</h2>'
        f"<p><b>目标仓库</b>:{repo_slug}<br>"
        f"<b>客户邮箱</b>:{email}<br>"
        f"<b>Session</b>:{session['id']}</p>"
        f'<p>交付工单:<a href="{issue_url}">{issue_url}</a></p>'
        f"<p>按工单 checklist 交付即可。</p></div>"
    )
    payload = json.dumps(
        {
            "from": EMAIL_FROM,
            "to": [ALERT_EMAIL],
            "subject": f"💰 $49 成交:{repo_slug}",
            "html": html,
        }
    ).encode()
    http_json(
        "https://api.resend.com/emails",
        {"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"},
        data=payload,
        method="POST",
    )


def main() -> int:
    if not STRIPE_KEY:
        print("STRIPE_RESTRICTED_KEY not set — skipping (add the secret to activate).")
        return 0
    sessions = stripe_sessions()
    if not sessions:
        print("No paid sessions in lookback window.")
        return 0
    seen = existing_order_ids()
    new = [s for s in sessions if s["id"] not in seen]
    if not new:
        print(f"{len(sessions)} paid session(s), all already ticketed.")
        return 0
    for session in new:
        repo_slug = decode_repo(session.get("client_reference_id"))
        issue_url = create_issue(session, repo_slug)
        send_alert(session, repo_slug, issue_url)
        print(f"NEW ORDER: {session['id']} → {issue_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
