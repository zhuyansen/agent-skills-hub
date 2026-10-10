"""Evidence pages and page data for the Obsidian test.

  python ops/obsidian-runs/evidence.py      # after score_obsidian.py

Writes frontend/public/best-runs/obsidian/<owner__repo>.html (noindex: the 15 answers with
the judge's marks, and how the tool was used) and the "obsidian-second-brain" entry of
frontend/scripts/scenario-runs.json (type "table"). Every tool that ran, and the control
with plain file tools, answered all 15, so the table is about cost, not accuracy.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from runs_common import PUBLIC, REPO_URL, esc, final_message, key, pair, shell, update_method, write_runs  # noqa: E402

SLUG, DATE, CONTROL = "obsidian-second-brain", "2026-10-10", "octocat/Hello-World"
URL = REPO_URL + "obsidian-runs/"
OUT = HERE / "out"
TRUTH = json.loads((HERE / "truth.json").read_text())
NEEDS_APP = ("Works only through the Local REST API plugin inside the running Obsidian desktop app; a headless sandbox has none.",
             "只能通过正在运行的 Obsidian 桌面应用里的 Local REST API 插件工作；无界面的沙箱里没有。")
NOT_RUN = {
    "MarkusPfundstein/mcp-obsidian": NEEDS_APP, "jacksteamdev/obsidian-mcp-tools": NEEDS_APP, "cyanheads/obsidian-mcp-server": NEEDS_APP,
    "kepano/obsidian-skills": ("Its skills teach an agent to write Obsidian formats (Markdown, Bases, Canvas); the only one that reads a vault drives the Obsidian app.",
                               "它的 skill 教 agent 写 Obsidian 的格式（Markdown、Bases、Canvas）；唯一能读库的那个要驱动 Obsidian 应用。"),
    "breferrari/obsidian-mind": ("Its server only exposes folders listed in a manifest inside the vault, and its search needs qmd; our test vault has neither, and adding them would change the vault.",
                                 "它的服务只开放库内清单文件里列出的文件夹，搜索还要装 qmd；测试库两样都没有，加进去就改动了库。"),
}
NOTES = {
    "AgriciDaniel/claude-obsidian": ("The skill was loaded once; the searching and reading were done with Claude Code's own file tools.", "skill 只加载了一次；搜索和读取用的是 Claude Code 自带的文件工具。"),
    "eugeniughelbur/obsidian-second-brain": ("Answered with Claude Code's own file tools; the skill is for building and maintaining a vault.", "用 Claude Code 自带的文件工具回答；这个 skill 是用来建库和维护库的。"),
    "Ar9av/obsidian-wiki": ("The skill was loaded once; the searching and reading were done with Claude Code's own file tools.", "skill 只加载了一次；搜索和读取用的是 Claude Code 自带的文件工具。"),
    "bitbonsai/mcpvault": ("Reads the vault folder directly, no Obsidian app needed; nearly every step went through its own tools.", "直接读库文件夹，不需要 Obsidian 应用；几乎每一步都走它自己的工具。"),
    "StevenStavrakis/obsidian-mcp": ("Reads the vault folder directly; its search returns long results, which is where the tokens went.", "直接读库文件夹；它的搜索返回的结果很长，token 就花在这里。"),
}
VERDICT = {
    "rule": ["Listed by tokens used. Accuracy does not rank them: every tool that ran, and Claude Code with plain file tools, answered all 15 questions. One run each, on a 560-note vault.",
             "按消耗的 token 排列。准确率分不出高下：跑成的每个工具，以及只用普通文件工具的 Claude Code，15 道题全部答对。每个只跑一次，测试库有 560 条笔记。"],
    "picks": [
        {"repo": "bitbonsai/mcpvault", "role": ["If you want an MCP server for your vault", "想给知识库接一个 MCP 服务"],
         "why": ["It reads the vault folder itself, so it works without the Obsidian app running, and it answered all 15 through its own tools for about twice the tokens of plain file tools. That is the price of using it from a client that has no file access.",
                 "它自己读库文件夹，不用开着 Obsidian 应用；15 道题全部通过它自己的工具答对，token 大约是普通文件工具的两倍。这是在没有文件访问权限的客户端里用它要付的价钱。"]},
        {"repo": "AgriciDaniel/claude-obsidian", "role": ["If you work in Claude Code and want a vault workflow", "在 Claude Code 里想要一套建库流程"],
         "why": ["The cheapest of the tools that ran (about 1.7 times the control). It did not change how questions get answered: Claude Code read the notes with its own tools. Install it for the note-taking workflow, not for recall.",
                 "跑成的工具里最省的（约为对照的 1.7 倍）。它没有改变回答问题的方式：笔记是 Claude Code 用自带工具读的。装它是为了记笔记的流程，不是为了检索。"]},
    ],
    "avoid_label": ["Check before you install:", "安装前先确认："],
    "avoid": [
        {"repo": "MarkusPfundstein/mcp-obsidian", "why": ["the most-starred MCP server here needs Obsidian open with the Local REST API plugin, as do obsidian-mcp-tools and obsidian-mcp-server", "这里星数最高的 MCP 服务，必须开着 Obsidian 并启用 Local REST API 插件；obsidian-mcp-tools 和 obsidian-mcp-server 也一样"]},
        {"repo": "StevenStavrakis/obsidian-mcp", "why": ["all 15 right, at six times the tokens of plain file tools", "15 题全对，但 token 是普通文件工具的六倍"]},
    ],
    "caveat": ["If you already use Claude Code in the vault folder, you may not need any of these to ask your notes a question: with no tool installed it answered all 15, including the three the vault cannot answer, for the fewest tokens.",
               "如果你本来就在库文件夹里用 Claude Code，问笔记问题可能根本不需要这些工具：什么都不装，它 15 题全对（包括库里答不出的 3 题），用的 token 还最少。"],
}


def page(r: dict, name: str) -> str:
    run = OUT / key(r["repo"])
    answers = (run / "deliverables" / "answers.md").read_text()
    rows = "".join(f"<tr><td>{t['n']}. {esc(t['question'])}<br><span class='mute'>{esc(t['ability'])} · expected: {esc(t['answer'])}</span></td>"
                   f"<td>{'<span class=ok>right</span>' if r['marks'][str(t['n'])] else '<span class=no>wrong</span>'}</td></tr>" for t in TRUTH)
    note = f"<p>{esc(NOTES[r['repo']][0])}</p>" if r["repo"] in NOTES else ""
    return shell(f"{name}: Obsidian test", ("/best/obsidian-second-brain/", "Obsidian AI tools"), f"""<h1>{esc(name)}: test run, {DATE}</h1>
<p class="mute">15 questions about a 560-note test vault, three for each of LongMemEval's five abilities. Claude Code (Claude Opus 5.5) installed the tool in a throwaway sandbox and answered through it;
a judge (gpt-6-astra, three passes) marked the answers. <a href="{URL}RESULTS.md">All results</a> · <a href="{URL}make_vault.py">The vault and questions</a> · <a href="{URL}in/prompt.txt">Task</a></p>
<p><b>{r['correct']} of 15 right.</b> {r['tool_calls']} calls through the tool, {r['file_calls']} through plain file tools; {r['tokens']:,} tokens; {r['minutes']} min.</p>{note}
<h2>Question by question</h2><table><tr><th>Question</th><th>Mark</th></tr>{rows}</table>
<h2>The answers as written</h2><pre>{esc(answers[:6000])}</pre>
<h2>How it was run (the session's closing message)</h2><pre>{esc(final_message(run / 'transcript.jsonl')[:4000])}</pre>""")


def card(r: dict, base: int) -> dict:
    if not r["ran"]:
        why = NOT_RUN.get(r["repo"], ("did not run", "未能运行"))
        return {"ran": False, "stars": r["stars"], "sheet": "", "reason": why[0], "reason_zh": why[1]}
    times = round(r["tokens"] / base, 1)
    cells = [[f"{r['correct']}/15", None, "touch-ups" if r["correct"] == 15 else ""], [str(r["tool_calls"]), None, "num"], [str(r["file_calls"]), None, "num"],
             [f"{r['tokens']:,} ({times}×)", None, "substantial" if times >= 4 else "num"], [f"{r['minutes']} min", f"{r['minutes']} 分钟", "num"]]
    bits = [[f"answered {r['correct']} of 15 questions about a test vault", f"测试库的 15 道题答对 {r['correct']} 道"],
            [f"{times}× the tokens of plain file tools", f"token 是普通文件工具的 {times} 倍"],
            [f"{r['tool_calls']} calls through the tool, {r['file_calls']} through plain file tools", f"{r['tool_calls']} 次调用走工具，{r['file_calls']} 次走普通文件工具"]]
    out = {"ran": True, "stars": r["stars"], "sheet": key(r["repo"]) + ".html", "cells": cells, "bits": bits}
    if r["repo"] in NOTES:
        out.update(note=NOTES[r["repo"]][0], note_zh=NOTES[r["repo"]][1])
    return out


def main() -> None:
    out = PUBLIC / "obsidian"; out.mkdir(parents=True, exist_ok=True)
    rows = json.loads((HERE / "results.json").read_text())
    control = next(r for r in rows if r["repo"] == CONTROL)
    tools = sorted((r for r in rows if r["repo"] != CONTROL), key=lambda r: (not r["ran"], r.get("tokens", 0)))
    ran = [r for r in tools if r["ran"]]
    for r in [control, *ran]:
        (out / (key(r["repo"]) + ".html")).write_text(page(r, "Control: Claude Code with plain file tools" if r is control else r["repo"]))
    lo, hi = (round(f(r["tokens"] for r in ran) / control["tokens"], 1) for f in (min, max))
    need_app = sum(NOT_RUN.get(r["repo"]) is NEEDS_APP for r in tools)
    write_runs(SLUG, {
        "type": "table", "date": DATE, "dir": "/best-runs/obsidian/", "results": URL + "RESULTS.md",
        "title": ["Obsidian AI tools tested: 15 questions about the same vault", "实测对比：同一个库的 15 道题"],
        "intro": [f"On {DATE} we ran {len(tools)} of these tools and {len(ran)} ran. Each was installed in a throwaway sandbox and asked the same 15 questions about a 560-note test vault (daily notes, projects, meetings, people, with near misses planted). The questions follow LongMemEval's five abilities, three each: find one fact, reason across notes, reason about dates, keep up with a fact that a later note changed, and say so when the vault does not hold the answer. A judge (gpt-6-astra, three passes) marked the answers. Claude Code with plain file tools did the same as a control.",
                  f"{DATE} 我们实跑了其中 {len(tools)} 个，跑成 {len(ran)} 个。每个装在用完即删的沙箱里，回答关于同一个 560 条笔记测试库（日记、项目、会议、人物，并埋了相似的干扰项）的 15 道题。题目按 LongMemEval 的五种能力出，每种三道：找一个事实、跨笔记推理、按日期推理、跟上被后来笔记改掉的事实、库里没有答案时如实说没有。评审是 gpt-6-astra，三遍取多数。只用普通文件工具的 Claude Code 做同样的事，作为对照。"],
        "finding": [f"Every one that ran answered all 15, and so did the control: on a vault this size, search and read are enough. What differs is cost. The control used {control['tokens']:,} tokens; the tools used {lo} to {hi} times that. The three skills that ran did their searching with Claude Code's own file tools, not through the skill. And {need_app} of the {len(tools)} could not run without the Obsidian desktop app open.",
                    f"跑成的每一个都 15 题全对，对照组也是：这个规模的库，搜索加读取就够了。差别在成本。对照组用了 {control['tokens']:,} 个 token，工具是它的 {lo} 到 {hi} 倍。跑成的三个 skill，搜索用的都是 Claude Code 自带的文件工具，不是 skill。{len(tools)} 个里有 {need_app} 个不开着 Obsidian 桌面应用就跑不了。"],
        "name_col": ["Tool", "工具"],
        "columns": [["Right (of 15)", "答对（共 15）"], ["Calls through the tool", "走工具的调用"], ["Plain file calls", "普通文件调用"], ["Tokens (× control)", "Token（对照的倍数）"], ["Time", "耗时"]],
        "see": ["See the answers →", "看 15 道题的回答 →"], "evidence": ["The answers", "回答"],
        "line_label": [f"Obsidian AI test, {DATE}:", f"{DATE} 实测："], "control": {"sheet": key(CONTROL) + ".html"},
        "not_run_label": ["Could not run in a sandbox", "沙箱里跑不了"], "not_run_line": ["Could not run in our sandbox:", "沙箱里跑不了："],
        "verdict": VERDICT, "runs": {r["repo"]: card(r, control["tokens"]) for r in tools}})
    update_method(SLUG, [
        pair(f"On a 560-note vault no tool answered better than plain file tools. All {len(ran)} tools that ran got 15 of 15, and so did Claude Code with nothing installed, including the three questions the vault cannot answer. This matches Letta's result that an agent with a filesystem does well on memory benchmarks.",
             f"在 560 条笔记的库上，没有工具比普通文件工具答得更好。跑成的 {len(ran)} 个工具都是 15 题全对，什么都不装的 Claude Code 也一样，包括库里答不出的 3 题。这和 Letta 的结论一致：有文件系统可用的 agent 在记忆基准上表现就很好。"),
        pair(f"The tools cost {lo} to {hi} times the tokens of the control for the same answers; the most expensive returned long search results.",
             f"同样的答案，工具消耗的 token 是对照组的 {lo} 到 {hi} 倍；最贵的那个返回的搜索结果很长。"),
        pair(f"{need_app} of {len(tools)} tools, the most-starred MCP server among them, only work through the Local REST API plugin of a running Obsidian app.",
             f"{len(tools)} 个工具里有 {need_app} 个（包括星数最高的 MCP 服务）只能通过正在运行的 Obsidian 应用里的 Local REST API 插件工作。")],
        pair(f"Ran {len(tools)} of the tools on the same 15 questions about a 560-note test vault, with Claude Code and plain file tools as the control, and marked every answer (gpt-6-astra, three passes). Results are in the test section above and on each card.",
             f"让其中 {len(tools)} 个工具回答同一个 560 条笔记测试库的 15 道题，用只带普通文件工具的 Claude Code 做对照，逐题评分（gpt-6-astra，三遍）。结果在上面的实测区和每张卡片上。"),
        pair("The vault is small and tidy, so the test cannot show what these tools do at tens of thousands of notes, where search quality starts to matter; every tool tied on accuracy. The questions are in English and ask for recall, not for writing or organising notes, which is what most of the skills are for. One run per tool; tools that need the Obsidian desktop app were not run.",
             "测试库又小又整齐，测不出这些工具在几万条笔记时的表现（那时搜索质量才开始重要）；准确率上所有工具打平。题目是英文的，考的是检索，不是写笔记和整理笔记，而多数 skill 是为后者做的。每个工具只跑一次；需要 Obsidian 桌面应用的没有跑。"),
        "no tool answered better than plain file tools")
    print(f"{len(ran)} ran of {len(tools)}; tokens {lo}x to {hi}x; need app {need_app}")


if __name__ == "__main__":
    main()
