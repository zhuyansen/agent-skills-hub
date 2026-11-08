"""Evidence for the anti-slop page's interface test: the AI-looking page, each tool's redesign beside it, and the
test's entry in frontend/scripts/scenario-runs.json ("anti-slop-ui", shown on /best/anti-slop/ under the
writing test).

  python3 ops/slop-ui-runs/evidence_ui.py

Writes frontend/public/best-runs/slop-ui/ (WebP copies of the first screen and the phone view, and one noindex
page per run with what score_ui.py measured) and ops/slop-ui-runs/RESULTS.md. A page's look is named from
measurements, not by eye: the first screen's background colour (the colour covering most of it) and the
headline's font.
"""
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runs_common import WEBP_QUALITY, webp_copy as webp  # noqa: E402 (shared with the other tests' evidence)
from evidence_ui_copy import (ANSWER,  # noqa: E402
                               AVOID, BG, COLUMNS, COMMON_BG, DATE, FILTERS, FINDING, GROUP, INTRO, NOT_RUN,
                              PICKS, SEE, SERIF, TELLS_BEFORE, page)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT, BEFORE = HERE / "out", HERE / "before"
DEST = ROOT / "frontend" / "public" / "best-runs" / "slop-ui"
RUNS_JSON = ROOT / "frontend" / "scripts" / "scenario-runs.json"
KEY, PAGE, ANCHOR, DIR = "anti-slop-ui", "anti-slop", "test-results-ui", "/best-runs/slop-ui/"
URL = "https://github.com/zhuyansen/agent-skills-hub/blob/main/ops/slop-ui-runs/"
FOLD_W, FOLD_H = 720, 450            # the first screen (1440 x 900) at half size
THUMB_W, THUMB_H = 160, 100          # in the table, shown at this size from a copy twice as big
PAGE_W, PAGE_MAX_H = 720, 2400       # the whole page at 1440 px, top part only
PHONE_W, PHONE_MAX_H = 375, 2000
SAMPLE = (360, 225)                  # the first screen shrunk to find its background colour
BG_SHARE = 0.4                       # the colour must cover this much of the first screen to count as the background
DARK_MAX, PAPER_MIN, PAPER_WARMTH = 80, 225, 6         # channel values: dark below; paper light, red above blue by this
WHITE_MIN, WHITE_SPREAD, TINTED_MIN = 240, 6, 200      # white: light and grey (channels this close); tinted: light, not grey
SAT_MIN, VALUE_MIN, SATURATED_SHARE = 0.45, 0.3, 0.05   # strong colour (HSV), and how much of the first screen it must cover
JUDGE_TOP = 5


def background(fold: Path) -> str:
    """The colour that covers most of the first screen: paper (warm off-white), white, tinted (another light
    colour), dark or colour; gradient when no one colour covers enough of it."""
    im = Image.open(fold).convert("RGB").resize(SAMPLE)
    (r, g, b), n = Counter(im.getdata()).most_common(1)[0]
    if n / (SAMPLE[0] * SAMPLE[1]) < BG_SHARE:
        return "gradient"
    if max(r, g, b) < DARK_MAX:
        return "dark"
    if r >= PAPER_MIN and r - b >= PAPER_WARMTH and r >= g >= b:
        return "paper"
    if min(r, g, b) >= WHITE_MIN and max(r, g, b) - min(r, g, b) <= WHITE_SPREAD:
        return "white"
    return "tinted" if min(r, g, b) >= TINTED_MIN else "colour"


def publish(name: str, measure: Path) -> dict:
    """The run's pictures in DEST; returns their paths and sizes for the pages."""
    sizes = {k: webp(measure / f, DEST / f"{name}-{k}.webp", w, h) for k, f, w, h in (
        ("fold", "fold.png", FOLD_W, None), ("desktop", "desktop.png", PAGE_W, PAGE_MAX_H), ("mobile", "mobile.png", PHONE_W, PHONE_MAX_H))}
    webp(measure / "fold.png", DEST / f"{name}-thumb.webp", THUMB_W * 2)
    return {"fold": f"{name}-fold.webp", "desktop": f"{name}-desktop.webp", "mobile": f"{name}-mobile.webp",
            "desktop_size": sizes["desktop"], "mobile_size": sizes["mobile"], "before_fold": "before-fold.webp"}


def issues(a: dict) -> list[tuple[str, str]]:
    """The brief's rules a page broke: the phone layout, outside files (web fonts are allowed), one file, facts."""
    out = []
    if a.get("sideways"):
        out.append(("Phone layout scrolls sideways", "手机上能左右滑"))
    if a.get("outside"):
        hosts = ", ".join(a["outside"])
        out.append((f"Loads files from {hosts}", f"从 {hosts} 加载文件"))
    if a.get("local_files"):
        n = len(a["local_files"]) + 1
        out.append((f"Split into {n} files, not one", f"拆成 {n} 个文件，不是一个"))
    lost = [k for k, v in a["facts"].items() if not v]
    if lost:
        out.append((f"Lost facts: {', '.join(lost)}", f"丢了事实：{', '.join(lost)}"))
    return out


def look(a: dict, bg: str) -> tuple[str, str]:
    font = str(a.get("h1_font") or "")
    kind = ("serif", "衬线") if font.lower() in SERIF else ("sans", "无衬线")
    return f"{BG[bg][0]} · {kind[0]}", f"{BG[bg][1]} · {kind[1]}"


def row(c: dict) -> dict | None:
    """One run that made a page, with everything the table, the card line and its evidence page need."""
    run = OUT / c["repo"].replace("/", "__")
    if not (run / "score.json").exists():
        return None
    s = json.loads((run / "score.json").read_text())
    if not s.get("page"):
        return None
    a, j = s["after"], s.get("judge") or {}
    bg, colour = background(run / "measure" / "fold.png"), saturated(run / "measure" / "fold.png")
    commit = (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else ""
    broken = issues(a)
    return {"repo": c["repo"], "label": "Claude Code, no skill" if c["repo"] == "control" else c["repo"], "stars": c["stars"],
            "after": a, "judge": j, "bg": bg, "minutes": round(s["run"]["seconds"] / 60, 1), "commit": commit,
            "tells": sum(a["tells"].values()), "issues": broken, "look": look(a, bg), "own": own_look(c["repo"], bg, colour, broken),
            "repo_url": URL + "RESULTS.md", "prompt_url": URL + "in/prompt.txt"}


def saturated(fold: Path) -> float:
    """The share of the first screen in strong colour (a colour block, a coloured frame), not tints or text."""
    import colorsys
    px = list(Image.open(fold).convert("RGB").resize(SAMPLE).getdata())
    strong = sum(1 for r, g, b in px if (lambda h, s, v: s > SAT_MIN and v > VALUE_MIN)(*colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)))
    return strong / len(px)


def own_look(repo: str, bg: str, colour: float, broken: list) -> bool:
    """A first screen unlike the warm paper or white most fixes landed on (another background, or strong colour
    over SATURATED_SHARE of it), on a page that kept every rule; not the AI page's own look kept (AVOID)."""
    differs = bg not in COMMON_BG or colour >= SATURATED_SHARE
    return differs and not broken and repo != "control" and repo not in {a for a, _ in AVOID}


def cells(r: dict) -> list:
    g = "rule" if r["issues"] else "clean"
    phone = ("Scrolls sideways", "能左右滑", "substantial") if r["after"].get("sideways") else ("Fits", "不溢出", "")
    d = r["judge"].get("designed")
    return [[*GROUP[g], "substantial" if g == "rule" else "touch-ups"], [str(r["tells"]), str(r["tells"]), "num"], list(phone),
            [*r["look"], "touch-ups" if r["own"] else ""], [f"{d}/5" if d else "-", f"{d}/5" if d else "-", "num"],
            [f"{r['minutes']} min", f"{r['minutes']} 分钟", "num"]]


def bits(r: dict) -> list:
    """The card's "Tested" line."""
    d = r["judge"].get("designed")
    out = [[f"AI tells {TELLS_BEFORE} → {r['tells']}", f"AI 痕迹 {TELLS_BEFORE} → {r['tells']}"],
           [f"judge {d}/5", f"评审 {d}/5"], [f"{r['minutes']} min", f"{r['minutes']} 分钟"]]
    return out + [list(i) for i in r["issues"]]


def card(r: dict) -> dict:
    name = r["repo"].replace("/", "__")
    out = {"ran": True, "stars": r["stars"], "minutes": r["minutes"], "sheet": f"{name}.html", "date": DATE,
           "group": "rule" if r["issues"] else "clean", "look": "own" if r["own"] else "", "cells": cells(r), "bits": bits(r),
           "strip": {"src": f"{name}-thumb.webp", "w": THUMB_W, "h": THUMB_H}}
    if r["issues"]:
        out["issues"] = ["; ".join(i[0] for i in r["issues"]), "；".join(i[1] for i in r["issues"])]
    return out


def ordered(rows: list[dict]) -> list[dict]:
    """Rules kept first, then the judge's score, the AI tells left and the time."""
    return sorted(rows, key=lambda r: (bool(r["issues"]), -(r["judge"].get("designed") or 0), r["tells"], r["minutes"]))


TILE_W, TILE_H, LABEL_H, COLS = 240, 150, 18, 6
OUTLINE = {"before": "#cf222e", "control": "#0969da"}


def short(label: str, tiles: list) -> str:
    """The repo's name, or owner/repo when two share it (Gesso-Build/skills, nickture/skills)."""
    name = label.split("/")[-1]
    return label if sum(1 for _, other, _ in tiles if other.split("/")[-1] == name) > 1 else name


def mosaic(rows: list[dict]) -> dict:
    """Every first screen in one picture: the AI-looking original first (red), then no skill (blue), then the skills."""
    from PIL import ImageDraw
    tiles = [("before", "The AI-looking original", BEFORE / "fold.png")] + [
        (r["repo"], r["label"], OUT / r["repo"].replace("/", "__") / "measure" / "fold.png") for r in rows]
    grid = Image.new("RGB", (COLS * TILE_W, -(-len(tiles) // COLS) * (TILE_H + LABEL_H)), "white")
    draw = ImageDraw.Draw(grid)
    for i, (key, label, src) in enumerate(tiles):
        x, y = (i % COLS) * TILE_W, (i // COLS) * (TILE_H + LABEL_H)
        grid.paste(Image.open(src).convert("RGB").resize((TILE_W - 4, TILE_H - 4), Image.LANCZOS), (x + 2, y + LABEL_H + 2))
        draw.text((x + 3, y + 3), short(label, tiles)[:34], fill="#1f2328")
        if key in OUTLINE:
            draw.rectangle((x, y + LABEL_H, x + TILE_W - 1, y + LABEL_H + TILE_H - 1), outline=OUTLINE[key], width=3)
    grid.save(DEST / "first-screens.webp", "WEBP", quality=WEBP_QUALITY)
    return {"src": "first-screens.webp", "w": grid.width, "h": grid.height, "count": len(tiles) - 2}


def pair() -> dict:
    """The original and Claude Code's fix with no skill, side by side."""
    a, b = (Image.open(p).convert("RGB").resize((FOLD_W, FOLD_H), Image.LANCZOS) for p in (BEFORE / "fold.png", OUT / "control" / "measure" / "fold.png"))
    canvas = Image.new("RGB", (FOLD_W * 2 + 12, FOLD_H), "white")
    canvas.paste(a, (0, 0))
    canvas.paste(b, (FOLD_W + 12, 0))
    canvas.save(DEST / "before-and-control.webp", "WEBP", quality=WEBP_QUALITY)
    return {"src": "before-and-control.webp", "w": canvas.width, "h": canvas.height}


def counts(control: dict, skills: list[dict], tried: int) -> dict:
    return {"n": tried, "delivered": len(skills), "date": DATE, "cm": control["minutes"], "ct": control["tells"],
            "five": sum(1 for r in skills if r["judge"].get("designed") == JUDGE_TOP),
            "paper": sum(1 for r in skills if r["bg"] == "paper")}


def verdict(by: dict) -> dict:
    picks = []
    for repo, (role, role_zh, en, zh) in PICKS.items():
        r = by[repo]
        vals = {"m": r["minutes"], "t": r["tells"], "n": len(r["after"].get("local_files") or []) + 1}
        picks.append({"repo": repo, "role": [role, role_zh], "why": [en.format(**vals), zh.format(**vals)]})
    return {"title": ["Which one to use", "用哪个"], "ranked": False, "picks": picks,
            "avoid_label": ["Skip:", "别用："], "avoid": [{"repo": a, "why": list(w)} for a, w in AVOID],
            "caveat": list(ANSWER),
            "rule": ["Picked, by measurement, for a first screen unlike the warm paper or white most fixes landed on (another background, or strong colour over 5% of it), on a page that kept every rule of the brief.",
                     "按测量挑选：首屏不是多数改法用的米白或白底（换了底色，或有超过 5% 的面积是浓重色块），并且守住测试题全部规则。"]}


def not_run(c: dict) -> dict:
    en, zh = NOT_RUN[c["repo"]]
    return {"ran": False, "stars": c["stars"], "reason": en, "reason_zh": zh, "date": DATE}


def entry(c: dict, control: dict, skills: list[dict], missing: list[dict], figures: tuple[dict, dict]) -> dict:
    two, grid = figures
    return {
        "type": "table", "page": PAGE, "anchor": ANCHOR, "date": DATE, "dir": DIR, "results": URL + "RESULTS.md",
        "list_anchor": "tested-ui", "list_title": ["Tested end to end: interfaces", "端到端实测：界面"],
        "agent": "Claude Code (Claude Opus 5.5)", "judge": "gpt-6-astra",
        "title": ["Test results: making an AI-looking page look designed", "实测：把一个 AI 味网页改得像人做的"],
        "intro": [INTRO[0].format(**c), INTRO[1].format(**c)], "finding": [FINDING[0].format(**c), FINDING[1].format(**c)],
        "verdict": verdict({r["repo"]: r for r in skills}),
        "compare": [{**two, "en": f"Before, and after Claude Code with no skill ({control['minutes']} minutes): the first screen.",
                     "zh": f"改前，和不装 skill 的 Claude Code 改后（{control['minutes']} 分钟）的首屏。"},
                    {**grid, "en": f"All {grid['count']} skills' first screens, after the original (red) and the page made with no skill (blue).",
                     "zh": f"{grid['count']} 个 skill 改出的首屏，排在原页（红框）和不装 skill 的那页（蓝框）之后。"}],
        "control": {"sheet": "control.html", "label": ["See the page Claude Code made with no skill →", "看不装 skill 改出的页面 →"]},
        "name_col": ["Skill and its first screen", "Skill 和它改出的首屏"], "columns": [list(x) for x in COLUMNS],
        "filters": [{"id": i, "label": list(label)} for i, label in FILTERS], "see": list(SEE), "evidence": ["Before / after", "改前改后"],
        "line_label": [f"Interface test, {DATE}:", f"{DATE} 界面实测："],
        "not_run_label": ["Made no page", "没交页面"], "not_run_line": ["Tried in our interface test, no page:", "界面实测时没交页面："],
        "runs": {**{r["repo"]: card(r) for r in skills}, **{m["repo"]: not_run(m) for m in missing}}}


def results_md(control: dict, skills: list[dict], missing: list[dict]) -> str:
    head = ("# Interface de-slop test, " + DATE + "\n\nGenerated by evidence_ui.py from score_ui.py's measurements. "
            f"The original page had {TELLS_BEFORE} AI tells, 15 marketing words and a phone layout that scrolled sideways.\n\n"
            "| Skill | AI tells left | Facts | Phone | Look | Judge | Minutes | Rules broken |\n|---|---|---|---|---|---|---|---|\n")
    line = lambda r: (f"| {r['label']} | {r['tells']} | {sum(r['after']['facts'].values())}/11 | "  # noqa: E731
                      f"{'sideways' if r['after'].get('sideways') else 'fits'} | {r['look'][0]} | {r['judge'].get('designed', '-')}/5 | "
                      f"{r['minutes']} | {'; '.join(i[0] for i in r['issues']) or '-'} |")
    tail = "\n\n## Made no page\n\n" + "\n".join(f"- {m['repo']}: {NOT_RUN[m['repo']][0]}" for m in missing)
    return head + "\n".join(line(r) for r in [control, *skills]) + tail + "\n"


def main() -> None:
    cands = json.loads((HERE / "candidates.json").read_text())
    rows = {c["repo"]: row(c) for c in cands}
    missing = [c for c in cands if not rows[c["repo"]] and c["repo"] in NOT_RUN]
    waiting = [c["repo"] for c in cands if not rows[c["repo"]] and c["repo"] not in NOT_RUN]
    control = rows.pop("control")
    skills = ordered([r for r in rows.values() if r])
    before = json.loads((BEFORE / "facts.json").read_text())
    webp(BEFORE / "fold.png", DEST / "before-fold.webp", FOLD_W)
    for r in [control, *skills]:
        name = r["repo"].replace("/", "__")
        (DEST / f"{name}.html").write_text(page(r, before, publish(name, OUT / name / "measure")))
    c = counts(control, skills, len(cands) - 1)
    runs = json.loads(RUNS_JSON.read_text())
    runs[KEY] = entry(c, control, skills, missing, (pair(), mosaic([control, *skills])))
    RUNS_JSON.write_text(json.dumps(runs, indent=1, ensure_ascii=False) + "\n")
    (HERE / "RESULTS.md").write_text(results_md(control, skills, missing))
    print(f"{len(skills)} pages, {len(missing)} made none, waiting: {waiting or 'none'}; {c}")


if __name__ == "__main__":
    main()
