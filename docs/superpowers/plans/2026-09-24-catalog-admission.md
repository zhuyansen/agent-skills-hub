# Catalog Admission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the three manual ingestion steps (weekly coverage list, submission issues, admin approval) into one admission rule that auto-admits ≥1000★ on-topic repos and routes the rest to a one-command review, and stop silently truncating wave queries.

**Architecture:** One pure module (`catalog_admission.py`) holds the rule, the URL/command parsers and the single `extra_repos` write path (pending-only overwrite). Three thin `ops/` scripts call it from three GitHub Actions triggers (weekly scan, issue opened, issue comment); comments, labels and closes are done by `gh` in the workflow from files the scripts write. The sync gains a truncation warning and star-band slices for `created:>=` queries.

**Tech Stack:** Python 3.12 (stdlib + psycopg2, dotenv), pytest, GitHub Actions + `gh` CLI, Supabase Postgres (`extra_repos` table, no schema change).

**Spec:** `docs/superpowers/specs/2026-09-24-catalog-admission-design.md`

**Facts the code relies on (verified 2026-09-24):**
- `extra_repos(full_name UNIQUE, is_active, status pending|approved|rejected, submitted_by, reviewed_at, created_at)`; the sync fetches every row with `is_active = true` by name each run (`jobs.py:420`).
- `ops/` scripts install only `psycopg2-binary python-dotenv`; the triage script additionally needs the backend scanner, so its workflow installs `backend/requirements.txt`.
- Scripts import the rule with `sys.path.insert(0, "backend")` from the repo root; the workflows run from the repo root.

---

## File map

| File | Responsibility | Task |
|---|---|---|
| `backend/app/services/catalog_admission.py` (new) | rule, parsers, write path | 1 |
| `backend/tests/test_catalog_admission.py` (new) | their tests | 1 |
| `ops/find_missing_repos.py` | `--write`, tiered lists, issue body file | 2 |
| `.github/workflows/catalog-coverage.yml` | write mode, two-section issue | 2 |
| `ops/triage_submission.py` (new) + `.github/workflows/submissions.yml` (new) | submission-issue pre-review | 3 |
| `ops/admission_command.py` (new) + `.github/workflows/admission-commands.yml` (new) | `/approve` `/reject` | 4 |
| `backend/app/services/sync_selection.py`, `backend/app/scheduler/jobs.py` | truncation warning, wave slices | 5 |

---

### Task 1: The admission rule and the one write path

**Files:** Create `backend/app/services/catalog_admission.py`; Test `backend/tests/test_catalog_admission.py`

- [ ] **Step 1: Failing tests**

```python
"""The admission rule, its parsers, and the pending-only write."""
from app.services.catalog_admission import (
    AUTO_APPROVE_MIN_STARS, UPSERT_SQL, admission, parse_commands, parse_repo_url,
)


def repo(full_name, stars, description="", archived=False, fork=False):
    return {"full_name": full_name, "stargazers_count": stars, "description": description,
            "archived": archived, "fork": fork}


def test_high_star_on_topic_is_approved():
    assert admission(repo("dream-num/univer", 14411, "The Office Harness for AI Agents")) == "approved"


def test_the_seleniumbase_boundary_is_admitted_on_purpose():
    # 13K stars, "AI agents" in the description: browser automation is inside the catalog's remit.
    assert admission(repo("seleniumbase/SeleniumBase", 13025, "Browser automation … for AI agents")) == "approved"


def test_just_under_the_star_line_is_pending():
    assert admission(repo("x/agent-skills", AUTO_APPROVE_MIN_STARS - 1, "agent skills")) == "pending"


def test_high_stars_without_a_topic_word_is_pending():
    assert admission(repo("x/fast-json", 20000, "A JSON parser")) == "pending"


def test_topic_word_in_the_name_counts():
    assert admission(repo("humanlayer/skills", 4339, None)) == "approved"


def test_forks_archived_and_lists_are_excluded():
    assert admission(repo("x/skills", 5000, "agent skills", fork=True)) == "excluded"
    assert admission(repo("x/skills", 5000, "agent skills", archived=True)) == "excluded"
    assert admission(repo("x/awesome-agents", 5000, "curated list of agents")) == "excluded"


def test_parse_repo_url_accepts_the_usual_spellings():
    for text in ("https://github.com/agentbody/skills", "see github.com/agentbody/skills/ please",
                 "https://github.com/agentbody/skills.git", "https://github.com/agentbody/skills/tree/main/x"):
        assert parse_repo_url(text) == "agentbody/skills"
    assert parse_repo_url("no link here") is None
    assert parse_repo_url("https://github.com/agentbody") is None


def test_parse_commands_reads_one_per_line_and_rejects_bad_names():
    body = "/approve Hisn00w/ASu-skills\nsome prose\n/reject bad name here\n/approve ../../etc\n/reject x/y"
    cmds, bad = parse_commands(body)
    assert cmds == [("approve", "Hisn00w/ASu-skills"), ("reject", "x/y")]
    assert bad == ["/reject bad name here", "/approve ../../etc"]


def test_upsert_only_overwrites_pending_rows():
    assert "ON CONFLICT (full_name) DO UPDATE" in UPSERT_SQL
    assert "WHERE extra_repos.status = 'pending'" in UPSERT_SQL
```

- [ ] **Step 2: Run to see them fail** — `cd backend && python -m pytest tests/test_catalog_admission.py -q` → `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

```python
"""Who gets into the catalog without a person looking, and how the rest are recorded.

One rule for three entrances — the weekly coverage scan, submission issues, and
maintainer commands — so they can never disagree. Pure except `apply`, which
takes a psycopg2 connection.

    approved   ≥ AUTO_APPROVE_MIN_STARS and a topic word in name or description:
               written active, the next sync fetches it by name
    pending    everything else worth a look: written inactive, listed for a
               /approve or /reject command
    excluded   fork, archived, or a known collision: not written, not listed

Policy decided 2026-09-24 (spec 2026-09-24-catalog-admission-design.md): the
2026-08-20 rule that a search query alone can never pollute the catalog stays
for the long tail; two thresholds together are the automatic door.
"""
from __future__ import annotations

import re
from typing import Literal

AUTO_APPROVE_MIN_STARS = 1000
TOPIC_WORDS = re.compile(r"\b(?:skills?|mcp|agents?|claude|codex|openclaw)\b", re.IGNORECASE)
# Same collisions the scenario pages exclude, plus link lists (they are indexes, not tools).
EXCLUDE = re.compile(r"awesome-|curated list|jevois|jevons", re.IGNORECASE)
REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_REPO_URL = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?=[/\s)>\]#?]|$)")
_COMMAND = re.compile(r"^/(approve|reject)\s+(\S+)\s*$")

Verdict = Literal["approved", "pending", "excluded"]

SOURCE_AUTO = "coverage-auto"
SOURCE_PENDING = "coverage-pending"

# Only a pending row can be rewritten: a decision (approved/rejected) is never undone by
# a re-submission or a later scan. Returns the row's status after the statement.
UPSERT_SQL = (
    "INSERT INTO extra_repos (full_name, is_active, status, submitted_by) "
    "VALUES (%(full_name)s, %(is_active)s, %(status)s, %(submitted_by)s) "
    "ON CONFLICT (full_name) DO UPDATE SET status = EXCLUDED.status, "
    "is_active = EXCLUDED.is_active, submitted_by = EXCLUDED.submitted_by, reviewed_at = now() "
    "WHERE extra_repos.status = 'pending' "
    "RETURNING status"
)
STATUS_SQL = "SELECT status FROM extra_repos WHERE full_name = %(full_name)s"


def admission(repo: dict) -> Verdict:
    """repo: a GitHub API repository object (full_name, description, stargazers_count, archived, fork)."""
    if repo.get("archived") or repo.get("fork"):
        return "excluded"
    text = f"{repo.get('full_name', '')} {repo.get('description') or ''}"
    if EXCLUDE.search(text):
        return "excluded"
    if (repo.get("stargazers_count") or 0) >= AUTO_APPROVE_MIN_STARS and TOPIC_WORDS.search(text):
        return "approved"
    return "pending"


def parse_repo_url(text: str) -> str | None:
    m = _REPO_URL.search(text or "")
    return f"{m.group(1)}/{m.group(2)}" if m else None


def parse_commands(body: str) -> tuple[list[tuple[str, str]], list[str]]:
    """(valid commands, rejected lines). A repo name is untrusted input: only
    owner/repo characters pass, and nothing here is ever interpolated into SQL."""
    good, bad = [], []
    for line in (body or "").splitlines():
        line = line.strip()
        if not line.startswith("/"):
            continue
        m = _COMMAND.match(line)
        if m and REPO_NAME.match(m.group(2)):
            good.append((m.group(1), m.group(2)))
        elif line.startswith(("/approve", "/reject")):
            bad.append(line)
    return good, bad


def apply(conn, full_name: str, verdict: Verdict, submitted_by: str) -> str:
    """Write one verdict. Returns the row's resulting status ('approved' / 'pending' /
    'rejected'), which equals the verdict unless a decided row already existed."""
    if verdict == "excluded":
        return "excluded"
    with conn.cursor() as cur:
        cur.execute(UPSERT_SQL, {"full_name": full_name, "is_active": verdict == "approved",
                                 "status": verdict, "submitted_by": submitted_by})
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(STATUS_SQL, {"full_name": full_name})
        return cur.fetchone()[0]


def decide(conn, full_name: str, decision: str, login: str) -> str:
    """A maintainer's /approve or /reject. Approve inserts when absent; reject only
    touches an existing pending row (nothing to reject otherwise)."""
    with conn.cursor() as cur:
        if decision == "approve":
            cur.execute(
                "INSERT INTO extra_repos (full_name, is_active, status, submitted_by) "
                "VALUES (%(n)s, true, 'approved', %(by)s) "
                "ON CONFLICT (full_name) DO UPDATE SET status = 'approved', is_active = true, "
                "submitted_by = EXCLUDED.submitted_by, reviewed_at = now() "
                "WHERE extra_repos.status = 'pending' RETURNING status",
                {"n": full_name, "by": f"command-{login}"})
        else:
            cur.execute(
                "UPDATE extra_repos SET status = 'rejected', is_active = false, "
                "submitted_by = %(by)s, reviewed_at = now() "
                "WHERE full_name = %(n)s AND status = 'pending' RETURNING status",
                {"n": full_name, "by": f"command-{login}"})
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(STATUS_SQL, {"full_name": full_name})
        row = cur.fetchone()
        return row[0] if row else "absent"
```

- [ ] **Step 4: Run** — 9 passed; full suite green. **Commit** — `git add backend/app/services/catalog_admission.py backend/tests/test_catalog_admission.py && git commit -m "feat(catalog): one admission rule for the coverage scan, submissions and commands"`

---

### Task 2: Weekly coverage scan writes by tier

**Files:** Modify `ops/find_missing_repos.py` (lines 98-135), `.github/workflows/catalog-coverage.yml`

- [ ] **Step 1: Replace everything from `missing = [...]` (line 111) to the end**

```python
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
from app.services.catalog_admission import SOURCE_AUTO, SOURCE_PENDING, admission, apply  # noqa: E402

WRITE = '--write' in sys.argv

missing = [v for k, v in found.items() if k.lower() not in have]
missing.sort(key=lambda i: -i['stargazers_count'])
tiers = {'approved': [], 'pending': [], 'excluded': []}
for i in missing:
    tiers[admission(i)].append(i)

# Form submissions waiting in extra_repos join the review list so both roads meet in one issue.
cur = conn.cursor()
cur.execute("SELECT full_name FROM extra_repos WHERE status = 'pending' "
            "AND (submitted_by IS NULL OR submitted_by NOT LIKE 'coverage-%%' "
            "AND submitted_by NOT LIKE 'issue-%%' AND submitted_by NOT LIKE 'command-%%')")
form_pending = [r[0] for r in cur.fetchall()]

written = {'approved': 0, 'pending': 0}
if WRITE:
    for verdict in ('approved', 'pending'):
        for i in tiers[verdict]:
            result = apply(conn, i['full_name'], verdict,
                           SOURCE_AUTO if verdict == 'approved' else SOURCE_PENDING)
            written[verdict] += result == verdict
    conn.commit()
conn.close()

def line(i):
    return f"- {i['full_name']} ★{i['stargazers_count']:,} — {(i['description'] or '')[:80]}"

def review_line(name):
    return f"- {name} · `/approve {name}` · `/reject {name}`"

body = [f"本周扫描:GitHub 命中 {len(found)},未收录 {len(missing)}"
        f"{'' if WRITE else '(report-only,未写库)'}。", ""]
if tiers['approved']:
    body += [f"## 已自动收录(≥1000★ 且命中主题词) {len(tiers['approved'])} 个 — 下轮 sync 可见", ""]
    body += [line(i) for i in tiers['approved']] + [""]
review = [line(i) for i in tiers['pending']] + [review_line(n) for n in form_pending]
if review:
    body += [f"## 待你定 {len(review)} 个 — 回复命令即可", ""]
    body += [f"{line(i)}\n  `/approve {i['full_name']}` · `/reject {i['full_name']}`" for i in tiers['pending']]
    body += [review_line(n) for n in form_pending] + [""]
body += [f"排除(fork/archived/清单):{len(tiers['excluded'])} 个,未列出。"]

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUT_DIR, exist_ok=True)
rows = [{'full_name': i['full_name'], 'stars': i['stargazers_count'],
         'description': i['description'], 'verdict': admission(i)} for i in missing]
json.dump(rows, open(os.path.join(OUT_DIR, 'missing-repos.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT_DIR, 'issue-body.md'), 'w').write("\n".join(body))
summary = {'scanned': len(found), 'missing': len(missing), 'auto_admitted': len(tiers['approved']),
           'to_review': len(review), 'written': written, 'top': rows[:20]}
json.dump(summary, open(os.path.join(OUT_DIR, 'missing-repos-summary.json'), 'w'), ensure_ascii=False, indent=1)
gh_out = os.environ.get('GITHUB_OUTPUT')
if gh_out:
    with open(gh_out, 'a') as f:
        f.write(f"missing={len(missing)}\nto_review={len(review)}\nauto_admitted={len(tiers['approved'])}\n")

print(f"\nGitHub 命中 {len(found)},未收录 {len(missing)}:自动收录 {len(tiers['approved'])}"
      f"({'已写库' if WRITE else '未写库'}),待定 {len(review)},排除 {len(tiers['excluded'])}")
for verdict in ('approved', 'pending'):
    for i in tiers[verdict]:
        print(f"  {verdict:9s} {i['stargazers_count']:>7,}★  {i['full_name']:<46} {(i['description'] or '')[:40]}")
```

Also change `conn.close()` at the old line 109 to stay open (the code above closes it): delete that line. Update the module docstring's last paragraph: "Run weekly; report-only by default, `--write` records verdicts in extra_repos (approved rows go active for the next sync, pending rows wait for a command)."

- [ ] **Step 2: Workflow** — in `catalog-coverage.yml`: the Scan step runs `python ops/find_missing_repos.py --write`; `outputs` gain `to_review` and `auto_admitted`; the Summary step prints those two numbers; `raise-issue` condition becomes `if: always() && needs.scan.outputs.missing != '' && needs.scan.outputs.missing != '0'`, adds `- uses: actions/download-artifact@v4` with `name: catalog-coverage` and `path: ops/output`, and its script builds the body from the file:

```js
            const fs = require('fs');
            const body = fs.readFileSync('ops/output/issue-body.md', 'utf8')
              + `\n\n[查看运行](https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId})`;
            const title = `目录覆盖:自动收录 ${'${{ needs.scan.outputs.auto_admitted }}'} 个,待定 ${'${{ needs.scan.outputs.to_review }}'} 个`;
```

(keep the existing open-issue lookup and comment-vs-create logic; drop the `n`/`total` lines).

- [ ] **Step 3: Dry run against #21's list (no `--write`)** — `python ops/find_missing_repos.py` locally (it needs `gh auth token` + `backend/.env`). Read the tier lines; expected ≈ 11 approved, the rest pending/excluded. Paste to the owner.
- [ ] **Step 4: Real run** — `python ops/find_missing_repos.py --write`; then `SELECT full_name, status, is_active, submitted_by FROM extra_repos WHERE submitted_by LIKE 'coverage-%' ORDER BY created_at DESC` shows the rows.
- [ ] **Step 5: YAML check + commit** — `python -c "import yaml; yaml.safe_load(open('.github/workflows/catalog-coverage.yml'))"`; `git commit -am "feat(coverage): the weekly scan admits high-star on-topic repos and lists the rest for a command"`

---

### Task 3: Submission-issue pre-review

**Files:** Create `ops/triage_submission.py`, `.github/workflows/submissions.yml`

- [ ] **Step 1: Script**

```python
"""Pre-review a 'Submit repository' issue: apply the admission rule, record the
verdict in extra_repos, and write a comment + labels for the workflow to post.

Reads ISSUE_NUMBER, ISSUE_TITLE, ISSUE_BODY, GITHUB_TOKEN, SUPABASE_DB_URL.
Writes ops/output/comment.md and appends labels=<a,b> close=<true|false> to
GITHUB_OUTPUT. Never fails the job for a bad submission — a missing link or a
404 is an answer to the submitter, not an error. With --dry-run nothing is written.
"""
import json, os, sys, urllib.error, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
from app.services.catalog_admission import admission, apply, parse_repo_url  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
DRY = '--dry-run' in sys.argv
README_MAX = 50000


def gh(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def readme_preview(full_name, repo):
    """Grade the README with the same rules the catalog uses; flag names only, no text."""
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{full_name}/readme", headers={
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github.raw"})
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", "replace")[:README_MAX]
    except Exception:
        return "无 README(无法评级)"
    from types import SimpleNamespace
    from app.services.security_scanner import SecurityScanner
    skill = SimpleNamespace(readme_content=text, author_name=full_name.split('/')[0],
                            stars=repo.get('stargazers_count', 0), license=(repo.get('license') or {}).get('spdx_id'),
                            repo_full_name=full_name, homepage_url=repo.get('homepage') or '')
    grade, flags = SecurityScanner().scan_single(skill)
    return f"{grade}" + (f"(标记:{', '.join(flags)})" if flags else "")


def finish(lines, labels, close=False):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'comment.md'), 'w').write("\n".join(lines))
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out, 'a') as f:
            f.write(f"labels={','.join(labels)}\nclose={'true' if close else 'false'}\n")
    print("\n".join(lines))


def main():
    n = os.environ['ISSUE_NUMBER']
    full_name = parse_repo_url(os.environ.get('ISSUE_BODY', '')) or parse_repo_url(os.environ.get('ISSUE_TITLE', ''))
    if not full_name:
        return finish(["没有在正文里找到 `github.com/owner/repo` 链接。请编辑 issue 补上仓库地址。"], ["needs-info"])
    try:
        repo = gh(f"/repos/{full_name}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return finish([f"`{full_name}` 在 GitHub 上不存在或是私有仓库,无法收录。"], ["needs-info"], close=True)
        return finish([f"GitHub 暂时不可用({e.code}),稍后重试。"], ["needs-retry"])
    verdict = admission(repo)
    status = verdict
    if not DRY and verdict != "excluded":
        import psycopg2
        conn = psycopg2.connect(os.environ['SUPABASE_DB_URL'], connect_timeout=30)
        status = apply(conn, repo['full_name'], verdict, f"issue-{n}")
        conn.commit(); conn.close()
    card = [f"### 预审:`{repo['full_name']}`", "",
            f"- ★ {repo.get('stargazers_count', 0):,} · 许可证 {(repo.get('license') or {}).get('spdx_id') or '无'}"
            f" · {'archived' if repo.get('archived') else ''}{'fork' if repo.get('fork') else ''}".rstrip(" ·"),
            f"- 主题词命中:{'是' if verdict != 'pending' or (repo.get('stargazers_count') or 0) < 1000 else '否'}",
            f"- README 安全评级预览:{readme_preview(repo['full_name'], repo)}", ""]
    if status == "approved":
        return finish(card + ["**已收录**,下轮同步(≤8h)后在目录可见。"], ["admitted"], close=True)
    if status == "rejected":
        return finish(card + ["这个仓库此前已被拒绝,不再收录。"], [], close=True)
    if verdict == "excluded":
        return finish(card + ["**未收录**:fork / archived / 链接清单不进目录。"], [], close=True)
    return finish(card + [f"**待定**:星数不足 1000 或描述未命中主题词。维护者回复 `/approve {repo['full_name']}` 收录,"
                          f"`/reject {repo['full_name']}` 拒绝。"], ["pending-review"])


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Workflow `.github/workflows/submissions.yml`**

```yaml
name: Submission triage

# A 'Submit repository' issue gets a pre-review comment within minutes: the
# admission rule (backend/app/services/catalog_admission.py) decides whether it
# is admitted now or waits for a maintainer's /approve. Until 2026-09-24 nothing
# read these issues at all.

on:
  issues:
    types: [opened]
  workflow_dispatch:
    inputs:
      issue:
        description: "Issue number to triage"
        required: true

permissions:
  contents: read
  issues: write

jobs:
  triage:
    if: github.event_name == 'workflow_dispatch' || startsWith(github.event.issue.title, 'Submit repository:') || startsWith(github.event.issue.title, '[Submission]')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: backend/requirements.txt
      # The README preview runs the catalog's own scanner, which lives in the backend.
      - name: Install deps
        run: pip install -r backend/requirements.txt

      - name: Load the issue
        id: issue
        env:
          GH_TOKEN: ${{ github.token }}
          N: ${{ github.event.inputs.issue || github.event.issue.number }}
        run: |
          echo "number=$N" >> "$GITHUB_OUTPUT"
          gh issue view "$N" --json title --jq .title > /tmp/title
          gh issue view "$N" --json body --jq .body > /tmp/body
          echo "title<<EOF" >> "$GITHUB_OUTPUT"; cat /tmp/title >> "$GITHUB_OUTPUT"; echo "EOF" >> "$GITHUB_OUTPUT"

      - name: Triage
        id: triage
        env:
          GITHUB_TOKEN: ${{ github.token }}
          SUPABASE_DB_URL: ${{ secrets.SUPABASE_DB_URL }}
          ISSUE_NUMBER: ${{ steps.issue.outputs.number }}
          ISSUE_TITLE: ${{ steps.issue.outputs.title }}
        run: |
          export ISSUE_BODY="$(cat /tmp/body)"
          python ops/triage_submission.py

      - name: Comment, label, close
        env:
          GH_TOKEN: ${{ github.token }}
          N: ${{ steps.issue.outputs.number }}
        run: |
          gh issue comment "$N" --body-file ops/output/comment.md
          if [ -n "${{ steps.triage.outputs.labels }}" ]; then gh issue edit "$N" --add-label "${{ steps.triage.outputs.labels }}"; fi
          if [ "${{ steps.triage.outputs.close }}" = "true" ]; then gh issue close "$N"; fi
```

Labels `admitted`, `pending-review`, `needs-info`, `needs-retry` must exist: `for l in admitted pending-review needs-info needs-retry; do gh label create "$l" --color 5319e7 2>/dev/null || true; done`.

- [ ] **Step 3: Dry run on the five open issues** — for each of 14 15 16 17 18: `ISSUE_NUMBER=N ISSUE_TITLE="$(gh issue view N --json title --jq .title)" ISSUE_BODY="$(gh issue view N --json body --jq .body)" GITHUB_TOKEN=$(gh auth token) python ops/triage_submission.py --dry-run` → prints the card and the tier. Paste the five verdicts to the owner.
- [ ] **Step 4: Commit** — `git add ops/triage_submission.py .github/workflows/submissions.yml && git commit -m "feat(submissions): pre-review submission issues with the admission rule"`. After push, `gh workflow run submissions.yml -f issue=N` for each of the five.

---

### Task 4: `/approve` and `/reject` commands

**Files:** Create `ops/admission_command.py`, `.github/workflows/admission-commands.yml`

- [ ] **Step 1: Script**

```python
"""Apply /approve owner/repo and /reject owner/repo from a maintainer's comment.

Reads COMMENT_BODY, COMMENT_AUTHOR, COMMENT_ASSOCIATION, ISSUE_TITLE,
SUPABASE_DB_URL. Writes ops/output/comment.md (empty when there is nothing to
say) and close=<true|false> to GITHUB_OUTPUT. Non-maintainers are ignored
silently: replying would make the bot a toy.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
from app.services.catalog_admission import decide, parse_commands  # noqa: E402

MAINTAINERS = {"OWNER", "MEMBER", "COLLABORATOR"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
DONE = {"approved": "已收录,下轮同步可见", "rejected": "已拒绝", "absent": "没有这条记录,无法拒绝"}


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
    conn.commit(); conn.close()
    for line in bad:
        lines.append(f"- 无法解析:`{line}`(格式 `/approve owner/repo`)")
    # A submission issue is done once its repo is decided; the weekly coverage issue stays open.
    is_submission = os.environ.get('ISSUE_TITLE', '').startswith(('Submit repository:', '[Submission]'))
    close = is_submission and bool(results) and all(r in ('approved', 'rejected') for r in results)
    finish(lines, close)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Workflow `.github/workflows/admission-commands.yml`**

```yaml
name: Admission commands

# /approve owner/repo and /reject owner/repo in an issue comment, from a
# maintainer, flip the extra_repos row. The weekly coverage issue and the
# submission pre-review both hand out these commands.

on:
  issue_comment:
    types: [created]

permissions:
  contents: read
  issues: write

jobs:
  apply:
    if: contains(github.event.comment.body, '/approve') || contains(github.event.comment.body, '/reject')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: pip install psycopg2-binary

      - name: Apply
        id: apply
        env:
          SUPABASE_DB_URL: ${{ secrets.SUPABASE_DB_URL }}
          COMMENT_BODY: ${{ github.event.comment.body }}
          COMMENT_AUTHOR: ${{ github.event.comment.user.login }}
          COMMENT_ASSOCIATION: ${{ github.event.comment.author_association }}
          ISSUE_TITLE: ${{ github.event.issue.title }}
        run: python ops/admission_command.py

      - name: Reply
        if: steps.apply.outputs.say == 'true'
        env:
          GH_TOKEN: ${{ github.token }}
          N: ${{ github.event.issue.number }}
        run: |
          gh issue comment "$N" --body-file ops/output/comment.md
          if [ "${{ steps.apply.outputs.close }}" = "true" ]; then gh issue close "$N"; fi
```

- [ ] **Step 3: Commit** — `git add ops/admission_command.py .github/workflows/admission-commands.yml && git commit -m "feat(catalog): /approve and /reject commands for maintainers"`. After push, test on the weekly issue with a `/reject` of a known false positive and confirm the reply.

---

### Task 5: Truncation warning and wave-query slices

**Files:** Modify `backend/app/services/sync_selection.py`, `backend/app/scheduler/jobs.py:454-475`; Test `backend/tests/test_sync_selection.py`

- [ ] **Step 1: Failing tests** (append)

```python
from app.services.sync_selection import wave_slices


def test_wave_queries_get_star_band_slices():
    q = "jev in:name,description,topics created:>=2026-09-15"
    assert wave_slices(q) == [q + " stars:50..199", q + " stars:20..49"]


def test_ordinary_queries_get_no_slices():
    assert wave_slices("mcp-server in:name,topics") == []
```

- [ ] **Step 2: Implement** in `sync_selection.py`

```python
# A wave query (created:>=) returns thousands of repos, sorted by stars, and the
# sync reads 300. The top 300 covers everything a scenario page shows (≥50★),
# but the 20–199★ tail — the repos the wave page will list next month — never
# enters. Two star bands, each read to the same 3-page cap, catch it.
WAVE_STAR_BANDS = ("stars:50..199", "stars:20..49")


def wave_slices(query: str) -> list[str]:
    if "created:>" not in query:
        return []
    return [f"{query} {band}" for band in WAVE_STAR_BANDS]
```

- [ ] **Step 3: jobs.py Phase 1** — after `effective_query = with_push_filter(query, pushed_filter)`, iterate over `[effective_query, *wave_slices(effective_query)]` in place of the single query; keep the page loop per variant; when `page == 3 and len(items) == 100`, log `logger.warning("Search truncated at 300 for [%s]: total_count=%s", variant, data.get("total_count"))`. Concretely:

```python
                effective_query = with_push_filter(query, pushed_filter)
                for variant in [effective_query, *wave_slices(effective_query)]:
                    try:
                        for page in range(1, 4):  # up to 3 pages per query
                            data = await _github_request(
                                client,
                                "https://api.github.com/search/repositories",
                                params={"q": variant, "per_page": 100, "page": page, "sort": "stars"},
                            )
                            items = data.get("items", [])
                            for repo in items:
                                fn = repo.get("full_name", "")
                                if fn and fn not in all_repos:
                                    all_repos[fn] = repo
                            if len(items) < 100:
                                break
                            if page == 3:
                                logger.warning("Search truncated at 300 for [%s]: total_count=%s",
                                               variant, data.get("total_count"))
                            # Respect search rate limit: 30 req/min → ~2s per request
                            await asyncio.sleep(2.5)
                    except Exception as exc:
                        logger.error("Search failed [%s]: %s", variant, exc)
                    await asyncio.sleep(2)
```

Import `wave_slices` beside `with_push_filter`.

- [ ] **Step 4: Run** — suite green; `python -c "import app.scheduler.jobs"`. **Commit** — `git commit -am "feat(sync): slice wave queries by star band and log search truncation"`. Verify on the next sync log: `Search truncated` lines and the Jev slices present.

---

### Task 6: Rollout

- [ ] Push Task 1–2 first; run the coverage scan dry, paste tiers, run `--write`, confirm `extra_repos` rows; next sync ingests them (check `/skill/dream-num/univer/` exists after the deploy).
- [ ] Push Tasks 3–4; create the four labels; dispatch `submissions.yml` for issues 14–18; check each got its card.
- [ ] Push Task 5; read the next sync log.
- [ ] Memory: `catalog-admission-2026-09.md` (rule, sources, commands) + MEMORY.md line; update `sync-discovery-gap-2026-09.md` "How to apply" to point at the rule.
