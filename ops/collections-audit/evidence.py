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
NOT_COLLECTION = {
    "travisvn/awesome-claude-skills": ("A list of links to skills kept elsewhere: there is no skill in it to install.", "一份指向别处 skill 的链接清单：里面没有可安装的 skill。"),
    "karanb192/awesome-claude-skills": ("A list of links to skills kept elsewhere: there is no skill in it to install.", "一份指向别处 skill 的链接清单：里面没有可安装的 skill。"),
    "jarrodwatts/claude-hud": ("A status line plugin for Claude Code, not a skill collection.", "Claude Code 的状态栏插件，不是 skill 合集。"),
    "winfunc/opcode": ("A desktop app for Claude Code, not a skill collection.", "Claude Code 的桌面应用，不是 skill 合集。"),
}
NOTES = {
    "thedotmack/claude-mem": ("A memory tool that ships its own skills; you install the tool, not the skills one by one.", "一个记忆工具，自带 skill；装的是工具，不是逐个装 skill。"),
    "alirezarezvani/claude-skills": ("Nearly half the skill files are copies of the same skill packaged for other agents or plugins.", "将近一半的 skill 文件是同一个 skill 为别的 agent 或插件打包的副本。"),
    "sergebulaev/linkedin-skills": ("Each skill is in the repository twice.", "每个 skill 在仓库里都有两份。"),
    "davila7/claude-code-templates": ("140 of its skills are longer than the 500 lines the format's guidance recommends.", "有 140 个 skill 超过格式指南建议的 500 行。"),
}
VERDICT = {
    "title": ["Which one to install", "到底装哪个"],
    "basis": ["after counting what is inside each", "数完每个合集里有什么之后"], "more": ["See the audit →", "看合集体检 →"],
    "lead": ["We counted every skill file in {n} of these repositories. This is what we would pick; the [full audit](#{anchor}) is below.",
             "我们数了其中 {n} 个仓库里的每一个 skill 文件,结论如下,[完整体检](#{anchor})在下面。"],
    "rule": ["Listed by size, smallest first: Claude Code shows descriptions for only about the first hundred skills' worth, so the smaller the collection, the more of it the agent can actually see. Counted from the files at the commit on each evidence page; no skill was run, so this does not say which skills are good.",
             "按体量从小到大排列：Claude Code 只给大约前一百个 skill 的量显示描述，所以合集越小，agent 真正看得到的比例越高。数字来自各证据页所标 commit 的文件；没有运行任何 skill，所以这说明不了哪个 skill 好用。"],
    "picks": [
        {"repo": "anthropics/claude-plugins-official", "role": ["To start", "刚开始用"],
         "why": ["Anthropic's own directory: every skill in it meets the format, and it is small enough that each one keeps its description in the list. Current, and a safe first install.",
                 "Anthropic 自己的目录：里面每个 skill 都符合格式，体量也小，每个都能在列表里保留描述。跟得上版本，适合第一次安装。"]},
        {"repo": "gamedev-skills/awesome-gamedev-agent-skills", "role": ["For one domain, done cleanly", "只做一个领域，做得干净"],
         "why": ["75 skills on one subject, all 75 valid, no duplicates, none over 500 lines. If game development is not your field, this is still the shape to look for: small and single-topic.",
                 "75 个 skill 只讲一个主题，75 个全部合规，没有重复，没有超过 500 行的。就算你不做游戏，这也是值得找的样子：小而专。"]},
        {"repo": "davila7/claude-code-templates", "role": ["For breadth, picked by name", "要广度，但按名字挑着装"],
         "why": ["The widest collection here: 886 distinct skills plus commands and agents. Install the few you need. Installed whole, most of them would be listed by name only.",
                 "这里最全的合集：886 个不重复的 skill，另有命令和子 agent。只装你需要的几个。整包装上的话，大多数只会按名字列出。"]},
    ],
    "avoid_label": ["Do not install whole:", "别整包安装："],
    "avoid": [
        {"repo": "davila7/claude-code-templates", "why": ["886 skills, of which Claude Code would show a description for a few dozen", "886 个 skill，Claude Code 只会给其中几十个显示描述"]},
        {"repo": "alirezarezvani/claude-skills", "why": ["443 distinct skills, and 403 of its 846 skill files are copies", "443 个不重复的 skill，846 个 skill 文件里有 403 个是副本"]},
    ],
    "caveat": ["Whichever you pick: four of the ten entries on this page are not skill collections at all (two link lists, a status line, a desktop app). Check what a repository is before you run its install command.",
               "不管选哪个：本页 10 个条目里有 4 个根本不是 skill 合集（两个链接清单、一个状态栏、一个桌面应用）。跑安装命令之前，先弄清这个仓库是什么。"],
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
    heavy = r["standing_tokens"] >= 20000
    cells = [[f"{r['unique']:,}", None, "num"], [f"{valid}%", None, "touch-ups" if valid == 100 else ""], [str(r["repeated_names"]), None, "num"],
             [str(r["with_scripts"]), None, "num"], [f"{r['standing_tokens']:,}", None, "substantial" if heavy else "num"]]
    bits = [[f"{r['unique']:,} distinct skills", f"{r['unique']:,} 个不重复的 skill"], [f"{valid}% meet the format", f"{valid}% 符合格式"],
            [f"names and descriptions run to about {r['standing_tokens']:,} tokens", f"名字和描述合计约 {r['standing_tokens']:,} 个 token"]]
    out = {**base, "ran": True, "cells": cells, "bits": bits}
    if r["repo"] in NOTES:
        out.update(note=NOTES[r["repo"]][0], note_zh=NOTES[r["repo"]][1])
    return out


def main() -> None:
    out = PUBLIC / "collections"; out.mkdir(parents=True, exist_ok=True)
    rows = sorted(json.loads((HERE / "results.json").read_text()), key=lambda r: (not r["skills"], r["standing_tokens"]))
    real = [r for r in rows if r["skills"]]
    for r in real:
        (out / (key(r["repo"]) + ".html")).write_text(page(r))
    big = max(real, key=lambda r: r["standing_tokens"])
    copies = sum(r["repeated_names"] for r in real)
    files = sum(r["skills"] for r in real)
    write_runs(SLUG, {
        "type": "table", "date": DATE, "dir": "/best-runs/collections/", "results": URL + "RESULTS.md",
        "title": ["Claude Code skills collections audited: what is inside each", "合集体检：每个合集里到底有什么"],
        "list_title": ["Collection audit", "合集体检"],
        "intro": [f"On {DATE} we opened all {len(rows)} repositories on this page and counted, from the files alone: how many skills each holds, how many are distinct, how many meet the Agent Skills format (a name of at most 64 lowercase letters, digits and hyphens; a description of 1 to 1,024 characters), how many ship scripts, and how long all their names and descriptions are together (at four characters per token). Then we measured what Claude Code does with a large install: session size with 12, 112 and 512 skills installed.",
                  f"{DATE} 我们打开了本页全部 {len(rows)} 个仓库，只看文件数了这些：每个仓库有多少 skill、多少个不重复、多少个符合 Agent Skills 格式（名字不超过 64 个小写字母、数字和连字符；描述 1 到 1,024 个字符）、多少个带脚本，以及所有名字和描述加起来有多长（按每 4 个字符 1 个 token 估算）。然后实测了 Claude Code 面对大量安装时怎么做：装 12、112、512 个 skill 时的会话大小。"],
        "finding": [f"{len(real)} of the {len(rows)} hold skills; the other {len(rows) - len(real)} are link lists or tools. Of {files:,} skill files, {copies} are copies of a skill already in the same repository. Claude Code does not pay the full price for a big install: a session started at 17,781 tokens with 12 skills, 24,499 with 112 and 25,289 with 512, because past a budget it lists skills by name only (about 47 of 512 kept a description, by its own count). The largest collection here ({big['repo'].split('/')[1]}, {big['unique']} distinct skills) would mostly be names.",
                    f"{len(rows)} 个里有 {len(real)} 个含 skill，另外 {len(rows) - len(real)} 个是链接清单或工具。{files:,} 个 skill 文件里，有 {copies} 个是同一仓库里已有 skill 的副本。Claude Code 不会为大量安装付全价：装 12 个 skill 时会话起始是 17,781 个 token，112 个是 24,499，512 个是 25,289，因为超出预算后它只按名字列出 skill（按它自己数的，512 个里约 47 个还带描述）。本页最大的合集（{big['repo'].split('/')[1]}，{big['unique']} 个不重复的 skill）装上后大部分只剩名字。"],
        "name_col": ["Collection", "合集"],
        "columns": [["Distinct skills", "不重复的 skill"], ["Meet the format", "符合格式"], ["Copies in the repo", "仓库内的副本"], ["Ship scripts", "带脚本"],
                    ["Names and descriptions, in tokens (estimate)", "名字加描述的长度（token，估算）"]],
        "see": ["See the count →", "看体检明细 →"], "evidence": ["The count", "体检明细"], "line_label": [f"Claude Code skills audit, {DATE}:", f"{DATE} 体检："],
        "not_run_label": ["Not skill collections", "不是 skill 合集"], "not_run_line": ["Not a skill collection:", "不是 skill 合集："],
        "verdict": VERDICT, "runs": {r["repo"]: card(r) for r in rows}})
    print(f"{len(real)} collections, {files} skill files, {copies} copies; biggest {big['repo']} {big['standing_tokens']}")


if __name__ == "__main__":
    main()
