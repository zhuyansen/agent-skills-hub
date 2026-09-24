"""Pre-review a 'Submit repository' issue: apply the admission rule, record the
verdict in extra_repos, and write a comment + labels for the workflow to post.

Reads ISSUE_NUMBER, ISSUE_TITLE, ISSUE_BODY, GITHUB_TOKEN, SUPABASE_DB_URL.
Writes ops/output/comment.md and appends labels=<a,b> close=<true|false> to
GITHUB_OUTPUT. Never fails the job for a bad submission — a missing link or a
404 is an answer to the submitter, not an error. With --dry-run nothing is written.
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
from app.services.catalog_admission import admission, apply, on_topic, parse_repo_url  # noqa: E402

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
    except Exception:  # noqa: BLE001 — 404 or network: the preview is optional
        return "无 README(无法评级)"
    from types import SimpleNamespace
    from app.services.security_scanner import SecurityScanner
    skill = SimpleNamespace(readme_content=text, author_name=full_name.split('/')[0],
                            stars=repo.get('stargazers_count', 0),
                            license=(repo.get('license') or {}).get('spdx_id'),
                            repo_full_name=full_name, homepage_url=repo.get('homepage') or '')
    grade, flags = SecurityScanner().scan_single(skill)
    return grade + (f"(标记:{', '.join(flags)})" if flags else "")


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
        conn.commit()
        conn.close()
    kind = " · ".join(k for k, on in (("archived", repo.get('archived')), ("fork", repo.get('fork'))) if on)
    card = [f"### 预审:`{repo['full_name']}`", "",
            f"- ★ {repo.get('stargazers_count', 0):,} · 许可证 {(repo.get('license') or {}).get('spdx_id') or '无'}"
            + (f" · {kind}" if kind else ""),
            f"- 主题词命中:{'是' if on_topic(repo) else '否'}",
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
