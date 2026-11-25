"""Mail the security-scan alert once per incident, not once per sync.

    python scan_alert.py        (sync.yml runs it after the sync step, whatever its outcome)

jobs._grade_security leaves a note in $SCAN_ALERT_FILE when the scan stopped with an error or
skipped READMEs the scanner raised on. A README that keeps raising does so on every sync, three a
day, so an open GitHub issue labelled scan-alert says "already told": the first note mails and
opens it, later notes are added to it as comments, and the first sync that grades cleanly closes
it. The next incident mails again. A sync that failed says nothing about the scan, so it changes
nothing.

Needs GH_TOKEN (issues: write), GITHUB_REPOSITORY, RUN_URL, SYNC_OUTCOME, and for the mail
RESEND_API_KEY, EMAIL_FROM, EMAIL_TO (comma-separated).
"""
from __future__ import annotations

import html
import json
import os
import subprocess
import urllib.request
from pathlib import Path

LABEL = "scan-alert"
SUBJECT = "⚠️ AgentSkillsHub 安全评级出错"
RESEND_TIMEOUT = 30


def decide(note: str, open_issue: str | None, sync_ok: bool) -> str:
    """mail (and open the issue), comment, close, or nothing."""
    if not sync_ok:
        return "nothing"
    if note and open_issue:
        return "comment"
    if note:
        return "mail"
    return "close" if open_issue else "nothing"


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout.strip()


def open_issue(repo: str) -> str | None:
    found = gh("issue", "list", "--repo", repo, "--label", LABEL, "--state", "open",
               "--json", "number", "--jq", ".[0].number // empty")
    return found or None


def send_mail(note: str, run_url: str) -> None:
    to = [x.strip() for x in os.environ["EMAIL_TO"].split(",") if x.strip()]
    body = (f"<p>这次同步的安全评级出了问题，新收录的仓库可能没有评级，日报会缺候选。"
            f"在 GitHub 上关掉 {LABEL} issue 之前，之后的同步只在 issue 里补充，不再发邮件。</p>"
            f"<pre>{html.escape(note)}</pre><p><a href='{run_url}'>看运行日志</a></p>")
    req = urllib.request.Request(
        "https://api.resend.com/emails", method="POST",
        data=json.dumps({"from": os.environ["EMAIL_FROM"], "to": to, "subject": SUBJECT, "html": body}).encode(),
        headers={"Authorization": "Bearer " + os.environ["RESEND_API_KEY"], "Content-Type": "application/json",
                 "User-Agent": "agentskillshub-sync"})
    print(urllib.request.urlopen(req, timeout=RESEND_TIMEOUT).read().decode())


def open_new_issue(repo: str, note: str, run_url: str) -> None:
    gh("label", "create", LABEL, "--repo", repo, "--color", "B60205", "--force",
       "--description", "The sync's security scan failed or skipped READMEs; mailed once")
    gh("issue", "create", "--repo", repo, "--label", LABEL, "--title", "Security scan: grading failed or skipped READMEs",
       "--body", f"{note}\n\n[Run]({run_url})\n\nThe first sync that grades cleanly closes this issue.")


def main() -> None:
    path = Path(os.environ["SCAN_ALERT_FILE"])
    note = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    repo, run_url = os.environ["GITHUB_REPOSITORY"], os.environ["RUN_URL"]
    issue = open_issue(repo)
    action = decide(note, issue, os.environ.get("SYNC_OUTCOME") == "success")
    print(f"scan alert: {action}" + (f" (issue #{issue})" if issue else ""))
    if action == "mail":
        send_mail(note, run_url)  # first, so a failed mail leaves no issue and the next sync mails again
        open_new_issue(repo, note, run_url)
    elif action == "comment":
        gh("issue", "comment", issue, "--repo", repo, "--body", f"Still failing:\n\n{note}\n\n[Run]({run_url})")
    elif action == "close":
        gh("issue", "close", issue, "--repo", repo, "--comment", f"This sync graded cleanly. [Run]({run_url})")


if __name__ == "__main__":
    main()
