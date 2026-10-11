"""Evidence pages and page data for the Jev first-run test.

  python ops/jev-runs/evidence.py      # after the runs in out/

Each project was installed from its README in a throwaway sandbox with a Jev API key in the
environment, and its own quick start was run once. Writes results.json and RESULTS.md here,
frontend/public/best-runs/jev/<owner__repo>.html (noindex) and the "typesafe-jev" entry of
frontend/scripts/scenario-runs.json (type "table"). The projects do different jobs, so this
is not a comparison of quality: it says which ones a new user can get running, and what else
they need.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from runs_common import PUBLIC, REPO_URL, esc, final_message, key, shell, write_runs  # noqa: E402

SLUG, DATE = "typesafe-jev", "2026-10-11"
URL = REPO_URL + "jev-runs/"
OUT = HERE / "out"
# What stopped a first run, in a reader's words, from each run's report (read by hand).
BLOCKED = {
    "browser-use/jev-ultrafast": ("Needs a second paid key: Jev picked the first action, then the agent stopped for want of a text-model key (TEXT_MODEL_API_KEY).",
                                  "还要第二个付费密钥：Jev 选出了第一个动作，随后 agent 因为缺少文本模型的密钥（TEXT_MODEL_API_KEY）停了下来。"),
    "thruwire/foreman": ("Jev's routing and assessments came back, but its default workers need the Codex CLI installed and signed in.",
                         "Jev 的路由和评估都返回了，但它默认的 worker 需要装好并登录 Codex CLI。"),
    "superagents-lab/jev-search": ("Needs a Cloudflare account: its dev server opens a remote Workers AI session and would not start without one.",
                                   "需要 Cloudflare 账号：它的开发服务器要开一个远程 Workers AI 会话，没有账号就起不来。"),
}
CANNOT_JUDGE = {
    "gargpratyush/jev-router": ("It routes inside a signed-in Claude Code or Codex; our sandbox runs Claude Code on a token, which it does not accept, so the test could not reach its first step.",
                                "它在已登录的 Claude Code 或 Codex 里做路由；我们的沙箱用令牌运行 Claude Code，它不认，所以测试走不到它的第一步。"),
}
VERDICT = {
    "title": ["Which one to try first", "先试哪个"],
    "basis": ["after running each one's quick start", "把每个的快速上手跑了一遍之后"], "more": ["See the first runs →", "看首次运行结果 →"],
    "lead": ["We ran the quick start of {n} of these projects with a Jev key. This is what we would try first; the [full results](#{anchor}) are below.",
             "我们用 Jev 密钥跑了其中 {n} 个项目的快速上手,下面是我们会先试的,[完整结果](#{anchor})在下面。"],
    "rule": ["Listed by GitHub stars. These projects do different jobs, so this is not a ranking of quality: it is whether a new user with only a Jev key gets through the README's first example. One run each, a handful of Jev calls.",
             "按 GitHub 星数排列。这些项目做的事各不相同，所以这不是质量排名：看的是只有一个 Jev 密钥的新用户能不能跑通 README 的第一个示例。每个只跑一次，只调用了几次 Jev。"],
    "picks": [
        {"repo": "dzhng/jevgrep", "role": ["To search code by what it does", "按功能搜代码"],
         "why": ["One npm install, one command to save the key, a doctor check that confirmed the connection, and a search that returned a result. No other key or account needed.",
                 "一条 npm 安装、一条保存密钥的命令、一次确认连接的自检，然后搜索就返回了结果。不需要别的密钥或账号。"]},
        {"repo": "tamaratran/fast-jev-compaction", "role": ["To cut what Claude Code spends on compaction", "减少 Claude Code 压缩上下文的开销"],
         "why": ["It ran in one Jev request (under half a second) and returned keep-or-drop decisions for each tool call. The README's example is cut short, so expect to write a few more messages before Jev is asked anything.",
                 "只用了一次 Jev 请求（不到半秒），返回了每次工具调用该保留还是丢弃的判断。README 的示例是截断的，要自己多写几条消息 Jev 才会被调用。"]},
        {"repo": "jkudish/jev-mcp", "role": ["To use Jev from any agent, as MCP tools", "在任意 agent 里以 MCP 工具使用 Jev"],
         "why": ["Registered with one claude mcp add and answered its first call: one claim verified, one contradicted. There is no command-line example; you call it from an agent.",
                 "一条 claude mcp add 就注册好，第一次调用就有结果：一条说法得到验证，一条被判矛盾。它没有命令行示例，要从 agent 里调用。"]},
    ],
    "avoid_label": ["A Jev key alone is not enough for these:", "这几个只有 Jev 密钥还不够："],
    "avoid": [
        {"repo": "browser-use/jev-ultrafast", "why": ["the most-starred project here also needs a paid text-model key", "这里星数最高的项目，还要一个付费的文本模型密钥"]},
        {"repo": "thruwire/foreman", "why": ["needs the Codex CLI signed in", "需要已登录的 Codex CLI"]},
        {"repo": "superagents-lab/jev-search", "why": ["needs a Cloudflare account", "需要 Cloudflare 账号"]},
    ],
    "caveat": ["Whichever you pick: every project that ran did so on a few Jev calls costing a fraction of a cent, so trying one is cheap. Read what else a project needs before you start.",
               "不管选哪个：跑通的项目都只用了几次 Jev 调用，花费不到一分钱，所以试一个的成本很低。开始之前先看清它还需要什么。"],
}


def row(c: dict) -> dict:
    run = OUT / key(c["repo"])
    report = run / "deliverables" / "report.json"
    meta = json.loads((run / "run.json").read_text())
    rep = json.loads(report.read_text()) if report.exists() else {}
    return {**c, "installed": bool(rep.get("installed")), "worked": bool(rep.get("first_run_worked")), "calls": rep.get("jev_calls_made"),
            "install_command": rep.get("install_command"), "quick_start": rep.get("quick_start"), "result": rep.get("result"),
            "beyond_readme": rep.get("beyond_readme") or [], "blocked_by": rep.get("blocked_by") or "", "seconds": meta["seconds"],
            "commit": (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else None}


def page(r: dict) -> str:
    extra = "".join(f"<li>{esc(x)}</li>" for x in r["beyond_readme"]) or "<li>None.</li>"
    outcome = '<span class="ok">ran</span>' if r["worked"] else '<span class="no">did not run</span>'
    return shell(f"{r['repo']}: first-run test", ("/best/typesafe-jev/", "TypeSafe Jev projects"), f"""<h1>{esc(r['repo'])}: first run, {DATE}</h1>
<p class="mute">Installed from its README in a throwaway sandbox by Claude Code (Claude Opus 5.5), with a Jev API key in the environment and nothing else: no GPU, no desktop, no other paid keys, no accounts.
The README's first example was run once. Repo commit {esc(r['commit'])}; {r['seconds']} seconds. <a href="{URL}RESULTS.md">All results</a> · <a href="{URL}in/prompt.txt">Task</a></p>
<p><b>Quick start: {outcome}.</b> Jev calls made: {esc(r['calls'])}.</p>
<table><tr><th>Install</th><td><code>{esc(r['install_command'])}</code></td></tr><tr><th>Quick start, as run</th><td><code>{esc(r['quick_start'])}</code></td></tr>
<tr><th>What came back</th><td>{esc(r['result'])}</td></tr><tr><th>What stopped it</th><td>{esc(r['blocked_by'] or 'Nothing.')}</td></tr></table>
<h2>Steps the README does not mention</h2><ul>{extra}</ul>
<h2>The session's closing message</h2><pre>{esc(final_message(OUT / key(r['repo']) / 'transcript.jsonl')[:4000])}</pre>""")


def card(r: dict) -> dict:
    base = {"stars": r["stars"], "sheet": key(r["repo"]) + ".html"}
    if r["repo"] in CANNOT_JUDGE:
        return {**base, "ran": False, "reason": CANNOT_JUDGE[r["repo"]][0], "reason_zh": CANNOT_JUDGE[r["repo"]][1]}
    needs = BLOCKED.get(r["repo"], ("A Jev key only", "只要 Jev 密钥"))
    ok = ["Ran", "跑通", "touch-ups"] if r["worked"] else ["Did not run", "没跑通", "substantial"]
    extra = len(r["beyond_readme"])
    cells = [ok, [needs[0], needs[1]], [str(extra), None, "num"], [str(r["calls"]), None, "num"], [f"{r['seconds']} s", f"{r['seconds']} 秒", "num"]]
    bits = [["its quick start ran on a Jev key alone", "只用一个 Jev 密钥就跑通了快速上手"] if r["worked"] else ["its quick start did not run on a Jev key alone", "只有 Jev 密钥跑不通它的快速上手"],
            *([[needs[0], needs[1]]] if not r["worked"] else []),
            [f"{extra} steps beyond the README", f"README 之外多做了 {extra} 步"], [f"{r['seconds']} s to install and run", f"安装加运行 {r['seconds']} 秒"]]
    return {**base, "ran": True, "cells": cells, "bits": bits}


def markdown(rows: list[dict]) -> str:
    out = [f"# Jev first-run test, {DATE}", "", "| Project | ★ | Quick start ran | Jev calls | Steps beyond README | Seconds | Stopped by |", "|---|---:|---|---:|---:|---:|---|"]
    out += [f"| {r['repo']} | {r['stars']} | {'yes' if r['worked'] else 'no'} | {r['calls']} | {len(r['beyond_readme'])} | {r['seconds']} | {r['blocked_by'][:160] or '-'} |" for r in rows]
    return "\n".join(out) + "\n"


def main() -> None:
    dest = PUBLIC / "jev"; dest.mkdir(parents=True, exist_ok=True)
    rows = sorted((row(c) for c in json.loads((HERE / "candidates.json").read_text())), key=lambda r: -r["stars"])
    for r in rows:
        (dest / (key(r["repo"]) + ".html")).write_text(page(r))
    (HERE / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    (HERE / "RESULTS.md").write_text(markdown(rows))
    judged = [r for r in rows if r["repo"] not in CANNOT_JUDGE]
    ran = sum(r["worked"] for r in judged)
    write_runs(SLUG, {
        "type": "table", "date": DATE, "dir": "/best-runs/jev/", "results": URL + "RESULTS.md",
        "title": ["TypeSafe Jev projects tested: does the quick start run", "实测对比：快速上手跑不跑得通"],
        "list_title": ["First-run test", "首次运行实测"],
        "intro": [f"On {DATE} we took {len(rows)} of these projects that call the hosted Jev API and gave each the same test in a throwaway sandbox, driven by Claude Code (Claude Opus 5.5): install it the way its README says, then run the README's first example once, with a Jev API key in the environment and nothing else (no GPU, no desktop, no other paid keys, no accounts). The projects do different jobs, so this does not compare how good they are. It answers one thing: can a new user get it running.",
                  f"{DATE} 我们挑了其中 {len(rows)} 个调用托管 Jev API 的项目，在用完即删的沙箱里由 Claude Code（Claude Opus 5.5）做同一个测试：按 README 的方式安装，再把 README 的第一个示例跑一次；环境里只有一个 Jev API 密钥，别的都没有（没有 GPU、没有桌面、没有别的付费密钥、没有账号）。这些项目做的事各不相同，所以这不是比谁更好，只回答一件事：新用户能不能跑起来。"],
        "finding": [f"{ran} of the {len(judged)} we could judge ran their quick start on a Jev key alone, each in about a minute and on a handful of Jev calls. The {len(judged) - ran} that did not each need something more: a second paid key, a signed-in Codex CLI, or a Cloudflare account. The most-starred project on the page is one of them.",
                    f"能评判的 {len(judged)} 个里，有 {ran} 个只靠一个 Jev 密钥就跑通了快速上手，每个大约一分钟、只用了几次 Jev 调用。没跑通的 {len(judged) - ran} 个各自还需要别的东西：第二个付费密钥、已登录的 Codex CLI，或者 Cloudflare 账号。本页星数最高的项目就在其中。"],
        "name_col": ["Project", "项目"],
        "columns": [["Quick start", "快速上手"], ["What it needs", "需要什么"], ["Steps beyond the README", "README 之外的步骤"], ["Jev calls", "Jev 调用次数"], ["Install and run", "安装加运行"]],
        "see": ["See the first run →", "看首次运行 →"], "evidence": ["The run", "运行记录"], "line_label": [f"Jev first-run test, {DATE}:", f"{DATE} 实测："],
        "not_run_label": ["Could not be judged in a sandbox", "沙箱里评不了"], "not_run_line": ["Our test could not judge it:", "这轮实测评不了："],
        "verdict": VERDICT, "runs": {r["repo"]: card(r) for r in rows}})
    print(markdown(rows)); print(f"{ran}/{len(judged)} ran")


if __name__ == "__main__":
    main()
