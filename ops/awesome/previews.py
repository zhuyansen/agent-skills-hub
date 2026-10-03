"""Pick one preview image per repo from the repo's own README, and thumbnail it.

The list shows what the tools make. Linking to the author's file did not hold up:
on the first day a third of the pictures failed to load in the README (2 MB files
from raw.githubusercontent.com, slow or refused behind a proxy). So the list carries
its own thumbnails: a reduced copy, 520 px wide, only for projects under a permissive
license, each recorded with its source and license in assets/previews/NOTICE.md.
Videos are skipped (GitHub renders them only on a line of their own).

Usage: python ops/awesome/previews.py find <readme-cache-dir> <out.json> [names.json]
       python ops/awesome/previews.py thumbs <previews.json> <list-dir>
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import tempfile
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
SHOWS_OUTPUT = re.compile(r"demo|preview|showcase|example|sample|result|output|thumb|poster|frame|scene|film|"
                          r"style|gallery|效果|演示|示例|成片|样片|预览", re.I)
# Pictures of the tool rather than of what it makes.
SHOWS_TOOL = re.compile(r"structure|architect|workflow|pipeline|diagram|flow|overview|infographic|cover|banner|"
                        r"hero|input|report|board|install|setup|editor|dashboard|screenshot|架构|流程", re.I)
PERMISSIVE = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "CC0-1.0", "Unlicense", "CC-BY-4.0",
              "MPL-2.0", "0BSD"}
THUMB_WIDTH = 520
JPEG_QUALITY = 82
MOTION_WIDTH = 320
MOTION_SECONDS = 5
MOTION_FPS = 8
MOTION_MAX_BYTES = 1_200_000


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
        label = f"{url.rsplit('/', 1)[-1]} {alt}"
        score = (3 if url.lower().split("?")[0].endswith(".gif") else 0) \
            + (2 if SHOWS_OUTPUT.search(label) else 0) - (2.5 if SHOWS_TOOL.search(label) else 0) - i * 0.05
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
            return {"repo": repo, "url": cand["url"], "alt": cand["alt"], "score": round(cand["score"], 2), **info}
    return None


def find(cache: Path, out: Path, names: set[str] | None) -> None:
    """Previews for repos whose README is in the cache and that have none yet. Earlier
    finds are kept: the daily job starts with an empty cache (only the READMEs it read
    that day), and a fresh write would drop every other repo's preview."""
    known = json.loads(out.read_text()) if out.exists() else {}
    if names is not None:
        known = {repo: p for repo, p in known.items() if repo in names}
    jobs = [(p.stem.replace("__", "/", 1), p.read_text()) for p in sorted(cache.glob("*.md"))]
    jobs = [(repo, text) for repo, text in jobs
            if repo.count("/") == 1 and repo not in known and (names is None or repo in names)]
    with ThreadPoolExecutor(WORKERS) as pool:
        found = [r for r in pool.map(lambda j: preview(*j), jobs) if r]
    known.update({r["repo"]: r for r in found})
    out.write_text(json.dumps(dict(sorted(known.items())), ensure_ascii=False, indent=1) + "\n")
    gifs = sum(p["type"] == "image/gif" for p in known.values())
    print(f"{len(found)} new previews from {len(jobs)} READMEs; {len(known)} repos have one ({gifs} GIFs)")


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "agentskillshub-list"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT * 3) as res:
        return res.read(MAX_BYTES + 1)


def still(data: bytes) -> bytes:
    """A 520 px JPEG; for an animation, the frame two fifths of the way in."""
    from PIL import Image  # imported here so `find` needs no Pillow
    image = Image.open(io.BytesIO(data))
    image.seek(int(getattr(image, "n_frames", 1) * 0.4))
    frame = image.convert("RGB")
    if frame.width > THUMB_WIDTH:
        frame = frame.resize((THUMB_WIDTH, round(frame.height * THUMB_WIDTH / frame.width)), Image.LANCZOS)
    out = io.BytesIO()
    frame.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return out.getvalue()


def motion(data: bytes) -> bytes | None:
    """A short, small GIF of an animated source, or None when it would be too heavy."""
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "in.gif", Path(tmp) / "out.gif"
        src.write_bytes(data)
        chain = (f"fps={MOTION_FPS},scale={MOTION_WIDTH}:-1:flags=lanczos,split[a][b];"
                 "[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4")
        done = subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", str(MOTION_SECONDS), "-i", str(src),
                               "-vf", chain, str(dst)], capture_output=True)
        if done.returncode or not dst.exists() or dst.stat().st_size > MOTION_MAX_BYTES:
            return None
        return dst.read_bytes()


def thumbnail(item: dict, folder: Path) -> dict | None:
    try:
        data = download(item["url"])
        name = item["repo"].replace("/", "__")
        (folder / f"{name}.jpg").write_bytes(still(data))
        moving = motion(data) if item["type"] == "image/gif" else None
        if moving:
            (folder / f"{name}.gif").write_bytes(moving)
        return {**item, "file": f"{name}.{'gif' if moving else 'jpg'}", "still": f"{name}.jpg"}
    except Exception as exc:  # noqa: BLE001 — one bad image must not lose the rest
        print(f"  skipped {item['repo']}: {str(exc)[:90]}", file=sys.stderr)
        return None


def notice(done: list[dict], licenses: dict) -> str:
    lines = ["# Preview images", "",
             "Reduced copies (520 px wide, or a 5-second 320 px GIF) of images published in each project's own",
             "README. Included only for projects under a permissive license. The images belong to their",
             "authors and stay under the license of the project they come from. To have one removed, open an issue.",
             "", "| File | Project | License | Original |", "|---|---|---|---|"]
    for d in sorted(done, key=lambda d: d["repo"].lower()):
        lines.append(f"| `{d['file']}` | [{d['repo']}](https://github.com/{d['repo']}) | {licenses[d['repo']]} "
                     f"| [source]({d['url']}) |")
    return "\n".join(lines) + "\n"


def thumbs(previews_file: Path, list_dir: Path) -> None:
    previews = json.loads(previews_file.read_text())
    skills = json.loads((list_dir / "data/skills.json").read_text())["skills"]
    licenses = {s["repo_full_name"]: s.get("license") for s in skills if not s.get("path")}
    allowed = [p for repo, p in previews.items() if licenses.get(repo) in PERMISSIVE]
    folder = list_dir / "assets/previews"
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.*"):
        old.unlink()
    with ThreadPoolExecutor(WORKERS) as pool:
        done = [d for d in pool.map(lambda p: thumbnail(p, folder), allowed) if d]
    (folder / "NOTICE.md").write_text(notice(done, licenses))
    (folder / "index.json").write_text(json.dumps({d["repo"]: d for d in done}, ensure_ascii=False, indent=1) + "\n")
    size = sum(f.stat().st_size for f in folder.glob("*.*"))
    print(f"{len(done)} thumbnails ({sum(d['file'].endswith('.gif') for d in done)} moving) of {len(previews)} previews; "
          f"{len(previews) - len(allowed)} left out for their license; folder {size / 1e6:.1f} MB")


def main() -> None:
    step = sys.argv[1]
    if step == "find":
        names = set(json.loads(Path(sys.argv[4]).read_text())) if len(sys.argv) > 4 else None
        find(Path(sys.argv[2]), Path(sys.argv[3]), names)
    else:
        thumbs(Path(sys.argv[2]), Path(sys.argv[3]).expanduser())


if __name__ == "__main__":
    main()
