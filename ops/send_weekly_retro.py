"""Email the Monday SEO retro (ops/weekly-retro/<date>.md) to the operator.

The weekly-seo-retro scheduled task runs on the operator's Mac, not in Actions, so it cannot use the
Actions copy of the Resend key, and the key in backend/.env was revoked on 2026-10-22. It reads the
site's live key from Supabase Vault (resend_api_key, the one the verification mail uses) at send
time instead: held in memory for this one request, never written to disk or printed.

Env (read from backend/.env): SUPABASE_DB_URL, EMAIL_FROM. DIGEST_TO in the environment overrides
the recipient (defaults to the operator).
Usage: python ops/send_weekly_retro.py ops/weekly-retro/2026-11-09.md [--subject "…"]
"""
import os
import re
import sys

import psycopg2

from send_digest_email import TO_DEFAULT, send_email

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", ".env")
FOOTER = ('<p style="font-size:12px;color:#888">AgentSkillsHub · 周一 SEO 周复盘 · '
          "全文存在本机 ops/weekly-retro/</p>")


def read_env(path=ENV_FILE):
    """backend/.env as a dict (KEY=value lines, quotes stripped)."""
    env = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)", line)
        if m:
            env[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return env


def vault_resend_key(db_url):
    """The site's Resend key from Supabase Vault: one select on one short-lived connection."""
    conn = psycopg2.connect(db_url, connect_timeout=15)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("select decrypted_secret from vault.decrypted_secrets where name = %s",
                        ("resend_api_key",))
            row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        sys.exit("Supabase Vault has no resend_api_key")
    return row[0]


def arg(flag, default):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        sys.exit("usage: send_weekly_retro.py ops/weekly-retro/<date>.md [--subject \"…\"]")
    path = sys.argv[1]
    env = read_env()
    if not env.get("EMAIL_FROM") or not env.get("SUPABASE_DB_URL"):
        sys.exit("EMAIL_FROM / SUPABASE_DB_URL not set in backend/.env")
    date = os.path.splitext(os.path.basename(path))[0]
    subject = arg("--subject", f"🗓️ SEO 周复盘 {date}")
    to = os.environ.get("DIGEST_TO", TO_DEFAULT)
    text = open(path, encoding="utf-8").read()
    rid = send_email(vault_resend_key(env["SUPABASE_DB_URL"]), env["EMAIL_FROM"], to, subject, text, FOOTER)
    print(f"✓ weekly retro emailed to {to} ({subject}) resend_id={rid}")


if __name__ == "__main__":
    main()
