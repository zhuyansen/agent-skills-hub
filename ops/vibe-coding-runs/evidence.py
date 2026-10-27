"""Evidence pages, comparison pictures and page data for the vibe coding test.

  python3 ops/vibe-coding-runs/evidence.py      # after score.py (results.json, with review.json applied)

Writes frontend/public/best-runs/vibe/: <owner__repo>.html (noindex: what each request became,
the checks with the tester's screenshots, where the build stopped to ask, the install), the
screenshots, compare-t1.jpg and compare-t2.jpg (every build after the tester's entries, the
control first), and the "vibe-coding" entry of frontend/scripts/scenario-runs.json (type "table").
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from runs_common import PUBLIC, REPO_URL, esc, key, shell, write_runs  # noqa: E402

SLUG, DATE, CONTROL = "vibe-coding", "2026-10-27", "octocat/Hello-World"
URL = REPO_URL + "vibe-coding-runs/"
OUT = HERE / "out"
DEST = PUBLIC / "vibe"
SHOT_WIDTH, SHOT_MAX_H, THUMB, GRID_COLS, LABEL_H = 800, 2600, (400, 330), 5, 26
TASKS = {"t1": ("One sentence: an expense page", "一句话：记账小网页"), "t2": ("One paragraph: a family ledger", "一段话：家庭记账本")}
COMPARE_SHOT = {"t1": "total", "t2": "category"}      # the screenshot each grid shows: the app with the tester's entries in
CHECKS = {
    "open": ("opens", "能打开"), "add": ("records an expense", "能记一笔"), "total": ("total is right", "合计正确"),
    "reopen": ("still there after closing and reopening", "关掉重开还在"), "record": ("records income and expenses", "收支记得进"),
    "month": ("month's income, spending and balance", "月度收支和结余"), "category": ("spending by category", "分类统计"),
    "by-month": ("switches between months", "按月切换"), "budget": ("warns over budget", "超预算提醒"), "export": ("exports a spreadsheet", "导出表格"),
}
OPENED = {"file": ("Double-click", "双击就能打开"), "command": ("One command first", "要先跑一条命令"), "failed": ("Did not open", "打不开")}
OPENS_BIT = {"file": ("opens by double-click", "双击就能打开"), "command": ("needs a start command first", "要先跑一条启动命令"), "failed": ("did not open", "打不开")}
REPLY = (HERE / "in" / "reply.txt").read_text().strip()
REVIEW = json.loads((HERE / "review.json").read_text()) if (HERE / "review.json").exists() else {}
# Short card notes, written by hand from the runs (review.json has the long versions).
NOTES = {
    "gsd-build/get-shit-done": ("Ran out of the 45 minutes on the ledger with only its first phase built.", "家庭记账本 45 分钟里只做完第一阶段。"),
    "anombyte93/prd-taskmaster": ("Still planning and building at both time limits; both pages were unfinished.", "两题都到时间上限还没做完，页面是半成品。"),
    "nurettincoban/ai-prd-workflow": ("At the 45-minute limit the ledger had no budget and no export.", "45 分钟时记账本还没有预算和导出。"),
    "coleam00/context-engineering-intro": ("The ledger needs a start command first: bash output/start.sh.", "记账本要先运行一条命令：bash output/start.sh。"),
}
VERDICT = {
    "title": ["Which one to install", "到底装哪个"],
    "basis": ["after building two apps with each", "每个都实际做了两个网页之后"], "more": ["See the test →", "看实测 →"],
    "rule": ["Ranked by checks passed on the two apps, then whether a person can open them by double-click, then the minutes you wait, then how often the build stopped to ask, then GitHub stars. One run per tool and request, limits of 30 and 45 minutes; the requests are small apps, not the larger projects these tools are built for.",
             "排名规则：先看两个网页的检查过了几项，再看能不能双击打开，再看要等多少分钟，再看中途停下来问了几次，最后看 GitHub 星数。每个工具每题只跑一次，时间上限 30 和 45 分钟；题目是小网页，不是这些工具主要面向的大项目。"],
    "picks": [
        {"repo": "SuperClaude-Org/SuperClaude_Framework", "role": ["If you want one installed", "真要装一个"],
         "why": ["Every check on both apps, in 7.6 minutes in all (Claude Code with no tool: 5.0), at 1.8 times its usage. It stopped to ask once per app.",
                 "两个网页的检查全过，两题共 7.6 分钟（不装工具是 5.0 分钟），用量是不装工具的 1.8 倍。每题中途问了一次。"]},
        {"repo": "KhazP/vibe-coding-prompt-template", "role": ["If you would rather not be asked anything", "不想被问问题"],
         "why": ["Every check on both apps without stopping to ask once, in 9.3 minutes in all, at 2.4 times the usage of no tool.",
                 "两个网页的检查全过，一次都没停下来问，两题共 9.3 分钟，用量是不装工具的 2.4 倍。"]},
        {"repo": "botingw/rulebook-ai", "role": ["If you want house rules, not a workflow", "只想加几条规矩、不要流程"],
         "why": ["It only adds rule files, and stayed closest to no tool: every check, 7.8 minutes, 1.7 times the usage, one question per app.",
                 "它只往项目里加规则文件，表现也最接近不装工具：检查全过，共 7.8 分钟，用量 1.7 倍，每题问了一次。"]},
    ],
    "avoid_label": ["Out of time before the ledger was finished:", "家庭记账本到时间还没做完："],
    "avoid": [
        {"repo": "gsd-build/get-shit-done", "why": ["2 of 8 at 45 minutes, its first phase of four done", "45 分钟只过 2 项，四个阶段做完一个"]},
        {"repo": "anombyte93/prd-taskmaster", "why": ["1 of 4 on the one-sentence page and 3 of 8 on the ledger", "一句话记账过 1 项，记账本过 3 项"]},
        {"repo": "nurettincoban/ai-prd-workflow", "why": ["6 of 8, at 13.5 times the usage of no tool", "过 6 项，用量是不装工具的 13.5 倍"]},
    ],
    "caveat": ["Whichever you pick: Claude Code with no tool built both apps in 5 minutes with every check passed, on less usage than any tool. At this size a tool adds steps, questions and usage, not passed checks. Start without one; try a tool when a project outgrows a single request.",
               "不管选哪个：不装任何工具的 Claude Code 5 分钟就把两个网页都做对了，用量比任何一个工具都少。在这个规模上，装工具多出来的是步骤、提问和用量，不是通过的检查。先别装；等项目大到一句话说不清时再试工具。"],
}


def load() -> dict:
    """results.json as {repo: {task: row}}."""
    by = {}
    for r in json.loads((HERE / "results.json").read_text()):
        by.setdefault(r["repo"], {})[r["task"]] = r
    return by


def checks_of(repo: str, task: str) -> list[dict]:
    run = OUT / task / key(repo)
    report = json.loads((run / "test" / "report.json").read_text()) if (run / "test" / "report.json").exists() else {}
    fixed = REVIEW.get(f"{task}/{repo}", {}).get("checks", {})
    return [{**c, "pass": fixed[c["id"]]["pass"] if c["id"] in fixed else bool(c.get("pass")),
             "observed": fixed.get(c["id"], {}).get("why") or c.get("observed", "")} for c in report.get("checks", [])]


def publish_shots(repo: str, task: str) -> list[tuple[str, dict]]:
    """The tester's screenshots for one build, scaled into the page folder."""
    out = []
    for c in checks_of(repo, task):
        src = OUT / task / key(repo) / "test" / (c.get("shot") or "")
        if not c.get("shot") or not src.exists():
            continue
        name = f"{key(repo)}-{task}-{c['id']}.jpg"
        im = Image.open(src).convert("RGB")
        im = im.resize((SHOT_WIDTH, round(im.height * SHOT_WIDTH / im.width)))
        im.crop((0, 0, SHOT_WIDTH, min(im.height, SHOT_MAX_H))).save(DEST / name, quality=70)
        out.append((name, c))
    return out


def stops(repo: str, task: str) -> list[str]:
    """What the build said each time it stopped short of a finished app (the turns that got the stock reply)."""
    p = OUT / task / key(repo) / "turns.json"
    turns = json.loads(p.read_text()) if p.exists() else []
    return [t["result"] for t in turns[:-1]]


def task_html(repo: str, task: str, r: dict) -> str:
    brief = (HERE / "in" / f"brief-{task}.txt").read_text().strip()
    rows = "".join(f"<tr><th>{esc(CHECKS[c['id']][0])}</th><td>{'<span class=ok>pass</span>' if c['pass'] else '<span class=no>fail</span>'}</td>"
                   f"<td>{esc(c['observed'])}</td><td><a href='{name}'><img src='{name}' alt='{esc(c['id'])}' width='240' loading='lazy'></a></td></tr>"
                   for name, c in publish_shots(repo, task))
    asked = "".join(f"<li><pre>{esc(s[-1500:])}</pre></li>" for s in stops(repo, task)) or "<li>It did not stop to ask.</li>"
    cmd = f" The command: <code>{esc(r['start_command'])}</code>." if r["start_command"] else ""
    note = REVIEW.get(f"{task}/{repo}", {}).get("note")
    return f"""<h2>{esc(TASKS[task][0])}</h2><p class="mute">The request, word for word: {esc(brief)}</p>
<p><b>{f"Ran: all {r['of']} checks passed" if r['ran'] else f"{r['passed']} of {r['of']} checks passed"}.</b> Opens: {esc(OPENED[r['opened']][0].lower())}.{cmd}
Built in {r['minutes']} minutes (limit {30 if task == 't1' else 45}); it stopped to ask {r['stops']} time(s); how it ended: {esc(r['ending'])}.
Usage at API prices: ${r['usage']['usd']} ({r.get('usage_x', '-')} times the run with no tool). Packages: {esc(', '.join(r['packages']) or 'none (plain HTML, CSS and JavaScript)')}.</p>
{f'<p><b>Our note:</b> {esc(note)}</p>' if note else ''}
<table><tr><th>Check</th><th>Verdict</th><th>What the tester saw</th><th>Screenshot</th></tr>{rows}</table>
<h3>Where it stopped, and got the reply 「{esc(REPLY)}」</h3><ol>{asked}</ol>"""


def page(repo: str, runs: dict) -> str:
    name = "Control: Claude Code with no tool" if repo == CONTROL else repo
    first = next(iter(runs.values()))
    setup = "" if repo == CONTROL else f"<p><b>Install:</b> {esc(first['setup'])} (repo commit {esc(first['commit'])})</p>"
    body = "".join(task_html(repo, t, runs[t]) for t in TASKS if t in runs)
    return shell(f"{name}: vibe coding test", ("/best/vibe-coding/", "Vibe coding tools"), f"""<h1>{esc(name)}: vibe coding test</h1>
<p class="mute">Installed from its README in a throwaway sandbox, then used by Claude Code (Claude Opus 5.5) to build two apps from requests
written the way someone who cannot code would write them. Whenever the build stopped to ask a question or for approval, it got the same reply.
A separate tester session, with no tool loaded, opened each app in a browser and ran the checks; we went through every screenshot.
<a href="{URL}RESULTS.md">All results</a> · <a href="{URL}in/prompt.txt">The task</a> · <a href="{URL}in/test-t2.md">The tester's checks</a></p>
{setup}{body}""")


def compare(rows: list[tuple[str, dict]], task: str) -> tuple[int, int]:
    """Every build with the tester's entries in, in one grid, the control first."""
    font = ImageFont.load_default(size=14)
    grid = Image.new("RGB", (THUMB[0] * GRID_COLS, (THUMB[1] + LABEL_H) * -(-len(rows) // GRID_COLS)), "white")
    d = ImageDraw.Draw(grid)
    for i, (repo, r) in enumerate(rows):
        x, y = (i % GRID_COLS) * THUMB[0], (i // GRID_COLS) * (THUMB[1] + LABEL_H)
        shot = next((OUT / task / key(repo) / "test" / c["shot"] for c in checks_of(repo, task) if c["id"] == COMPARE_SHOT[task] and c.get("shot")), None)
        if shot and shot.exists():
            im = Image.open(shot).convert("RGB")
            im = im.resize((THUMB[0], round(im.height * THUMB[0] / im.width))).crop((0, 0, THUMB[0], THUMB[1]))
            grid.paste(im, (x, y + LABEL_H))
        label = "no tool (control)" if repo == CONTROL else repo.split("/")[1]
        d.text((x + 6, y + 5), f"{label}: {r['passed']}/{r['of']}", fill="black", font=font)
    grid.save(DEST / f"compare-{task}.jpg", quality=80)
    return grid.size


def usage_x(runs: dict, ctrl: dict) -> float:
    """Both builds' usage at API prices, as a multiple of the two builds with no tool."""
    base = sum(ctrl[t]["usage"]["usd"] for t in TASKS)
    return round(sum(runs[t]["usage"]["usd"] for t in TASKS if t in runs) / base, 1)


def opens(runs: dict, words: dict = OPENED) -> tuple[str, str]:
    how = {t: runs[t]["opened"] for t in TASKS if t in runs}
    if len(set(how.values())) == 1:
        return words[next(iter(how.values()))]
    return (f"Page: {words[how['t1']][0].lower()}; ledger: {words[how['t2']][0].lower()}", f"记账网页{words[how['t1']][1]}；记账本{words[how['t2']][1]}")


def asked_bit(n: int) -> list[str]:
    if n == 0:
        return ["never stopped to ask", "一次都没停下来问"]
    return [f"stopped to ask {'once' if n == 1 else f'{n} times'}", f"中途停下来问了 {n} 次"]


def card(repo: str, runs: dict, ctrl: dict) -> dict:
    t1, t2 = runs["t1"], runs["t2"]
    x, asked = usage_x(runs, ctrl), t1["stops"] + t2["stops"]
    cls = lambda r: "touch-ups" if r["ran"] else "substantial"   # noqa: E731
    how = opens(runs)
    cells = [[f"{t1['passed']}/{t1['of']}", None, cls(t1)], [f"{t2['passed']}/{t2['of']}", None, cls(t2)], [how[0], how[1]],
             [str(asked), None, "num"], [f"{t1['minutes']} + {t2['minutes']} min", f"{t1['minutes']} + {t2['minutes']} 分钟", "num"], [f"×{x}", None, "num"]]
    bits = [[f"one-sentence page: {t1['passed']} of {t1['of']} checks", f"一句话记账：{t1['of']} 项过 {t1['passed']} 项"],
            [f"family ledger: {t2['passed']} of {t2['of']}", f"家庭记账本：{t2['of']} 项过 {t2['passed']} 项"],
            list(opens(runs, OPENS_BIT)), asked_bit(asked),
            [f"{t1['minutes']} + {t2['minutes']} min, {x}× the usage of no tool", f"{t1['minutes']} + {t2['minutes']} 分钟，用量是不装工具的 {x} 倍"]]
    out = {"ran": True, "stars": t1["stars"], "sheet": key(repo) + ".html", "cells": cells, "bits": bits}
    if repo in NOTES:
        out.update(note=NOTES[repo][0], note_zh=NOTES[repo][1])
    return out


def order(item: tuple[str, dict]) -> tuple:
    """Best first: checks passed, opens by double-click, minutes waited, fewer stops, stars (VERDICT["rule"])."""
    repo, runs = item
    t1, t2 = runs["t1"], runs["t2"]
    return (-(t1["passed"] + t2["passed"]), t1["opened"] != "file" or t2["opened"] != "file", t1["minutes"] + t2["minutes"],
            t1["stops"] + t2["stops"], -t1["stars"])


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    by = load()
    for repo, runs in by.items():
        (DEST / (key(repo) + ".html")).write_text(page(repo, runs))
    sizes = {t: compare([(repo, runs[t]) for repo, runs in by.items() if t in runs], t) for t in TASKS}
    ctrl = by.pop(CONTROL)
    tools = sorted(((repo, runs) for repo, runs in by.items() if set(TASKS) <= set(runs)), key=order)
    print("\n".join(f"{repo}: {runs['t1']['passed']}/{runs['t1']['of']} {runs['t2']['passed']}/{runs['t2']['of']} ×{usage_x(runs, ctrl)}" for repo, runs in tools))
    if not VERDICT:
        print("VERDICT not written yet: page data not updated"); return
    write_runs(SLUG, entry(tools, ctrl, sizes))


def entry(tools: list, ctrl: dict, sizes: dict) -> dict:
    full = [(r, v) for r, v in tools if v["t1"]["ran"] and v["t2"]["ran"]]
    short = [(r, v) for r, v in tools if not (v["t1"]["ran"] and v["t2"]["ran"])]
    base_min = ctrl["t1"]["minutes"] + ctrl["t2"]["minutes"]
    waits = [(v["t1"]["minutes"] + v["t2"]["minutes"]) / base_min for _, v in full]
    xs = [usage_x(v, ctrl) for _, v in full]
    short_x = [usage_x(v, ctrl) for _, v in short]
    reply = REPLY
    return {
        "type": "table", "date": DATE, "dir": "/best-runs/vibe/", "results": URL + "RESULTS.md",
        "title": ["Vibe coding tools tested: one sentence and one paragraph, two apps", "实测对比：一句话、一段话，各做一个能用的网页"],
        "intro": [f"On 26 and 27 October 2026 we gave {len(tools)} of these tools the same two requests, written the way someone who cannot code would write them: one sentence for an expense page, and one paragraph for a family ledger with monthly totals, a category chart, a budget warning and an Excel export. Each was installed from its README in a throwaway sandbox and used through its own workflow by Claude Code (Claude Opus 5.5). When a build stopped to ask a question or for approval, it got the same reply, 「{reply}」 (\"I don't know about this; do what you recommend and carry on\"). Limits: 30 minutes for the page, 45 for the ledger. A separate tester session opened each app in a browser and ran 4 and 8 checks, and we went through every screenshot. Claude Code with no tool did the same as a control.",
                  f"2026 年 10 月 26–27 日，我们给其中 {len(tools)} 个工具同样两个需求，照不会写代码的人的说法写：一句话做一个记账小网页；一段话做一个家庭记账本，要按月看收支、分类图、预算提醒和导出 Excel。每个工具在用完即删的沙箱里照 README 安装，由 Claude Code（Claude Opus 5.5）按工具自己的流程使用。中途停下来提问或要求确认时，一律回复「{reply}」。时间上限：记账网页 30 分钟，记账本 45 分钟。另起一个测试会话在浏览器里打开成品，分别做 4 项和 8 项检查，每张截图我们都看过。不装任何工具的 Claude Code 做同样的题作对照。"],
        "finding": [f"Claude Code with no tool built both apps and passed all 12 checks, in {ctrl['t1']['minutes']} and {ctrl['t2']['minutes']} minutes. {len(full)} of the {len(tools)} tools passed all 12 as well, taking {min(waits):.1f} to {max(waits):.1f} times as long and {min(xs)} to {max(xs)} times the usage: a tool added time and usage, not a passed check. {len(short)} ran out of time with work unfinished, at {min(short_x)} to {max(short_x)} times the usage. Every finished app opened by double-click except one ledger that needs a start command.",
                    f"不装任何工具的 Claude Code 两个网页都做出来了，12 项检查全过，分别用了 {ctrl['t1']['minutes']} 和 {ctrl['t2']['minutes']} 分钟。{len(tools)} 个工具里有 {len(full)} 个也是 12 项全过，但耗时是它的 {min(waits):.1f} 到 {max(waits):.1f} 倍，用量是它的 {min(xs)} 到 {max(xs)} 倍：装工具多花了时间和用量，没有多过任何一项。{len(short)} 个到时间还没做完，用量是对照组的 {min(short_x)} 到 {max(short_x)} 倍。做完的网页除了一个记账本要先跑启动命令，都能双击打开。"],
        "compare": [{"src": "compare-t2.jpg", "w": sizes["t2"][0], "h": sizes["t2"][1],
                     "en": "Every family ledger after the tester entered October's records, the no-tool build first; the number is checks passed of 8.",
                     "zh": "测试员录入 10 月记录后的每个家庭记账本，第一个是不装工具做的；数字是 8 项检查过了几项。"},
                    {"src": "compare-t1.jpg", "w": sizes["t1"][0], "h": sizes["t1"][1],
                     "en": "Every one-sentence expense page after three entries (total 41.50), the no-tool build first.",
                     "zh": "每个一句话记账网页记了三笔之后（合计应为 41.50），第一个是不装工具做的。"}],
        "name_col": ["Tool", "工具"],
        "columns": [["One sentence (4 checks)", "一句话记账（4 项）"], ["One paragraph (8 checks)", "一段话记账本（8 项）"], ["How it opens", "怎么打开"],
                    ["Stopped to ask", "中途问了几次"], ["Build time (page + ledger)", "做了多久（网页 + 记账本）"], ["Usage vs no tool", "用量（不装工具 = 1）"]],
        "see": ["See both builds →", "看两次实测 →"], "evidence": ["Both builds", "两次实测"],
        "line_label": [f"Vibe coding test, {DATE}:", f"{DATE} 实测："],
        "control": {"sheet": key(CONTROL) + ".html", "label": ["See the no-tool run →", "看不装工具的对照 →"]},
        "verdict": VERDICT, "runs": {repo: card(repo, runs, ctrl) for repo, runs in tools}}


if __name__ == "__main__":
    main()
