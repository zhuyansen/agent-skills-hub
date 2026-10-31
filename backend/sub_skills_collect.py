#!/usr/bin/env python3
"""Sub-skill collector: one sub_skills row per SKILL.md in repositories that hold several skills.

The catalog is one row per repository, so a skill that lives in a folder of a larger
repository (mnapoli/skills holds unslop, implement, interview...) had no page of its own
and could not rank for its own name. Most-starred repositories first, this lists each
repository's files with one GitHub trees call, downloads every SKILL.md from
raw.githubusercontent.com (not counted against the API quota), reads its frontmatter,
grades the text with the README scanner, and writes sub_skills (migration 039). A
repository with fewer than MIN_SKILLS SKILL.md files gets no rows: its own page covers it.

sub_skill_scans remembers each repository's last listing. A repository is listed again
only when it has commits since (skills.last_commit_at) or after RESCAN_DAYS, and a
SKILL.md whose blob is unchanged is not downloaded again.

Shares readme_backfill's pacing, quota floor and running-sync check.

Env:  GH_TOKEN; SUPABASE_DB_URL (or backend/.env);
      GITHUB_REPOSITORY + ACTIONS_TOKEN (optional) to see a running sync.
Args: --min-stars N (500)  --cap N (400)  --minutes N (35)  --repo OWNER/NAME (repeatable)
      --refresh (parse unchanged SKILL.md files again, after a parser change)  --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from types import SimpleNamespace

from readme_backfill import Pacer, db_url, quota_exhausted, summarize, sync_active

MIN_SKILLS = 2              # fewer SKILL.md files than this: the repository page is the skill page
MAX_SKILLS_PER_REPO = 300   # a collection with thousands of skills keeps its first 300 (by path)
RESCAN_DAYS = 30
DEFAULT_MIN_STARS = 500     # the parents whose pages Google may index (MIN_STARS_TO_INDEX)
DEFAULT_CAP = 400           # repositories per run: one trees call each
DEFAULT_MINUTES = 35        # then stop cleanly; the Actions job is killed at 45
MIN_INTERVAL = 0.25         # seconds between request starts; most are raw downloads, which the quota skips
HTTP_TIMEOUT = 30
DESCRIPTION_MAX = 600
EXCERPT_MAX = 900
SKILL_MD_MAX = 60000
SKILL_FILE = "skill.md"
SKIP_SEGMENTS = {"node_modules", "vendor", "dist", "build", "fixtures", ".git", "template", "templates",
                 "_template", "skill-template",
                 # drafts and retired skills (mattpocock/skills keeps drafts in skills/in-progress/)
                 "deprecated", "archive", "archived", "wip", "draft", "drafts", "in-progress",
                 # demos and test data (gemini-cli's packages/sdk/test-data/skills/pirate-skill)
                 "example", "examples", "test", "tests", "test-data", "testdata", "__tests__"}
# Translated copies (affaan-m/ECC keeps 700 of its 1,068 SKILL.md files under docs/<language>/).
LOCALE_FOLDER = re.compile(r"^([a-z]{2})[-_]([a-z]{2}|hans|hant)$", re.I)  # ja-JP, zh-cn, pt_BR, zh-Hans
LOCALE_PARENTS = {"docs", "doc", "i18n", "l10n", "locales", "locale", "translations", "lang", "languages"}
LANGUAGES = {"ar", "de", "es", "fr", "id", "it", "ja", "ko", "nl", "pl", "pt", "ru", "th", "tr", "uk", "vi", "zh"}
RESERVED_SLUGS = {"index", "zh"}
LIST_MARK = re.compile(r"^\s{0,3}(?:[-*+]|\d+\.)\s+")
SENTENCE_ENDS = tuple(".!?:;,。！？；：")
USER_AGENT = "agentskillshub-sub-skills"

CANDIDATE_SQL = (
    "SELECT s.repo_full_name, s.stars, s.license FROM skills s "
    "LEFT JOIN sub_skill_scans c ON c.repo_full_name = s.repo_full_name "
    "WHERE s.stars >= %(min_stars)s AND s.repo_status IS DISTINCT FROM 'gone' "
    f"AND (c.repo_full_name IS NULL OR c.scanned_at < now() - interval '{RESCAN_DAYS} days' "
    "OR s.last_commit_at > c.scanned_at) "
    "ORDER BY (c.repo_full_name IS NULL) DESC, s.stars DESC LIMIT %(cap)s"
)
NAMED_SQL = "SELECT repo_full_name, stars, license FROM skills WHERE repo_full_name = ANY(%(names)s)"
KNOWN_SQL = "SELECT path, blob_sha, slug, name, description, body_excerpt, security_grade, security_flags " \
            "FROM sub_skills WHERE repo_full_name = %s"
UPSERT_SQL = (
    "INSERT INTO sub_skills (repo_full_name, path, slug, name, description, body_excerpt, "
    "security_grade, security_flags, blob_sha, fetched_at) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, now()) "
    "ON CONFLICT (repo_full_name, path) DO UPDATE SET slug = EXCLUDED.slug, name = EXCLUDED.name, "
    "description = EXCLUDED.description, body_excerpt = EXCLUDED.body_excerpt, "
    "security_grade = EXCLUDED.security_grade, security_flags = EXCLUDED.security_flags, "
    "blob_sha = EXCLUDED.blob_sha, fetched_at = now()"
)
# Rows for folders that no longer hold a SKILL.md; all of them when the repository is gone or
# now holds a single skill.
PRUNE_SQL = "DELETE FROM sub_skills WHERE repo_full_name = %s AND NOT (path = ANY(%s::text[]))"
SCAN_SQL = (
    "INSERT INTO sub_skill_scans (repo_full_name, tree_sha, skill_count, status, scanned_at) "
    "VALUES (%s, %s, %s, %s, now()) ON CONFLICT (repo_full_name) DO UPDATE SET "
    "tree_sha = EXCLUDED.tree_sha, skill_count = EXCLUDED.skill_count, status = EXCLUDED.status, scanned_at = now()"
)


# ── pure helpers (tested in tests/test_sub_skills_collect.py) ──────────────────────────

def is_locale(segment: str, parent: str) -> bool:
    m = LOCALE_FOLDER.match(segment)
    if m:
        return m.group(1).lower() in LANGUAGES
    return parent.lower() in LOCALE_PARENTS and segment.lower() in LANGUAGES


def is_translation(segments: list[str]) -> bool:
    """docs/ja-JP/..., i18n/zh-CN/..., docs/tr/...: a translated copy of a skill."""
    return any(is_locale(seg, parent) for parent, seg in zip([""] + segments, segments))


def skill_md_blobs(tree: list[dict]):
    """(folder, blob sha) for every SKILL.md outside vendored, build, template and translation folders."""
    for entry in tree:
        path = entry.get("path", "")
        if entry.get("type") != "blob" or path.rsplit("/", 1)[-1].lower() != SKILL_FILE:
            continue
        folder = path.rsplit("/", 1)[0] if "/" in path else ""
        segments = [s for s in folder.split("/") if s]
        if not any(s.lower() in SKIP_SEGMENTS for s in segments) and not is_translation(segments):
            yield folder, entry.get("sha", "")


def canonical_rank(folder: str) -> tuple[int, int, str]:
    """Fewest dot-folders, then shallowest: skills/x beats .kiro/skills/x and pi/core/skills/x."""
    segments = folder.split("/") if folder else []
    return sum(s.startswith(".") for s in segments), len(segments), folder


def skill_md_paths(tree: list[dict]) -> list[tuple[str, str]]:
    """(folder, blob sha), one per skill name: copies made for other agents collapse to one."""
    best: dict[str, tuple[str, str]] = {}
    for folder, sha in skill_md_blobs(tree):
        key = folder.rsplit("/", 1)[-1].lower()
        if key not in best or canonical_rank(folder) < canonical_rank(best[key][0]):
            best[key] = (folder, sha)
    return sorted(sorted(best.values(), key=lambda v: canonical_rank(v[0]))[:MAX_SKILLS_PER_REPO])


def slugify(text: str) -> str:
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def assign_slugs(items: list[tuple[str, str]], stable: dict[str, str] | None = None) -> dict[str, str]:
    """folder -> URL slug, unique within the repository. A published slug (`stable`) never changes;
    a new skill gets its folder's last segment, else its name."""
    slugs: dict[str, str] = dict(stable or {})
    taken: set[str] = set(slugs.values())
    for folder, name in items:
        if folder in slugs:
            continue
        base = slugify(folder.rsplit("/", 1)[-1] if folder else name) or "skill"
        if base in RESERVED_SLUGS:
            base = f"{base}-skill"
        slug, n = base, 2
        while slug in taken:
            slug, n = f"{base}-{n}", n + 1
        taken.add(slug)
        slugs[folder] = slug
    return slugs


def split_frontmatter(text: str) -> tuple[dict, str]:
    """(frontmatter fields, body). A file without a closing '---' has no frontmatter."""
    lines = text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        return {}, text
    return parse_fields("\n".join(lines[1:end])), "\n".join(lines[end + 1:])


def parse_fields(block: str) -> dict:
    import yaml
    try:
        data = yaml.safe_load(block)
        if isinstance(data, dict):
            return data
    except yaml.YAMLError:
        pass
    # Unquoted colons break YAML ("description: Use when: ..."); take the plain lines.
    return {k: v.strip().strip("\"'") for k, v in re.findall(r"^(name|description):\s*(.+)$", block, re.M)}


def close_list_items(text: str) -> str:
    """Drop list markers and end each item with a full stop, so "Use for: - Test failures - Bugs"
    does not read "Test failures Bugs" once the lines are joined. Indented lines continue an item."""
    out: list[str] = []
    open_item = False
    for line in text.split("\n"):
        starts = LIST_MARK.match(line) is not None
        continues = open_item and not starts and line[:1] in (" ", "\t") and line.strip() != ""
        if open_item and not continues and not out[-1].rstrip().endswith(SENTENCE_ENDS):
            out[-1] = out[-1].rstrip() + "."
        open_item = starts or continues
        out.append(LIST_MARK.sub("", line) if starts else line)
    if open_item and not out[-1].rstrip().endswith(SENTENCE_ENDS):
        out[-1] = out[-1].rstrip() + "."
    return "\n".join(out)


def plain_text(markdown: str) -> str:
    """Prose only: headings, code, tables' rules and slash-command placeholders would run into it."""
    text = re.sub(r"```.*?```", " ", markdown, flags=re.S)
    text = re.sub(r"^\s{0,3}#{1,6}\s.*$|^[\s|:-]{3,}$|\$ARGUMENTS\b", " ", text, flags=re.M)
    text = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s{0,3}>\s+", "", close_list_items(text), flags=re.M)
    text = re.sub(r"[*`|]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def cut(text: str, limit: int) -> str:
    """At most `limit` characters, ending on a sentence when one ends past the halfway mark."""
    if len(text) <= limit:
        return text
    head = text[:limit]
    end = max(head.rfind(". "), head.rfind("。"), head.rfind("! "), head.rfind("? "))
    return head[:end + 1].strip() if end > limit // 2 else head.rsplit(" ", 1)[0].strip() + "…"


def parse_skill_md(text: str, folder: str) -> tuple[str, str, str]:
    """(name, description, excerpt) of one SKILL.md; the folder names a skill without frontmatter."""
    fields, body = split_frontmatter(text[:SKILL_MD_MAX])
    excerpt = cut(plain_text(body), EXCERPT_MAX)
    name = str(fields.get("name") or "").strip() or (folder.rsplit("/", 1)[-1] if folder else "")
    description = re.sub(r"\s+", " ", str(fields.get("description") or "")).strip()
    return name, cut(description or excerpt, DESCRIPTION_MAX), excerpt


# ── GitHub ────────────────────────────────────────────────────────────────────────────

def http_get(url: str, token: str | None, pacer: Pacer, accept: str) -> tuple[int, bytes, int, str]:
    """(status, body, API quota left, URL answered after redirects). Quota is 5000 for raw
    downloads, which do not count."""
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    pacer.wait()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=HTTP_TIMEOUT) as r:
            return r.status, r.read(), int(r.headers.get("X-RateLimit-Remaining", "5000")), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, b"", int(e.headers.get("X-RateLimit-Remaining", "5000")), url
    except Exception:  # noqa: BLE001 — URLError, timeout, SSL: count as an error, retry next run
        return 0, b"", 5000, url


def list_tree(full_name: str, token: str, pacer: Pacer) -> tuple[str, dict | None, int]:
    """('ok' | 'moved' | 'absent' | 'error', tree json or None, quota). A renamed repository answers
    its old name with a redirect to /repositories/<id>/ (affaan-m/everything-claude-code, now
    affaan-m/ECC): the catalog's row under the new name gets the skills, not this stale one."""
    url = f"https://api.github.com/repos/{full_name}/git/trees/HEAD?recursive=1"
    status, body, left, answered = http_get(url, token, pacer, "application/vnd.github+json")
    if status == 200:
        return ("ok", json.loads(body), left) if answered == url else ("moved", None, left)
    if status in (403, 429):
        return "error", None, 0  # rate limited: the quota check ends the run
    return ("absent", None, left) if status in (404, 409) else ("error", None, left)


def download(full_name: str, folder: str, pacer: Pacer) -> str | None:
    path = f"{folder}/SKILL.md" if folder else "SKILL.md"
    url = f"https://raw.githubusercontent.com/{full_name}/HEAD/{path}"
    status, body, _, _ = http_get(url, None, pacer, "text/plain")
    return body.decode("utf-8", "replace") if status == 200 else None


# ── one repository ────────────────────────────────────────────────────────────────────

@dataclass
class Repo:
    full_name: str
    stars: int
    license: str | None
    rows: list[tuple] = field(default_factory=list)


def grade(text: str, repo: Repo) -> tuple[str, list[str]]:
    from app.services.security_scanner import SecurityScanner
    owner = repo.full_name.split("/")[0]
    target = SimpleNamespace(readme_content=text, author_name=owner, license=repo.license, stars=repo.stars)
    return SecurityScanner().scan_single(target)


def parse_all(repo: Repo, paths: list[tuple[str, str]], known: dict, pacer: Pacer, refresh: bool) -> dict:
    """folder -> ('keep', stored row) | ('new', (sha, text, name, description, excerpt)). An unchanged
    blob keeps its stored row instead of a new download; so does one whose download failed this time."""
    parsed = {}
    for folder, sha in paths:
        if not refresh and folder in known and known[folder][1] == sha:
            parsed[folder] = ("keep", known[folder])
            continue
        text = download(repo.full_name, folder, pacer)
        if text is not None:
            parsed[folder] = ("new", (sha, text, *parse_skill_md(text, folder)))
        elif folder in known:
            parsed[folder] = ("keep", known[folder])
    return parsed


def build_rows(repo: Repo, paths: list[tuple[str, str]], known: dict, pacer: Pacer, refresh: bool) -> None:
    parsed = parse_all(repo, paths, known, pacer, refresh)
    stable = {f: known[f][2] for f in parsed if f in known}
    slugs = assign_slugs([(f, v[1][3] if v[0] == "keep" else v[1][2]) for f, v in parsed.items()], stable)
    for folder, (kind, data) in parsed.items():
        if kind == "keep":
            _, sha, _, name, desc, excerpt, sec_grade, flags = data
        else:
            sha, text, name, desc, excerpt = data
            sec_grade, flags = grade(text, repo)
        repo.rows.append((repo.full_name, folder, slugs[folder], name, desc, excerpt,
                          sec_grade, json.dumps(flags if isinstance(flags, list) else list(flags or [])), sha))


def write_repo(conn, repo: Repo, tree_sha: str | None, count: int, status: str) -> None:
    with conn, conn.cursor() as cur:
        cur.execute("SET LOCAL statement_timeout = '30s'")
        # Prune first: a skill whose folder moved keeps its slug, which the old row still holds.
        cur.execute(PRUNE_SQL, (repo.full_name, [r[1] for r in repo.rows]))
        for row in repo.rows:
            cur.execute(UPSERT_SQL, row)
        cur.execute(SCAN_SQL, (repo.full_name, tree_sha, count, status))


def known_rows(conn, full_name: str) -> dict:
    with conn, conn.cursor() as cur:
        cur.execute("SET LOCAL statement_timeout = '30s'")
        cur.execute(KNOWN_SQL, (full_name,))
        return {r[0]: r for r in cur.fetchall()}


def process(conn, repo: Repo, token: str, pacer: Pacer, args: argparse.Namespace) -> tuple[str, int, int]:
    """(status, SKILL.md files found, quota left) for one repository."""
    status, tree, left = list_tree(repo.full_name, token, pacer)
    if status == "error":
        return status, 0, left
    paths = skill_md_paths(tree.get("tree", [])) if tree else []
    if len(paths) >= MIN_SKILLS:
        build_rows(repo, paths, known_rows(conn, repo.full_name), pacer, args.refresh)
    if not args.dry_run:
        write_repo(conn, repo, tree.get("sha") if tree else None, len(paths), status)
    return status, len(paths), left


# ── run ───────────────────────────────────────────────────────────────────────────────

def candidates(conn, min_stars: int, cap: int, names: list[str] | None) -> list[Repo]:
    """The next batch, or the named repositories whatever their last scan."""
    with conn, conn.cursor() as cur:
        cur.execute("SET LOCAL statement_timeout = '60s'")
        if names:
            cur.execute(NAMED_SQL, {"names": names})
        else:
            cur.execute(CANDIDATE_SQL, {"min_stars": min_stars, "cap": cap})
        return [Repo(full_name=r[0], stars=r[1] or 0, license=r[2]) for r in cur.fetchall()]


def tally(counts: dict, repo: Repo, status: str, found: int) -> None:
    counts["repos"] += 1
    if status != "ok":
        counts[status] += 1
    counts["multi"] += found >= MIN_SKILLS
    counts["rows"] += len(repo.rows)
    if repo.rows:
        print(f"  {repo.full_name}: {len(repo.rows)} skills", flush=True)


def run(conn, targets: list[Repo], token: str, args: argparse.Namespace) -> tuple[dict, str]:
    """Stops early, keeping what it wrote, for a running sync, the time budget or the quota floor."""
    pacer = Pacer(MIN_INTERVAL)
    deadline = time.monotonic() + args.minutes * 60
    counts = {"repos": 0, "multi": 0, "rows": 0, "absent": 0, "moved": 0, "error": 0}
    for i, repo in enumerate(targets):
        if i % 50 == 0 and sync_active():
            return counts, "a sync is queued or running"
        if time.monotonic() > deadline:
            return counts, f"time budget ({args.minutes:g} min) used"
        status, found, left = process(conn, repo, token, pacer, args)
        tally(counts, repo, status, found)
        if quota_exhausted(left):
            return counts, f"GitHub quota {left} under the floor"
    return counts, ""


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-stars", type=int, default=DEFAULT_MIN_STARS)
    ap.add_argument("--cap", type=int, default=DEFAULT_CAP)
    ap.add_argument("--minutes", type=float, default=DEFAULT_MINUTES, help="time budget")
    ap.add_argument("--repo", action="append", help="this repository only, whatever its last scan (repeatable)")
    ap.add_argument("--refresh", action="store_true", help="parse every SKILL.md again, unchanged ones too")
    ap.add_argument("--dry-run", action="store_true", help="list and parse, write nothing")
    return ap.parse_args()


def main() -> int:
    import psycopg2
    args = parse_args()
    token = os.environ["GH_TOKEN"].strip()
    conn = psycopg2.connect(db_url(), connect_timeout=30)
    targets = candidates(conn, args.min_stars, args.cap, args.repo)
    print(f"targets: {len(targets)} (>= {args.min_stars} stars, cap {args.cap})", flush=True)
    counts, stopped = run(conn, targets, token, args)
    conn.close()
    summarize([
        "## Sub-skill collector" + (" (dry run)" if args.dry_run else ""),
        f"- repositories listed: {counts['repos']} · with {MIN_SKILLS}+ SKILL.md: {counts['multi']} · "
        f"skills written: {counts['rows']} · gone or empty: {counts['absent']} · old names of renamed "
        f"repositories: {counts['moved']} · errors (retried next run): {counts['error']}",
        f"- stopped early: {stopped}" if stopped else "- ran to the end of its batch",
    ])
    return 1 if counts["error"] > max(10, counts["repos"] // 10) else 0


if __name__ == "__main__":
    sys.exit(main())
