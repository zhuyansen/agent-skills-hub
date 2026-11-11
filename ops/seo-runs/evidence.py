"""Results table, evidence pages and page data for the SEO tools test.

  python ops/seo-runs/evidence.py      # after score_seo.py (and marks.json, the hand check of false claims)

Writes results.json and RESULTS.md here, frontend/public/best-runs/seo/<owner__repo>.html (noindex: what the
tool reported, defect by defect, with the judge's marks and the false claims) and the "seo-tools" entry of
frontend/scripts/scenario-runs.json (type "table"), which the page's opening answer and test section read.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runs_common import PUBLIC as PUBLIC_ROOT, REPO_URL as REPO_ROOT, esc, final_message, key, shell, update_method, write_runs   # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "out"
# The public rerun (public/, 2026-11-12): the same site at https://lumentea-test.vercel.app/, for the tools that refuse
# private addresses, plus a control there. Their rows come from public/out.
PUBLIC_OUT = HERE / "public/out"
PUBLIC_DATE = "2026-11-12"
PUBLIC_HOST = "https://lumentea-test.vercel.app/"
RERUN = ("Bhanunamikaze/Agentic-SEO-Skill", "Auriti-Labs/geo-optimizer-skill", "JeffLi1993/seo-audit-skill")
PUBLIC = PUBLIC_ROOT / "seo"
REPO_URL = REPO_ROOT + "seo-runs/"
TRUTH = json.loads((HERE / "truth.json").read_text())
PLANTED = len(TRUTH["defects"])
CONTROL = "control"
DATE = "2026-11-11"
BACK = ("/best/seo-tools/", "Claude SEO skills & SEO MCP servers")
# Read from each run by hand: why a tool produced no audit, and what a reader should know beside the numbers.
NOT_RUN = {
    "JeffLi1993/seo-audit-skill": ("It refuses private addresses, so it ran on the public copy, where its site audit stopped: it requires a Google PageSpeed Insights API key, which we did not give it.",
                                   "它拒绝内网地址，所以改在公网副本上跑；在那里它的站点审计停了：必须有 Google PageSpeed Insights API key，我们没给。"),
    "every-app/open-seo": ("Its audit runs on OpenSEO's servers and needs an OpenSEO account sign-in, so it cannot audit a site that is not on the public internet.",
                           "它的审计在 OpenSEO 自己的服务器上跑，还要登录 OpenSEO 账号，所以审不了不在公网上的站点。"),
}
ROBOTS_NOTE = "It obeys robots.txt, so it did not read the two blog pages the test blocks and missed the four problems on them; it did report the block."
ROBOTS_NOTE_ZH = "它遵守 robots.txt，没有读测试里被屏蔽的两个博客页，漏掉了那里的四个问题；屏蔽本身它报了。"
RERUN_NOTE = (f"It refuses private addresses, so it ran on {PUBLIC_DATE} on a public copy of the same site; Claude Code with no tool found all 16 there too.",
              f"它拒绝内网地址，所以 {PUBLIC_DATE} 改在同一个站的公网副本上跑；不装工具的 Claude Code 在那里也找全了 16 个。")
NOTES = {
    "Bhanunamikaze/Agentic-SEO-Skill": (RERUN_NOTE[0] + " It took the /shop/ redirect for a duplicate of /teas/ and counted no product links on /teas/, which has two.",
                                        RERUN_NOTE[1] + "它把 /shop/ 重定向当成 /teas/ 的重复页，还说 /teas/ 上没有商品链接，其实有两个。"),
    "Auriti-Labs/geo-optimizer-skill": (RERUN_NOTE[0] + " A GEO scorer page by page: it missed the robots.txt block and the redirect chain, reported 0 broken links on the article that has one, and said the contact page has no contact details.",
                                        RERUN_NOTE[1] + "它按页给 GEO 打分：漏了 robots.txt 屏蔽和重定向链，说有断链的那篇文章断链为 0，还说联系页没有联系方式。"),
    "aaron-he-zhu/aaron-marketing-skills": ("A 120-skill marketing plugin; its site-audit route ran. Its fetch scripts refuse private addresses unless their built-in allow-private option is on, which the run turned on.",
                                            "一个含 120 个 skill 的营销插件，跑的是它的站点审计流程。它的抓取脚本默认拒绝内网地址，要打开脚本自带的允许内网选项，这次运行打开了。"),
    "squirrelscan/squirrelscan": ("A crawler CLI with 310+ rules, run in its offline mode: its cloud service cannot reach a private site.",
                                  "一个带 310 多条规则的爬虫命令行工具，用的是离线模式：它的云服务连不到内网站点。"),
    "coreyhaines31/marketingskills": ("Its seo-audit skill is a written checklist: Claude Code followed it with curl. It missed the noindex sent in an HTTP header.",
                                      "它的 seo-audit skill 是一份成文的检查清单，由 Claude Code 照着用 curl 检查。漏掉的是写在 HTTP 响应头里的 noindex。"),
    "AgriciDaniel/claude-seo": (ROBOTS_NOTE + " Its summary then said every page has a viewport tag and that titles and descriptions are unique, which the blog pages contradict. Ten specialist agents, a score of 61/100.",
                                ROBOTS_NOTE_ZH + "它的总结却说每页都有 viewport、标题和描述都不重复，而博客页正好违反这两条。共 10 个专项 agent，给了 61/100。"),
    "zubair-trabzada/geo-seo-claude": (ROBOTS_NOTE + " It also said the guides have no author, byline or Article schema; the blog post has all three, but it had not read it.",
                                       ROBOTS_NOTE_ZH + "它还说指南类内容没有作者、署名和 Article 结构化数据；博客文章其实三样都有，只是它没读。"),
    "iannuttall/seo": (ROBOTS_NOTE + " Its MCP crawl failed with a parameter error (Unrecognized key: \"saveReport\"), so the run used its CLI, which needed no account.",
                       ROBOTS_NOTE_ZH + "它的 MCP 抓取报参数错误（Unrecognized key: \"saveReport\"），所以改用它的命令行版本，不需要账号。"),
    "tigerless-labs/seo-ops": ("30 fixed checks. It passed \"robots.txt allows AI crawlers\" and \"redirect hops ≤1\" although the blog is blocked for every crawler and the main menu link takes two hops.",
                               "30 项固定检查。它判「robots.txt 允许 AI 爬虫」和「重定向不超过 1 跳」通过，但博客对所有爬虫都被屏蔽，主菜单链接要跳两次。"),
    "seo-skills/seo-audit-skill": ("SEOmator's CLI. It took the /shop/ redirect for a second page and reported a duplicate title, H1 and content with /teas/, and read the home page's JSON-LD array as having no @type. It missed the robots.txt block.",
                                   "SEOmator 的命令行工具。它把 /shop/ 这个重定向当成另一个页面，报它和 /teas/ 标题、H1、内容重复；还把首页的 JSON-LD 数组读成没有 @type。robots.txt 屏蔽博客它漏了。"),
    "addyosmani/agentic-seo": ("It checks files for AI agents at the site root (llms.txt, robots rules for AI crawlers); it does not crawl pages, so page problems are outside what it looks at.",
                               "它检查站点根目录下给 AI agent 看的文件（llms.txt、针对 AI 爬虫的 robots 规则），不抓页面，页面上的问题不在它的检查范围内。"),
}
VERDICT = {
    "title": ["Which one to install", "到底装哪个"],
    "rule": [f"Ranked by planted problems found, then false claims, then time. One run per tool, on a test site we built. This set does not rank tools above the control: Claude Code with nothing installed found all {PLANTED} in two minutes with no false claim.",
             f"排名规则：先看找到几个埋入问题，再看说错几处，最后看耗时。每个工具跑一次，测试站是我们自己搭的。这套题排不出比对照组更好的工具：什么都不装的 Claude Code 两分钟找全 {PLANTED} 个、没说错一处。"],
    "picks": [
        {"repo": "aaron-he-zhu/aaron-marketing-skills", "role": ["If you want an SEO audit skill at all", "只想装一个 SEO 审计 skill"],
         "why": [f"The only tool to find all {PLANTED} planted problems, the X-Robots-Tag header and the orphan page among them, with no false claim. That equals Claude Code with nothing installed, in five minutes instead of two; what it adds is a fixed audit route and a prioritised report.",
                 f"唯一一个找全 {PLANTED} 个埋入问题的工具，包括 HTTP 头里的 noindex 和孤立页，没说错一处。这和什么都不装的 Claude Code 打平，用时 5 分钟而不是 2 分钟；它多给的是固定的审计流程和分好优先级的报告。"]},
        {"repo": "squirrelscan/squirrelscan", "role": ["If you want a crawler you can rerun", "想要能反复跑的爬虫"],
         "why": [f"Found 15 of {PLANTED} with no false claim in about a minute and a half, from a local CLI with 310+ fixed rules, so the next run checks the same things. It missed the hreflang pointing at a 404.",
                 f"约一分半钟找到 {PLANTED} 个里的 15 个，没说错一处；是本地命令行工具，310 多条固定规则，下次跑查的还是同样的东西。漏掉的是指向 404 的 hreflang。"]},
        {"repo": "coreyhaines31/marketingskills", "role": ["If you want the lightest install", "想装得最轻"],
         "why": [f"Its seo-audit skill is a checklist that Claude Code follows with curl: 15 of {PLANTED} with no false claim in about a minute. It missed the noindex sent in an HTTP header.",
                 f"它的 seo-audit skill 是一份清单，由 Claude Code 照着用 curl 检查：约一分钟找到 {PLANTED} 个里的 15 个，没说错一处。漏掉的是写在 HTTP 头里的 noindex。"]},
    ],
    "avoid_label": ["Check these reports against the pages:", "这几个的报告要对照页面核实："],
    "avoid": [
        {"repo": "seo-skills/seo-audit-skill", "why": ["6 false claims among 64 items, such as a redirect taken for a duplicate page", "64 条里说错 6 处，例如把重定向当成重复页面"]},
        {"repo": "tigerless-labs/seo-ops", "why": ["passed robots.txt and redirect checks the site fails", "robots.txt 和重定向两项检查判了通过，其实测试站都不合格"]},
        {"repo": "AgriciDaniel/claude-seo", "why": ["skipped the robots-blocked blog, then said every page has a viewport tag", "跳过了被 robots 屏蔽的博客，又说每页都有 viewport"]},
    ],
    "caveat": [f"Whichever you pick: Claude Code with nothing installed found all {PLANTED} in two minutes. Before you point a tool at a staging site, check that it can reach one: 3 of 13 refuse private addresses outright.",
               f"不管选哪个：什么都不装的 Claude Code 两分钟就找全了 {PLANTED} 个。拿工具审预发布站之前，先确认它连得上：13 个里有 3 个一律拒绝内网地址。"],
}
TEXT = {
    "title": [f"SEO skills and MCP servers tested: one test site, {PLANTED} planted problems", f"实测对比：同一个测试站，埋了 {PLANTED} 个 SEO 问题"],
    "intro": [f"On {DATE} we ran 13 of these tools and 11 produced an audit. Each audited the same test shop, nine pages served inside a throwaway sandbox (for the three tools that refuse private addresses, a public copy on {PUBLIC_DATE}), with {PLANTED} planted problems: robots.txt blocking the blog, a noindex in a meta tag and another in an HTTP header, a canonical pointing at the home page, a missing title, duplicate titles and descriptions, a broken link, a 404 in the sitemap, invalid JSON-LD, a missing alt, a missing H1, a missing viewport, a two-hop redirect on the main menu, an orphan page and an hreflang to a 404. Claude Code (Claude Opus 5.5) installed each tool from its README and ran its audit; a judge (Claude Opus 5.5, three passes, given the whole site) marked each report, and every false claim was checked by hand. Claude Code with no tool did the same job as a control.",
              f"{DATE} 我们实跑了其中 13 个，11 个交出了审计报告。每个审同一个测试网店：9 个页面，放在用完即删的沙箱里（拒绝内网地址的 3 个工具在 {PUBLIC_DATE} 改审公网副本），埋了 {PLANTED} 个问题：robots.txt 屏蔽整个博客、一个 meta 里的 noindex 和一个 HTTP 头里的 noindex、canonical 指向首页、缺 title、标题和描述重复、断链、sitemap 里有 404、JSON-LD 格式错误、图片缺 alt、缺 H1、缺 viewport、主菜单链接两跳重定向、孤立页、hreflang 指向 404。由 Claude Code（Claude Opus 5.5）按各自 README 安装并跑审计；评审是 Claude Opus 5.5，拿到整个站点，三遍取多数，每一处说错都人工核对过。不装任何工具的 Claude Code 做了同样的事，作为对照。"],
    "name_col": ["Tool", "工具"],
    "columns": [[f"Planted problems found (of {PLANTED})", f"找到埋入问题（共 {PLANTED} 个）"], ["False claims", "说错几处"], ["Problems raised", "报出问题数"], ["Time", "耗时"]],
    "line_label": [f"SEO audit test, {DATE}:", f"{DATE} 实测："],
    "see": ["See every report →", "看每份报告 →"], "evidence": ["The reports", "报告原文"],
}


def load(run: Path, name: str) -> dict | None:
    f = run / name
    return json.loads(f.read_text()) if f.exists() else None


def setup_seconds(run: Path) -> float:
    """How long the install session took (setup.jsonl), so the time shown is the audit's own."""
    f = run / "setup.jsonl"
    if not f.exists():
        return 0
    total = 0
    for line in f.read_text(errors="ignore").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "result":
            total += e.get("duration_ms", 0) / 1000
    return total


def row_at(c: dict, run: Path) -> dict:
    """A row read from a given run folder (the public copy's control)."""
    score = load(run, "score.json")
    meta = load(run, "run.json") or {}
    return {**c, "ran": True, "found": score["found"], "problems": score["problems"], "false": len(score["false_claims"]),
            "minutes": max(1, round(meta.get("seconds", 0) / 60)), "missed": [d for d, v in score["defects"].items() if not v["hit"]], "commit": None}


def run_dir(repo: str) -> Path:
    return (PUBLIC_OUT if repo in RERUN else OUT) / key(repo)


def row(c: dict) -> dict:
    run = run_dir(c["repo"])
    score = load(run, "score.json")
    meta = load(run, "run.json") or {}
    minutes = max(1, round((meta.get("seconds", 0) - setup_seconds(run)) / 60))
    commit = (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else None
    if c["repo"] in NOT_RUN or not score or not score.get("reported"):
        en, zh = NOT_RUN.get(c["repo"], ("It produced no audit in the time given.", "限定时间内没有交出审计报告。"))
        return {**c, "ran": False, "reason": en, "reason_zh": zh, "minutes": minutes, "commit": commit}
    missed = [d for d, v in score["defects"].items() if not v["hit"]]
    return {**c, "ran": True, "found": score["found"], "problems": score["problems"], "false": len(score["false_claims"]),
            "minutes": minutes, "missed": missed, "commit": commit}


def defect_rows(score: dict) -> str:
    rows = []
    for d in TRUTH["defects"]:
        v = score["defects"][d["id"]]
        mark = '<span class="ok">found</span>' if v["hit"] else '<span class="no">missed</span>'
        quote = f"<br><span class='mute'>“{esc(v['quote'][:300])}”</span>" if v["hit"] and v.get("quote") else ""
        rows.append(f"<tr><td><b>{d['id']}</b> {esc(d['where'])}<br>{esc(d['defect'])}{quote}</td><td>{mark}</td></tr>")
    return "".join(rows)


def report_files(run: Path) -> str:
    deliver = run / "deliverables"
    if not deliver.exists():
        return "<p class='mute'>No report file.</p>"
    out = []
    for f in sorted(deliver.rglob("*"), key=lambda f: (f.name != "report.md", str(f))):
        if f.is_file() and f.suffix in (".md", ".txt", ".json", ".csv") and f.stat().st_size < 400_000:
            out.append(f"<details{' open' if f.name == 'report.md' else ''}><summary>{esc(f.relative_to(deliver))}</summary>"
                       f"<pre>{esc(f.read_text(errors='ignore')[:20000])}</pre></details>")
    return "".join(out) or "<p class='mute'>No report file.</p>"


def sheet(r: dict, run: Path | None = None) -> str:
    run = run or run_dir(r["repo"])
    public = run.parent == PUBLIC_OUT
    name = "Control: Claude Code with no SEO tool" if r["repo"] == CONTROL else r["repo"]
    name += " (public copy)" if public and r["repo"] == CONTROL else ""
    where = (f"a public copy of the test shop at {PUBLIC_HOST} ({PUBLIC_DATE}), the same pages as the sandbox one"
             if public else "a 9-page test shop at http://lumentea.test/, served inside a throwaway sandbox")
    date = PUBLIC_DATE if public else DATE
    intro = (f"<p class='mute'>The same task for every tool: audit {where}, "
             f"with {PLANTED} planted SEO problems. Claude Code (Claude Opus 5.5) installed the tool from its README and ran its audit; "
             f"a judge (Claude Opus 5.5, three passes, given the whole site) marked the report, and every false claim was checked by hand."
             f"{' Repo commit ' + esc(r['commit']) + '.' if r.get('commit') else ''} "
             f"<a href='{REPO_URL}RESULTS.md'>All results</a> · <a href='{REPO_URL}make_fixture.py'>The test site</a> · "
             f"<a href='{REPO_URL}in/prompt.txt'>Task</a></p>")
    note = f"<p>{esc(NOTES[r['repo']][0])}</p>" if r["repo"] in NOTES else ""
    if not r["ran"]:
        body = f"<h1>{esc(name)}: test run, {date}</h1>{intro}<p><b>No audit:</b> {esc(r['reason'])}</p>{note}"
        return shell(f"{name}: SEO audit test", BACK, body + f"<h2>The session's closing message</h2><pre>{esc(final_message(run / 'transcript.jsonl')[:5000])}</pre>")
    score = load(run, "score.json")
    false = "".join(f"<li>{esc(c.get('claim'))}<br><span class='mute'>{esc(c.get('why'))}</span></li>" for c in score["false_claims"]) or "<li>None.</li>"
    body = f"""<h1>{esc(name)}: test run, {date}</h1>{intro}
<p><b>Found {r['found']} of {PLANTED} planted problems</b>; {r['false']} false claim{'s' if r['false'] != 1 else ''} about the site; {r['problems']} problems raised in all; {r['minutes']} min.</p>{note}
<h2>The planted problems</h2><table><tr><th>Planted problem</th><th>Result</th></tr>{defect_rows(score)}</table>
<h2>False claims (checked by hand)</h2><ul>{false}</ul>
<h2>The report</h2>{report_files(run)}
<h2>The session's closing message</h2><pre>{esc(final_message(run / 'transcript.jsonl')[:5000])}</pre>"""
    return shell(f"{name}: SEO audit test", BACK, body)


def card(r: dict) -> dict:
    base = {"stars": r["stars"], "sheet": key(r["repo"]) + ".html"}
    if not r["ran"]:
        return {**base, "ran": False, "reason": r["reason"], "reason_zh": r["reason_zh"]}
    tone = "touch-ups" if r["found"] == PLANTED else "substantial" if r["found"] <= PLANTED // 2 else ""
    out = {**base, "ran": True,
           "cells": [[f"{r['found']}/{PLANTED}", None, tone], [str(r["false"]), None, "num"], [str(r["problems"]), None, "num"],
                     [f"{r['minutes']} min", f"{r['minutes']} 分钟", "num"]],
           "bits": [[f"found {r['found']} of {PLANTED} planted problems", f"找到 {PLANTED} 个埋入问题中的 {r['found']} 个"],
                    [f"{r['false']} false claim{'s' if r['false'] != 1 else ''} about the site", f"说错 {r['false']} 处"],
                    [f"{r['problems']} problems raised", f"共报 {r['problems']} 条"], [f"{r['minutes']} min", f"{r['minutes']} 分钟"]]}
    if r["repo"] in NOTES:
        out.update(note=NOTES[r["repo"]][0], note_zh=NOTES[r["repo"]][1])
    return out


def markdown(control: dict, rows: list[dict]) -> str:
    out = [f"# SEO tools test, {DATE}", "",
           f"One 9-page test shop (http://lumentea.test/, served in the sandbox) with {PLANTED} planted SEO problems; see make_fixture.py, truth.json and score_seo.py.", "",
           "| Tool | Kind | ★ | Found | False claims | Problems raised | Min | Missed |", "|---|---|---:|---:|---:|---:|---:|---|"]
    for r in [control, *[r for r in rows if r["ran"]]]:
        name = "Control: Claude Code, no tool" if r["repo"] == CONTROL else r["repo"]
        out.append(f"| {name} | {r.get('kind', '-')} | {r.get('stars') or '-'} | {r['found']}/{PLANTED} | {r['false']} | {r['problems']} | {r['minutes']} | {', '.join(r['missed']) or '-'} |")
    out += ["", "No audit:", ""] + [f"- {r['repo']}: {r['reason']}" for r in rows if not r["ran"]]
    if NOTES:
        out += ["", "Notes:", ""] + [f"- {k}: {v[0]}" for k, v in NOTES.items()]
    return "\n".join(out) + "\n"


def public_md(c: dict) -> str:
    return (f"\n## Public copy, {PUBLIC_DATE}\n\nThe three tools that refuse private addresses ran again on {PUBLIC_HOST} (Vercel; public/site, "
            f"public/run_all.sh): the same pages with that host in their URLs, and the same 301 chain, X-Robots-Tag header and 404s "
            f"(vercel.json). Their rows above come from that run. The control ran there too: found {c['found']}/{PLANTED}, "
            f"{c['false']} false claim (a summary line calling the article's title fine; it had reported the missing title), "
            f"{c['problems']} problems, {c['minutes']} min. The copy has no noindex added: a site-wide noindex would have hidden "
            f"the two planted ones (D2, D13), so it stays up only for the test and is then to be taken down.\n")


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    cands = json.loads((HERE / "candidates.json").read_text())
    control = row({"repo": CONTROL, "kind": "control", "stars": 0})
    rows = sorted((row(c) for c in cands), key=lambda r: (not r["ran"], -r.get("found", 0), r.get("false", 0), r.get("minutes", 0)))
    for r in [control, *rows]:
        (PUBLIC / (key(r["repo"]) + ".html")).write_text(sheet(r))
    public_control = row_at({"repo": CONTROL, "kind": "control", "stars": 0}, PUBLIC_OUT / CONTROL)
    (PUBLIC / "control-public.html").write_text(sheet(public_control, PUBLIC_OUT / CONTROL))
    (HERE / "results.json").write_text(json.dumps([control, *rows], indent=1, ensure_ascii=False) + "\n")
    (HERE / "RESULTS.md").write_text(markdown(control, rows) + public_md(public_control))
    ran = [r for r in rows if r["ran"]]
    n = {"level": sum(r["found"] == PLANTED and not r["false"] for r in ran), "wrong": sum(r["false"] > 0 for r in ran),
         "robots": sum(r["repo"] in NOTES and NOTES[r["repo"]][0].startswith(ROBOTS_NOTE) for r in ran), "no": len(rows) - len(ran),
         "all": len(rows), "ran": len(ran), "min": control["minutes"]}
    finding = [f"No tool beat the control. Claude Code with nothing installed found all {PLANTED} planted problems in about {n['min']} minutes with no false claim; {n['level']} tool matched it and none did better. What separates the tools: {n['wrong']} stated things about the site that are false, most often a clean bill for a check it fails; {n['robots']} obey robots.txt and so missed the four problems on the blocked blog; and 3 refuse private addresses outright, so they could only audit a public copy.",
               f"没有工具超过对照组。什么都不装的 Claude Code 约 {n['min']} 分钟找全 {PLANTED} 个埋入问题，没说错一处；{n['level']} 个工具和它打平，没有更好的。工具之间的差别在于：{n['wrong']} 个说错了站点上的事实，最常见的是把不合格的检查判成通过；{n['robots']} 个遵守 robots.txt，因而漏掉了被屏蔽的博客上的四个问题；还有 3 个一律拒绝内网地址，只能审公网副本。"]
    write_runs("seo-tools", {
        "type": "table", "date": DATE, "dir": "/best-runs/seo/", "results": REPO_URL + "RESULTS.md",
        **TEXT, "finding": finding, "control": {"sheet": key(CONTROL) + ".html"}, "verdict": VERDICT, "runs": {r["repo"]: card(r) for r in rows}})
    update_method("seo-tools", [
        {"item": finding[0], "item_zh": finding[1]},
        {"item": f"False claims were mostly clean bills: \"a viewport tag on every page\", \"robots.txt allows AI crawlers\", \"redirect hops ≤1\", on a site that fails each one. A report that says a check passes needs checking as much as one that says it fails.",
         "item_zh": "说错的大多是「判通过」：「每页都有 viewport」「robots.txt 放行 AI 爬虫」「重定向不超过 1 跳」，而测试站这几项都不合格。报告说某项通过，和说某项不合格一样需要核实。"},
        {"item": f"Tools that crawl politely see less: the {n['robots']} that obey robots.txt reported the blog block but none of the problems behind it. On your own site, audit with robots rules ignored as well.",
         "item_zh": f"守规矩的爬虫看到的少：遵守 robots.txt 的 {n['robots']} 个报了博客被屏蔽，却看不到屏蔽后面的问题。审自己的站时，也要忽略 robots 规则再跑一遍。"},
    ], {"item": f"Ran {n['all']} tools on {DATE}: each installed from its README in a throwaway sandbox and run on the same nine-page test shop with {PLANTED} planted problems, plus Claude Code with no tool as a control. A judge (Claude Opus 5.5, three passes) marked each report against the planted problems; every false claim was read by hand.",
        "item_zh": f"{DATE} 实跑了 {n['all']} 个工具：每个在用完即删的沙箱里按 README 安装，审同一个埋了 {PLANTED} 个问题的 9 页测试网店，另有不装工具的 Claude Code 作对照。评审（Claude Opus 5.5，三遍）按埋入问题给每份报告打分，每一处说错都人工核对。"},
       {"item": "One run per tool, on a small test site we built. Servers that read Search Console or DataForSEO data, or that need an account or API key (OpenSEO, a PageSpeed key), were not judged. A planted problem is not a ranking forecast.",
        "item_zh": "每个工具只跑一次，测试站是我们自己搭的。读 Search Console 或 DataForSEO 数据的服务，以及需要账号或 API key 的（OpenSEO、PageSpeed key），都没有评。埋入的问题不等于排名预测。"},
       marker="No tool beat the control. Claude Code with nothing installed found all", replaces=("We did not run these tools against a site",))
    print(markdown(control, rows))


if __name__ == "__main__":
    main()
