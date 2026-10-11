"""Evidence pages and page data for the trigger test (Codex skills page), and the crowding
finding it adds to the Claude Code skills page.

  python ops/codex-runs/evidence.py      # after the six runs in out/ (run.sh, FILLERS=0|100|500, codex|claude)

Writes frontend/public/best-runs/codex/<owner__repo>.html and overview.html (noindex), the
"codex-skills" entry of frontend/scripts/scenario-runs.json (type "table"), and the findings in
both pages' method blocks.
"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from runs_common import PUBLIC, REPO_URL, RUNS_JSON, esc, key, pair, shell, update_method, write_runs  # noqa: E402

SLUG, DATE = "codex-skills", "2026-10-11"
URL = REPO_URL + "codex-runs/"
LEVELS = [0, 100, 500]
AGENTS = [("codex", "Codex", "gpt-6-astra"), ("claude", "Claude Code", "Claude Opus 5.5")]
KINDS = {"direct": "asked plainly", "indirect": "described without the skill's words", "other_language": "in the other language"}
BUDGET_MESSAGE = "Exceeded skills context budget. All skill descriptions were removed and 134 additional skills were not included in the model-visible skills list."
NOTES = {
    "cyber-ppt": ("With 500 other skills installed, Codex opened codex-ppt for all three of its requests: with descriptions gone, the two deck skills cannot be told apart by name.",
                  "旁边再装 500 个 skill 时，Codex 把它的三条请求都交给了 codex-ppt：描述没了，两个做 PPT 的 skill 光看名字分不开。"),
    "visio-image-rebuilder": ("At 500, Codex opened image-to-editable-ppt first on one request, then searched the disk and read this skill too; we count the first one opened.",
                              "500 那档有一条请求 Codex 先打开了 image-to-editable-ppt，随后自己搜索磁盘又读了这个 skill；我们按先打开的算。"),
    "complexity-optimizer": ("The least reliable to trigger: it was also the one miss at 100 on both agents.", "触发最不稳的一个：100 那档两个 agent 各漏的一条也是它。"),
}
LATE = ["qiaomu-goal-meta-skill", "startup-pressure-test", "travel-photo-abstraction", "visio-image-rebuilder"]
VERDICT = {
    "title": ["Which one to install", "到底装哪个"],
    "basis": ["after testing whether Codex reaches for each", "实测 Codex 会不会用它之后"],
    "rule": ["Ranked by how often the right skill was opened, over 18 tries each (three requests, three crowding levels, two agents), then GitHub stars. This measures whether the agent finds the skill, not how good its output is. One run per request; the requests were written from each skill's own description.",
             "排名规则：按「正确的 skill 被打开的次数」排，每个 skill 共 18 次（3 条请求 × 3 档拥挤度 × 2 个 agent），再看 GitHub 星数。这量的是 agent 找不找得到这个 skill，不是它做出来的东西好不好。每条请求只跑一次；请求是照各 skill 自己的描述写的。"],
    "picks": [
        {"repo": "ningzimu/codex-ppt-skill", "role": ["For slide decks", "做 PPT"],
         "why": ["Opened every time in Codex, even with 500 other skills installed and its description stripped (17 of 18 over both agents): the name says what it does. It also took over the requests meant for another deck skill, so install one deck skill, not several.",
                 "在 Codex 里每一次都被打开，哪怕旁边装了 500 个 skill、描述被去掉（两个 agent 合计 18 次中 17 次）：名字本身就说明了用途。它还接走了本该给另一个 PPT skill 的请求，所以 PPT skill 装一个就够，别装好几个。"]},
        {"repo": "ningzimu/image-to-editable-ppt-skill", "role": ["To make image slides editable", "把图片版幻灯片变成可编辑"],
         "why": ["18 of 18, and a different job from the one above, so the two do not compete.",
                 "18 次全中，而且和上面那个做的不是一件事，两者不会互相抢。"]},
        {"repo": "vibeforge1111/keep-codex-fast", "role": ["To keep Codex itself fast", "让 Codex 自己保持顺畅"],
         "why": ["18 of 18. A maintenance skill: a read-only report first, backups before any change.",
                 "18 次全中。是一个维护用的 skill：先出只读报告，改动前先备份。"]},
    ],
    "avoid_label": ["Fine alone, lost in a crowd (Codex with 500 others installed):", "单独用没问题，装多了就找不到（Codex 旁边再装 500 个时）："],
    "avoid": [
        {"repo": "crazyykhllc-bit/CyberPPT", "why": ["0 of 3: every request went to codex-ppt", "3 次全没中：请求都被 codex-ppt 接走"]},
        {"repo": "Kappaemme-git/codex-startup-pressure-test-skill", "why": ["0 of 3, like the three other skills whose names come late in the alphabet", "3 次全没中，另外三个名字排在字母表后面的 skill 也一样"]},
    ],
    "caveat": ["Whichever you pick: keep the number of installed skills low in Codex. With 512 installed it dropped every description and hid 134 skills, and the right skill was opened 17 times of 36, against 35 or 36 with up to 112 installed.",
               "不管选哪个：在 Codex 里别装太多 skill。装到 512 个时它去掉了所有描述、还隐藏了 134 个 skill，36 次里只有 17 次打开了正确的 skill；装到 112 个以内时是 35 或 36 次。"],
}


def load(agent: str, level: int) -> list[dict]:
    return json.loads((HERE / "out" / (agent + (f"-{level}" if level else "")) / "results.json").read_text())


def session_tokens(agent: str, level: int) -> int | None:
    """Tokens the agent starts a session with, from the six unrelated requests of that run."""
    vals = []
    for f in sorted((HERE / "out" / (agent + (f"-{level}" if level else ""))).glob("none_*.jsonl")):
        for line in f.read_text(errors="ignore").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if agent == "claude" and e.get("type") == "assistant":
                u = e["message"].get("usage") or {}
                vals.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)); break
            if agent == "codex" and e.get("type") == "turn.completed":
                vals.append(e["usage"]["input_tokens"]); break
    return round(statistics.median(vals)) if vals else None


def totals(rows: list[dict]) -> dict:
    pos = [r for r in rows if r["skill"]]
    right = sum(r["opened"] == r["skill"] for r in pos)
    wrong = sum(bool(r["opened"]) and r["opened"] != r["skill"] for r in pos)
    return {"right": right, "wrong": wrong, "none": len(pos) - right - wrong, "of": len(pos),
            "false": sum(bool(r["opened"]) for r in rows if not r["skill"]), "unrelated": sum(not r["skill"] for r in rows)}


def cell(r: dict) -> str:
    if r["opened"] == r["skill"]:
        return f'<span class="ok">opened it</span> <span class="mute">{r["seconds"]}s</span>'
    if r["opened"]:
        return f'<span class="no">opened {esc(r["opened"])}</span>'
    return f'<span class="no">no skill opened</span> <span class="mute">{esc(r["ended"])}</span>'


def skill_page(repo: str, name: str, runs: dict) -> str:
    prompts = [r for r in runs[("codex", 0)] if r["skill"] == name]
    head = "".join(f"<th>{label}, {lvl} others</th>" for _, label, _ in AGENTS for lvl in LEVELS)
    body = ""
    for p in prompts:
        cells = "".join(f"<td>{cell(next(r for r in runs[(a, lvl)] if r['id'] == p['id']))}</td>" for a, _, _ in AGENTS for lvl in LEVELS)
        body += f"<tr><td><b>{esc(KINDS[p['kind']])}</b><br><span class='mute'>{esc(p['prompt'][:400])}</span></td>{cells}</tr>"
    note = f"<p>{esc(NOTES[name][0])}</p>" if name in NOTES else ""
    return shell(f"{repo}: trigger test", ("/best/codex-skills/", "Codex skills"), f"""<h1>{esc(repo)}: does the agent reach for it? {DATE}</h1>
<p class="mute">Twelve Codex skills were installed together and each agent was sent three requests meant for this skill (<code>{esc(name)}</code>), in a throwaway sandbox. A run stopped as soon as a skill was opened.
Then the same requests with 100 and 500 other real skills installed beside the twelve. Codex ran gpt-6-astra, Claude Code ran Claude Opus 5.5.
<a href="overview.html">All levels</a> · <a href="{URL}in/prompts.json">The requests</a> · <a href="{URL}in/trigger.py">How a run is scored</a></p>{note}
<table><tr><th>Request</th>{head}</tr>{body}</table>""")


def overview(runs: dict) -> str:
    rows = ""
    for lvl in LEVELS:
        for a, label, model in AGENTS:
            t = totals(runs[(a, lvl)]); tok = session_tokens(a, lvl)
            rows += (f"<tr><td>{lvl}</td><td>{label} <span class='mute'>{model}</span></td><td>{t['right']}/{t['of']}</td><td>{t['wrong']}</td><td>{t['none']}</td>"
                     f"<td>{t['false']}/{t['unrelated']}</td><td>{f'{tok:,}' if tok else 'not recorded'}</td></tr>")
    return shell("Trigger test: all levels", ("/best/codex-skills/", "Codex skills"), f"""<h1>Trigger test, all levels, {DATE}</h1>
<p class="mute">Twelve Codex skills installed together; 36 requests that should reach one of them and 6 that should reach none; then again with 100 and 500 other real skills
(from two public collections) installed beside them. <a href="{URL}">Scripts and raw results</a></p>
<table><tr><th>Other skills installed</th><th>Agent</th><th>Right skill opened</th><th>Another skill opened</th><th>No skill opened</th><th>Opened on an unrelated request</th><th>Tokens at session start</th></tr>{rows}</table>
<h2>What Codex said at 500</h2><pre>{esc(BUDGET_MESSAGE)}</pre>
<p class="mute">Printed by Codex at the start of every session at that level. Claude Code with the same 512 skills listed every name and kept descriptions for about 47 of them (its own count).
The four test skills Codex never opened at 500 ({esc(', '.join(LATE))}) are the four whose names come last in the alphabet; that they were among the 134 left out is our inference, Codex does not list them.</p>""")


def card(c: dict, name: str, runs: dict) -> dict:
    def hits(agent: str, lvl: int) -> int:
        return sum(r["opened"] == name for r in runs[(agent, lvl)] if r["skill"] == name)
    grid = {(a, lvl): hits(a, lvl) for a, _, _ in AGENTS for lvl in LEVELS}
    total = sum(grid.values())
    cls = lambda n: "touch-ups" if n == 3 else "substantial" if n == 0 else ""   # noqa: E731
    cells = [[f"{total}/18", None, "touch-ups" if total == 18 else ""], *[[f"{grid[('codex', lvl)]}/3", None, cls(grid[("codex", lvl)])] for lvl in LEVELS],
             [f"{grid[('claude', 500)]}/3", None, cls(grid[("claude", 500)])]]
    crowd = grid[("codex", 500)]
    bits = [[f"the agent opened it {total} of 18 times it should have", f"该用它的 18 次里，agent 打开了它 {total} 次"],
            [f"in Codex with 500 other skills installed: {crowd} of 3", f"Codex 旁边再装 500 个 skill 时：3 次中 {crowd} 次"],
            [f"in Claude Code with 500 others: {grid[('claude', 500)]} of 3", f"Claude Code 旁边再装 500 个时：3 次中 {grid[('claude', 500)]} 次"]]
    out = {"ran": True, "stars": c["stars"], "sheet": key(c["repo"]) + ".html", "cells": cells, "bits": bits, "total": total}
    if name in NOTES:
        out.update(note=NOTES[name][0], note_zh=NOTES[name][1])
    return out


def main() -> None:
    out = PUBLIC / "codex"; out.mkdir(parents=True, exist_ok=True)
    runs = {(a, lvl): load(a, lvl) for a, _, _ in AGENTS for lvl in LEVELS}
    name_of = {r["repo"]: r["skill"] for r in runs[("codex", 0)] if r["skill"]}
    cands = json.loads((HERE / "candidates.json").read_text())
    cards = {c["repo"]: card(c, name_of[c["repo"]], runs) for c in cands}
    for c in cands:
        (out / (key(c["repo"]) + ".html")).write_text(skill_page(c["repo"], name_of[c["repo"]], runs))
    (out / "overview.html").write_text(overview(runs))
    t = {k: totals(v) for k, v in runs.items()}
    tok = {k: session_tokens(*k) for k in runs}
    ordered = dict(sorted(cards.items(), key=lambda kv: (-kv[1].pop("total"), -kv[1]["stars"])))
    cx, cc = t[("codex", 500)], t[("claude", 500)]
    write_runs(SLUG, {
        "type": "table", "date": DATE, "dir": "/best-runs/codex/", "results": URL,
        "title": ["Codex skills tested: does the agent reach for the right one", "实测对比：agent 会不会用对 skill"],
        "intro": [f"On {DATE} we installed {len(cands)} of these skills together in a throwaway sandbox and sent each agent 36 requests that should reach one of them (three per skill: asked plainly, described without the skill's own words, and in the other language) and 6 that should reach none. A run stopped as soon as a skill was opened, so this measures which skill the agent reaches for, not what the skill then produces. Then the same requests with 100 and with 500 other real skills installed beside the twelve. Codex ran gpt-6-astra; Claude Code, which loads the same SKILL.md format, ran Claude Opus 5.5.",
                  f"{DATE} 我们在用完即删的沙箱里把其中 {len(cands)} 个 skill 一起装上，给每个 agent 发 36 条应该触发其中某个 skill 的请求（每个 skill 三条：直说、不用 skill 自己的词来描述、换一种语言），另加 6 条不该触发任何 skill 的请求。一旦有 skill 被打开就停止，所以量的是 agent 会去用哪个 skill，不是 skill 之后做出了什么。然后在这 12 个旁边再装 100 个、500 个别的真实 skill，重发同样的请求。Codex 用 gpt-6-astra；Claude Code 加载同样的 SKILL.md 格式，用 Claude Opus 5.5。"],
        "finding": [f"With only the twelve installed, both agents opened the right skill 36 times of 36, and neither opened one for an unrelated request at any level. With 100 others, 35 of 36 each. With 500 others, Claude Code still managed {cc['right']} of {cc['of']}, and Codex {cx['right']} of {cx['of']}: it reported that it had removed every skill description and left 134 skills out of the list. Four test skills were never opened again, and one deck skill took every request meant for another.",
                    f"只装这 12 个时，两个 agent 都是 36 次里 36 次打开了正确的 skill；任何一档都没有为无关请求打开 skill。再装 100 个，各 35 次。再装 500 个，Claude Code 仍有 {cc['right']}/{cc['of']}，Codex 是 {cx['right']}/{cx['of']}：它自己报告去掉了所有 skill 的描述，并有 134 个 skill 没列进列表。有 4 个测试 skill 再也没被打开过，还有一个 PPT skill 把本该给另一个的请求全接走了。"],
        "name_col": ["Skill", "Skill"],
        "columns": [["Right skill opened (of 18)", "打开正确 skill（共 18 次）"], ["Codex, 12 installed", "Codex，装 12 个"], ["Codex, +100", "Codex，再装 100 个"],
                    ["Codex, +500", "Codex，再装 500 个"], ["Claude Code, +500", "Claude Code，再装 500 个"]],
        "see": ["See every request →", "看每条请求的结果 →"], "evidence": ["The requests", "请求明细"],
        "line_label": [f"Codex skill trigger test, {DATE}:", f"{DATE} 实测："],
        "control": {"sheet": "overview.html", "label": ["See all three levels →", "看三档完整结果 →"]},
        "verdict": VERDICT, "runs": ordered})
    drop = pair(f"How many skills are installed matters more than which. With 12 or 112 skills installed, Codex opened the right one 36 and 35 times of 36. With 512 it managed {cx['right']}: it removed every description and left 134 skills out of its list, by its own message.",
                f"装多少比装哪个更重要。装 12 个或 112 个 skill 时，Codex 在 36 次里有 36 次和 35 次打开了正确的 skill。装到 512 个时只有 {cx['right']} 次：按它自己的提示，它去掉了所有描述，并把 134 个 skill 留在列表之外。")
    update_method(SLUG, [
        drop,
        pair("Without descriptions, a skill is found by its name alone. The skills still opened every time at 512 have names that say what they do (codex-ppt, image-to-editable-ppt, keep-codex-fast); requests for cyber-ppt all went to codex-ppt, and the four test skills last in the alphabet were never opened.",
             "没有描述时，skill 只能靠名字被找到。装到 512 个仍然每次都被打开的 skill，名字本身就说明用途（codex-ppt、image-to-editable-ppt、keep-codex-fast）；给 cyber-ppt 的请求全去了 codex-ppt，字母表最后的 4 个测试 skill 再也没被打开。"),
        pair(f"Claude Code degrades differently. With the same 512 skills it kept every name and dropped most descriptions, and still opened the right skill {cc['right']} times of {cc['of']}; its session started at {tok[('claude', 500)]:,} tokens, against {tok[('claude', 0)]:,} with 12 installed.",
             f"Claude Code 的退化方式不同。同样装 512 个，它保留了每个名字、去掉大部分描述，{cc['of']} 次里仍有 {cc['right']} 次打开了正确的 skill；会话起始是 {tok[('claude', 500)]:,} 个 token，装 12 个时是 {tok[('claude', 0)]:,}。")],
        pair(f"Installed {len(cands)} of the skills together and sent Codex and Claude Code the same 42 requests at three crowding levels (12, 112 and 512 skills installed), stopping each run when a skill was opened. Results are in the test section above and on each card.",
             f"把其中 {len(cands)} 个 skill 一起装上，在三档拥挤度（装 12、112、512 个 skill）下给 Codex 和 Claude Code 发同样的 42 条请求，有 skill 被打开就停止。结果在上面的实测区和每张卡片上。"),
        pair("This tests whether a skill is found, not whether its output is any good. Each request ran once, and the requests were written from each skill's own description, which favours triggering. The two agents ran different models (gpt-6-astra and Claude Opus 5.5), so a gap between them may be the model or the agent. That the four skills never opened at 512 were among the 134 Codex left out is inferred from their names coming last in the alphabet.",
             "这测的是 skill 找不找得到，不是它的产出好不好。每条请求只跑一次，而且是照各 skill 自己的描述写的，对触发有利。两个 agent 用的模型不同（gpt-6-astra 和 Claude Opus 5.5），两者的差距可能来自模型，也可能来自 agent。「装到 512 个时再没被打开的 4 个 skill 属于 Codex 丢掉的 134 个」是根据它们的名字排在字母表最后推断的。"),
        "How many skills are installed matters more")
    # The Claude Code skills page: the same crowding result, as a reason not to install a collection whole.
    data = json.loads(RUNS_JSON.read_text())
    ccs = data["claude-code-skills"]
    base_en, base_zh = (x.split(" Crowded:")[0].split(" 装多了：")[0] for x in ccs["finding"])
    ccs["finding"] = [base_en + f" Crowded: with 500 other skills installed beside 12 test skills, Claude Code still opened the right one {cc['right']} times of {cc['of']}, while Codex managed {cx['right']} of {cx['of']} after dropping every description and hiding 134 skills.",
                      base_zh + f" 装多了：在 12 个测试 skill 旁边再装 500 个时，Claude Code 仍有 {cc['right']}/{cc['of']} 次打开了正确的 skill；Codex 去掉所有描述并隐藏 134 个 skill 之后只有 {cx['right']}/{cx['of']}。"]
    ccs["control"] = {"sheet": "../codex/overview.html", "label": ["See the crowding test →", "看拥挤度实测 →"]}
    RUNS_JSON.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    update_method("claude-code-skills", [
        pair(f"Install everything and Claude Code copes, Codex does not. With 512 skills installed, Claude Code opened the right one of 12 test skills {cc['right']} times of {cc['of']}; Codex, which shares the SKILL.md format, managed {cx['right']} of {cx['of']} after removing every description and leaving 134 skills out of its list.",
             f"全部装上，Claude Code 撑得住，Codex 不行。装 512 个 skill 时，Claude Code 对 12 个测试 skill 在 {cc['of']} 次里有 {cc['right']} 次打开了正确的那个；用同样 SKILL.md 格式的 Codex 去掉了所有描述、把 134 个 skill 留在列表之外，只有 {cx['right']}/{cx['of']}。"),
        pair(f"The cost in Claude Code is descriptions, not tokens: a session started at {tok[('claude', 0)]:,} tokens with 12 skills, {tok[('claude', 100)]:,} with 112 and {tok[('claude', 500)]:,} with 512. Past about a hundred, skills are listed by name only.",
             f"在 Claude Code 里代价是描述，不是 token：装 12 个 skill 时会话起始 {tok[('claude', 0)]:,} 个 token，112 个时 {tok[('claude', 100)]:,}，512 个时 {tok[('claude', 500)]:,}。超过一百个左右，skill 就只按名字列出。")],
        pair("Counted every SKILL.md in the most-starred collections on this page against the Agent Skills format, and measured what Claude Code and Codex do with 12, 112 and 512 skills installed. Results are in the audit section above and on each card.",
             "按 Agent Skills 格式数了本页星数最高的合集里的每一个 SKILL.md，并实测了装 12、112、512 个 skill 时 Claude Code 和 Codex 的表现。结果在上面的体检区和每张卡片上。"),
        pair("We counted files and tested finding, not doing: none of these collections' skills was run for its output, so this says nothing about whether a given skill is any good. The 12 test skills have descriptive names; a skill with a vague name and no visible description may fare worse in Claude Code, and we did not test that. One run per request.",
             "我们数了文件、测了「找不找得到」，没有测「做得好不好」：这些合集里的 skill 没有一个被运行来看产出，所以这说明不了某个 skill 好不好用。12 个测试 skill 的名字本身就说明用途；名字含糊又看不到描述的 skill 在 Claude Code 里可能更差，这一点没有测。每条请求只跑一次。"),
        "Install everything and Claude Code copes", replaces=("Counted every SKILL.md", "We counted files"))
    print({f"{a}-{lvl}": f"{t[(a, lvl)]['right']}/{t[(a, lvl)]['of']} tok {tok[(a, lvl)]}" for a, _, _ in AGENTS for lvl in LEVELS})


if __name__ == "__main__":
    main()
