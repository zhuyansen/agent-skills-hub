"""Email service: send verification, welcome & newsletter emails via Resend or BillionMail."""

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ── Shared footer builder ──

def _footer_html(unsubscribe_url: str = "") -> str:
    """Shared footer with optional unsubscribe link."""
    unsub_link = ""
    if unsubscribe_url:
        unsub_link = f'<a href="{unsubscribe_url}" style="color:#94a3b8;text-decoration:underline;">Unsubscribe</a> · '

    return f"""\
  <tr><td style="background:#f8fafc;padding:20px 40px;text-align:center;border-top:1px solid #e2e8f0;">
    <p style="color:#a0aec0;font-size:12px;margin:0;">
      {unsub_link}<a href="{settings.site_url}" style="color:#4f46e5;">Agent Skills Hub</a> · Auto-updated every 8 hours
    </p>
  </td></tr>"""


def _email_wrapper(inner: str) -> str:
    """Wrap email content in the standard layout shell."""
    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
{inner}
</table>
</td></tr>
</table>
</body>
</html>"""


def _header_html(title: str, subtitle: str) -> str:
    """Gradient header block."""
    return f"""\
  <tr><td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:32px 40px;text-align:center;">
    <h1 style="color:#fff;margin:0;font-size:24px;">{title}</h1>
    <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px;">{subtitle}</p>
  </td></tr>"""


# ── Trending rows builder (shared by welcome + newsletter) ──

def _trending_rows_html(trending_skills: list, max_items: int = 10) -> str:
    """Build the trending skills table rows."""
    rows = ""
    for i, skill in enumerate(trending_skills[:max_items]):
        name = skill.get("repo_name", "unknown")
        desc = skill.get("description", "")[:120]
        stars = skill.get("stars", 0)
        url = skill.get("repo_url", "#")
        score = skill.get("score", 0)
        category = skill.get("category", "tool")
        momentum = skill.get("star_momentum", 0)

        badge_color = "#10b981" if momentum > 0.6 else "#f59e0b" if momentum > 0.4 else "#6b7280"
        rows += f"""\
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
            <span style="color:#f59e0b;font-size:13px;">&#11088; {stars:,}</span><br>
            <span style="color:#94a3b8;font-size:11px;">Score: {score}</span>
          </td>
        </tr>
        </table>
      </td>
    </tr>"""
    return rows


def _velocity_rows_html(trending_skills: list, max_items: int = 20) -> str:
    """Build Star Velocity History ranking rows for newsletter."""
    rows = ""
    for i, skill in enumerate(trending_skills[:max_items]):
        name = skill.get("repo_name", "unknown")
        author = skill.get("author_name", "")
        desc = skill.get("description", "")[:100]
        stars = skill.get("stars", 0)
        velocity = skill.get("star_velocity", 0)
        url = skill.get("repo_url", "#")

        if velocity >= 1000:
            vel_str = f"{velocity/1000:.1f}k/day"
        else:
            vel_str = f"{velocity:.0f}/day"

        if stars >= 1000:
            stars_str = f"&#11088; {stars/1000:.1f}k"
        else:
            stars_str = f"&#11088; {stars:,}"

        rank_bg = "#ea580c" if i < 3 else "#94a3b8"

        rows += f"""\
    <tr>
      <td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;">
        <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:28px;vertical-align:top;padding-top:2px;">
            <span style="display:inline-block;width:24px;height:24px;background:{rank_bg};color:#fff;border-radius:50%;text-align:center;line-height:24px;font-size:11px;font-weight:700;">{i+1}</span>
          </td>
          <td style="padding-left:10px;">
            <a href="{url}" style="color:#1e293b;font-weight:600;text-decoration:none;font-size:14px;">{name}</a>
            <span style="color:#94a3b8;font-size:12px;margin-left:4px;">{author}</span>
            <br>
            <span style="color:#ea580c;font-weight:600;font-size:12px;">{vel_str}</span>
            <span style="color:#64748b;font-size:12px;margin-left:8px;">{desc}</span>
          </td>
          <td style="width:70px;text-align:right;vertical-align:top;white-space:nowrap;">
            <span style="color:#f59e0b;font-size:12px;">{stars_str}</span>
          </td>
        </tr>
        </table>
      </td>
    </tr>"""
    return rows


def _new_skills_rows_html(new_skills: list, max_items: int = 20) -> str:
    """Build New This Week ranking rows for newsletter."""
    rows = ""
    for i, skill in enumerate(new_skills[:max_items]):
        name = skill.get("repo_name", "unknown")
        author = skill.get("author_name", "")
        desc = skill.get("description", "")[:100]
        stars = skill.get("stars", 0)
        star_gain = skill.get("star_gain", 0)
        url = skill.get("repo_url", "#")
        category = skill.get("category", "")
        site_url = settings.site_url or "https://agentskillshub.top"
        full_name = skill.get("repo_full_name", "")
        skill_page_url = f"{site_url}/skill/{full_name}/"

        if stars >= 1000:
            stars_str = f"&#11088; {stars/1000:.1f}k"
        else:
            stars_str = f"&#11088; {stars:,}"

        gain_str = f"+{star_gain:,}" if star_gain > 0 else "new"
        gain_color = "#10b981" if star_gain > 100 else "#ea580c" if star_gain > 0 else "#6b7280"

        # Category badge color
        cat_colors = {
            "mcp-server": "#7c3aed",
            "claude-skill": "#ea580c",
            "codex-skill": "#2563eb",
            "agent-tool": "#10b981",
            "ai-skill": "#f59e0b",
        }
        cat_color = cat_colors.get(category, "#6b7280")

        rank_bg = "#10b981" if i < 3 else "#94a3b8"

        rows += f"""\
    <tr>
      <td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;">
        <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:28px;vertical-align:top;padding-top:2px;">
            <span style="display:inline-block;width:24px;height:24px;background:{rank_bg};color:#fff;border-radius:50%;text-align:center;line-height:24px;font-size:11px;font-weight:700;">{i+1}</span>
          </td>
          <td style="padding-left:10px;">
            <a href="{skill_page_url}" style="color:#1e293b;font-weight:600;text-decoration:none;font-size:14px;">{name}</a>
            <span style="color:#94a3b8;font-size:12px;margin-left:4px;">{author}</span>
            <span style="display:inline-block;padding:1px 6px;background:{cat_color}18;color:{cat_color};border-radius:8px;font-size:10px;margin-left:6px;">{category}</span>
            <br>
            <span style="color:{gain_color};font-weight:600;font-size:12px;">{gain_str}</span>
            <span style="color:#64748b;font-size:12px;margin-left:8px;">{desc}</span>
          </td>
          <td style="width:70px;text-align:right;vertical-align:top;white-space:nowrap;">
            <span style="color:#f59e0b;font-size:12px;">{stars_str}</span>
          </td>
        </tr>
        </table>
      </td>
    </tr>"""
    return rows


# ═══════════════════════════════════════════════════════
# 1. Verification Email
# ═══════════════════════════════════════════════════════

def _verification_email_html(verify_url: str) -> str:
    inner = _header_html(
        "&#129302; Agent Skills Hub",
        "Discover Agent Skills, Tools & MCP Servers",
    )
    inner += f"""\
  <tr><td style="padding:40px;">
    <h2 style="color:#1a1a2e;margin:0 0 16px;font-size:20px;">Confirm your subscription</h2>
    <p style="color:#4a5568;line-height:1.6;margin:0 0 24px;">
      Thanks for subscribing to the Agent Skills Hub weekly newsletter!
      Click the button below to verify your email address and start receiving updates.
    </p>
    <table cellpadding="0" cellspacing="0" style="margin:0 auto 24px;">
    <tr><td style="background:#4f46e5;border-radius:8px;">
      <a href="{verify_url}" style="display:inline-block;padding:14px 32px;color:#fff;text-decoration:none;font-weight:600;font-size:16px;">
        &#9989; Verify Email Address
      </a>
    </td></tr>
    </table>
    <p style="color:#718096;font-size:13px;line-height:1.5;">
      If you didn't subscribe, you can safely ignore this email.
    </p>
  </td></tr>"""
    inner += _footer_html()  # No unsubscribe link on verification
    return _email_wrapper(inner)


# ═══════════════════════════════════════════════════════
# 2. Welcome Email (sent after verification, with trending)
# ═══════════════════════════════════════════════════════

def _welcome_email_html(
    trending_skills: list,
    total_skills: int,
    unsubscribe_url: str = "",
) -> str:
    """Welcome email sent immediately after email verification."""
    inner = _header_html(
        "&#127881; Welcome to Agent Skills Hub!",
        "You're now subscribed to our weekly newsletter",
    )

    # Welcome message
    inner += f"""\
  <tr><td style="padding:32px 40px 16px;">
    <h2 style="color:#1a1a2e;margin:0 0 12px;font-size:20px;">&#128075; Thanks for verifying!</h2>
    <p style="color:#4a5568;line-height:1.6;margin:0 0 8px;">
      Your email is now verified. Every <strong>Monday</strong>, you'll receive a curated digest
      of the hottest Agent Skills, Tools & MCP Servers from the past week.
    </p>
    <p style="color:#4a5568;line-height:1.6;margin:0;">
      To get you started, here are <strong>this week's trending skills</strong> from our collection
      of <strong>{total_skills:,}</strong> skills:
    </p>
  </td></tr>"""

    # Trending section
    if trending_skills:
        trending_rows = _trending_rows_html(trending_skills, max_items=5)
        inner += f"""\
  <tr><td style="padding:8px 40px 4px;">
    <h3 style="color:#1a1a2e;margin:0 0 4px;font-size:16px;">&#128293; Trending This Week</h3>
  </td></tr>
  <tr><td style="padding:0 24px 24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
    {trending_rows}
    </table>
  </td></tr>"""

    # CTA
    inner += f"""\
  <tr><td style="padding:0 40px 32px;text-align:center;">
    <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
    <tr><td style="background:#4f46e5;border-radius:8px;">
      <a href="{settings.site_url}" style="display:inline-block;padding:14px 32px;color:#fff;text-decoration:none;font-weight:600;font-size:15px;">
        Explore All Skills &#8594;
      </a>
    </td></tr>
    </table>
  </td></tr>"""

    inner += _footer_html(unsubscribe_url)
    return _email_wrapper(inner)


# ═══════════════════════════════════════════════════════
# 3. Weekly Newsletter Email
# ═══════════════════════════════════════════════════════

def _newsletter_email_html(
    new_skills: list,
    trending_skills: list,
    total_skills: int,
    week_period: str,
    unsubscribe_url: str = "",
) -> str:
    """Generate a weekly newsletter HTML email with New This Week + Top Trending."""
    site_url = settings.site_url or "https://agentskillshub.top"

    inner = _header_html(
        "&#127381; New This Week",
        f"{len(new_skills)} fresh AI agent tools discovered — {week_period}",
    )

    # Stats bar
    inner += f"""\
  <tr><td style="padding:16px 40px;background:#f8fafc;border-bottom:1px solid #e2e8f0;">
    <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td style="text-align:center;width:33%;">
        <span style="font-size:22px;font-weight:700;color:#4f46e5;">{total_skills:,}</span><br>
        <span style="font-size:12px;color:#94a3b8;">Total Skills</span>
      </td>
      <td style="text-align:center;width:34%;">
        <span style="font-size:22px;font-weight:700;color:#10b981;">{len(new_skills)}</span><br>
        <span style="font-size:12px;color:#94a3b8;">New This Week</span>
      </td>
      <td style="text-align:center;width:33%;">
        <span style="font-size:22px;font-weight:700;color:#ea580c;">{len(trending_skills)}</span><br>
        <span style="font-size:12px;color:#94a3b8;">Top Trending</span>
      </td>
    </tr>
    </table>
  </td></tr>"""

    # New This Week section (main content)
    new_rows = _new_skills_rows_html(new_skills)
    inner += f"""\
  <tr><td style="padding:24px 40px 8px;">
    <h2 style="color:#1a1a2e;margin:0 0 4px;font-size:18px;">&#127381; New This Week — Top 20</h2>
    <p style="color:#94a3b8;font-size:13px;margin:0 0 16px;">{week_period} · Newly indexed AI agent tools, ranked by stars</p>
  </td></tr>
  <tr><td style="padding:0 16px 24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
    {new_rows}
    </table>
  </td></tr>"""

    # Top Trending section (compact, top 5)
    if trending_skills:
        velocity_rows = _velocity_rows_html(trending_skills, max_items=5)
        inner += f"""\
  <tr><td style="padding:8px 40px 8px;">
    <h2 style="color:#1a1a2e;margin:0 0 4px;font-size:16px;">&#128293; Still Trending</h2>
    <p style="color:#94a3b8;font-size:12px;margin:0 0 12px;">Fastest-growing this week by star velocity</p>
  </td></tr>
  <tr><td style="padding:0 16px 24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
    {velocity_rows}
    </table>
  </td></tr>"""

    # CTA
    inner += f"""\
  <tr><td style="padding:0 40px 32px;text-align:center;">
    <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
    <tr><td style="background:#4f46e5;border-radius:8px;">
      <a href="{site_url}" style="display:inline-block;padding:14px 32px;color:#fff;text-decoration:none;font-weight:600;font-size:15px;">
        Explore All Skills &#8594;
      </a>
    </td></tr>
    </table>
  </td></tr>"""

    inner += _footer_html(unsubscribe_url)
    return _email_wrapper(inner)


# ═══════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════

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


def send_welcome_email(
    email: str,
    trending_skills: list[dict],
    total_skills: int,
    unsubscribe_url: str = "",
) -> bool:
    """Send welcome email after verification with this week's trending skills."""
    if not settings.resend_api_key:
        logger.warning("Resend API key not configured, cannot send welcome email")
        return False

    html = _welcome_email_html(trending_skills, total_skills, unsubscribe_url)
    return _send_via_resend(
        to=email,
        subject="Welcome to Agent Skills Hub! Here's this week's trending skills",
        html=html,
    )


def send_newsletter(
    recipients: list[dict],
    new_skills: list[dict],
    trending_skills: list[dict],
    total_skills: int,
    week_period: str = "",
) -> dict:
    """Send weekly newsletter to all verified subscribers.

    recipients: list of dicts with 'email' and 'unsubscribe_token' keys.
    new_skills: list of newly indexed skills this week.
    trending_skills: list of top trending skills (velocity).
    Returns dict with sent/failed/total counts.
    """
    if not settings.resend_api_key:
        logger.error("Resend API key not configured, cannot send newsletter")
        return {"sent": 0, "failed": 0, "total": len(recipients), "error": "Resend API key not configured"}

    import time

    sent, failed = 0, 0

    for i, recipient in enumerate(recipients):
        email = recipient["email"]
        unsub_token = recipient.get("unsubscribe_token", "")
        unsubscribe_url = f"{settings.site_url}/api/unsubscribe?token={unsub_token}" if unsub_token else ""

        html = _newsletter_email_html(new_skills, trending_skills, total_skills, week_period, unsubscribe_url)
        subject = f"New This Week — {week_period}" if week_period else "Agent Skills Weekly"
        ok = _send_via_resend(
            to=email,
            subject=subject,
            html=html,
        )
        if ok:
            sent += 1
        else:
            failed += 1

        # Resend free tier: max 2 requests/second, use 1.2s to be safe
        if i < len(recipients) - 1:
            time.sleep(1.2)

    logger.info("Newsletter sent: %d/%d successful, %d failed", sent, len(recipients), failed)
    return {"sent": sent, "failed": failed, "total": len(recipients)}


# ── Transport layer ──

def _send_via_resend(to: str, subject: str, html: str) -> bool:
    """Send email using Resend API with retry on 429."""
    import time

    max_retries = 3
    for attempt in range(max_retries):
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
                logger.info("Email sent via Resend to %s (subject: %s)", to, subject[:50])
                return True
            elif resp.status_code == 429:
                wait = 2 ** attempt + 1  # 2s, 3s, 5s
                logger.warning("Resend 429 rate limit for %s, retry %d/%d in %ds", to, attempt + 1, max_retries, wait)
                time.sleep(wait)
                continue
            else:
                logger.warning("Resend API returned %d: %s", resp.status_code, resp.text[:300])
                return False
        except Exception as exc:
            logger.warning("Resend API call failed for %s: %s", to, exc)
            return False
    logger.warning("Resend failed after %d retries for %s", max_retries, to)
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
