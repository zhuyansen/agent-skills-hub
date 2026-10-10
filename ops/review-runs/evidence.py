"""Results table, evidence pages and page data for the code-review test.

  python ops/review-runs/evidence.py      # after score_review.py

Writes results.json and RESULTS.md here, frontend/public/best-runs/review/<owner__repo>.html
(noindex: what the tool said about each of the 12 pull requests, with the judge's marks)
and the "code-review" entry of frontend/scripts/scenario-runs.json (type "table").
The control, Claude Code with no tool installed, found all eight planted defects with no
false alarm, so this set cannot rank the tools that match it; the page says so.
"""
import html
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
OUT = HERE / "out"
PUBLIC = ROOT / "frontend/public/best-runs/review"
RUNS_JSON = ROOT / "frontend/scripts/scenario-runs.json"
TRUTH = json.loads((HERE / "truth.json").read_text())
DATE = "2026-10-10"
CONTROL = "octocat/Hello-World"
REPO_URL = "https://github.com/zhuyansen/agent-skills-hub/blob/main/ops/review-runs/"
PLANTED = sum(bool(t["defect"]) for t in TRUTH.values())
OWN_MODEL_MENTIONS = 5     # a tool that brings its own LLM names the model all over its transcript
NOT_RUN = {
    "w1ckedxt/cynical-sally": ("It sends the diff to its own hosted service, which answered Service Unavailable.", "它把 diff 发到自己的托管服务，当时返回服务不可用。"),
    "HexmosTech/git-lrc": ("It sends the diff to a LiveReview server; there is none to review with locally.", "它把 diff 发给 LiveReview 服务器，本地没有可用的。"),
    "GGGODLIN/claude-pr-review": ("It reviews pull requests on Bitbucket through the Bitbucket API; it has no way to review a local branch.", "它通过 Bitbucket API 审 Bitbucket 上的 PR，审不了本地分支。"),
}
NOTES = {  # what a reader should know beside the numbers, from reading the run
    "Gentleman-Programming/gentleman-guardian-angel": ("It checks code against a rules file you write. The test repo had none, so the agent wrote one from gga's Python example; its 30 failures on clean pull requests are that file's docstring and type-hint rules, not false alarms.",
                                                       "它按你写的规则文件检查。测试库里没有，agent 照 gga 的 Python 示例写了一份；干净 PR 上的 30 条不通过是那份规则里的 docstring 和类型标注要求，不是误报。"),
    "alibaba/open-code-review": ("It skipped the two pull requests that only change tests, so the weakened test went unreviewed.", "它跳过了两个只改测试的 PR，被削弱的测试没有审到。"),
    "adamjgmiller/adamsreview": ("Hit the 30-minute limit with one pull request unfinished; it found the defect in all seven it finished.", "30 分钟到时还有一个 PR 没审完；审完的七个带缺陷的全部找到。"),
    "codexstar69/bug-hunter": ("Treats test files as context only, by design, so it does not report a weakened test.", "按设计把测试文件只当上下文，所以不会报被削弱的测试。"),
    "hyhmrright/brooks-lint": ("Reviews for design decay (coupling, complexity), not security: the logged card token and the weakened test scored 100/100.", "它审的是设计劣化（耦合、复杂度），不是安全：把卡号写进日志和削弱测试的 PR 都拿了 100/100。"),
    "getsentry/warden": ("Its verification pass threw out candidate findings on the pull requests it missed, the SQL injection among them.", "它的复核步骤把漏掉的那几个 PR 上的候选发现否掉了，包括 SQL 注入。"),
    "spencermarx/open-code-review": ("Several reviewer personas write one report: every defect is in it, among 7 findings per pull request.", "多个审查角色合写一份报告：缺陷都在里面，但每个 PR 平均有 7 条发现。"),
    "kenn-io/roborev": ("Runs in the background on every commit; here it reviewed with gpt-6-astra through OpenCode and still found all eight.", "在后台对每次提交自动审查；这里通过 OpenCode 用 gpt-6-astra 审，仍然八个全中。"),
}
GGA = "Gentleman-Programming/gentleman-guardian-angel"
VERDICT = {
    "title": ["Which one to install", "到底装哪个"],
    "rule": [f"Listed by defects found, then time. This set does not rank the tools at the top: Claude Code with no tool installed found all {PLANTED} planted defects in a minute with no false alarm, and six tools did the same. Tools that bring their own model reviewed with gpt-6-astra, the skills with Claude Opus 5.5, so a gap between those two groups may be the model.",
             f"按找到的缺陷数、再按耗时排列。这套题分不出头部名次：不装任何工具的 Claude Code 一分钟找全 {PLANTED} 个缺陷、零误报，有 6 个工具结果相同。自带模型的工具用 gpt-6-astra 审，skill 用 Claude Opus 5.5 审，两组之间的差距可能来自模型。"],
    "picks": [
        {"repo": "awesome-skills/code-review-skill", "role": ["If you want a review skill at all", "只想加一个审查 skill"],
         "why": ["Found all eight planted defects with no false alarm on the clean pull requests, in about a minute and under two findings per pull request. That equals Claude Code with nothing installed: it adds a written checklist and a fixed report format, not detection.",
                 "八个埋入的缺陷全部找到，干净 PR 上零误报，约一分钟，每个 PR 不到两条发现。这和不装任何东西的 Claude Code 一样：它带来的是成文的检查清单和固定的报告格式，不是更强的检出。"]},
        {"repo": "kenn-io/roborev", "role": ["If you want every commit reviewed without asking", "想让每次提交自动被审"],
         "why": ["It reviews in the background as you commit, and it found all eight even with a different model (gpt-6-astra) doing the reading, with under one finding per pull request. Slower: 13 minutes for the twelve.",
                 "你提交时它在后台审；这次换了一个模型（gpt-6-astra）来读，仍然八个全中，每个 PR 不到一条发现。比较慢：12 个 PR 用了 13 分钟。"]},
        {"repo": "adamjgmiller/adamsreview", "role": ["If you would rather wait than read noise", "宁可多等也不想看噪音"],
         "why": ["The quietest reviewer that missed nothing it finished: 0.5 findings per pull request, the defect found in all seven it completed. It ran out of our 30 minutes on the twelfth.",
                 "审完的部分一个没漏，也是最安静的：每个 PR 0.5 条发现，完成的七个带缺陷 PR 全部找到。我们给的 30 分钟内差一个没审完。"]},
    ],
    "avoid_label": ["Know what these do not look for:", "先弄清这几个不查什么："],
    "avoid": [
        {"repo": "hyhmrright/brooks-lint", "why": ["design decay only; it passed a logged card token at 100/100", "只查设计劣化；把卡号写进日志的 PR 给了 100/100"]},
        {"repo": "codexstar69/bug-hunter", "why": ["ignores test files, so a weakened test goes through", "不看测试文件，被削弱的测试会放过"]},
    ],
    "caveat": ["Whichever you pick, the hardest defect was not in the code: four of 13 reviewers passed a pull request that quietly weakened a test's assertion. Read test changes yourself.",
               "不管选哪个，最难抓的缺陷不在业务代码里：13 个里有 4 个放过了悄悄削弱测试断言的 PR。测试的改动要自己看。"],
}
STYLE = """:root{--bg:#fff;--fg:#1f2328;--mute:#59636e;--line:#d0d7de;--card:#f6f8fa;--ok:#1a7f37;--no:#cf222e}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mute:#9198a1;--line:#30363d;--card:#161b22;--ok:#3fb950;--no:#f85149}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,'PingFang SC',sans-serif}
main{max-width:960px;margin:0 auto;padding:24px 16px 48px}a{color:#0969da}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px}.mute{color:var(--mute);font-size:13px}.ok{color:var(--ok);font-weight:600}.no{color:var(--no);font-weight:600}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}
th{background:var(--card)}pre{white-space:pre-wrap;word-wrap:break-word;margin:6px 0 0;padding:12px;border:1px solid var(--line);
border-radius:8px;background:var(--card);font:13px/1.5 ui-monospace,Menlo,monospace;max-height:420px;overflow:auto}summary{cursor:pointer}"""


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def key(repo: str) -> str:
    return repo.replace("/", "__")


def final_message(run: Path) -> str:
    last = ""
    for line in (run / "transcript.jsonl").read_text(errors="ignore").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "result":
            last = e.get("result") or ""
    return last


def row(c: dict) -> dict:
    run = OUT / key(c["repo"])
    score = json.loads((run / "score.json").read_text()) if (run / "score.json").exists() else None
    if not score or not score["reviewed"]:
        return {**c, "ran": False, "reason": NOT_RUN.get(c["repo"], ("did not run", "未能运行"))[0], "reason_zh": NOT_RUN.get(c["repo"], ("", "未能运行"))[1]}
    own = (run / "transcript.jsonl").read_text(errors="ignore").count("gpt-6-astra") > OWN_MODEL_MENTIONS
    missed = [b for b, v in score["branches"].items() if v["planted"] and not v["found"]]
    return {**c, "ran": True, "found": score["found"], "planted_reviewed": score["planted_reviewed"], "reviewed": score["reviewed"],
            "false_alarms": score["false_alarms"], "per_pr": score["findings_per_pr"], "minutes": max(1, round(score["run"]["seconds"] / 60)),
            "model": "gpt-6-astra" if own else "Claude Opus 5.5", "missed": missed,
            "commit": (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else None}


def page(r: dict) -> str:
    run = OUT / key(r["repo"])
    score = json.loads((run / "score.json").read_text())
    rows = []
    for b, t in TRUTH.items():
        v = score["branches"].get(b)
        review = (run / "deliverables" / f"{b}.md")
        if not v:
            mark = '<span class="mute">not reviewed</span>'
        elif v["planted"]:
            mark = '<span class="ok">found</span>' if v["found"] else '<span class="no">missed</span>'
        else:
            mark = '<span class="ok">no blocking finding</span>' if not v["blocking"] else f'<span class="no">{v["blocking"]} blocking</span>'
        text = f"<details><summary>The review</summary><pre>{esc(review.read_text()[:6000])}</pre></details>" if review.exists() else ""
        rows.append(f"<tr><td><b>{esc(b)}</b><br><span class='mute'>{esc(t['defect'] or 'Clean: nothing planted')}</span>{text}</td><td>{mark}</td></tr>")
    note = f"<p>{esc(NOTES[r['repo']][0])}</p>" if r["repo"] in NOTES else ""
    back = "" if r["repo"] == CONTROL else f" Repo commit {esc(r.get('commit'))}."
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>{esc(r['name'])}: code review test</title><style>{STYLE}</style></head><body><main>
<p class="mute"><a href="/best/code-review/">← AI code review tools</a></p>
<h1>{esc(r['name'])}: test run, {DATE}</h1>
<p class="mute">Twelve pull requests against a small Python order service: eight with one planted defect each, four clean. Claude Code (Claude Opus 5.5) installed the tool in a throwaway sandbox and
reported what the tool said; the reviewing itself was done by {esc(r['model'])}. A judge (gpt-6-astra, three passes) marked each review against the planted defect.{back}
<a href="{REPO_URL}RESULTS.md">All results</a> · <a href="{REPO_URL}make_fixture.py">The pull requests</a> · <a href="{REPO_URL}in/prompt.txt">Task</a></p>
<p><b>Found {r['found']} of {r['planted_reviewed']} planted defects</b>; {r['per_pr']} findings per pull request; {r['minutes']} min for the set.</p>{note}
<h2>Pull request by pull request</h2><table><tr><th>Pull request</th><th>Result</th></tr>{''.join(rows)}</table>
<h2>How it was run (the session's closing message)</h2><pre>{esc(final_message(run)[:5000])}</pre>
</main></body></html>"""


def card(r: dict) -> dict:
    base = {"stars": r["stars"], "sheet": key(r["repo"]) + ".html"}
    if not r["ran"]:
        return {**base, "ran": False, "reason": r["reason"], "reason_zh": r["reason_zh"]}
    full = r["found"] == r["planted_reviewed"]
    found = [f"{r['found']}/{r['planted_reviewed']}", None, "touch-ups" if full else "substantial" if r["found"] <= PLANTED // 2 + 1 else ""]
    alarms = ["see note", "见说明"] if r["repo"] == GGA else [str(r["false_alarms"]), None]
    bits = [[f"found {r['found']} of {r['planted_reviewed']} planted defects", f"找到 {r['planted_reviewed']} 个埋入缺陷中的 {r['found']} 个"],
            None if r["repo"] == GGA else [f"{r['false_alarms']} false alarms on 4 clean pull requests", f"4 个干净 PR 上误报 {r['false_alarms']} 条"],
            [f"{r['per_pr']} findings per pull request", f"每个 PR {r['per_pr']} 条发现"], [f"{r['minutes']} min", f"{r['minutes']} 分钟"],
            [f"reviewed by {r['model']}", f"由 {r['model']} 审查"]]
    out = {**base, "ran": True, "cells": [found, alarms, [str(r["per_pr"]), None, "num"], [f"{r['minutes']} min", f"{r['minutes']} 分钟", "num"], [r["model"], None]],
           "bits": [b for b in bits if b]}
    if r["repo"] in NOTES:
        out.update(note=NOTES[r["repo"]][0], note_zh=NOTES[r["repo"]][1])
    return out


def markdown(control: dict, rows: list[dict]) -> str:
    out = [f"# Code review test, {DATE}", "", f"12 pull requests, {PLANTED} with a planted defect, 4 clean. See make_fixture.py and score_review.py.", "",
           "| Tool | ★ | Found | False alarms on clean | Findings per PR | Min | Reviewed by | Missed |", "|---|---:|---:|---:|---:|---:|---|---|"]
    for r in [control, *[r for r in rows if r["ran"]]]:
        name = "Control: Claude Code, no tool" if r["repo"] == CONTROL else r["repo"]
        alarms = "n/a (rules file written for the test)" if r["repo"] == GGA else r["false_alarms"]
        out.append(f"| {name} | {r['stars'] or '-'} | {r['found']}/{r['planted_reviewed']} | {alarms} | {r['per_pr']} | {r['minutes']} | {r['model']} | {', '.join(b[:5] for b in r['missed']) or '-'} |")
    out += ["", "Could not run:", ""] + [f"- {r['repo']}: {r['reason']}" for r in rows if not r["ran"]]
    out += ["", "Notes:", ""] + [f"- {k}: {v[0]}" for k, v in NOTES.items()]
    return "\n".join(out) + "\n"


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    cands = json.loads((HERE / "candidates.json").read_text())
    control = row({"repo": CONTROL, "kind": "control", "stars": 0, "grade": None})
    rows = sorted((row(c) for c in cands), key=lambda r: (not r["ran"], -(r.get("found", 0) / max(r.get("planted_reviewed", 1), 1)), r.get("minutes", 0)))
    for r in [control, *[r for r in rows if r["ran"]]]:
        (PUBLIC / (key(r["repo"]) + ".html")).write_text(page({**r, "name": "Control: Claude Code with no review tool" if r["repo"] == CONTROL else r["repo"]}))
    (HERE / "results.json").write_text(json.dumps([control, *rows], indent=1, ensure_ascii=False))
    (HERE / "RESULTS.md").write_text(markdown(control, rows))
    ran = [r for r in rows if r["ran"]]
    level = sum(r["found"] == r["planted_reviewed"] and r["reviewed"] == len(TRUTH) and not r["false_alarms"] for r in ran)
    weak = sum("pr-12-speed-up-tests" in r["missed"] for r in ran)
    runs = json.loads(RUNS_JSON.read_text())
    runs["code-review"] = {
        "type": "table", "date": DATE, "dir": "/best-runs/review/", "results": REPO_URL + "RESULTS.md",
        "title": ["Claude Code review tools, tested on the same 12 pull requests", "实测对比：同样的 12 个 PR"],
        "intro": [f"On {DATE} we ran {len(rows)} of these tools and {len(ran)} ran. Each reviewed the same 12 pull requests against a small Python service in a throwaway sandbox: {PLANTED} carry one planted defect (an off-by-one, an SQL injection, a card token in the logs, a missing permission check, a retry that never ends, a swallowed error, an inverted condition, a weakened test) and 4 are clean. Two numbers per tool, as in SWR-Bench: defects found, and blocking findings on the clean ones. A judge (gpt-6-astra, three passes) marked each review. Claude Code with no tool installed did the same job as a control.",
                  f"{DATE} 我们实跑了其中 {len(rows)} 个，跑成 {len(ran)} 个。每个在用完即删的沙箱里审同样的 12 个 PR（一个小型 Python 服务）：{PLANTED} 个各埋了一个缺陷（差一错误、SQL 注入、卡号写进日志、漏掉权限检查、永不结束的重试、吞掉的异常、写反的条件、被削弱的测试），4 个是干净的。按 SWR-Bench 的做法每个工具给两个数：找到几个缺陷、在干净 PR 上报了几条阻塞问题。评审是 gpt-6-astra，三遍取多数。不装任何工具的 Claude Code 做了同样的事，作为对照。"],
        "finding": [f"No tool beat the control. Claude Code with nothing installed found all {PLANTED} defects in about a minute with no false alarm ({control['per_pr']} findings per pull request); {level} tools matched it and none did better. What separates the tools is noise (0.5 to 7.2 findings per pull request) and time (1 to 30 minutes). The defect missed most was the weakened test: {weak} of {len(ran)} let it through.",
                    f"没有工具超过对照组。不装任何东西的 Claude Code 约一分钟找全 {PLANTED} 个缺陷、零误报（每个 PR {control['per_pr']} 条发现）；{level} 个工具与它持平，没有更好的。工具之间真正的差别是噪音（每个 PR 0.5 到 7.2 条发现）和耗时（1 到 30 分钟）。漏得最多的是被削弱的测试：{len(ran)} 个里有 {weak} 个放过了。"],
        "name_col": ["Tool", "工具"],
        "columns": [[f"Defects found (of {PLANTED})", f"找到缺陷（共 {PLANTED} 个）"], ["False alarms on 4 clean PRs", "4 个干净 PR 上的误报"], ["Findings per PR", "每个 PR 发现数"], ["Time", "耗时"], ["Reviewed by", "审查模型"]],
        "line_label": [f"Claude Code review test, {DATE}:", f"{DATE} 实测："], "see": ["See every review →", "看每个 PR 的审查 →"], "evidence": ["The reviews", "审查原文"],
        "control": {"sheet": key(CONTROL) + ".html"},
        "verdict": VERDICT, "runs": {r["repo"]: card(r) for r in rows}}
    RUNS_JSON.write_text(json.dumps(runs, indent=1, ensure_ascii=False) + "\n")
    print(markdown(control, rows))
    print(f"level with control: {level}; weakened test missed by {weak} of {len(ran)}")


if __name__ == "__main__":
    main()
