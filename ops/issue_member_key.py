#!/usr/bin/env python3
"""Issue (or revoke) a Pro member key. Manual, low-volume — run per new member.

Usage:
  python ops/issue_member_key.py member@email.com                # ¥365 standard, 1y
  python ops/issue_member_key.py member@email.com --note 早鸟199  # early bird, 1y
  python ops/issue_member_key.py --revoke ash_pro_xxxx           # revoke a leaked key

Prints the RAW key exactly once — only the sha256 hash is stored. Send the raw
key to the member (club welcome DM); if lost, revoke + reissue.
"""

import hashlib
import os
import secrets
import sys

import psycopg2
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, "backend", ".env"))


def connect():
    return psycopg2.connect(
        os.environ["SUPABASE_DB_URL"],
        connect_timeout=15,
        options="-c statement_timeout=30000",
        keepalives=1,
    )


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1

    conn = connect()
    cur = conn.cursor()

    if args[0] == "--revoke":
        raw = args[1]
        h = hashlib.sha256(raw.encode()).hexdigest()
        cur.execute("UPDATE member_keys SET revoked = true WHERE key_hash = %s", (h,))
        conn.commit()
        print(f"revoked {cur.rowcount} key(s)")
        conn.close()
        return 0

    email = args[0]
    note = args[args.index("--note") + 1] if "--note" in args else "标准365"
    raw = "ash_pro_" + secrets.token_urlsafe(24)
    h = hashlib.sha256(raw.encode()).hexdigest()
    cur.execute(
        """INSERT INTO member_keys (key_hash, email, tier, expires_at, note)
           VALUES (%s, %s, 'pro', now() + interval '1 year', %s)""",
        (h, email, note),
    )
    conn.commit()
    conn.close()
    print("会员 key(只显示这一次,发给会员后自己不要留明文):\n")
    print(f"  {raw}\n")
    print(f"email={email} · tier=pro · 有效期 1 年 · note={note}")
    print("使用:https://agentskillshub.top/pro/ 粘贴 key 即可")
    return 0


if __name__ == "__main__":
    sys.exit(main())
