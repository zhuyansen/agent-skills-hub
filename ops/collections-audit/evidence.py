"""Evidence pages and page data for the collection audit.

  python ops/collections-audit/evidence.py      # after audit.py

Writes frontend/public/best-runs/collections/<owner__repo>.html (noindex) and the
"claude-code-skills" entry of frontend/scripts/scenario-runs.json (type "table").
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from runs_common import PUBLIC, REPO_URL, esc, key, shell, write_runs  # noqa: E402

SLUG, DATE = "claude-code-skills", "2026-10-11"
URL = REPO_URL + "collections-audit/"
# Claude Code's skill list grew by about 7,500 tokens and then stopped (17,781 -> 25,289 at 512 skills). A collection
# whose names and descriptions fit in that keeps them all; one a little over loses some; one far over is mostly names.
BUDGET_TOKENS, FAR_OVER = 7000, 15000
FIT = {"all": (["All keep a description", "都能保留描述", "touch-ups"], ["installed whole, every skill keeps its description", "整包装上，每个 skill 都能保留描述"]),
       "some": (["Some lose their description", "部分会丢描述", ""], ["installed whole, some skills lose their description", "整包装上，部分 skill 会丢掉描述"]),
       "few": (["Most listed by name only", "大多只剩名字", "substantial"], ["installed whole, most skills are listed by name only", "整包装上，大多数 skill 只剩名字"])}


def fit(tokens: int) -> str:
    return "all" if tokens <= BUDGET_TOKENS else "some" if tokens <= FAR_OVER else "few"
NOT_COLLECTION = {
    "hesreallyhim/awesome-claude-code": ("A list of links to Claude Code resources kept elsewhere: there is no skill in it to install.", "一份指向别处 Claude Code 资源的链接清单：里面没有可安装的 skill。"),
    "travisvn/awesome-claude-skills": ("A list of links to skills kept elsewhere: there is no skill in it to install.", "一份指向别处 skill 的链接清单：里面没有可安装的 skill。"),
    "VoltAgent/awesome-claude-code-subagents": ("A collection of subagent files, not skills: it has no SKILL.md to count.", "这是子 agent 文件的合集，不是 skill：里面没有 SKILL.md 可数。"),
}
NOTES = {
    "sickn33/agentic-awesome-skills": ("The largest here: 8,323 skill files, of which 2,675 are distinct; the rest are the same skills packaged again for other agents.", "这里最大的一个：8,323 个 skill 文件，其中 2,675 个不重复；其余是同一批 skill 为别的 agent 重新打包的副本。"),
    "mukul975/Anthropic-Cybersecurity-Skills": ("Every one of its 818 skills ships a scripts folder. Read a skill's scripts before you let an agent run it.", "818 个 skill 每一个都带脚本文件夹。让 agent 运行之前，先读一遍它的脚本。"),
    "ComposioHQ/awesome-claude-skills": ("Named an awesome list, but it holds 864 skills of its own; 92 of them miss the format.", "名字是 awesome 清单，但仓库里自己就有 864 个 skill；其中 92 个不符合格式。"),
    "SnailSploit/Claude-Red": ("Only 33 of its 79 skills meet the format, and 41 run past 500 lines.", "79 个 skill 里只有 33 个符合格式，41 个超过 500 行。"),
    "alirezarezvani/claude-skills": ("Nearly half the skill files are copies of the same skill packaged for other agents or plugins.", "将近一半的 skill 文件是同一个 skill 为别的 agent 或插件打包的副本。"),
    "davila7/claude-code-templates": ("140 of its skills are longer than the 500 lines the format's guidance recommends.", "有 140 个 skill 超过格式指南建议的 500 行。"),
    "sergebulaev/linkedin-skills": ("Each skill is in the repository twice.", "每个 skill 在仓库里都有两份。"),
    "Imbad0202/academic-research-skills": ("Five skills, each over 500 lines, with 47 subagents behind them: a workflow more than a collection.", "5 个 skill，每个都超过 500 行，背后有 47 个子 agent：与其说是合集，不如说是一套工作流。"),
}
VERDICT = {
    "title": ["Which one to install", "到底装哪个"],
    "basis": ["after counting what is inside each", "数完每个合集里有什么之后"], "more": ["See the audit →", "看合集体检 →"],
    "lead": ["We counted every skill file in {n} of these collections. This is what we would pick; the [full audit](#{anchor}) is below.",
             "我们数了其中 {n} 个合集里的每一个 skill 文件,结论如下,[完整体检](#{anchor})在下面。"],
    "rule": ["Listed by GitHub stars, as on the page: this is a count of what each collection holds, not a ranking of how good its skills are. Counted from the files at the commit on each evidence page; no skill was run.",
             "按 GitHub 星数排列，和页面一致：这是在数每个合集里有什么，不是给 skill 的好坏排名。数字来自各证据页所标 commit 的文件；没有运行任何 skill。"],
    "picks": [
        {"repo": "anthropics/skills", "role": ["To start", "刚开始用"],
         "why": ["Anthropic's own set and the reference for the format: 20 skills, small enough that every one keeps its description when installed together. Its sibling, claude-plugins-official, is the vendor's plugin directory.",
                 "Anthropic 自己的一套，也是格式的参照：20 个 skill，一起装上每个都能保留描述。它的姊妹仓库 claude-plugins-official 是官方的插件目录。"]},
        {"repo": "mattpocock/skills", "role": ["For everyday engineering", "日常写代码"],
         "why": ["The most-starred collection here and one of the leanest: 38 skills, all 38 meet the format, about 1,500 tokens of names and descriptions in total.",
                 "这里星数最高的合集，也是最精简的之一：38 个 skill，38 个全部合规，名字加描述一共约 1,500 个 token。"]},
        {"repo": "coreyhaines31/marketingskills", "role": ["For one field, done cleanly", "只做一个领域，做得干净"],
         "why": ["50 marketing skills, all valid, none over 500 lines, none shipping scripts; its descriptions are long, so installed whole a few may lose theirs. For security work the same shape is trailofbits/skills (85 of 85 valid).",
                 "50 个营销 skill，全部合规，没有超过 500 行的，也都不带脚本；它的描述偏长，整包装上可能有几个会丢描述。做安全的话，同样干净的是 trailofbits/skills（85 个全部合规）。"]},
    ],
    "avoid_label": ["Pick from these by name; do not install them whole:", "从里面按名字挑着装，别整包安装："],
    "avoid": [
        {"repo": "sickn33/agentic-awesome-skills", "why": ["2,675 distinct skills; Claude Code would show a description for a few dozen and Codex would hide most of the rest", "2,675 个不重复的 skill；Claude Code 只会给几十个显示描述，Codex 会把其余大部分隐藏"]},
        {"repo": "davila7/claude-code-templates", "why": ["886 skills, 140 of them over 500 lines", "886 个 skill，其中 140 个超过 500 行"]},
        {"repo": "mukul975/Anthropic-Cybersecurity-Skills", "why": ["818 skills, every one with scripts to read first", "818 个 skill，每个都带需要先读的脚本"]},
    ],
    "caveat": ["Whichever you pick: size is the thing to watch. Of the {audited} collections we counted, {over} are so big that Claude Code would list most of their skills by name only, and Codex with 512 skills installed opened the right one 17 times of 36.",
               "不管选哪个：要盯的是体量。我们数过的 {audited} 个合集里，有 {over} 个大到 Claude Code 只能把大多数 skill 按名字列出；Codex 装到 512 个 skill 时，36 次里只有 17 次打开了正确的那个。"],
}


def page(r: dict) -> str:
    rows = [("Skill files (SKILL.md)", r["skills"]), ("Distinct skills by name", r["unique"]), ("Meet the Agent Skills format", f"{r['valid']} of {r['skills']}"),
            ("Format problems", ", ".join(f"{k}: {v}" for k, v in r["problems"].items()) or "none"), ("Longer than 500 lines", r["long_bodies"]),
            ("With a scripts folder", r["with_scripts"]), ("Median description length", f"{r['median_desc_chars']} characters"),
            ("Length of all names and descriptions, in tokens (estimate)", f"about {r['standing_tokens']:,}"), ("Command files", r["commands"]), ("Agent files", r["agents"])]
    body = "".join(f"<tr><th>{esc(a)}</th><td>{esc(b)}</td></tr>" for a, b in rows)
    note = f"<p>{esc(NOTES[r['repo']][0])}</p>" if r["repo"] in NOTES else ""
    return shell(f"{r['repo']}: collection audit", ("/best/claude-code-skills/", "Claude Code skills"), f"""<h1>{esc(r['repo'])}: what is inside, {DATE}</h1>
<p class="mute">Counted from the repository's files at commit {esc(r['commit'])}; nothing was run. A skill meets the format when its name is at most 64 lowercase letters, digits and hyphens and its
description is 1 to 1,024 characters. The token figure is the combined length of distinct names and descriptions at four characters per token. Claude Code does not load all of it: past a budget it lists skills by name only (we measured 25,289 tokens at session start with 512 skills installed, against 17,781 with 12).
<a href="{URL}RESULTS.md">All collections</a> · <a href="{URL}audit.py">How it is counted</a></p>{note}
<table>{body}</table>""")


def card(r: dict) -> dict:
    base = {"stars": r["stars"], "sheet": key(r["repo"]) + ".html"}
    if not r["skills"]:
        why = NOT_COLLECTION[r["repo"]]
        return {**base, "ran": False, "reason": why[0], "reason_zh": why[1]}
    valid = round(100 * r["valid"] / r["skills"])
    column, line = FIT[fit(r["standing_tokens"])]
    cells = [[f"{r['unique']:,}", None, "num"], [f"{valid}%", None, "touch-ups" if valid == 100 else "substantial" if valid < 80 else ""],
             [str(r["with_scripts"]), None, "num"], [f"{r['standing_tokens']:,}", None, "num"],
             column]
    bits = [[f"{r['unique']:,} distinct skills", f"{r['unique']:,} 个不重复的 skill"], [f"{valid}% meet the format", f"{valid}% 符合格式"],
            line]
    out = {**base, "ran": True, "cells": cells, "bits": bits}
    if r["repo"] in NOTES:
        out.update(note=NOTES[r["repo"]][0], note_zh=NOTES[r["repo"]][1])
    return out


def main() -> None:
    out = PUBLIC / "collections"; out.mkdir(parents=True, exist_ok=True)
    rows = sorted(json.loads((HERE / "results.json").read_text()), key=lambda r: (not r["skills"], -r["stars"]))
    real = [r for r in rows if r["skills"]]
    for r in real:
        (out / (key(r["repo"]) + ".html")).write_text(page(r))
    big = max(real, key=lambda r: r["unique"])
    over = sum(fit(r["standing_tokens"]) == "few" for r in real)
    verdict = {**VERDICT, "caveat": [c.format(audited=len(real), over=over) for c in VERDICT["caveat"]]}
    copies = sum(r["repeated_names"] for r in real)
    files = sum(r["skills"] for r in real)
    write_runs(SLUG, {
        "type": "table", "date": DATE, "dir": "/best-runs/collections/", "results": URL + "RESULTS.md",
        "title": ["Claude Code skills collections audited: what is inside each", "合集体检：每个合集里到底有什么"],
        "list_title": ["Collection audit", "合集体检"],
        "intro": [f"On {DATE} we opened the {len(rows)} most-starred collections on this page and counted, from the files alone: how many skills each holds, how many are distinct, how many meet the Agent Skills format (a name of at most 64 lowercase letters, digits and hyphens; a description of 1 to 1,024 characters), how many ship scripts, and how long all their names and descriptions are together (at four characters per token). Then we measured what Claude Code does with a large install: session size with 12, 112 and 512 skills installed.",
                  f"{DATE} 我们打开了本页星数最高的 {len(rows)} 个合集，只看文件数了这些：每个仓库有多少 skill、多少个不重复、多少个符合 Agent Skills 格式（名字不超过 64 个小写字母、数字和连字符；描述 1 到 1,024 个字符）、多少个带脚本，以及所有名字和描述加起来有多长（按每 4 个字符 1 个 token 估算）。然后实测了 Claude Code 面对大量安装时怎么做：装 12、112、512 个 skill 时的会话大小。"],
        "finding": [f"{len(real)} of the {len(rows)} hold skills in the SKILL.md format; the other {len(rows) - len(real)} are link lists or subagent sets. They range from 5 skills to {big['unique']:,}. Of {files:,} skill files, {copies:,} are copies of a skill already in the same repository, and {over} collections are so big that Claude Code would list most of their skills by name only. Claude Code does not pay the full price for a big install: a session started at 17,781 tokens with 12 skills, 24,499 with 112 and 25,289 with 512, because past a budget it lists skills by name only (about 47 of 512 kept a description, by its own count). ",
                    f"{len(rows)} 个里有 {len(real)} 个含 SKILL.md 格式的 skill，另外 {len(rows) - len(real)} 个是链接清单或子 agent 合集。体量从 5 个 skill 到 {big['unique']:,} 个不等。{files:,} 个 skill 文件里，有 {copies:,} 个是同一仓库里已有 skill 的副本；有 {over} 个合集大到 Claude Code 只能把其中大多数 skill 按名字列出。Claude Code 不会为大量安装付全价：装 12 个 skill 时会话起始是 17,781 个 token，112 个是 24,499，512 个是 25,289，因为超出预算后它只按名字列出 skill（按它自己数的，512 个里约 47 个还带描述）。"],
        "name_col": ["Collection", "合集"],
        "columns": [["Distinct skills", "不重复的 skill"], ["Meet the format", "符合格式"], ["Ship scripts", "带脚本"],
                    ["Names and descriptions, in tokens (estimate)", "名字加描述的长度（token，估算）"], ["If you install all of it", "整包装上的话"]],
        "see": ["See the count →", "看体检明细 →"], "evidence": ["The count", "体检明细"], "line_label": [f"Claude Code skills audit, {DATE}:", f"{DATE} 体检："],
        "not_run_label": ["No SKILL.md files to count", "没有可数的 SKILL.md"], "not_run_line": ["No skill files to count:", "没有可数的 skill 文件："],
        "verdict": verdict, "runs": {r["repo"]: card(r) for r in rows}})
    print(f"{len(real)} collections, {files} skill files, {copies} copies; biggest {big['repo']} {big['standing_tokens']}")


if __name__ == "__main__":
    main()
