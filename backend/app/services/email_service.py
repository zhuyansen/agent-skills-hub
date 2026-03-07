"""Email service: send verification & newsletter emails via Resend or BillionMail."""

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ── HTML Templates ──

def _verification_email_html(verify_url: str) -> str:
    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <tr><td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:32px 40px;text-align:center;">
    <h1 style="color:#fff;margin:0;font-size:24px;">🤖 Agent Skills Hub</h1>
    <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px;">Discover Agent Skills, Tools & MCP Servers</p>
  </td></tr>
  <tr><td style="padding:40px;">
    <h2 style="color:#1a1a2e;margin:0 0 16px;font-size:20px;">Confirm your subscription</h2>
    <p style="color:#4a5568;line-height:1.6;margin:0 0 24px;">
      Thanks for subscribing to the Agent Skills Hub weekly newsletter!
      Click the button below to verify your email address and start receiving updates.
    </p>
    <table cellpadding="0" cellspacing="0" style="margin:0 auto 24px;">
    <tr><td style="background:#4f46e5;border-radius:8px;">
      <a href="{verify_url}" style="display:inline-block;padding:14px 32px;color:#fff;text-decoration:none;font-weight:600;font-size:16px;">
        ✅ Verify Email Address
      </a>
    </td></tr>
    </table>
    <p style="color:#718096;font-size:13px;line-height:1.5;">
      If you didn't subscribe, you can safely ignore this email.
    </p>
  </td></tr>
  <tr><td style="background:#f8fafc;padding:20px 40px;text-align:center;border-top:1px solid #e2e8f0;">
    <p style="color:#a0aec0;font-size:12px;margin:0;">
      Agent Skills Hub · Auto-updated every 8 hours · <a href="{settings.site_url}" style="color:#4f46e5;">Visit Site</a>
    </p>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def _newsletter_email_html(
    trending_skills: list,
    new_skills_count: int,
    total_skills: int,
    unsubscribe_url: str = "",
) -> str:
    """Generate a weekly newsletter HTML email."""

    # Build trending section
    trending_rows = ""
    for i, skill in enumerate(trending_skills[:10]):
        name = skill.get("repo_name", "unknown")
        desc = skill.get("description", "")[:120]
        stars = skill.get("stars", 0)
        url = skill.get("repo_url", "#")
        score = skill.get("score", 0)
        category = skill.get("category", "tool")
        momentum = skill.get("star_momentum", 0)

        badge_color = "#10b981" if momentum > 0.6 else "#f59e0b" if momentum > 0.4 else "#6b7280"
        trending_rows += f"""\
    <tr>
      <td style="padding:14px 16px;border-bottom:1px solid #f1f5f9;">
        <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:28px;vertical-align:top;padding-top:2px;">
            <span style="display:inline-block;width:24px;height:24px;background:#eef2ff;color:#4f46e5;border-radius:50%;text-align:center;line-height:24px;font-size:12px;font-weight:600;">{i+1}</span>
          </td>
          <td style="padding-left:12px;">
            <a href="{url}" style="color:#1e293b;font-weight:600;text-decoration:none;font-size:15px;">{name}</a>
            <span style="display:inline-block;padding:2px 8px;background:{badge_color}20;color:{badge_color};border-radius:10px;font-size:11px;margin-left:6px;">{category}</span>
            <p style="color:#64748b;font-size:13px;margin:4px 0 0;line-height:1.4;">{desc}</p>
          </td>
          <td style="width:80px;text-align:right;vertical-align:top;">
            <span style="color:#f59e0b;font-size:13px;">⭐ {stars:,}</span><br>
            <span style="color:#94a3b8;font-size:11px;">Score: {score}</span>
          </td>
        </tr>
        </table>
      </td>
    </tr>"""

    unsub_section = ""
    if unsubscribe_url:
        unsub_section = f'<a href="{unsubscribe_url}" style="color:#94a3b8;">Unsubscribe</a> · '

    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:32px 40px;text-align:center;">
    <h1 style="color:#fff;margin:0;font-size:24px;">🤖 Agent Skills Hub Weekly</h1>
    <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px;">Your weekly digest of trending Agent Skills</p>
  </td></tr>

  <!-- Stats bar -->
  <tr><td style="padding:20px 40px;background:#f8fafc;border-bottom:1px solid #e2e8f0;">
    <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td style="text-align:center;width:33%;">
        <span style="font-size:24px;font-weight:700;color:#4f46e5;">{total_skills:,}</span><br>
        <span style="font-size:12px;color:#94a3b8;">Total Skills</span>
      </td>
      <td style="text-align:center;width:33%;">
        <span style="font-size:24px;font-weight:700;color:#10b981;">+{new_skills_count}</span><br>
        <span style="font-size:12px;color:#94a3b8;">New This Week</span>
      </td>
      <td style="text-align:center;width:33%;">
        <span style="font-size:24px;font-weight:700;color:#f59e0b;">🔥</span><br>
        <span style="font-size:12px;color:#94a3b8;">Trending</span>
      </td>
    </tr>
    </table>
  </td></tr>

  <!-- Trending Skills -->
  <tr><td style="padding:24px 40px 8px;">
    <h2 style="color:#1a1a2e;margin:0 0 4px;font-size:18px;">🔥 Trending This Week</h2>
    <p style="color:#94a3b8;font-size:13px;margin:0 0 16px;">Top skills by momentum &amp; community growth</p>
  </td></tr>
  <tr><td style="padding:0 24px 24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
    {trending_rows}
    </table>
  </td></tr>

  <!-- CTA -->
  <tr><td style="padding:0 40px 32px;text-align:center;">
    <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
    <tr><td style="background:#4f46e5;border-radius:8px;">
      <a href="{settings.site_url}" style="display:inline-block;padding:14px 32px;color:#fff;text-decoration:none;font-weight:600;font-size:15px;">
        Explore All Skills →
      </a>
    </td></tr>
    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#f8fafc;padding:20px 40px;text-align:center;border-top:1px solid #e2e8f0;">
    <p style="color:#a0aec0;font-size:12px;margin:0;">
      {unsub_section}<a href="{settings.site_url}" style="color:#4f46e5;">Agent Skills Hub</a> · Auto-updated every 8 hours
    </p>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def send_verification_email(email: str, token: str) -> bool:
    """Send verification email. Tries Resend first, then BillionMail."""
    verify_url = f"{settings.site_url}/api/verify-email?token={token}"

    # Try Resend first
    if settings.resend_api_key:
        return _send_via_resend(
            to=email,
            subject="Confirm your Agent Skills Hub subscription",
            html=_verification_email_html(verify_url),
        )

    # Fall back to BillionMail
    if settings.billionmail_api_url and settings.billionmail_api_key:
        return _send_via_billionmail(email, token, verify_url)

    logger.warning("No email provider configured. Verification email NOT sent for %s (token: %s)", email, token)
    return False


def send_newsletter(
    recipients: list[str],
    trending_skills: list[dict],
    new_skills_count: int,
    total_skills: int,
) -> dict:
    """Send weekly newsletter to all verified subscribers.

    Returns dict with sent/failed/total counts.
    """
    if not settings.resend_api_key:
        logger.error("Resend API key not configured, cannot send newsletter")
        return {"sent": 0, "failed": 0, "total": len(recipients), "error": "Resend API key not configured"}

    html = _newsletter_email_html(trending_skills, new_skills_count, total_skills)
    sent, failed = 0, 0

    for email in recipients:
        ok = _send_via_resend(
            to=email,
            subject=f"🤖 Agent Skills Weekly: {new_skills_count} new skills this week",
            html=html,
        )
        if ok:
            sent += 1
        else:
            failed += 1

    logger.info("Newsletter sent: %d/%d successful, %d failed", sent, len(recipients), failed)
    return {"sent": sent, "failed": failed, "total": len(recipients)}


def _send_via_resend(to: str, subject: str, html: str) -> bool:
    """Send email using Resend API."""
    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.email_from,
                "to": [to],
                "subject": subject,
                "html": html,
            },
            timeout=15.0,
        )
        if resp.status_code in (200, 201):
            logger.info("Email sent via Resend to %s", to)
            return True
        else:
            logger.warning("Resend API returned %d: %s", resp.status_code, resp.text[:300])
            return False
    except Exception as exc:
        logger.warning("Resend API call failed for %s: %s", to, exc)
        return False


def _send_via_billionmail(email: str, token: str, verify_url: str) -> bool:
    """Send verification email via BillionMail."""
    try:
        resp = httpx.post(
            f"{settings.billionmail_api_url}/api/batch_mail/api/send",
            headers={
                "X-API-Key": settings.billionmail_api_key,
                "Content-Type": "application/json",
            },
            json={
                "recipient": email,
                "attribs": {
                    "source": "agent-skills-hub",
                    "type": "verification",
                    "verify_url": verify_url,
                },
            },
            timeout=10.0,
        )
        if resp.status_code == 200:
            logger.info("Verification email sent via BillionMail: %s", email)
            return True
        else:
            logger.warning("BillionMail API returned %d: %s", resp.status_code, resp.text[:200])
            return False
    except Exception as exc:
        logger.warning("BillionMail API call failed: %s", exc)
        return False
