#!/usr/bin/env python3
"""Poll Stripe for new paid checkout sessions → fulfill Pro/CI-Gate keys,
notify operator + buyer via Resend, and create deduped GitHub delivery issues.

Runs on GitHub Actions cron (every 30 min). Idempotent: dedupes against
existing GitHub issues labeled `order` that contain the session id, and
`issue_pro_key` itself dedupes on `p_order_id = session["id"]`.

Supported client_reference_id prefixes:
  - `pro--...`        → Pro Deep Search membership (`$29/yr` / `$49/yr`)
  - `cigate--...`     → Team CI Skill Gate (`$49/mo` + bundled Team `ash_pro_` key)
  - `fasttrack--...`  → 48h Fast-Track Security Review (`$49`)
The Stripe account is shared with other products, so a session is only handled
when it comes from one of PAYMENT_LINK_SKUS, carries metadata
source=agentskillshub, or has one of the prefixes above. Everything else is skipped.

Env:
  STRIPE_RESTRICTED_KEY       restricted key, read-only on Checkout Sessions and Subscriptions
  RESEND_API_KEY / EMAIL_FROM notification & buyer delivery email
  GITHUB_TOKEN / GITHUB_REPOSITORY  issue creation (provided by Actions)
  ALERT_EMAIL                 where to send operator alerts
  VITE_SUPABASE_URL / AGENTSKILLSHUB_SUPABASE_URL  for issue_pro_key RPC
  VITE_SUPABASE_ANON_KEY / AGENTSKILLSHUB_ANON_KEY for issue_pro_key RPC
  AGENTSKILLSHUB_ISSUE_SECRET shared secret for issue_pro_key RPC

Privacy: customer email and plaintext `ash_pro_` keys go ONLY into private
emails, NEVER into the public GitHub issue (this repository is public).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from html import escape
from urllib.parse import urlencode
import os
import sys
import time
import urllib.error
import urllib.request

STRIPE_KEY = os.environ.get("STRIPE_RESTRICTED_KEY", "")
RESEND_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "m17551076169@gmail.com")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO = os.environ.get("GITHUB_REPOSITORY", "zhuyansen/agent-skills-hub")

POSTHOG_PROJECT_KEY = os.environ.get(
    "POSTHOG_PROJECT_KEY", "phc_wCjMwyvaJQAHodWWKMeBWxoCmwo8puNJdyxKtomET8j5"
).strip()
POSTHOG_CAPTURE_URL = os.environ.get(
    "POSTHOG_CAPTURE_URL", "https://us.i.posthog.com/capture/"
).strip()
SUMMARY_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "summary.json")

SUPABASE_URL = (
    os.environ.get("AGENTSKILLSHUB_SUPABASE_URL")
    or os.environ.get("VITE_SUPABASE_URL")
    or ""
).rstrip("/")
SUPABASE_ANON_KEY = (
    os.environ.get("AGENTSKILLSHUB_ANON_KEY")
    or os.environ.get("VITE_SUPABASE_ANON_KEY")
    or ""
)
ISSUE_SECRET = os.environ.get("AGENTSKILLSHUB_ISSUE_SECRET", "")

LOOKBACK_SECONDS = int(os.environ.get("LOOKBACK_HOURS") or 48) * 3600
# Orders younger than this belong to the Stripe webhook (supabase/functions/stripe-fulfill),
# which fulfils within seconds; this poll is the fallback. Same value as its
# WEBHOOK_WINDOW_SECONDS. Acting sooner, both could record the same order at once.
WEBHOOK_WINDOW_SECONDS = 600
SESSION_PAGE = 100
GRACE_SECONDS = 3 * 24 * 3600
EARLY_BIRD_LIMIT = 100
EARLY_BIRD_LINK = "plink_1UchmqC0OZ4h2np2kGFSR5Qr"
EARLY_BIRD_SOLD = 0

# Live Payment Links created 2026-11-17 (each also carries metadata source=agentskillshub + sku).
PAYMENT_LINK_SKUS = {
    "plink_1Uci7YC0OZ4h2np2hIc1ZLGo": "pro",  # $49/yr standard
    "plink_1UchmqC0OZ4h2np2kGFSR5Qr": "pro",  # $29/yr early bird
    "plink_1UchmwC0OZ4h2np2J1kAJkOW": "fasttrack",  # $49 one-time
    "plink_1UchmyC0OZ4h2np253XNPeHj": "cigate",  # $49/mo
}


def http_json(url: str, headers: dict[str, str], data: bytes | None = None, method: str = "GET"):
    headers = {"User-Agent": "AgentSkillsHub/1.0", **headers}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw.strip() else {}


def stripe_sessions() -> list[dict]:
    # Include old sessions: renewals/cancellations must still update old keys.
    params = {"limit": SESSION_PAGE, "status": "complete", "expand[]": "data.subscription"}
    sessions = []
    while True:
        out = http_json("https://api.stripe.com/v1/checkout/sessions?" + urlencode(params),
                        {"Authorization": f"Bearer {STRIPE_KEY}"})
        page = out.get("data", [])
        sessions.extend(s for s in page if s.get("payment_status") == "paid")
        if not out.get("has_more"):
            return sessions
        if not page:
            raise RuntimeError("Stripe returned an empty page with has_more")
        params["starting_after"] = page[-1]["id"]


def subscription_expiry(sub: dict) -> str:
    status = sub.get("status")
    items = (sub.get("items") or {}).get("data") or [sub]
    starts = [i.get("current_period_start") or sub.get("current_period_start") for i in items]
    ends = [i.get("current_period_end") or sub.get("current_period_end") for i in items]
    if status in {"canceled", "unpaid", "incomplete_expired", "paused", "incomplete"}:
        stamp = sub.get("ended_at") or int(time.time())
    elif status == "past_due" and all(starts):
        stamp = min(starts) + GRACE_SECONDS
    elif status in {"active", "trialing"} and all(ends):
        stamp = min(ends) + (0 if sub.get("cancel_at_period_end") else GRACE_SECONDS)
        if sub.get("cancel_at"):
            stamp = min(stamp, sub["cancel_at"])
    else:
        raise ValueError("Missing subscription period or unsupported status")
    return datetime.fromtimestamp(stamp, timezone.utc).isoformat()


def sync_subscriptions(sessions: list[dict]) -> None:
    items = []
    for session in sessions:
        if not classify_session(session) or session.get("mode") != "subscription":
            continue
        sub = session.get("subscription")
        if not isinstance(sub, dict):
            raise ValueError("Subscription expansion missing; check Stripe read permissions")
        items.append({"order_id": session["id"], "expires_at": subscription_expiry(sub)})
    for offset in range(0, len(items), 1000):
        out = http_json(f"{SUPABASE_URL}/rest/v1/rpc/sync_member_key_expiry",
                        {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                         "Content-Type": "application/json"},
                        json.dumps({"p_secret": ISSUE_SECRET, "p_items": items[offset:offset + 1000]}).encode(), "POST")
        if out.get("status") != "ok":
            raise RuntimeError("Subscription sync failed")
        print(f"Subscription sync: {out['received']} checked, {out['updated']} updated.")


def existing_order_ids() -> set[str]:
    url = (
        f"https://api.github.com/repos/{GH_REPO}/issues"
        "?labels=order&state=all&per_page=100"
    )
    issues = []
    page = 1
    while True:
        batch = http_json(url + f"&page={page}",
                          {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"})
        issues.extend(batch)
        if len(batch) < SESSION_PAGE:
            break
        page += 1
    ids: set[str] = set()
    for issue in issues:
        body = issue.get("body") or ""
        for token in body.split():
            cleaned = token.strip("`.,;:")
            if cleaned.startswith("cs_"):
                ids.add(cleaned)
    return ids


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "(none)"
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


def split_client_ref(raw_ref: str) -> tuple[str, str]:
    """Extract (clean_ref, posthog_distinct_id) from client_reference_id."""
    ref = (raw_ref or "").strip()
    if "__ph_" in ref:
        base, ph_id = ref.split("__ph_", 1)
        return base.strip(), ph_id.strip()
    return ref, ""


def is_ours(session: dict) -> bool:
    """The Stripe account also sells other products; only fulfill sessions that are provably ours."""
    meta = session.get("metadata") or {}
    ref, _ = split_client_ref(session.get("client_reference_id") or "")
    return (
        session.get("payment_link") in PAYMENT_LINK_SKUS
        or meta.get("source") == "agentskillshub"
        or ref.startswith(("pro--", "cigate--", "fasttrack--"))
    )


def classify_session(session: dict) -> tuple[str, str] | None:
    """Return (sku, target_label) from metadata / client_reference_id / payment link.

    Returns None for sessions that belong to other products on the same account.
    """
    if not is_ours(session):
        return None
    meta = session.get("metadata") or {}
    ref, _ = split_client_ref(session.get("client_reference_id") or "")
    meta_sku = str(meta.get("sku") or "").lower()

    if meta_sku in {"pro", "fasttrack", "cigate", "deep_audit"}:
        sku = meta_sku
        target = ref.split("--", 1)[1].replace("--", "/") if "--" in ref else (ref or "(self-serve)")
        return sku, target

    if ref.startswith("pro--"):
        target = ref.removeprefix("pro--").replace("--", "/") or "pro-member"
        return "pro", target
    if ref.startswith("cigate--"):
        target = ref.removeprefix("cigate--").replace("--", "/") or "team-ci-gate"
        return "cigate", target
    if ref.startswith("fasttrack--"):
        target = ref.removeprefix("fasttrack--").replace("--", "/") or "(not provided)"
        return "fasttrack", target

    link_sku = PAYMENT_LINK_SKUS.get(session.get("payment_link") or "")
    if link_sku:
        defaults = {"pro": "pro-member", "cigate": "team-ci-gate", "fasttrack": "(not provided)"}
        return link_sku, ref.replace("--", "/") if ref else defaults[link_sku]
    return None


def issue_member_key(session: dict, sku: str, buyer_email: str) -> dict | None:
    """Call Supabase `issue_pro_key` RPC for `pro` or `cigate` purchases."""
    if sku not in {"pro", "cigate"}:
        return None
    if not (SUPABASE_URL and SUPABASE_ANON_KEY and ISSUE_SECRET and buyer_email and "@" in buyer_email):
        return None

    amount_cents = session.get("amount_total") or 0
    if sku == "cigate":
        note = "cigate-team-49"
    elif session.get("payment_link") == EARLY_BIRD_LINK or (
        not session.get("payment_link") and amount_cents <= 3000
    ):
        note = "pro-usd-29"
    else:
        note = "pro-usd-49"

    payload = json.dumps({
        "p_secret": ISSUE_SECRET,
        "p_email": buyer_email,
        "p_note": note,
        "p_order_id": session["id"],
    }).encode()
    try:
        return http_json(
            f"{SUPABASE_URL}/rest/v1/rpc/issue_pro_key",
            {
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                "Content-Type": "application/json",
            },
            data=payload,
            method="POST",
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"WARNING: issue_pro_key RPC failed for {session['id']}: {type(exc).__name__}")
        return {"status": "rpc_error", "error": type(exc).__name__}


def send_buyer_key_email(buyer_email: str, sku: str, issued_key: str) -> bool:
    if not (RESEND_KEY and EMAIL_FROM and buyer_email and "@" in buyer_email and issued_key):
        return False
    is_cigate = sku == "cigate"
    subject = (
        "Your Agent Skills Hub Team CI Gate + Pro Key (`ash_pro_...`)"
        if is_cigate
        else "Your Agent Skills Hub Pro Access Key"
    )
    setup_block = (
        "<p><b>CI Skill Gate workflow</b>: copy the GitHub Action from "
        '<a href="https://agentskillshub.top/ci-gate/">https://agentskillshub.top/ci-gate/</a> '
        "and store this key as <code>ASH_GATE_KEY</code> in your repo secrets.</p>"
        if is_cigate
        else "<p><b>Activate Pro Deep Search</b>: open "
        '<a href="https://agentskillshub.top/pro/">https://agentskillshub.top/pro/</a> '
        "and paste the key above (also works via <code>npx @agentskillshub/cli</code>).</p>"
    )
    html = (
        f"<div><h2>Thank you for supporting Agent Skills Hub</h2>"
        f"<p>Your access key is ready:</p>"
        f"<pre style='padding:12px;background:#f1f5f9;border-radius:8px;font-size:14px'>{issued_key}</pre>"
        f"{setup_block}"
        f"<p style='color:#64748b;font-size:12px'>Need help or a team invoice? Reply directly to this email.</p></div>"
    )
    payload = json.dumps({
        "from": EMAIL_FROM,
        "to": [buyer_email],
        "subject": subject,
        "html": html,
    }).encode()
    try:
        http_json(
            "https://api.resend.com/emails",
            {"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"},
            data=payload,
            method="POST",
        )
        return True
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"WARNING: failed to email buyer key: {type(exc).__name__}")
        return False


def create_issue(session: dict, sku: str, target: str, key_status: str) -> str:
    amount = (session.get("amount_total") or 0) / 100
    currency = (session.get("currency") or "usd").upper()
    customer_email = (session.get("customer_details") or {}).get("email", "")

    titles = {
        "pro": f"⚡ Pro Membership — {target}",
        "cigate": f"🛡️ Team CI Skill Gate — {target}",
        "fasttrack": f"🚀 48h Fast-Track Review — {target}",
        "deep_audit": f"💰 Deep Audit order — {target}",
    }
    checklists = {
        "pro": (
            "- [ ] Confirm `ash_pro_` key delivered to buyer email\n"
            "- [ ] Close this issue\n"
        ),
        "cigate": (
            "- [ ] Confirm Team `ash_pro_` key delivered\n"
            "- [ ] Send CI Gate onboarding / allowlist review check-in\n"
            "- [ ] Close this issue\n"
        ),
        "fasttrack": (
            f"- [ ] Run full manual + static review on `{target}` within 48h\n"
            "- [ ] Update catalog grade/notes if verified safe/fixed\n"
            "- [ ] Email 48h Fast-Track report to submitter\n"
            "- [ ] Close this issue\n"
        ),
        "deep_audit": (
            f"- [ ] Run deep audit on `{target}`\n"
            "- [ ] Write report\n"
            "- [ ] Send report to customer\n"
            "- [ ] Close this issue\n"
        ),
    }

    body = (
        f"New paid `{sku}` order.\n\n"
        f"- **SKU**: `{sku}`\n"
        f"- **Target**: `{target}`\n"
        f"- **Amount**: {amount:.2f} {currency}\n"
        f"- **Customer**: {mask_email(customer_email)}"
        f" (full details in the alert email / Stripe dashboard)\n"
        f"- **Auto key fulfillment**: `{key_status}`\n"
        f"- **Session**: `{session['id']}`\n\n"
        f"Delivery checklist:\n"
        f"{checklists[sku]}"
    )
    payload = json.dumps({
        "title": titles[sku],
        "body": body,
        "labels": ["order"],
    }).encode()
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


def send_alert(session: dict, sku: str, target: str, issue_url: str, key_status: str) -> None:
    if not (RESEND_KEY and EMAIL_FROM):
        raise RuntimeError("Operator email configuration missing")
    amount = (session.get("amount_total") or 0) / 100
    email = (session.get("customer_details") or {}).get("email", "(none)")
    currency = (session.get("currency") or "usd").upper()
    target, email, key_status = map(escape, (target, email, key_status))
    html = (
        f'<div lang="zh"><h2>💰 有人付款了!{amount:.2f} {currency}（{sku}）</h2>'
        f"<p><b>目标/团队</b>:{target}<br>"
        f"<b>客户邮箱</b>:{email}<br>"
        f"<b>自动发码状态</b>:{key_status}<br>"
        f"<b>Session</b>:{session['id']}</p>"
        f'<p>订单详情:<a href="{issue_url}">{issue_url}</a></p>'
        f"<p>美元早鸟已售：{EARLY_BIRD_SOLD}/{EARLY_BIRD_LIMIT}。</p>"
        f"<p>按工单 checklist 交付即可。</p></div>"
    )
    payload = json.dumps({
        "from": EMAIL_FROM,
        "to": [ALERT_EMAIL],
        "subject": f"💰 {amount:.2f} {currency} [{sku}] 成交:{target}",
        "html": html,
    }).encode()
    http_json(
        "https://api.resend.com/emails",
        {"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"},
        data=payload,
        method="POST",
    )


def send_posthog_purchase(session: dict, sku: str) -> bool:
    """Server-to-server PostHog `purchase_completed` event (no PII).

    Only Stripe live-mode sessions count as revenue. A unit-test fixture or a test-mode
    checkout has no `livemode: true`; before this check, every local run of
    test_poll_stripe.py posted a $0 `cs_test` purchase to the production project.
    PostHog does not deduplicate on `$insert_id` (the 12 `cs_test` events all stayed),
    so the caller must send this once per order; see process_session.
    """
    if session.get("livemode") is not True:
        return False
    if not (POSTHOG_PROJECT_KEY and POSTHOG_CAPTURE_URL):
        return False
    _, ph_id = split_client_ref(session.get("client_reference_id") or "")
    distinct_id = ph_id or ("stripe_" + hashlib.sha256(session["id"].encode()).hexdigest()[:16])
    amount_cents = int(session.get("amount_total") or 0)
    created_ts = int(session.get("created") or time.time())
    iso_ts = datetime.fromtimestamp(created_ts, timezone.utc).isoformat()
    payload = {
        "api_key": POSTHOG_PROJECT_KEY,
        "event": "purchase_completed",
        "distinct_id": distinct_id,
        "timestamp": iso_ts,
        "properties": {
            "sku": sku,
            "revenue": round(amount_cents / 100, 2),
            "amount_cents": amount_cents,
            "currency": (session.get("currency") or "usd").upper(),
            "is_early_bird": session.get("payment_link") == EARLY_BIRD_LINK,
            "attributed_to_session": bool(ph_id),
            "source": "stripe_s2s",
            # Sent from a GitHub runner: PostHog would place every purchase at the runner (it
            # put the first early-bird buyer, in the UK, in the United States).
            "$geoip_disable": True,
            "$insert_id": session["id"],
        },
    }
    try:
        http_json(
            POSTHOG_CAPTURE_URL,
            {"Content-Type": "application/json"},
            data=json.dumps(payload).encode(),
            method="POST",
        )
        return True
    except Exception as exc:  # best-effort: the order is already recorded and must not be retried
        print(f"WARNING: PostHog S2S capture failed for {session['id']}: {type(exc).__name__}")
        return False


def write_summary(sessions: list[dict]) -> dict:
    """Write strictly aggregate, zero-PII Stripe order & revenue summary for analytics_digest.py."""
    now = int(time.time())
    cut_7d = now - 7 * 86400
    cut_28d = now - 28 * 86400
    by_sku: dict[str, dict] = {}
    tot_orders = 0
    tot_cents = 0
    orders_7d = 0
    cents_7d = 0
    orders_28d = 0
    cents_28d = 0
    attributed_28d = 0

    for s in sessions:
        classified = classify_session(s)
        if not classified:
            continue
        sku, _ = classified
        cents = int(s.get("amount_total") or 0)
        created = int(s.get("created") or 0)
        _, ph_id = split_client_ref(s.get("client_reference_id") or "")

        row = by_sku.setdefault(
            sku,
            {"orders_all": 0, "revenue_all_usd": 0.0, "orders_28d": 0, "revenue_28d_usd": 0.0},
        )
        row["orders_all"] += 1
        row["revenue_all_usd"] = round(row["revenue_all_usd"] + cents / 100, 2)
        tot_orders += 1
        tot_cents += cents

        if created >= cut_28d:
            orders_28d += 1
            cents_28d += cents
            row["orders_28d"] += 1
            row["revenue_28d_usd"] = round(row["revenue_28d_usd"] + cents / 100, 2)
            if ph_id:
                attributed_28d += 1
        if created >= cut_7d:
            orders_7d += 1
            cents_7d += cents

    summary = {
        "generated_at": datetime.fromtimestamp(now, timezone.utc).isoformat(),
        "total_orders": tot_orders,
        "total_revenue_usd": round(tot_cents / 100, 2),
        "orders_7d": orders_7d,
        "revenue_7d_usd": round(cents_7d / 100, 2),
        "orders_28d": orders_28d,
        "revenue_28d_usd": round(cents_28d / 100, 2),
        "attributed_28d": attributed_28d,
        "early_bird_sold": sum(s.get("payment_link") == EARLY_BIRD_LINK for s in sessions),
        "early_bird_limit": EARLY_BIRD_LIMIT,
        "by_sku": by_sku,
    }
    os.makedirs(os.path.dirname(SUMMARY_OUT), exist_ok=True)
    with open(SUMMARY_OUT, "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    return summary


def process_session(session: dict) -> str:
    sku, target = classify_session(session)
    buyer_email = (session.get("customer_details") or {}).get("email", "")
    key_res = issue_member_key(session, sku, buyer_email)

    key_status = "n/a"
    if isinstance(key_res, dict):
        status = key_res.get("status", "unknown")
        raw_key = key_res.get("key") or ""
        if status == "issued" and raw_key:
            sent = send_buyer_key_email(buyer_email, sku, raw_key)
            key_status = "issued_and_emailed" if sent else "issued_manual_email_needed"
        else:
            key_status = str(status)
    elif sku in {"pro", "cigate"}:
        key_status = "pending_manual_issue"

    sync_subscriptions([session])
    send_alert(session, sku, target, "https://dashboard.stripe.com/payments", key_status)
    issue_url = create_issue(session, sku, target, key_status)
    # The issue marks the order done (main() skips sessions that have one). Sent before
    # it, a failed alert or issue made every 30-min retry report the purchase again.
    send_posthog_purchase(session, sku)
    return issue_url


def send_test_notification() -> int:
    if not (RESEND_KEY and EMAIL_FROM):
        raise RuntimeError("Operator email configuration missing")
    payload = {"from": EMAIL_FROM, "to": [ALERT_EMAIL],
               "subject": "【测试】Agent Skills Hub Stripe 收款通知已启用",
               "html": "<p>这是一封通知通道测试邮件，没有产生扣款或订单。</p>"
                       "<p>订单提醒每 30 分钟检查一次，包含金额、产品、发码状态和早鸟销量。</p>"}
    out = http_json("https://api.resend.com/emails",
                    {"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"},
                    json.dumps(payload).encode(), "POST")
    if not out.get("id"):
        raise RuntimeError("Resend did not acknowledge test notification")
    print("Test notification accepted by Resend (no charge or order created).")
    return 0


def pending_orders(sessions: list[dict], seen: set[str], cutoff: int, newest: int) -> list[dict]:
    """Paid sessions with no order issue yet, from the lookback window, leaving the webhook its window."""
    return [s for s in sessions if s["id"] not in seen and cutoff <= s.get("created", 0) <= newest]


def main() -> int:
    global EARLY_BIRD_SOLD
    if not STRIPE_KEY:
        if "--summary-only" in sys.argv:
            print("STRIPE_RESTRICTED_KEY 未设置，跳过 Stripe 汇总。")
            return 0
        raise RuntimeError("STRIPE_RESTRICTED_KEY not set")
    paid = stripe_sessions()
    sessions = [s for s in paid if classify_session(s)]
    EARLY_BIRD_SOLD = sum(s.get("payment_link") == EARLY_BIRD_LINK for s in sessions)
    summary = write_summary(sessions)
    if "--summary-only" in sys.argv:
        print(
            f"Stripe summary: 28d={summary['orders_28d']} orders (${summary['revenue_28d_usd']:.2f}), "
            f"early_bird={summary['early_bird_sold']}/{EARLY_BIRD_LIMIT}."
        )
        return 0
    sync_subscriptions(sessions)
    seen = existing_order_ids() if sessions else set()
    cutoff = int(time.time()) - LOOKBACK_SECONDS
    new = pending_orders(sessions, seen, cutoff, int(time.time()) - WEBHOOK_WINDOW_SECONDS)
    for session in new:
        issue_url = process_session(session)
        print(f"NEW ORDER: {session['id']} → {issue_url}")
    print(f"Orders: {len(new)} new; early bird: {EARLY_BIRD_SOLD}/{EARLY_BIRD_LIMIT}.")
    return 0


if __name__ == "__main__":
    sys.exit(send_test_notification() if "--test-notification" in sys.argv else main())
