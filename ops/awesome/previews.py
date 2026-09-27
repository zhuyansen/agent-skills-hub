"""Pick one preview image per repo from the repo's own README.

The list shows what the tools make. The picture is the one the author published:
it is linked from where the author hosts it, never copied into the list, and the
list says whose it is. Videos are skipped (GitHub renders them only on a line of
their own, not inside a table or a grid).

Usage: python ops/awesome/previews.py <readme-cache-dir> <out.json>
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MAX_BYTES = 12_000_000      # a 12 MB GIF is the most a README grid should pull
MIN_BYTES = 8_000           # smaller than this is an icon or a badge
HTTP_TIMEOUT = 20
WORKERS = 6
CANDIDATES = 6              # images tried per repo, in order of preference

IMAGE = re.compile(r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?[^)]*\)|<img[^>]*?src=[\"']([^\"']+)[\"'][^>]*>", re.I)
ALT = re.compile(r"alt=[\"']([^\"']*)[\"']", re.I)
NOT_A_PREVIEW = re.compile(
    r"shields\.io|badge|badgen|/logo|logo[-_.]|[-_.]logo|favicon|avatar|/icon|icon[-_.]|sponsor|contrib\.rocks|"
    r"star-history|visitor|komarev|github-readme-stats|trendshift|producthunt|buymeacoffee|wechat|qrcode|qr[-_.]|"
    r"\.svg(\?|$)|license|discord|twitter|x\.com", re.I)
SHOWS_OUTPUT = re.compile(r"demo|preview|showcase|example|sample|result|output|screenshot|hero|cover|banner|"
                          r"效果|演示|示例|成片|样片|预览", re.I)


def absolute(repo: str, src: str) -> str | None:
    src = src.strip()
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("http"):
        blob = re.match(r"https://github\.com/([^/]+/[^/]+)/(?:blob|raw)/([^/]+)/(.+)", src)
        return f"https://raw.githubusercontent.com/{blob[1]}/{blob[2]}/{blob[3].split('?')[0]}" if blob else src
    if src.startswith(("data:", "#", "mailto:")):
        return None
    return f"https://raw.githubusercontent.com/{repo}/HEAD/{src.lstrip('./').lstrip('/')}"


def candidates(repo: str, readme: str) -> list[dict]:
    found = []
    for i, m in enumerate(IMAGE.finditer(readme)):
        src = m.group(2) or m.group(3)
        alt = m.group(1) or (ALT.search(m.group(0)) or [None, ""])[1]
        url = absolute(repo, src or "")
        if not url or NOT_A_PREVIEW.search(url) or NOT_A_PREVIEW.search(alt or ""):
            continue
        score = (3 if url.lower().split("?")[0].endswith(".gif") else 0) \
            + (2 if SHOWS_OUTPUT.search(f"{url} {alt}") else 0) - i * 0.05
        found.append({"url": url, "alt": (alt or "").strip()[:80], "score": score})
    return sorted(found, key=lambda c: -c["score"])[:CANDIDATES]


def usable(url: str) -> dict | None:
    """Reachable, an image, and of a size a README can carry."""
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "agentskillshub-list", "Range": "bytes=0-0"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as res:
            kind = res.headers.get("Content-Type", "")
            total = res.headers.get("Content-Range", "").split("/")[-1] or res.headers.get("Content-Length", "0")
    except Exception:  # noqa: BLE001 — a dead link is simply not a preview
        return None
    size = int(total) if total.isdigit() else 0
    if not kind.startswith("image/") or "svg" in kind or not MIN_BYTES <= size <= MAX_BYTES:
        return None
    return {"type": kind.split(";")[0], "bytes": size}


def preview(repo: str, readme: str) -> dict | None:
    for cand in candidates(repo, readme):
        info = usable(cand["url"])
        if info:
            return {"repo": repo, "url": cand["url"], "alt": cand["alt"], **info}
    return None


def main() -> None:
    cache, out = Path(sys.argv[1]), Path(sys.argv[2])
    jobs = [(p.stem.replace("__", "/", 1), p.read_text()) for p in sorted(cache.glob("*.md"))]
    jobs = [(repo, text) for repo, text in jobs if repo.count("/") == 1]
    with ThreadPoolExecutor(WORKERS) as pool:
        found = [r for r in pool.map(lambda j: preview(*j), jobs) if r]
    out.write_text(json.dumps({r["repo"]: r for r in found}, ensure_ascii=False, indent=1) + "\n")
    gifs = sum(r["type"] == "image/gif" for r in found)
    print(f"{len(found)} of {len(jobs)} repos have a usable preview ({gifs} GIFs)")


if __name__ == "__main__":
    main()
