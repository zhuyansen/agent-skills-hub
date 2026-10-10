"""Evidence pages, comparison image and page data for the design test.

  python ops/design-runs/evidence.py      # after score_design.py

Writes frontend/public/best-runs/design/: <owner__repo>.html (noindex: both builds' first
screens, their font and colour signature, the checks), the screenshots, compare.jpg (every
skill's first build side by side, the no-skill page first), and the "ai-design" entry of
frontend/scripts/scenario-runs.json (type "table").
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from runs_common import PUBLIC, REPO_URL, esc, key, pair, shell, update_method, write_runs  # noqa: E402

SLUG, DATE, CONTROL = "ai-design", "2026-10-10", "octocat/Hello-World"
URL = REPO_URL + "design-runs/"
RUNS = {"a": HERE / "out", "b": HERE / "out-b"}
OUT = PUBLIC / "design"
SHOT_WIDTH, THUMB, GRID_COLS, LABEL_H = 1100, (480, 300), 4, 26
SIG = [("headline_font", "Headline font"), ("body_font", "Body font"), ("accent", "Accent colour"), ("background", "Background")]
CHECK_ZH = {"copy_complete": "文案完整", "nothing_added": "没有添加内容", "one_h1": "只有一个 h1", "button_on_first_screen": "首屏有按钮",
            "no_sideways_scroll": "手机上不横向滚动", "no_errors": "没有脚本错误", "self_contained": "没有外部请求"}
CHECK_EN = {"copy_complete": "copy complete", "nothing_added": "nothing added", "one_h1": "one h1", "button_on_first_screen": "button on the first screen",
            "no_sideways_scroll": "no sideways scroll on a phone", "no_errors": "no script errors", "self_contained": "no outside requests"}
NOTES = {
    "emilkowalski/skills": ("These skills are about motion and interaction detail. On fonts, colours and layout both builds match the no-skill page.", "这组 skill 讲的是动效和交互细节。字体、配色和版式上，两次产出都和不装 skill 的页面一样。"),
    "MengTo/Skills": ("Both builds share the no-skill page's fonts, accent and background.", "两次产出的字体、强调色和背景都和不装 skill 的页面相同。"),
    "dominikmartn/nothing-design-skill": ("One fixed identity: a dot-matrix headline, black on grey, both times. One build scrolled sideways on a phone.", "固定的一套风格：点阵字标题、灰底黑字，两次都一样。其中一次在手机上会横向滚动。"),
    "nextlevelbuilder/ui-ux-pro-max-skill": ("One of its two builds scrolled sideways on a phone.", "两次产出里有一次在手机上会横向滚动。"),
    "alchaincyf/huashu-design": ("The two builds look least alike: different fonts, layout and accent each time.", "两次产出差别最大：字体、版式和强调色每次都不同。"),
}
VERDICT = {
    "rule": ["Ranked by how little a build shares with the page Claude Code made with no skill (headline font, body font, accent family, background family), then by the seven page checks, then GitHub stars. This counts sameness, not taste: look at the pictures. Two builds per skill, one brief.",
             "排名规则：先看产出和不装 skill 时 Claude Code 做的页面有多少相同（标题字体、正文字体、强调色、背景），越少越靠前；再看七项页面检查，最后看 GitHub 星数。这量的是「像不像」，不是审美：请看图。每个 skill 做两遍，同一份需求。"],
    "picks": [
        {"repo": "Leonxlnx/taste-skill", "role": ["For a look that is not the default", "想要不撞脸的设计"],
         "why": ["Both builds passed all seven checks and shared almost nothing with the no-skill page: its own typeface, a cooler palette, and a second build that dared an orange accent.",
                 "两次产出都通过全部七项检查，和不装 skill 的页面几乎没有相同之处：自己的字体、偏冷的配色，第二次还用了橙色强调色。"]},
        {"repo": "Nutlope/hallmark", "role": ["For a different result each time", "想要每次都不一样"],
         "why": ["All seven checks twice, little in common with the default, and its two builds differ from each other: one flat and technical, one editorial with a serif headline.",
                 "两次都通过全部七项检查，和默认风格相同处很少，而且两次产出彼此不同：一次扁平偏技术，一次是衬线标题的杂志风。"]},
        {"repo": "dominikmartn/nothing-design-skill", "role": ["For one fixed identity", "想要一套固定风格"],
         "why": ["The same dot-matrix look both times, unlike anything else here. That is the point of it, and the limit: check the phone layout, one build scrolled sideways.",
                 "两次都是同一套点阵风格，和这里其他的都不像。这是它的目的，也是它的局限：记得检查手机版式，有一次会横向滚动。"]},
    ],
    "avoid_label": ["Changed nothing you can see in a still page:", "在静态页面上看不出区别："],
    "avoid": [
        {"repo": "emilkowalski/skills", "why": ["it is about motion; fonts, colours and layout matched the no-skill page", "它讲的是动效；字体、配色和版式与不装 skill 的页面一致"]},
        {"repo": "MengTo/Skills", "why": ["both builds matched the no-skill page on all four", "两次产出四项全部与不装 skill 的页面相同"]},
    ],
    "caveat": ["Whichever you pick: none of the 22 pages had the old AI look (purple gradient, gradient text, emoji icons, centred hero), with or without a skill. The sameness now is quieter: teal on cream, text left, a status card right.",
               "不管选哪个：22 个页面里没有一个是老式的 AI 味（紫色渐变、渐变文字、emoji 图标、居中大标题），装不装 skill 都一样。现在的「撞脸」更安静：米白底配青绿、左边文字、右边一张状态卡片。"],
}


def shot(run: Path, name: str, dest: str) -> str | None:
    src = run / name
    if not src.exists():
        return None
    im = Image.open(src).convert("RGB")
    im.resize((SHOT_WIDTH, round(im.height * SHOT_WIDTH / im.width))).save(OUT / dest, quality=80)
    return dest


def compare(rows: list[dict]) -> tuple[int, int]:
    """Every first build's first screen in one grid, the no-skill page first."""
    font = ImageFont.load_default(size=15)
    n = len(rows)
    grid = Image.new("RGB", (THUMB[0] * GRID_COLS, (THUMB[1] + LABEL_H) * -(-n // GRID_COLS)), "white")
    d = ImageDraw.Draw(grid)
    for i, r in enumerate(rows):
        x, y = (i % GRID_COLS) * THUMB[0], (i // GRID_COLS) * (THUMB[1] + LABEL_H)
        grid.paste(Image.open(RUNS["a"] / key(r["repo"]) / "fold.png").convert("RGB").resize(THUMB), (x, y + LABEL_H))
        d.text((x + 8, y + 5), "no skill (control)" if r["repo"] == CONTROL else r["repo"].split("/")[1], fill="black", font=font)
    grid.save(OUT / "compare.jpg", quality=82)
    return grid.size


def page(r: dict, name: str) -> str:
    k = key(r["repo"])
    cols = "".join(f"<div><p class='mute'>Build {n}</p><a href='{k}-{b}-full.jpg'><img src='{k}-{b}.jpg' alt='{esc(name)} build {n}, first screen'></a></div>"
                   for n, b in ((1, "a"), (2, "b")) if b in r["facts"])
    sig = "".join(f"<tr><th>{label}</th>" + "".join(f"<td>{esc(r['facts'][b]['signature'][s])}</td>" for b in ("a", "b") if b in r["facts"]) + "</tr>" for s, label in SIG)
    checks = "".join(f"<tr><th>{esc(CHECK_EN[c])}</th>" + "".join(f"<td>{'<span class=ok>pass</span>' if r['facts'][b]['checks'][c] else '<span class=no>fail</span>'}</td>"
                     for b in ("a", "b") if b in r["facts"]) + "</tr>" for c in CHECK_EN)
    note = f"<p>{esc(NOTES[r['repo']][0])}</p>" if r["repo"] in NOTES else ""
    return shell(f"{name}: design test", ("/best/ai-design/", "AI design skills"), f"""<h1>{esc(name)}: test run, {DATE}</h1>
<p class="mute">The same brief, built twice by Claude Code (Claude Opus 5.5) in a throwaway sandbox: a landing page for a made-up app, with fixed copy and the design left open. Measured in a browser at 1440 and 375 px.
<a href="{URL}RESULTS.md">All results</a> · <a href="{URL}in/brief.md">The brief</a> · <a href="{URL}score_design.py">How it is counted</a></p>
<p><b>Shares {r['like_default']} of 4 with the no-skill page</b>; its two builds share {r.get('self_alike', '-')} of 4; {r['checks']} of 7 checks passed.</p>{note}
<div class="two">{cols}</div><p class="mute">Click a picture for the whole page.</p>
<h2>Fonts and colours</h2><table><tr><th></th><th>Build 1</th><th>Build 2</th></tr>{sig}</table>
<h2>Page checks</h2><table><tr><th></th><th>Build 1</th><th>Build 2</th></tr>{checks}</table>""")


def card(r: dict) -> dict:
    like, same = r["like_default"], r.get("self_alike")
    failed = ", ".join(CHECK_EN[c] for c in r["failed"]) or "-"
    failed_zh = "、".join(CHECK_ZH[c] for c in r["failed"]) or "-"
    cells = [[f"{like}/4", None, "touch-ups" if like <= 1 else "substantial" if like >= 3.5 else ""], [f"{same}/4", None], [f"{r['checks']}/7", None],
             [failed, failed_zh], [" / ".join(f.title() for f in r["headline_fonts"]), None]]
    bits = [[f"shares {like} of 4 with the page built with no skill (fonts, accent, background)", f"和不装 skill 做的页面相比，字体、强调色、背景 4 项里有 {like} 项相同"],
            [f"its two builds share {same} of 4", f"它自己两次产出 4 项里 {same} 项相同"], [f"{r['checks']} of 7 page checks passed", f"7 项页面检查通过 {r['checks']} 项"]]
    out = {"ran": True, "stars": r["stars"], "sheet": key(r["repo"]) + ".html", "cells": cells, "bits": bits}
    if r["repo"] in NOTES:
        out.update(note=NOTES[r["repo"]][0], note_zh=NOTES[r["repo"]][1])
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [r for r in json.loads((HERE / "results.json").read_text()) if r["ran"]]
    control = next(r for r in rows if r["repo"] == CONTROL)
    skills = sorted((r for r in rows if r["repo"] != CONTROL), key=lambda r: (r["like_default"], -r["checks"], -r["stars"]))
    for r in rows:
        for b, d in RUNS.items():
            shot(d / key(r["repo"]), "fold.png", f"{key(r['repo'])}-{b}.jpg"); shot(d / key(r["repo"]), "desktop.png", f"{key(r['repo'])}-{b}-full.jpg")
        (OUT / (key(r["repo"]) + ".html")).write_text(page(r, "Control: Claude Code with no design skill" if r is control else r["repo"]))
    grid_w, grid_h = compare([control, *skills])
    same = sum(r["like_default"] >= 3.5 for r in skills)
    apart = sum(r["like_default"] <= 1 for r in skills)
    builds = sum(r["builds"] for r in rows)
    assert sum(r["tells"] for r in rows) == 0, "a build has an old-look tell: the findings text says none"
    write_runs(SLUG, {
        "type": "table", "date": DATE, "dir": "/best-runs/design/", "results": URL + "RESULTS.md",
        "title": ["Claude design skills tested: the same landing page, built twice", "实测对比：同一个落地页，各做两遍"],
        "intro": [f"On {DATE} we ran {len(skills)} of these skills. Each built the same landing page twice in a throwaway sandbox, driven by Claude Code (Claude Opus 5.5): a made-up app, fixed copy, the design left open. Claude Code with no skill built it twice as well. Nothing here is a taste score. A browser measured each page: seven checks any landing page should pass, and four things that make pages look alike (headline font, body font, accent colour family, background family), compared with the no-skill pages and between a skill's own two builds.",
                  f"{DATE} 我们实跑了其中 {len(skills)} 个。每个在用完即删的沙箱里由 Claude Code（Claude Opus 5.5）调用，把同一个落地页做两遍：一个虚构的应用，文案固定，设计自由。不装 skill 的 Claude Code 也做了两遍。这里没有审美分。每个页面由浏览器测量：任何落地页都该通过的七项检查，以及让页面「撞脸」的四样东西（标题字体、正文字体、强调色、背景），分别和不装 skill 的页面比、和它自己的另一次产出比。"],
        "finding": [f"None of the {builds} pages had the old AI look (a purple accent, gradient text, emoji icons, a centred hero), with or without a skill. The default now is teal on cream with a serif headline, and {same} of {len(skills)} skills reproduced it on all four counts; {apart} shared one or none. Every skill passed at least 6.5 of the 7 checks.",
                    f"{builds} 个页面里没有一个是老式的 AI 味（紫色强调色、渐变文字、emoji 图标、居中大标题），装不装 skill 都一样。现在的默认风格是米白底配青绿、衬线标题；{len(skills)} 个 skill 里有 {same} 个四项全部照搬，{apart} 个只有一项或零项相同。每个 skill 在 7 项检查里至少通过 6.5 项。"],
        "compare": [{"src": "compare.jpg", "w": grid_w, "h": grid_h, "en": "The first screen of each skill's first build; the page built with no skill is top left.", "zh": "每个 skill 第一次产出的首屏；左上角是不装 skill 做的页面。"}],
        "name_col": ["Skill", "Skill"],
        "columns": [["Shares with the no-skill page (of 4)", "与不装 skill 的页面相同（共 4 项）"], ["Its two builds share (of 4)", "自己两次产出相同（共 4 项）"],
                    ["Checks passed (of 7)", "页面检查通过（共 7 项）"], ["Failed", "未通过"], ["Headline font", "标题字体"]],
        "see": ["See both builds →", "看两次产出 →"], "evidence": ["Both builds", "两次产出"],
        "line_label": [f"Claude design skills test, {DATE}:", f"{DATE} 实测："], "control": {"sheet": key(CONTROL) + ".html"},
        "verdict": VERDICT, "runs": {r["repo"]: card(r) for r in skills}})
    update_method(SLUG, [
        pair(f"The old AI look is gone, with or without a skill: of {builds} pages built from one brief, none had a purple accent, gradient text, emoji icons or a centred hero.",
             f"老式的 AI 味已经没有了，装不装 skill 都一样：按同一份需求做出的 {builds} 个页面里，没有一个用了紫色强调色、渐变文字、emoji 图标或居中大标题。"),
        pair(f"There is a new default, and some skills do not move it. Claude Code alone chose a serif headline, teal and cream both times; {same} of {len(skills)} skills matched it on headline font, body font, accent and background, and {apart} shared one or none. This is the homogenisation Doshi and Hauser measured in writing, seen in pages.",
             f"新的默认风格已经出现，有些 skill 改变不了它。Claude Code 自己两次都选了衬线标题、青绿和米白；{len(skills)} 个 skill 里有 {same} 个在标题字体、正文字体、强调色和背景上与它完全一致，{apart} 个只有一项或零项相同。这就是 Doshi 和 Hauser 在写作上测到的同质化，出现在了页面上。"),
        pair("The basics are not what separates design skills: every one passed at least 6.5 of 7 checks (copy complete, nothing invented, one h1, button on the first screen, no sideways scroll on a phone, no errors, self-contained).",
             "基本功不是拉开差距的地方：每个 skill 在 7 项检查里至少通过 6.5 项（文案完整、没有编造内容、只有一个 h1、首屏有按钮、手机上不横向滚动、没有错误、自包含）。")],
        pair(f"Had {len(skills)} of the skills build the same landing page twice in a throwaway sandbox, with Claude Code and no skill as the control, and measured every page in a browser. Results and pictures are in the test section above and on each card.",
             f"让其中 {len(skills)} 个 skill 在用完即删的沙箱里把同一个落地页各做两遍，用不装 skill 的 Claude Code 做对照，并在浏览器里测量每个页面。结果和截图在上面的实测区和每张卡片上。"),
        pair("We count sameness and basics, not taste: no one rated these pages for beauty, and a page can differ from the default and still be worse. One brief (a consumer landing page), two builds per skill, still pages only, so motion and interaction are not measured. The subject may pull every design toward water colours.",
             "我们数的是「像不像」和基本功，不是审美：没有人给这些页面的美观程度打分，和默认风格不同的页面也可能更差。只有一份需求（面向消费者的落地页），每个 skill 两次产出，只看静态页面，所以动效和交互没有测。题材本身也可能把所有设计都拉向水的颜色。"),
        "old AI look is gone")
    print(f"{len(skills)} skills, {builds} pages; like default on all four: {same}; one or none: {apart}")


if __name__ == "__main__":
    main()
