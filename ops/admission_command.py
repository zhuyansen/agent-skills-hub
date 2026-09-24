"""Apply /approve owner/repo and /reject owner/repo from a maintainer's comment.

Reads COMMENT_BODY, COMMENT_AUTHOR, COMMENT_ASSOCIATION, ISSUE_TITLE,
SUPABASE_DB_URL. Writes ops/output/comment.md (empty when there is nothing to
say) and close=<true|false> say=<true|false> to GITHUB_OUTPUT. Non-maintainers
are ignored silently: replying would make the bot a toy.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
from app.services.catalog_admission import decide, parse_commands  # noqa: E402

MAINTAINERS = {"OWNER", "MEMBER", "COLLABORATOR"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
DONE = {"approved": "已收录,下轮同步可见", "rejected": "已拒绝", "absent": "没有这条记录,无法拒绝"}
SUBMISSION_TITLES = ("Submit repository:", "[Submission]")


def finish(lines, close=False):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'comment.md'), 'w').write("\n".join(lines))
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out, 'a') as f:
            f.write(f"close={'true' if close else 'false'}\nsay={'true' if lines else 'false'}\n")
    print("\n".join(lines))


def main():
    if os.environ.get('COMMENT_ASSOCIATION') not in MAINTAINERS:
        return finish([])
    cmds, bad = parse_commands(os.environ.get('COMMENT_BODY', ''))
    if not cmds and not bad:
        return finish([])
    import psycopg2
    conn = psycopg2.connect(os.environ['SUPABASE_DB_URL'], connect_timeout=30)
    lines, results = [], []
    for action, name in cmds:
        status = decide(conn, name, action, os.environ.get('COMMENT_AUTHOR', 'maintainer'))
        results.append(status)
        lines.append(f"- `{name}` → {DONE.get(status, status)}")
    conn.commit()
    conn.close()
    for line in bad:
        lines.append(f"- 无法解析:`{line}`(格式 `/approve owner/repo`)")
    # A submission issue is done once its repo is decided; the weekly coverage issue stays open.
    is_submission = os.environ.get('ISSUE_TITLE', '').startswith(SUBMISSION_TITLES)
    close = is_submission and bool(results) and all(r in ('approved', 'rejected') for r in results)
    finish(lines, close)


if __name__ == "__main__":
    main()
