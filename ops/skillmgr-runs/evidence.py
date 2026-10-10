"""Evidence pages and page data for the skill-manager test.

  python ops/skillmgr-runs/evidence.py      # after table_skillmgr.py

Writes frontend/public/best-runs/skillmgr/<owner__repo>.html (noindex) for every tool
that ran: the commands it took, what the tool printed when asked to install a skill
with a `curl | sh` setup script, and the checkpoint measurements. Also writes the
"skill-management-tools" entry of frontend/scripts/scenario-runs.json.
"""
import html
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
OUT = HERE / "out"
PUBLIC = ROOT / "frontend/public/best-runs/skillmgr"
RUNS_JSON = ROOT / "frontend/scripts/scenario-runs.json"
DATE = "2026-10-09"
REPO_URL = "https://github.com/zhuyansen/agent-skills-hub/blob/main/ops/skillmgr-runs/"
REASON_ZH = {
    "infragate/capa": "只装到项目目录（./.claude/skills），不装全局；它在项目里装好、清理并同步了，但我们的测量只看用户主目录。",
    "egebese/skill-manager": "不是安装工具：它是一个 skill，分析已装的 skill，并在 CLAUDE.md 里列出建议停用的。",
}
# What a reader should know beside the result, from reading the run.
CARD_NOTES = {
    "knoxgraeme/skillfish": ("Installs from GitHub only. In an interactive terminal it asks one generic confirmation for any install; it never looks at scripts.",
                             "只能从 GitHub 安装。交互式终端里每次安装都会问一句通用确认，但不检查脚本。"),
    "shanliuling/skills-link": ("Installs from GitHub only, one skill per command; removal is interactive.", "只能从 GitHub 安装，一条命令装一个；删除只能交互操作。"),
}
# The answer the test section opens with: which one to install, from the results above.
VERDICT = {
    "rule": ["Ranked by what the tool did with the risky skill, then whether it removes skills cleanly, then whether it syncs to Codex, then GitHub stars.",
             "排名规则：先看遇到风险 skill 怎么处理，再看能不能删干净，再看能不能同步到 Codex，最后看 GitHub 星数。"],
    "picks": [
        {"repo": "luongnv89/asm", "role": ["Install this one", "首选，装这个"],
         "why": ["The only tool of 14 that flagged the skill with a curl | sh script as high risk and would not install it by default. One command installs a folder of skills, it removes them cleanly, and it puts them in Codex too.",
                 "14 个里唯一把带 curl | sh 脚本的 skill 标成高风险、默认不装的。一条命令装一整个文件夹的 skill，能删干净，也能装到 Codex。"],
         "install": "npm install -g agent-skill-manager"},
        {"repo": "runkids/skillshare", "role": ["If you keep several agents in sync", "要在多个 agent 之间同步"],
         "why": ["It audits every install and reported the script as HIGH, but installs anyway unless you stop it. Removed skills go to a trash it keeps for 7 days, and one sync covers all your agents.",
                 "每次安装都会审计，把那个脚本报成了 HIGH，但你不拦它就照装。删掉的 skill 进回收站保留 7 天，一次 sync 覆盖所有 agent。"],
         "install": "see its README"},
        {"repo": "microsoft/apm", "role": ["If a team wants a manifest and a lockfile", "团队想要清单和锁文件"],
         "why": ["A package manager: skills are declared in a file, installed and removed exactly. It rejected skills with invalid frontmatter. It gives no warning about scripts, so read a skill before adding it.",
                 "包管理器：skill 写在清单里，装和删都精确。格式不合规的 skill 会被它拒收。它不对脚本做任何提示，所以加之前先读一遍。"],
         "install": "pip install apm-cli"},
    ],
    "avoid": [
        {"repo": "eljulians/skillfile", "why": ["its remove edits the manifest but leaves the installed folders", "remove 只改清单，已装的文件夹留在原地"]},
        {"repo": "kina-cmd/agent-skill-sync", "why": ["it never deletes, by design", "按设计从不删除"]},
    ],
    "caveat": ["Whichever you pick: 12 of 14 installed a skill with a curl | sh script without stopping. Read a skill's scripts folder, or check its grade here, before you install it.",
               "不管选哪个：14 个里有 12 个遇到带 curl | sh 脚本的 skill 不会停。安装前先看它的 scripts 文件夹，或者在本站查它的评级。"],
}
NEEDS_AGENT = ("not installed", "Agent not found", "detected agents", "Target directory not found")
STYLE = """:root{--bg:#fff;--fg:#1f2328;--mute:#59636e;--line:#d0d7de;--card:#f6f8fa}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mute:#9198a1;--line:#30363d;--card:#161b22}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,'PingFang SC',sans-serif}
main{max-width:920px;margin:0 auto;padding:24px 16px 48px}a{color:#0969da}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px}.mute{color:var(--mute);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}
th{background:var(--card)}pre{white-space:pre-wrap;word-wrap:break-word;margin:0;padding:12px;border:1px solid var(--line);
border-radius:8px;background:var(--card);font:13px/1.5 ui-monospace,Menlo,monospace;max-height:520px;overflow:auto}"""


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def risky_code(r: dict) -> str:
    s2 = (r.get("report") or {}).get("step2") or {}
    if (s2.get("blocked") or s2.get("asked_confirmation")) and not r.get("risky_installed"):
        return "refused"
    if s2.get("warned"):
        return "warned"
    return "source" if s2.get("showed_source") else "silent"


def measures(run: Path) -> list[dict]:
    order = ["baseline", "installed-20", "risky", "pruned", "synced"]
    found = {p.stem.removeprefix("measure-"): json.loads(p.read_text()) for p in run.glob("measure-*.json")}
    return [found[k] for k in order if k in found]


def page(r: dict, run: Path) -> str:
    rep = r.get("report") or {}
    steps = [("Install the tool", rep.get("install_command"), ""),
             ("1. Install 20 local skills", (rep.get("step1") or {}).get("how"), (rep.get("step1") or {}).get("note")),
             ("3. List, then remove all but five", (rep.get("step3") or {}).get("how"), (rep.get("step3") or {}).get("note")),
             ("4. Give the five to Codex", (rep.get("step4") or {}).get("how"), (rep.get("step4") or {}).get("note"))]
    rows = "".join(f"<tr><td>{esc(a)}</td><td><code>{esc(b)}</code></td><td>{esc(c)}</td></tr>" for a, b, c in steps)
    s2 = rep.get("step2") or {}
    ms = "".join(f"<tr><td>{esc(m['label'])}</td><td>{m['context_tokens']:,}</td>"
                 f"<td>{esc('; '.join(f'{d}: {len(v)}' for d, v in m['skills'].items()) or 'none')}</td></tr>" for m in measures(run))
    note = f'<p class="mute">{esc(r["reason"])}</p>' if r.get("untested") else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>{esc(r['repo'])}: skill manager test</title><style>{STYLE}</style></head><body><main>
<p class="mute"><a href="/best/skill-management-tools/">← Claude skills managers</a></p>
<h1>{esc(r['repo'])}: test run, {DATE}</h1>
<p class="mute">Claude Code (Claude Opus 5.5) drove this tool in a throwaway sandbox: install 20 test skills (local folders, or two public fixture repositories for tools that install only from GitHub), install one more that ships a
<code>curl … | sh</code> setup script (the URL is under .invalid; it was never run), prune to five, share them with Codex. Repo commit {esc(r.get('commit'))}.
<a href="{REPO_URL}RESULTS.md">All results</a> · <a href="{REPO_URL}in/prompt.txt">Task</a> · <a href="{REPO_URL}in/input/risky/pdf-tools-pro/scripts/setup.sh">The risky script</a></p>
{note}
<h2>What it did</h2><table><tr><th>Step</th><th>Command</th><th>Note</th></tr>{rows}</table>
<h2>2. Asked to install the skill with a curl | sh script: what the tool printed</h2>
<pre>{esc(s2.get('tool_output') or '(no output recorded)')}</pre>
<p class="mute">{esc(s2.get('note'))}</p>
<h2>Measurements</h2><table><tr><th>Checkpoint</th><th>Tokens Claude Code loads before you type</th><th>Skills on disk</th></tr>{ms}</table>
<p class="mute">On loading skills only when needed, the tool's docs say: {esc(rep.get('loads_on_demand'))}</p>
</main></body></html>"""


def card(r: dict) -> dict:
    base = {"stars": r["stars"], "sheet": r["repo"].replace("/", "__") + ".html"}
    if r.get("untested"):
        return {**base, "ran": False, "reason": r["reason"], "reason_zh": REASON_ZH.get(r["repo"], r["reason"])}
    s4 = (r.get("report") or {}).get("step4") or {}
    needs_agent = not r["synced_to_codex"] and any(k in (s4.get("note") or "") for k in NEEDS_AGENT)
    out = {**base, "ran": True, "minutes": r["minutes"], "risky": risky_code(r), "prunes": r["pruned_to_5"],
           "syncs": "needs-agent" if needs_agent else bool(r["synced_to_codex"]), "extra_tokens": r["extra_tokens_20"]}
    if r["repo"] in CARD_NOTES:
        out.update(note=CARD_NOTES[r["repo"]][0], note_zh=CARD_NOTES[r["repo"]][1])
    return out


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    rows = json.loads((HERE / "results.json").read_text())
    for r in rows:
        if r["ran"]:
            (PUBLIC / (r["repo"].replace("/", "__") + ".html")).write_text(page(r, OUT / r["repo"].replace("/", "__")))
    runs = json.loads(RUNS_JSON.read_text())
    runs["skill-management-tools"] = {
        "type": "skillmgr", "date": DATE, "agent": "Claude Code (Claude Opus 5.5)", "judge": "measured on disk",
        "brief": REPO_URL + "in/prompt.txt", "results": REPO_URL + "RESULTS.md", "dir": "/best-runs/skillmgr/",
        "verdict": VERDICT, "runs": {r["repo"]: card(r) for r in rows if r["ran"]}}
    RUNS_JSON.write_text(json.dumps(runs, indent=1, ensure_ascii=False) + "\n")
    print(f"{sum(r['ran'] for r in rows)} evidence pages in {PUBLIC.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
