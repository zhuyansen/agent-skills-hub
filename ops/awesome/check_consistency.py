"""A scenario page and its GitHub list must hold the same entries with the same types.

Reads the live page and the list's published data/skills.json. Exit code 1 on any
difference, with the entries named.

Usage: python ops/awesome/check_consistency.py [slug]   (default: claude-video-skills)
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

LISTS = {   # page slug -> its GitHub list repo
    "claude-video-skills": "zhuyansen/awesome-claude-video-skills",
    "ppt-presentation": "zhuyansen/awesome-codex-ppt-skills",
    "typesafe-jev": "zhuyansen/awesome-typesafe-jev",
}
sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_text_pages import PAGE_LISTS  # noqa: E402

LISTS.update({slug: cfg["repo"] for slug, cfg in PAGE_LISTS.items()})
SLUG = sys.argv[1] if len(sys.argv) > 1 else "claude-video-skills"
PAGE = f"https://agentskillshub.top/best/{SLUG}/"
LIST = f"https://raw.githubusercontent.com/{LISTS[SLUG]}/main/data/skills.json"
# Cards may carry more classes than bp-card: since 10-07 they are "bp-card bp-sc-card",
# and an exact match read every page as empty ("page 0 · list 327" on knowledge-base, 10-07).
# Each card is keyed by its GitHub link (bp-sc-gh), which names a sub-skill's folder the way
# the list does (owner/repo/skills/pptx). The title links to the sub-skill's own page
# (/skill/owner/repo/pptx/) once it has one, which drops the folder's parent.
CARD = re.compile(r'<div class="bp-card(?: [^"]*)?" data-kind="([^"]*)"[^>]*>.*?class="bp-sc-gh" href="([^"]+)"', re.S)
HTTP_TIMEOUT = 30


def get(url: str) -> str:
    req = urllib.request.Request(f"{url}?cb={int(time.time())}", headers={"User-Agent": "agentskillshub-check"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as res:
        return res.read().decode("utf-8")


def on_page(html: str) -> dict:
    found = {}
    for kind, href in CARD.findall(html):
        found[re.sub(r"^https://github\.com/|/tree/HEAD", "", href).lower()] = kind
    return found


def in_list(data: dict) -> dict:
    return {(s["repo_full_name"] + (f"/{s['path']}" if s.get("path") else "")).lower(): s["kind"]
            for s in data["skills"]}


def main() -> int:
    page, listed = on_page(get(PAGE)), in_list(json.loads(get(LIST)))
    only_page, only_list = sorted(set(page) - set(listed)), sorted(set(listed) - set(page))
    retyped = sorted(k for k in set(page) & set(listed) if page[k] != listed[k])
    print(f"page {len(page)} · list {len(listed)}")
    for label, names in (("on the page only", only_page), ("in the list only", only_list), ("type differs", retyped)):
        if names:
            print(f"{label}: {names}")
    same = not (only_page or only_list or retyped)
    print("consistent" if same else "NOT consistent")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
