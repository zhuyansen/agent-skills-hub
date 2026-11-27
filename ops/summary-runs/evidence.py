"""Evidence pages and page data for the meeting-summary test.

  python3 ops/summary-runs/evidence.py      # after score.py (results.json) and render.py (out/evidence/*.png)

Writes frontend/public/best-runs/summary/: <owner__repo>.html (noindex: both requests word for word, the 7
verdicts with what decided them, every statement the tester found made up, the evidence picture with the
script's marks, the summary as delivered, where the build stopped to ask, the install), the pictures as WebP,
and the "summarization" entry of frontend/scripts/scenario-runs.json (type "table").
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "in"))
from runs_common import PUBLIC, REPO_URL, esc, key, shell, webp_copy, write_runs  # noqa: E402
import kit  # noqa: E402

SLUG, DATE, CONTROL = "summarization", "2026-11-08", "octocat/Hello-World"
URL = REPO_URL + "summary-runs/"
OUT = HERE / "out"
DEST = PUBLIC / "summary"
PICTURE_WIDTH = 1000
TASKS = {"t1": ("One line", "一句话"), "t2": ("One paragraph", "一段话")}
CHECKS = {
    "length": "At most 800 字", "conclusion": "Opens with what was decided", "decisions": "All 7 decisions",
    "todos": "All 6 tasks, each with its owner and due date", "numbers": "Every figure as the record says it",
    "undecided": "The 3 open points marked not decided", "invented": "Nothing the record does not support (the tester)",
}
REPLY = (HERE / "in" / "reply.txt").read_text().strip()
# Short card notes, written by hand from results.json ("install", "why", "setup").
NOTES = {
    "phuryn/pm-skills": ("Its pm-execution plugin, which holds the summarize-meeting skill; only that plugin was installed.",
                         "装的是它的 pm-execution 插件（含 summarize-meeting skill），只装了这一个插件。"),
    "github/awesome-copilot": ("Only its meeting-minutes skill, which must ask up to 3 questions before writing; it stopped to ask once on each request.",
                               "只装了 meeting-minutes 这一个 skill，它要求动笔前先问最多 3 个问题；两种问法下各停下来问了一次。"),
    "composio-community/awesome-codex-skills": ("Only its meeting-notes-and-actions skill, which says both \"do not invent facts\" and \"suggest a deadline when one is missing\".",
                                                "只装了 meeting-notes-and-actions 这一个 skill，它既写「不要编造事实」，又写「缺截止日期就建议一个」。"),
    "genspark-ai/genoffice": ("Only its meeting-minutes skill, written for GenOffice's own AI; it delivered a Word file both times.",
                              "只装了 meeting-minutes 这一个 skill，它本来是写给 GenOffice 自带的 AI 用的；两次交的都是 Word 文件。"),
    "NousResearch/hermes-agent": ("Only its meeting-action-items skill, not the Hermes agent; the skill says never to invent a due date.",
                                  "只装了 meeting-action-items 这一个 skill，没装 Hermes 本体；这个 skill 写明截止日期绝不编。"),
    "steipete/summarize": ("A command-line summariser for files, pages and videos (summarize 0.26.0) with its skill, run through the logged-in Claude Code. Not made for meetings.",
                           "通用的命令行摘要工具（summarize 0.26.0，能总结文件、网页和视频），加上它的 skill，模型走已登录的 Claude Code。不是专门做会议的。"),
}
# One skill tested inside a bigger repository: its sub-skill page shows the result, the repository's own page does not.
SUBS = {"phuryn/pm-skills": "summarize-meeting", "github/awesome-copilot": "meeting-minutes", "composio-community/awesome-codex-skills": "meeting-notes-and-actions",
        "genspark-ai/genoffice": "meeting-minutes", "NousResearch/hermes-agent": "meeting-action-items"}
VERDICT = {
    "title": ["Which one to install", "到底装哪个"],
    "rule": ["Ranked by checks passed on both requests, then statements made up, then build time. One run per tool and request, on one made-up meeting record; the same 7 checks for both requests, the 800-字 limit included, which only the paragraph asks for.",
             "排名规则：先看两种问法一共过了几项，再看编了几处，最后看做了多久。每个工具每种问法只跑一次，用的是一份虚构的会议记录；两种问法用同一套 7 项检查，800 字的上限也算在内，虽然只有那段话提了这个要求。"],
    "picks": [
        {"repo": "phuryn/pm-skills", "role": ["If you want a meeting summary skill at all", "真要装一个会议总结 skill"],
         "why": ["On the one-paragraph request it passed all 7 checks and made nothing up, in 0.9 minutes of building; Claude Code with nothing installed did the same in 1.5. On the one-line request it passed 4 of 7 and made up 4 statements, against the control's 5 of 7 and 2.",
                 "一段话的问法下 7 项全过、没编一处，做了 0.9 分钟；什么都不装的 Claude Code 也是 7 项全过，用了 1.5 分钟。一句话的问法下它过 4 项、编了 4 处，对照组是过 5 项、编 2 处。"]},
        {"repo": "steipete/summarize", "role": ["If you will only ever type one line", "只打算说一句话"],
         "why": ["The only build that made nothing up on the one-line request, and the shortest at 942 字; every other ran past 2,000. With the paragraph it passed 5 of 7: one open point became a task with no 没定 mark, and one remark got an owner the record does not give.",
                 "一句话的问法下唯一一个没编任何东西的，也最短，942 字；其他都超过 2,000 字。按那段话问，它过 5 项：一件没定的事被写成了待办、没标没定，一句随口的话被安上了原文没有的负责人。"]},
        {"repo": "genspark-ai/genoffice", "role": ["If the summary must be a Word file", "必须交 Word 文件"],
         "why": ["The only tool that delivered a .docx both times. 6 of 7 on the paragraph, with 2 additions the record does not support (a note-taker 「待定」, an agenda 「待定」); 5 of 7 on the one line, with 3.",
                 "唯一两次都交 Word 文件的。一段话问法过 6 项，多写了两处原文没有的（「记录人 待定」「议程待定」）；一句话问法过 5 项，编了 3 处。"]},
    ],
    "avoid_label": ["Made up the most on the one-line request:", "一句话问法下编得最多："],
    "avoid": [
        {"repo": "composio-community/awesome-codex-skills", "why": ["10 statements, mostly 「建议」 due dates the record does not give", "编了 10 处，大多是原文没有的「建议」截止日期"]},
        {"repo": "github/awesome-copilot", "why": ["7 statements, and 2 of 7 checks, in a 12-section formal minutes template of 2,826 字", "编了 7 处，7 项只过 2 项，是一份 12 个部分、2,826 字的正式纪要"]},
        {"repo": "NousResearch/hermes-agent", "why": ["7 statements, although its skill says never to invent a due date", "编了 7 处，尽管它的 skill 写明截止日期绝不编"]},
    ],
    "caveat": ["Whichever you pick: the request did more than any tool. Asked with the one-paragraph request (it is on every evidence page), Claude Code with nothing installed passed all 7 checks; asked in one line, every build ran past 800 字 and 6 of 7 made something up. Check owners and due dates against the record before you send a summary on.",
               "不管选哪个：问法比工具管用。用那段话去问（每个证据页上都有原文），什么都不装的 Claude Code 7 项全过；只说一句话，每一份都超过 800 字，7 份里 6 份编了东西。总结转发之前，负责人和截止日期要对照原文核一遍。"],
}


def load() -> dict:
    """results.json as {repo: {task: row}}."""
    by = {}
    for r in json.loads((HERE / "results.json").read_text()):
        by.setdefault(r["repo"], {})[r["task"]] = r
    return by


def document(task: str, repo: str) -> tuple[str, str]:
    """The summary the tester read: its file name and text."""
    run = OUT / task / key(repo)
    report = json.loads((run / "test" / "report.json").read_text())
    named = report.get("file") or ""
    doc = run / "deliverables" / named[len("output/"):] if named.startswith("output/") else None
    doc = doc if doc and doc.is_file() else kit.deliverable(run / "deliverables")
    return doc.name, kit.read(doc)


def stops(repo: str, task: str) -> list[str]:
    """What the build said each time it stopped short of a finished summary (the turns that got the stock reply)."""
    p = OUT / task / key(repo) / "turns.json"
    turns = json.loads(p.read_text()) if p.exists() else []
    return [t["result"] for t in turns[:-1]]


def picture(repo: str, task: str) -> str:
    """The evidence picture (render.py) as WebP in the page folder; its file name, or "" without one."""
    src = OUT / "evidence" / f"{task}__{key(repo)}.png"
    if not src.exists():
        return ""
    name = f"{key(repo)}-{task}.webp"
    webp_copy(src, DEST / name, PICTURE_WIDTH)
    return name


def task_html(repo: str, task: str, r: dict) -> str:
    brief = (HERE / "in" / f"brief-{task}.txt").read_text().strip()
    rows = []
    for c, label in CHECKS.items():
        ok = r["checks"][c]
        seen = r["observed"].get(c) if c != "invented" else (f"{len(r['invented'])} statement(s) the record does not support, listed below" if r["invented"] else "None found")
        rows.append(f"<tr><th>{esc(label)}</th><td>{'<span class=ok>pass</span>' if ok else '<span class=no>fail</span>'}</td><td>{esc(seen)}</td></tr>")
    made_up = "".join(f"<li><pre>{esc(i['quote'])}</pre>{esc(i['why'])}</li>" for i in r["invented"]) or "<li>Nothing.</li>"
    doubts = "".join(f"<li><b>{esc(CHECKS[c])}:</b> {esc(d)}</li>" for c, d in r.get("doubts", {}).items())
    noise = f"<p><b>Small talk it kept:</b> {esc('、'.join(r['noise']))}</p>" if r.get("noise") else ""
    asked = "".join(f"<li><pre>{esc(s[-1500:])}</pre></li>" for s in stops(repo, task)) or "<li>It did not stop to ask.</li>"
    pic = picture(repo, task)
    shot = (f"<h3>The summary with the script's marks</h3><p class=mute>The picture shown in our video. Red: a figure the record does not say, "
            f"an old figure given as current, a task with the wrong owner or date, an open point not marked open. Yellow: lines the script "
            f"flagged for the tester to read (candidates, not verdicts; the tester's list above is the verdict). Blue: small talk.</p>"
            f"<a href='{pic}'><img src='{pic}' alt='{esc(repo)} {task} summary' width='{PICTURE_WIDTH}' loading='lazy'></a>") if pic else ""
    name, text = document(task, repo)
    return f"""<h2>{esc(TASKS[task][0])}</h2><p class="mute">The request, word for word: 「{esc(brief)}」</p>
<p><b>{r['passed']} of {r['of']} checks passed.</b> {r['zi']:,} 字, in {esc(name)}. Built in {r['minutes']} minutes; it stopped to ask {r['stops']} time(s);
how it ended: {esc(r['ending'])}. Usage at API prices: ${r['usage']['usd']} ({r.get('usage_x', '-')} times the run with no tool on this request).</p>
<table><tr><th>Check</th><th>Verdict</th><th>What decided it</th></tr>{''.join(rows)}</table>
<h3>What the tester found the record does not support</h3><ol>{made_up}</ol>{noise}
{f'<h3>Where the tester doubted how the script read it</h3><p class=mute>Some of these led to the script fixes listed in RESULTS.md; every verdict on this page comes from the fixed script.</p><ul>{doubts}</ul>' if doubts else ''}
<h3>The tester's notes</h3><p>{esc(r['tester_notes'])}</p>
{shot}
<details><summary>The summary as delivered ({esc(name)})</summary><pre>{esc(text)}</pre></details>
<h3>Where it stopped, and got the reply 「{esc(REPLY)}」</h3><ol>{asked}</ol>"""


def page(repo: str, runs: dict) -> str:
    name = "Control: Claude Code with nothing installed" if repo == CONTROL else repo
    first = runs["t1"]
    setup = "" if repo == CONTROL else (f"<p><b>Install:</b> {esc(first['setup'].removeprefix('SETUP: done').strip())} (repo commit {esc(first['commit'])})</p>"
                                        f"<p class=mute>Why it was in the test (our note before the run): {esc(first['why'])}</p>")
    body = "".join(task_html(repo, t, runs[t]) for t in TASKS if t in runs)
    return shell(f"{name}: meeting summary test", ("/best/summarization/", "Summarization tools"), f"""<h1>{esc(name)}: meeting summary test</h1>
<p class="mute">Test of {DATE}. Installed from its README in a throwaway sandbox, then used by Claude Code (Claude Opus 5.5) to summarise
the same made-up meeting record, an automatic transcript of a product team's weekly meeting of about 5,000 字, from two requests in the person's
words. Whenever the build stopped short of a finished summary, it got the same reply. A separate tester session, with no tool loaded, checked the
summary against 7 checks fixed before the runs: six scripted against an answer key written with the record, and one, anything the record does
not support, read by the tester sentence by sentence. Everything in the record is made up.
<a href="{URL}RESULTS.md">All results</a> · <a href="{URL}in/fixtures/会议记录.txt">The meeting record</a> · <a href="{URL}in/test.md">The checklist</a> · <a href="{URL}in/truth.json">The answer key</a></p>
{setup}{body}""")


def cls(r: dict) -> str:
    return "touch-ups" if r["passed"] == r["of"] else "substantial" if r["passed"] <= r["of"] // 2 else ""


def made_up(n: int) -> list[str]:
    return [f"made up {n} statement{'s' if n != 1 else ''}", f"编了 {n} 处"] if n else ["made up nothing", "没编"]


def card(repo: str, runs: dict) -> dict:
    t1, t2 = runs["t1"], runs["t2"]
    n1, n2 = len(t1["invented"]), len(t2["invented"])
    cells = [[f"{t1['passed']}/{t1['of']}", None, cls(t1)], [str(n1), None, "num"], [f"{t2['passed']}/{t2['of']}", None, cls(t2)], [str(n2), None, "num"],
             [f"{t1['zi']:,} / {t2['zi']:,}", None, "num"], [f"×{t1['usage_x']} / ×{t2['usage_x']}", None, "num"]]
    m1, m2 = made_up(n1), made_up(n2)
    bits = [[f"one-line request: {t1['passed']} of {t1['of']} checks, {m1[0]}", f"一句话：{t1['of']} 项过 {t1['passed']} 项，{m1[1]}"],
            [f"one-paragraph request: {t2['passed']} of {t2['of']}, {m2[0]}", f"一段话：{t2['of']} 项过 {t2['passed']} 项，{m2[1]}"],
            [f"{t1['zi']:,} and {t2['zi']:,} 字", f"{t1['zi']:,} 字和 {t2['zi']:,} 字"],
            [f"{t1['minutes']} + {t2['minutes']} min", f"{t1['minutes']} + {t2['minutes']} 分钟"]]
    out = {"ran": True, "stars": t1["stars"], "sheet": key(repo) + ".html", "cells": cells, "bits": bits}
    if repo in NOTES:
        out.update(note=NOTES[repo][0], note_zh=NOTES[repo][1])
    if repo in SUBS:
        out["sub"] = SUBS[repo]
    return out


def order(item: tuple[str, dict]) -> tuple:
    """Best first: checks passed on both requests, statements made up, build time, stars (VERDICT["rule"])."""
    _, runs = item
    t1, t2 = runs["t1"], runs["t2"]
    return (-(t1["passed"] + t2["passed"]), len(t1["invented"]) + len(t2["invented"]), t1["minutes"] + t2["minutes"], -t1["stars"])


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    by = load()
    for repo, runs in by.items():
        (DEST / (key(repo) + ".html")).write_text(page(repo, runs))
    ctrl = by.pop(CONTROL)
    tools = sorted(((repo, runs) for repo, runs in by.items() if set(TASKS) <= set(runs)), key=order)
    print("\n".join(f"{repo}: {runs['t1']['passed']}/7 ({len(runs['t1']['invented'])}) {runs['t2']['passed']}/7 ({len(runs['t2']['invented'])})" for repo, runs in tools))
    write_runs(SLUG, entry(tools, ctrl))


def entry(tools: list, ctrl: dict) -> dict:
    c1, c2 = ctrl["t1"], ctrl["t2"]
    rows = [c1] + [v["t1"] for _, v in tools]
    made = [r for r in rows if r["invented"]]
    full = [r for r, v in tools if v["t2"]["passed"] == v["t2"]["of"]]
    over = [r for r in rows if not r["checks"]["length"]]
    assert len(over) == len(rows), "every one-line summary ran past 800 字"
    counts = [(len(v["t1"]["invented"]), r.split("/")[1]) for r, v in tools if v["t1"]["invented"]]
    counts_en = ", ".join(f"{n} ({name})" for n, name in counts[:-1]) + f" and {counts[-1][0]} ({counts[-1][1]})"
    counts_zh = "、".join(f"{name} {n} 处" for n, name in counts)
    clean = [r for r, v in tools if not v["t1"]["invented"]]
    brief1 = (HERE / "in" / "brief-t1.txt").read_text().strip()
    return {
        "type": "table", "date": DATE, "dir": "/best-runs/summary/", "results": URL + "RESULTS.md",
        "title": ["Meeting summary tools tested: one made-up meeting, two ways of asking", "实测对比：同一份虚构会议记录，两种问法"],
        "intro": [f"On {DATE} we gave {len(tools)} of these tools the same made-up meeting record: the automatic transcript of a product team's weekly meeting, about 5,000 字, with 7 decisions, 6 tasks with an owner and a due date, 3 points left open, 7 figures the meeting replaced, loose remarks that are not tasks, and small talk. Each was installed from its README in a throwaway sandbox and used by Claude Code (Claude Opus 5.5) from two requests in the person's words: one line, 「{brief1}」 (\"Summarise this meeting record for me\"), and one paragraph asking for 800 字 or fewer, the conclusion first, every decision and every task with its owner and due date, figures as written, open points marked 没定, and nothing made up. A tester session with no tool loaded checked every summary against the same 7 checks, fixed before the runs: six scripted against an answer key, and one, anything the record does not support, read sentence by sentence. Claude Code with nothing installed did the same as a control.",
                  f"{DATE}，我们给其中 {len(tools)} 个工具同一份虚构的会议记录：一个产品团队周会的自动转写稿，约 5,000 字，里面有 7 个拍板的决定、6 个有负责人和截止日期的待办、3 件没定的事、7 个会上被推翻的旧数字，还有不算待办的随口一提和闲聊。每个工具在用完即删的沙箱里照 README 安装，由 Claude Code（Claude Opus 5.5）按两种说法使用：一句话，「{brief1}」；一段话，要求 800 字以内、先写结论、列全决定和待办（谁负责、哪天之前）、数字照原文、没定的标「没定」、原文没有的一个字都别编。另起一个不装工具的测试会话，用开跑前定好的同一套 7 项检查核对每份总结：6 项由脚本对照答案判定，1 项（有没有原文不支持的内容）由测试员逐句读。不装任何工具的 Claude Code 做同样的事，作为对照。"],
        "finding": [f"The request mattered more than the tool. Asked in one line, every build ran past 800 字 and {len(made)} of {len(rows)} made something up, the control included ({len(c1['invented'])} statements); the tools made up {counts_en}, and only {', '.join(r.split('/')[1] for r in clean)} made up nothing. Asked in one paragraph, Claude Code with nothing installed passed all 7 checks, as {len(full)} of the {len(tools)} tools did; none passed more. What was made up was most often an owner or a due date for a remark nobody was given as a task.",
                    f"问法比工具管用。只说一句话时，每一份都超过 800 字，{len(rows)} 份里 {len(made)} 份编了东西，对照组也编了 {len(c1['invented'])} 处；各工具编的处数：{counts_zh}，只有 {'、'.join(r.split('/')[1] for r in clean)} 一处没编。按那段话问时，什么都不装的 Claude Code 7 项全过，{len(tools)} 个工具里有 {len(full)} 个也全过，没有更好的。编出来的东西，最常见的是给一句没人领的随口话安上负责人或截止日期。"],
        "name_col": ["Tool", "工具"],
        "columns": [["One line (7 checks)", "一句话（7 项）"], ["Made up (line)", "编了几处（一句话）"], ["One paragraph (7 checks)", "一段话（7 项）"],
                    ["Made up (paragraph)", "编了几处（一段话）"], ["字 (line / paragraph)", "字数（一句话 / 一段话）"], ["Usage vs no tool", "用量（不装工具 = 1）"]],
        "see": ["See both summaries →", "看两份总结 →"], "evidence": ["Both summaries", "两份总结"],
        "line_label": [f"Meeting summary test, {DATE}:", f"{DATE} 会议总结实测："],
        "control": {"sheet": key(CONTROL) + ".html", "label": ["See the no-tool run →", "看不装工具的对照 →"]},
        "verdict": VERDICT, "runs": {repo: card(repo, runs) for repo, runs in tools}}


if __name__ == "__main__":
    main()
