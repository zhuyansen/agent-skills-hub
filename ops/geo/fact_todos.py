"""Turn fact-consistency conflicts into to-dos: which file to change, to what, and what to do after.

fact_consistency.py says *that* a node states a stale fact. This says where the text lives and
what to write instead, so the daily mail is a list of edits rather than a list of symptoms.

Rules for what to write (agreed 2026-11-22, because the catalog grows every sync):
  - a page this repo builds: use a count marker (<span data-count="total">), which the build
    fills from the database, so the page never goes stale again;
  - anything published and frozen (static JSON, a package README, a listing): a count rounded
    down to the 50,000 (indexed) or 5,000 (graded), written "250K+"; true as long as the
    catalog does not shrink, and inside the check's tolerance until it grows ~20% past it;
  - another fact (date, rule count, founder): the ledger's value.

Pure apart from reading files under `repo`; the GitHub lookup for the npm packages is passed in.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

FLOOR_STEP = {"directory_size": 50_000, "graded_count": 5_000}   # graded: the check allows only 5%
MARKER = {"directory_size": "total", "graded_count": "graded"}
NUMBER = re.compile(r"\d[\d,.]*\s?[KkMm]?")

# source -> where its text comes from
BUILT_PAGES = {
    "site_home": ["frontend/index.html", "frontend/scripts/home-markdown.mjs"],
    "site_about": ["frontend/scripts/generate-static-pages.mjs"],
    "site_ai_info": ["frontend/scripts/generate-static-pages.mjs"],
    "site_contact": ["frontend/scripts/generate-static-pages.mjs"],
    "site_how_we_grade": ["frontend/scripts/generate-static-pages.mjs"],
    "site_llms_txt": ["frontend/scripts/generate-llms-txt.mjs", "frontend/public/llms.txt"],
}
STATIC_FILES = {
    "site_mcp_server_card": ["frontend/public/.well-known/mcp/server-card.json"],
    "github_readme": ["README.md"],
}
PACKAGES = {  # npm package -> its GitHub repo and the files its copy lives in
    "npm_cli": ("zhuyansen/agentskillshub-cli", ["README.md", "SKILL.md", "bin/ash.mjs"]),
    "npm_mcp": ("zhuyansen/agentskillshub-mcp", ["README.md", "SKILL.md", "manifest.json", "src/index.mjs"]),
}
EXTERNAL = {
    "github_repo": ("GitHub 仓库简介", "gh repo edit zhuyansen/agent-skills-hub --description \"…\""),
    "wikidata_org": ("Wikidata Q141986406", "https://www.wikidata.org/wiki/Q141986406 手动编辑"),
    "wikidata_dataset": ("Wikidata Q141735092", "https://www.wikidata.org/wiki/Q141735092 手动编辑"),
    "zenodo_21292799": ("Zenodo 21292799", "Zenodo 上点 Edit 改描述（不必发新版本）"),
    "zenodo_24387074": ("Zenodo 24387074", "Zenodo 上点 Edit 改描述（不必发新版本）"),
}


def token_of(found: Any) -> str:
    """The text to search for: '132,000+ repositories' -> '132,000', '130K+ skills' -> '130K'."""
    m = NUMBER.match(str(found).strip())
    return m.group(0).strip() if m else str(found)


def floor_text(value: int, step: int) -> str:
    """281,000 rounded down to the 50,000, written as copy: '250K+'."""
    floored = max(step, value // step * step)
    return f"{floored // 1000}K+"


def closest_live(found_value: int, live: dict[str, int | None]) -> str:
    """Which live count a stale number was trying to state: the one it is closest to by ratio."""
    known = {k: v for k, v in live.items() if v}
    if not known:
        return "directory_size"
    return min(known, key=lambda k: abs(found_value - known[k]) / known[k])


def find_lines(repo: Path, files: list[str], token: str) -> list[dict[str, Any]]:
    hits = []
    for rel in files:
        path = repo / rel
        if not path.is_file():
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if token in line:
                at = line.index(token)
                near = line[max(0, at - 60): at + 60]
                hits.append({"file": rel, "line": i, "marked": "data-count" in near})
    return hits


def todo_for(conflict: dict[str, Any], live: dict[str, int | None], repo: Path,
             github_has: Callable[[str, str, str], bool | None] | None = None) -> dict[str, Any]:
    source, fact, found = conflict["source"], conflict["fact"], conflict["found"]
    token = token_of(found)
    todo: dict[str, Any] = {"source": source, "fact": fact, "found": str(found), "url": conflict["url"],
                            "where": [], "replace_with": str(conflict["expected"]), "then": "", "note": ""}

    count = fact == "skill_count"
    if count:
        from fact_consistency import parse_count  # same parser the check used
        try:
            which = closest_live(parse_count(token), live)
        except (ValueError, IndexError):
            which = "directory_size"
        live_value = live.get(which) or 0
        todo["replace_with"] = floor_text(live_value, FLOOR_STEP[which]) if live_value else str(conflict["expected"])
        smallest = min((v for v in live.values() if v), default=0)
        if smallest and parse_count(token) < smallest / 2:
            todo["replace_with"] = "先核对这个数说的是什么"
            todo["note"] = ("远小于两个实时数，多半是个子集（比如 CLI 离线目录）；是子集就把它写进 "
                            "brand-facts.json 的 other_counts，不是就按收录数往下取整")

    if source in BUILT_PAGES:
        hits = find_lines(repo, BUILT_PAGES[source], token)
        todo["where"] = [h for h in hits if not h["marked"]]
        todo["then"] = "合进 main 后等前端部署"
        if count:
            todo["replace_with"] = f'<span data-count="{MARKER[which]}">…</span>（构建时自动填数）'
        if hits and not todo["where"]:
            todo["note"] = "源文件里这个数已是自动填数标记，线上是旧构建；下次部署后自动消失，不用改"
        elif not hits:
            todo["note"] = "源文件里没搜到原文，可能已改好待部署，或文字由别处生成"
    elif source in STATIC_FILES:
        hits = find_lines(repo, STATIC_FILES[source], token)
        todo["where"] = hits
        todo["then"] = "合进 main 后等前端部署" if source.startswith("site_") else "合进 main 即生效"
        if not hits:
            todo["note"] = "仓库里已搜不到原文：已改好，等部署"
    elif source in PACKAGES:
        repo_name, files = PACKAGES[source]
        todo["where"] = [{"file": f"{repo_name}: {f}", "line": None, "marked": False} for f in files]
        todo["then"] = "升版本号，npm publish（要先 npm login）"
        fixed = [f for f in files if github_has and github_has(repo_name, f, token) is False]
        if github_has and len(fixed) == len(files):
            todo["where"] = []
            todo["note"] = "GitHub 上已改好，只差 npm publish"
    elif source in EXTERNAL:
        label, how = EXTERNAL[source]
        todo["where"] = [{"file": label, "line": None, "marked": False}]
        todo["then"] = how
    return todo


def build_todos(node: dict[str, Any], repo: Path,
                github_has: Callable[[str, str, str], bool | None] | None = None) -> list[dict[str, Any]]:
    """One to-do per (source, fact, found): the same stale text repeated on a page is one edit."""
    live = {"directory_size": node.get("live_directory_size"), "graded_count": node.get("live_graded_count")}
    seen, out = set(), []
    for c in node.get("conflicts", []):
        key = (c["source"], c["fact"], token_of(c["found"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(todo_for(c, live, repo, github_has))
    return out


def github_has_via(http_get: Callable[..., tuple[int, dict[str, str], str]]) -> Callable[[str, str, str], bool | None]:
    """Does `file` on a repo's main branch still contain `token`? None when it cannot be read."""
    def has(repo_name: str, file: str, token: str) -> bool | None:
        code, _, body = http_get(f"https://raw.githubusercontent.com/{repo_name}/main/{file}")
        return token in body if code == 200 else None
    return has
