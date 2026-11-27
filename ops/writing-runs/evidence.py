"""Evidence pages and page data for the quarterly-report test.

  python3 ops/writing-runs/evidence.py      # after score.py (results.json) and render.py (out/evidence/*.png)

Writes frontend/public/best-runs/writing/: <owner__repo>.html (noindex: both requests word for word, the 8
verdicts with what decided them, every statement the tester found the list does not support, the evidence
picture with the script's marks, the report as delivered, where the build stopped to ask, the install), the
pictures as WebP, and the "content-writing" entry of frontend/scripts/scenario-runs.json (type "table").
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "in"))
from runs_common import PUBLIC, REPO_URL, esc, key, shell, webp_copy, write_runs  # noqa: E402
import kit  # noqa: E402

SLUG, DATE, CONTROL = "content-writing", "2026-11-08", "octocat/Hello-World"
URL = REPO_URL + "writing-runs/"
OUT = HERE / "out"
DEST = PUBLIC / "writing"
PICTURE_WIDTH = 1000
TASKS = {"t1": ("One line", "一句话"), "t2": ("One paragraph", "一段话")}
CHECKS = {
    "length": "1,200 to 1,800 字", "structure": "Three parts in order: done, not done well, plans for Q4",
    "coverage": "All 4 projects and 4 plans, each with its key fact", "problems": "All 4 problems with a figure or cause, none turned into a success",
    "numbers": "Every figure from the list, none worked out, no old figure as current", "facts": "Nothing the list does not support (the tester)",
    "tone": "At most 2 stock phrases per 1,000 字", "parallel": "At most 1 排比",
}
REPLY = (HERE / "in" / "reply.txt").read_text().strip()
# Short card notes, written by hand from results.json ("install", "skill_md", "why").
NOTES = {
    "anthropics/skills": ("Only its internal-comms skill, Anthropic's skill for status reports and updates to leadership.",
                          "只装了 internal-comms 这一个 skill，是 Anthropic 官方写状态汇报、领导汇报的 skill。"),
    "op7418/Humanizer-zh": ("A Chinese anti-AI-tone skill: the report is written first, then revised by its patterns. Our tone lists drew on the same patterns.",
                            "中文去 AI 味 skill：先写稿再按它的模式改。这次 AI 味检查的词表参考了同一份模式。"),
    "larashero3-dotcom/lieflat-less-ai-tone": ("An anti-AI-tone skill that runs a detection script first and waits for 「按建议改」 before rewriting; it stopped once on each request.",
                                               "去 AI 味 skill：先跑脚本出检测报告，等用户回复「按建议改」再改写；两种问法下各停下来一次。"),
    "MrGeDiao/shuorenhua": ("A Chinese plain-language rewriting plugin that sets out to keep facts, conditions and commitments.",
                            "中文「说人话」改写插件，主打保事实、保条件、保承诺。"),
    "duyunzhoudyz/dyz-gongwen-skills": ("Its gongwen plugin (17 skills); reports go through gongwen-report, and it delivered a Word file both times.",
                                        "装的是它的 gongwen 插件（17 个 skill），总结汇报走 gongwen-report；两次交的都是 Word 文件。"),
    "Liuxiangjian-ai/official-document-skill": ("One SKILL.md for official-document writing, with a second review pass in the style of a humanizer.",
                                                "一个 SKILL.md 的公文写作 skill，带 humanizer 式的二次审稿。"),
}
# One skill tested inside a bigger repository: its sub-skill page shows the result, the repository's own page does not.
SUBS = {"anthropics/skills": "internal-comms", "duyunzhoudyz/dyz-gongwen-skills": "gongwen-report"}
VERDICT = {
    "title": ["Which one to install", "到底装哪个"],
    "rule": ["Ranked by checks passed on both requests, then statements the list does not support, then build time. One run per tool and request, on one made-up fact list; the same 8 checks for both requests, the 1,200-字 floor included, which only the paragraph asks for (about 1,500).",
             "排名规则：先看两种问法一共过了几项，再看有几处清单不支持，最后看做了多久。每个工具每种问法只跑一次，用的是一份虚构的事实清单；两种问法用同一套 8 项检查，1,200 字的下限也算在内，虽然只有那段话提了字数（1500 字左右）。"],
    "picks": [
        {"repo": "op7418/Humanizer-zh", "role": ["If you want one installed", "真要装一个"],
         "why": ["7 of 8 on both requests, with no figure worked out and nothing the list does not support; it failed only the length, at 938 and 978 字. On the one-line request that beat Claude Code alone (5 of 8); on the paragraph it was one check behind (8 of 8).",
                 "两种问法都是 8 项过 7 项，没有自己算的数字，也没有清单不支持的内容；只有字数没过，938 字和 978 字。一句话的问法下比只用 Claude Code（过 5 项）好；按那段话问，比它（8 项全过）少一项。"]},
        {"repo": "MrGeDiao/shuorenhua", "role": ["If you would rather install a Claude Code plugin", "想用 Claude Code 插件的方式装"],
         "why": ["The same 7 of 8 on both requests with nothing worked out or made up, at 2.1 and 2.3 times the usage of no tool; 920 and 1,155 字, both under the 1,200 the check asks for.",
                 "两种问法同样 8 项过 7 项，没有自己算的数，也没编，用量是不装工具的 2.1 倍和 2.3 倍；920 字和 1,155 字，都没到检查要求的 1,200 字。"]},
        {"repo": "larashero3-dotcom/lieflat-less-ai-tone", "role": ["If you want a report on the AI tone before the rewrite", "想先看一份 AI 味检测报告再改"],
         "why": ["7 of 8 on both with nothing worked out or made up. It stops once to show its detection report and waits, and used 3.9 and 5.7 times the usage of no tool; its one-line report was the shortest, 781 字.",
                 "两种问法都是 8 项过 7 项，没有自己算的数，也没编。它会停下来一次给你看检测报告、等你回复，用量是不装工具的 3.9 倍和 5.7 倍；一句话问法下写得最短，781 字。"]},
    ],
    "avoid_label": ["Check these against your facts:", "这几个要对照事实核一遍："],
    "avoid": [
        {"repo": "duyunzhoudyz/dyz-gongwen-skills", "why": ["8 figures it worked out itself on the one-line request, at 11.8 times the usage of no tool", "一句话问法下有 8 个自己算出来的数字，用量是不装工具的 11.8 倍"]},
        {"repo": "anthropics/skills", "why": ["its internal-comms skill added 3 statements the list does not support on the paragraph request", "它的 internal-comms skill 按那段话写时，加了 3 处清单不支持的内容"]},
        {"repo": "Liuxiangjian-ai/official-document-skill", "why": ["2 figures worked out on the one-line request and 1 cause the list does not give on the paragraph", "一句话问法下有 2 个自己算的数字，按那段话写时加了 1 个清单没给的原因"]},
    ],
    "caveat": ["Whichever you pick: with the one-paragraph request (it is on every evidence page), Claude Code with nothing installed passed all 8 checks in 1.2 minutes of writing and $0.19 of usage at API prices; every tool passed 7. A tool earned its place on the one-line request, where the anti-AI-tone skills kept to the list and Claude Code alone worked out figures of its own.",
               "不管选哪个：用那段话去问（每个证据页上都有原文），什么都不装的 Claude Code 8 项全过，写了 1.2 分钟，按 API 价用量 $0.19；每个工具都只过 7 项。工具真正有用的是一句话的问法：去 AI 味的 skill 守住了清单，只用 Claude Code 则自己算出了数字。"],
}


def load() -> dict:
    """results.json as {repo: {task: row}}."""
    by = {}
    for r in json.loads((HERE / "results.json").read_text()):
        by.setdefault(r["repo"], {})[r["task"]] = r
    return by


def document(task: str, repo: str) -> tuple[str, str]:
    """The report the tester read: its file name and text."""
    run = OUT / task / key(repo)
    report = json.loads((run / "test" / "report.json").read_text())
    named = report.get("file") or ""
    doc = run / "deliverables" / named[len("output/"):] if named.startswith("output/") else None
    doc = doc if doc and doc.is_file() else kit.deliverable(run / "deliverables")
    return doc.name, kit.read(doc)


def stops(repo: str, task: str) -> list[str]:
    """What the build said each time it stopped short of a finished report (the turns that got the stock reply)."""
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
        seen = r["observed"].get(c) if c != "facts" else (f"{len(r['invented'])} statement(s) the list does not support, listed below" if r["invented"] else "None found")
        rows.append(f"<tr><th>{esc(label)}</th><td>{'<span class=ok>pass</span>' if ok else '<span class=no>fail</span>'}</td><td>{esc(seen)}</td></tr>")
    made_up = "".join(f"<li><pre>{esc(i['quote'])}</pre>{esc(i['why'])}</li>" for i in r["invented"]) or "<li>Nothing.</li>"
    doubts = "".join(f"<li><b>{esc(CHECKS[c])}:</b> {esc(d)}</li>" for c, d in r.get("doubts", {}).items())
    asked = "".join(f"<li><pre>{esc(s[-1500:])}</pre></li>" for s in stops(repo, task)) or "<li>It did not stop to ask.</li>"
    pic = picture(repo, task)
    shot = (f"<h3>The report with the script's marks</h3><p class=mute>The picture shown in our video. Red: a figure the list does not give "
            f"(the tooltip in the original says how it may have been worked out), an old figure given as current, a problem turned into a success. "
            f"Yellow: stock phrases, vague verbs and empty elevation. Orange underline: 排比.</p>"
            f"<a href='{pic}'><img src='{pic}' alt='{esc(repo)} {task} report' width='{PICTURE_WIDTH}' loading='lazy'></a>") if pic else ""
    name, text = document(task, repo)
    f = r["found"]
    return f"""<h2>{esc(TASKS[task][0])}</h2><p class="mute">The request, word for word: 「{esc(brief)}」</p>
<p><b>{r['passed']} of {r['of']} checks passed.</b> {r['zi']:,} 字, in {esc(name)}. Figures not on the list: {f['extra_numbers']}, of them worked out: {f['worked_out']}.
Built in {r['minutes']} minutes ({r['run_minutes']} for the whole run, install and check included); it stopped to ask {r['stops']} time(s);
how it ended: {esc(r['ending'])}. Usage at API prices: ${r['usage']['usd']} ({r.get('usage_x', '-')} times the run with no tool on this request).</p>
<table><tr><th>Check</th><th>Verdict</th><th>What decided it</th></tr>{''.join(rows)}</table>
<h3>What the tester found the list does not support</h3><ol>{made_up}</ol>
{f'<h3>Where the tester doubted how the script read it</h3><p class=mute>Some of these led to the script fixes listed in RESULTS.md; every verdict on this page comes from the fixed script.</p><ul>{doubts}</ul>' if doubts else ''}
<h3>The tester's notes</h3><p>{esc(r['tester_notes'])}</p>
{shot}
<details><summary>The report as delivered ({esc(name)})</summary><pre>{esc(text)}</pre></details>
<h3>Where it stopped, and got the reply 「{esc(REPLY)}」</h3><ol>{asked}</ol>"""


def page(repo: str, runs: dict) -> str:
    name = "Control: Claude Code with nothing installed" if repo == CONTROL else repo
    first = runs["t1"]
    setup = "" if repo == CONTROL else (f"<p><b>Install:</b> {esc(first['setup'].removeprefix('SETUP: done').strip())} (repo commit {esc(first['commit'])})</p>"
                                        f"<p class=mute>Why it was in the test (our note before the run): {esc(first['why'])}</p>")
    body = "".join(task_html(repo, t, runs[t]) for t in TASKS if t in runs)
    return shell(f"{name}: quarterly report test", ("/best/content-writing/", "Content writing tools"), f"""<h1>{esc(name)}: quarterly report test</h1>
<p class="mute">Test of {DATE}. Installed from its README in a throwaway sandbox, then used by Claude Code (Claude Opus 5.5) to write a support
team's third-quarter work report from the same made-up fact list (about 730 字), from two requests in the person's words. Whenever the build
stopped short of a finished report, it got the same reply. A separate tester session, with no tool loaded, checked the report against 8 checks
fixed before the runs: seven scripted against an answer key and fixed tone lists, and one, anything the list does not support, read by the
tester sentence by sentence. Everything in the list is made up.
<a href="{URL}RESULTS.md">All results</a> · <a href="{URL}in/fixtures/季度事实清单.md">The fact list</a> · <a href="{URL}in/test.md">The checklist</a> · <a href="{URL}in/truth.json">The answer key</a></p>
{setup}{body}""")


def cls(r: dict) -> str:
    return "touch-ups" if r["passed"] == r["of"] else "substantial" if r["passed"] <= r["of"] // 2 else ""


def made_up(n: int) -> list[str]:
    return [f"{n} statement{'s' if n != 1 else ''} the list does not support", f"{n} 处清单不支持"] if n else ["nothing the list does not support", "没有清单不支持的内容"]


def card(repo: str, runs: dict) -> dict:
    t1, t2 = runs["t1"], runs["t2"]
    n1, n2 = len(t1["invented"]), len(t2["invented"])
    x1, w1 = t1["found"]["extra_numbers"], t1["found"]["worked_out"]
    cells = [[f"{t1['passed']}/{t1['of']}", None, cls(t1)], [f"{x1} ({w1})", None, "num"], [str(n1), None, "num"],
             [f"{t2['passed']}/{t2['of']}", None, cls(t2)], [str(n2), None, "num"],
             [f"{t1['zi']:,} / {t2['zi']:,}", None, "num"], [f"×{t1['usage_x']} / ×{t2['usage_x']}", None, "num"]]
    m1, m2 = made_up(n1), made_up(n2)
    figs = [f"{x1} figures not on the list ({w1} worked out)", f"{x1} 个清单没有的数字（{w1} 个自己算的）"] if x1 else ["no figure off the list", "没有清单以外的数字"]
    bits = [[f"one-line request: {t1['passed']} of {t1['of']} checks, {figs[0]}, {m1[0]}", f"一句话：{t1['of']} 项过 {t1['passed']} 项，{figs[1]}，{m1[1]}"],
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
    """Best first: checks passed on both requests, statements the list does not support, build time, stars (VERDICT["rule"])."""
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
    print("\n".join(f"{repo}: {runs['t1']['passed']}/8 ({len(runs['t1']['invented'])}) {runs['t2']['passed']}/8 ({len(runs['t2']['invented'])})" for repo, runs in tools))
    write_runs(SLUG, entry(tools, ctrl))


def entry(tools: list, ctrl: dict) -> dict:
    c1, c2 = ctrl["t1"], ctrl["t2"]
    assert c2["passed"] == c2["of"] and all(v["t2"]["passed"] == v["t2"]["of"] - 1 for _, v in tools), "the finding's claim about t2"
    short = [r for r, v in tools if not v["t2"]["checks"]["length"]]
    facts2 = [(r, len(v["t2"]["invented"])) for r, v in tools if v["t2"]["invented"]]
    deslop = [(r, v) for r, v in tools if v["t1"]["kind"] == "deslop"]
    assert all(v["t1"]["passed"] == 7 and not v["t1"]["found"]["extra_numbers"] and not v["t1"]["invented"] for _, v in deslop)
    over = [r for r in [c1] + [v["t1"] for _, v in tools] if not r["checks"]["length"]]
    assert len(over) == len(tools) + 1, "every one-line report fell outside 1,200-1,800 字"
    brief1 = (HERE / "in" / "brief-t1.txt").read_text().strip()
    f1 = c1["found"]
    short_name = lambda r: r if r.split("/")[1] == "skills" else r.split("/")[1]   # noqa: E731  "skills" alone says nothing
    names = lambda rs: ", ".join(short_name(r) for r in rs)   # noqa: E731
    facts_en = " and ".join(f"{short_name(r)} {n}" for r, n in facts2)
    facts_zh = "、".join(f"{short_name(r)} 加了 {n} 处" for r, n in facts2)
    return {
        "type": "table", "date": DATE, "dir": "/best-runs/writing/", "results": URL + "RESULTS.md",
        "title": ["Writing skills tested: one made-up fact list, a quarterly report, two ways of asking", "实测对比：同一份虚构事实清单写季度总结，两种问法"],
        "intro": [f"On {DATE} we gave {len(tools)} writing and anti-AI-tone skills the same job: write a support team's third-quarter work report from a made-up fact list of about 730 字, with 4 projects and their figures, 4 problems, the spending, 4 plans for the fourth quarter and 5 old figures that must not be given as current. Each was installed from its README in a throwaway sandbox and used by Claude Code (Claude Opus 5.5) from two requests in the person's words: one line, 「{brief1}」 (\"Write me a quarterly work report\"), and one paragraph asking for about 1,500 字 in three parts, only the list's facts and figures, nothing worked out, plain words with no stock phrases or 排比, and the problems told straight. A tester session with no tool loaded checked every report against the same 8 checks, fixed before the runs: seven scripted against an answer key and fixed tone lists, and one, anything the list does not support, read sentence by sentence. Claude Code with nothing installed did the same as a control.",
                  f"{DATE}，我们让 {len(tools)} 个写作和去 AI 味 skill 做同一件事：照一份约 730 字的虚构事实清单，写一个客服团队的第三季度工作总结。清单里有 4 个项目和数字、4 个没做好的地方、花费、4 项第四季度计划，还有 5 个不能当成现在的旧数字。每个工具在用完即删的沙箱里照 README 安装，由 Claude Code（Claude Opus 5.5）按两种说法使用：一句话，「{brief1}」；一段话，要求 1500 字左右、分三块、只用清单里的事实和数字、别自己算、说大白话、别用套话和排比、问题要写实。另起一个不装工具的测试会话，用开跑前定好的同一套 8 项检查核对每份总结：7 项由脚本对照答案和固定词表判定，1 项（有没有清单不支持的内容）逐句阅读。不装任何工具的 Claude Code 做同样的事，作为对照。"],
        "finding": [f"On the one-paragraph request no tool beat Claude Code with nothing installed: it passed all 8 checks in {c2['minutes']} minutes of writing ({c2['run_minutes']} for the whole run, the check included) and ${c2['usage']['usd']} of usage at API prices, and all {len(tools)} tools passed 7 of 8: {len(short)} came in under 1,200 字, and {facts_en} added statements the list does not support. On the one-line request the control passed {c1['passed']} of 8: it put in {f1['extra_numbers']} figures that are not on the list, {f1['worked_out']} of them worked out itself, and {len(c1['invented'])} statements the list does not support; the {len(deslop)} anti-AI-tone skills ({names(r for r, _ in deslop)}) passed 7 of 8 with neither. Every one-line report came in under 1,200 字.",
                    f"按那段话问，没有工具比什么都不装的 Claude Code 更好：它 8 项全过，写了 {c2['minutes']} 分钟（连检查在内整个运行 {c2['run_minutes']} 分钟），按 API 价用量 ${c2['usage']['usd']}；{len(tools)} 个工具都是 8 项过 7 项：{len(short)} 个不到 1,200 字，{facts_zh}清单不支持的内容。只说一句话时，对照组 8 项过 {c1['passed']} 项：写进了 {f1['extra_numbers']} 个清单里没有的数字，其中 {f1['worked_out']} 个是自己算的，还有 {len(c1['invented'])} 处清单不支持；{len(deslop)} 个去 AI 味 skill（{'、'.join(r.split('/')[1] for r, _ in deslop)}）8 项过 7 项，这两样都没有。一句话问法下的每一份都不到 1,200 字。"],
        "name_col": ["Tool", "工具"],
        "columns": [["One line (8 checks)", "一句话（8 项）"], ["Off-list figures (line, worked out)", "清单外数字（一句话，其中自己算的）"],
                    ["Unsupported (line)", "清单不支持（一句话）"], ["One paragraph (8 checks)", "一段话（8 项）"], ["Unsupported (paragraph)", "清单不支持（一段话）"],
                    ["字 (line / paragraph)", "字数（一句话 / 一段话）"], ["Usage vs no tool", "用量（不装工具 = 1）"]],
        "see": ["See both reports →", "看两份总结 →"], "evidence": ["Both reports", "两份总结"],
        "line_label": [f"Quarterly report test, {DATE}:", f"{DATE} 季度总结实测："],
        "control": {"sheet": key(CONTROL) + ".html", "label": ["See the no-tool run →", "看不装工具的对照 →"]},
        "verdict": VERDICT, "runs": {repo: card(repo, runs) for repo, runs in tools}}


if __name__ == "__main__":
    main()
