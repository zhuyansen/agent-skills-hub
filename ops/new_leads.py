"""Write yesterday's enterprise leads to a private file for the digest email.

The digest also lands in the run's Step Summary, and this repo is public: the summary,
the log and the artifacts can be read by anyone. Lead details (names, emails, what they
asked for) must reach the operator's inbox and nothing else, so this script writes them
to a file the workflow keeps in RUNNER_TEMP and prints only a count. Before this,
a lead sat unseen in the table until someone happened to look.

No leads: the file is left empty and the email shows nothing. Query failed: the file
says so, because a silent miss would read as "no leads".

Env: SUPABASE_DB_URL (required).
Usage: python ops/new_leads.py <out.md> [--days N]
"""
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import psycopg2

STATEMENT_TIMEOUT = "10s"
CONNECT_TIMEOUT = 15
# (column, label) in the order the email shows them; empty fields are skipped.
FIELDS = (
    ("full_name", "姓名"), ("email", "邮箱"), ("company", "公司"), ("role_title", "职位"),
    ("team_size", "团队"), ("industry", "行业"), ("timeline", "时间线"),
    ("estimated_budget", "预算"), ("current_stack", "现有技术栈"),
    ("compliance_requirements", "合规要求"), ("use_case", "用途"), ("message", "留言"),
)
# send_digest_email.py puts the text after "## " into the subject.
FAILED = "## ⚠️ 新留资没查成(见 Actions 日志)\n"


def window(days):
    """Whole UTC days before today: the run lands at ~00:20 UTC, so 1 is all of yesterday."""
    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return end - timedelta(days=days), end


def fetch(start, end):
    cols = ", ".join(column for column, _ in FIELDS)
    with psycopg2.connect(os.environ["SUPABASE_DB_URL"], connect_timeout=CONNECT_TIMEOUT) as conn, \
            conn.cursor() as cur:
        # SET LOCAL only: the pooler hands this connection to the next client afterwards.
        cur.execute(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'")
        cur.execute("SET LOCAL transaction_read_only = on")
        cur.execute(f"""select id, created_at, source, {cols} from enterprise_leads
                        where created_at >= %s and created_at < %s order by created_at""",
                    (start, end))
        return cur.fetchall()


def render(leads, start, end):
    last = end - timedelta(days=1)
    span = f"UTC {start:%m-%d}" + ("" if last.date() == start.date() else f" 至 {last:%m-%d}")
    lines = [f"## 🔔 新留资 {len(leads)} 条({span})", ""]
    for lead_id, created, source, *values in leads:
        lines.append(f"### #{lead_id} · {created.astimezone(timezone.utc):%m-%d %H:%M} UTC · {source}")
        lines += [f"{label}: {value}" for (_, label), value in zip(FIELDS, values) if value]
        lines.append("")
    return "\n".join(lines) + "\n"


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    parser = argparse.ArgumentParser(description="Private list of new enterprise leads.")
    parser.add_argument("out", help="markdown file for the email step (never the Step Summary)")
    parser.add_argument("--days", type=int, default=1, help="whole UTC days before today")
    args = parser.parse_args()
    start, end = window(args.days)
    try:
        leads = fetch(start, end)
    except (psycopg2.Error, KeyError) as exc:
        write(args.out, FAILED)
        # The type only: a driver message can carry connection details into a public log.
        sys.exit(f"lead query failed: {type(exc).__name__}")
    write(args.out, render(leads, start, end) if leads else "")
    print(f"{len(leads)} new lead(s), {start:%Y-%m-%d} to {end:%Y-%m-%d} UTC")


if __name__ == "__main__":
    main()
