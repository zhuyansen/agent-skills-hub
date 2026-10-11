"""Score the video runs: the same 15-second promo brief, each skill once.

  python ops/video-runs/score_video.py      # measures runs not yet measured, writes results.json and RESULTS.md

Four checks, all read from the file (see SOURCES.md for why these): it renders to a playable
video; duration, size and frame rate are what the brief asked for (ffprobe); every one of the
five lines of copy can be read in the frames sampled at 2 per second; and the picture moves.
The copy is read by a model (gpt-6-astra, three passes, majority) shown the sampled frames: for
each line, the frames where the whole line is on screen and legible. Deganutti et al.
(arXiv 2605.16223) found a model reads rendered text far better than OCR (0.940 against 0.659 on
perfect renders), and the reader is checked on the control video first. How good a video looks
is not scored: the videos are on the evidence pages.
"""
import base64
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
CONTROL = "octocat/Hello-World"
IMAGE = "pptrun:1"
COPY = [line.split(". ", 1)[1] for line in (HERE / "in" / "brief.md").read_text().split("## On-screen copy, in order")[1].split("## Requirements")[0].splitlines()
        if re.match(r"^\d\. ", line)]
SECONDS, WIDTH, HEIGHT, FPS = (14.5, 15.5), 1920, 1080, 30
READABLE_FRAMES = 1            # whole and legible in at least one sampled frame (the paper's strict match). On the control the
                               # reader marked a line it could plainly read in two frames as one, so two would fail a good video.
MOVES = 0.004                  # mean change between sampled frames above this: something moves
PASSES, RETRIES, RETRY_SECONDS = 3, 6, 20
CHECKS = ["playable", "spec", "copy", "moves"]
PROMPT = """These are frames from a short video, sampled two per second, in order (frame 1 first).
The video is supposed to show these lines of on-screen text:
{lines}
Return JSON only: {{"lines": {{"1": [<frame numbers where line 1 is on screen in full and legible>], "2": [...], ...}},
 "other_text": ["<any other sentence or tagline on screen that is not one of the lines; ignore a logo word and single labels>"]}}
A line counts in a frame only if every word of it is visible and readable there (it may be split over two rows or shown as
separate words side by side). A line that is still fading or typing in, cut off, or too faint to read does not count."""


def env() -> dict:
    vals = {}
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); vals[k.strip()] = v.strip().strip('"')
    return vals


def ask(e: dict, content: list) -> dict:
    body = {"model": e.get("FLATROUTER_MODEL", "gpt-6-astra"), "temperature": 0, "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request(e["FLATROUTER_BASE_URL"] + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + e["FLATROUTER_API_KEY"], "Content-Type": "application/json"})
    for attempt in range(RETRIES):
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=300) as r:
                return json.loads(json.load(r)["choices"][0]["message"]["content"])
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as err:
            if attempt == RETRIES - 1 or (isinstance(err, urllib.error.HTTPError) and err.code < 500 and err.code != 429):
                raise
            time.sleep(RETRY_SECONDS * (attempt + 1))
    return {}


def measure(run: Path) -> dict | None:
    if not (run / "deliverables" / "video.mp4").exists():
        return None
    if not (run / "measure.json").exists():
        subprocess.run(["docker", "run", "--rm", "--entrypoint", "python3", "-v", f"{run}:/run", "-v", f"{HERE}:/tool:ro", IMAGE, "/tool/measure_video.py", "/run"],
                       capture_output=True, timeout=600)
    return json.loads((run / "measure.json").read_text()) if (run / "measure.json").exists() else None


def read_copy(run: Path, e: dict) -> dict:
    """Per line, the frames it is readable in (majority of passes), and any text that is not in the brief."""
    if (run / "copy.json").exists():
        return json.loads((run / "copy.json").read_text())
    frames = sorted((run / "frames").glob("f-*.jpg"))
    content = [{"type": "text", "text": PROMPT.format(lines="\n".join(f"{n}. {c}" for n, c in enumerate(COPY, 1)))}]
    content += [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode()}} for f in frames]
    votes = [ask(e, content) for _ in range(PASSES)]
    seen = {str(n): sorted(f for f in range(1, len(frames) + 1) if sum(f in ((v.get("lines") or {}).get(str(n)) or []) for v in votes) * 2 > PASSES)
            for n in range(1, len(COPY) + 1)}
    other = [t for v in votes for t in (v.get("other_text") or [])]
    result = {"frames": seen, "other_text": sorted({t for t in other if sum(t in (v.get("other_text") or []) for v in votes) * 2 > PASSES})}
    (run / "copy.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result


def row(c: dict, e: dict) -> dict:
    run = OUT / c["repo"].replace("/", "__")
    if not (run / "run.json").exists():
        return {**c, "ran": False, "reason": "not run"}
    meta = json.loads((run / "run.json").read_text())
    m = measure(run)
    if not m or not m["playable"]:
        return {**c, "ran": False, "reason": meta["status"] if meta["status"] != "done" else "no playable video", "minutes": round(meta["seconds"] / 60, 1)}
    copy = read_copy(run, e)
    readable = [n for n, frames in copy["frames"].items() if len(frames) >= READABLE_FRAMES]
    spec = SECONDS[0] <= m["seconds"] <= SECONDS[1] and (m["width"], m["height"]) == (WIDTH, HEIGHT) and round(m["fps"]) == FPS and m["codec"] == "h264"
    checks = {"playable": True, "spec": spec, "copy": len(readable) == len(COPY), "moves": m["mean_change"] > MOVES and not m["dark_frames"] > m["sampled"] // 2}
    return {**c, "ran": True, "checks": checks, "passed": sum(checks.values()), "lines_readable": len(readable), "missing_lines": [COPY[int(n) - 1] for n in copy["frames"] if n not in readable],
            "other_text": copy["other_text"], "seconds": m["seconds"], "size": f"{m['width']}x{m['height']}", "fps": m["fps"], "audio": m["audio"],
            "mean_change": m["mean_change"], "still_share": round(m["still_pairs"] / max(m["pairs"], 1), 2), "minutes": round(meta["seconds"] / 60, 1),
            "commit": (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else None}


def markdown(rows: list[dict]) -> str:
    out = ["| Skill | ★ | Checks (of 4) | Lines readable (of 5) | Seconds | Size | Sound | Held frames | Added text | Min |", "|---|---:|---:|---:|---:|---|---|---:|---|---:|"]
    for r in sorted((r for r in rows if r["ran"]), key=lambda r: (r["repo"] != CONTROL, -r["passed"], -r["lines_readable"], r["minutes"])):
        out.append(f"| {r['repo']} | {r['stars']} | {r['passed']} | {r['lines_readable']} | {r['seconds']} | {r['size']} @ {r['fps']} | {'yes' if r['audio'] else 'no'} | "
                   f"{round(r['still_share'] * 100)}% | {'; '.join(r['other_text']) or '-'} | {r['minutes']} |")
    out += ["", "Not run or no video:", ""] + [f"- {r['repo']}: {r['reason']}" for r in rows if not r["ran"]]
    return "\n".join(out) + "\n"


def main() -> None:
    e = env()
    cands = json.loads((HERE / "candidates.json").read_text())
    rows = [row({"repo": CONTROL, "kind": "control", "stars": 0, "grade": None}, e), *[row(c, e) for c in cands]]
    (HERE / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    (HERE / "RESULTS.md").write_text(markdown(rows))
    print(markdown(rows))


if __name__ == "__main__":
    main()
