"""Score the quarterly-report runs: what a team lead gets from each tool when the AI writes the report.

  python3 ops/writing-runs/score.py      # after runs in out/t1 and out/t2: writes results.json and RESULTS.md, prints a table per brief

Per tool and brief, from out/<task>/<owner__repo>/ (see in/writing.py):
- opened: "file" (a document in output/ with text in it) or "failed";
- checks: the seven [script] checks of in/test.md computed here by in/kit.py on the delivered document
  (the same code the tester ran in the sandbox; where the tester's copy of a script verdict differs,
  "disagree" says so), and check 6, facts, the tester's (test/report.json). review.json corrects
  a verdict only where the script misread the document or the tester misjudged it, never to make an
  exception to the checklist after seeing a result; every correction carries its reason;
- ran: it opened and all 8 checks passed;
- stops: how many times the build stopped for the person and got the stock reply;
- minutes: the build, from the brief to its last turn; run_minutes: the whole run (install, build, tester);
- paused_seconds: how long the Mac slept during the build (not counted in minutes or limits);
- usage: every Claude Code session the build started, the tool's own included, at API rates, by the
  vibe coding test's pricing (ops/vibe-coding-runs/score.py); × control on the same brief; and the
  install and tester sessions' own totals, which the build's usage leaves out.
RUNS_HOME=<folder> reads out/ and review.json from, and writes results.json and RESULTS.md to,
another folder (the self-test); in/ and candidates.json are always this folder's.
"""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path(os.environ.get("RUNS_HOME") or HERE).resolve()
sys.path.insert(0, str(HERE / "in"))
import kit  # noqa: E402
import textcheck as tc  # noqa: E402

_spec = importlib.util.spec_from_file_location("vibe_score", HERE.parent / "vibe-coding-runs" / "score.py")
vibe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vibe)
CONTROL = "octocat/Hello-World"
CHECKS = kit.CHECKS
SCORED = {"t1": CHECKS, "t2": CHECKS}            # one checklist for both briefs
LABEL = {"length": "1200–1800字", "structure": "三块", "coverage": "项目计划", "problems": "问题写实", "numbers": "数字",
         "facts": "没编", "tone": "套话≤2/千字", "parallel": "排比≤1"}
TWIN = HERE.parent / "summary-runs" / "in" / "textcheck.py"


def _cost(log: Path) -> float:
    """A session's own total at API rates, from the last result event of its stream-json log."""
    last = {}
    for line in log.read_text(errors="ignore").splitlines() if log.exists() else []:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "result":
            last = e
    return round(last.get("total_cost_usd") or 0, 2)


def document(run: Path, report: dict):
    """The delivered document: the one the tester judged (report "file", relative to ~/work), else
    the one a person would open (textcheck.deliverable on deliverables/, the copy of output/)."""
    named = report.get("file") or ""
    if named.startswith("output/") and (run / "deliverables" / named[len("output/"):]).is_file():
        return run / "deliverables" / named[len("output/"):]
    return kit.deliverable(run / "deliverables")


def row(task: str, cand: dict, review: dict) -> dict | None:
    run = HOME / "out" / task / vibe.key(cand["repo"])
    if not (run / "run.json").exists():
        return None
    load = lambda p, d: json.loads((run / p).read_text()) if (run / p).exists() else d   # noqa: E731
    report, phases, turns, meta = load("test/report.json", {}), load("phases.json", {}), load("turns.json", []), load("run.json", {})
    fixed = review.get(f"{task}/{cand['repo']}", {})
    doc = document(run, report)
    text = kit.read(doc) if doc else ""
    mech = kit.check(text) if text.strip() else None
    tester = {c.get("id"): c for c in report.get("checks", [])}
    checks, disagree = {}, []
    for c in CHECKS:
        if c in kit.SCRIPTED:
            got = bool(mech and mech["checks"][c]["pass"])
            if c in tester and bool(tester[c].get("pass")) != got:
                disagree.append(c)
        else:
            got = bool(tester.get(c, {}).get("pass"))
        checks[c] = fixed.get("checks", {}).get(c, {}).get("pass", got)
    opened = fixed.get("opened", "file" if mech else "failed")
    scored = {c: checks[c] for c in SCORED[task]}
    m = mech["checks"] if mech else {}
    found = lambda k, f: sum(1 for r in m.get(k, {}).get("rows", []) if f(r))   # noqa: E731
    return {**cand, "task": task, "status": meta.get("status"), "ending": phases.get("ending"),
            "setup": (run / "setup.txt").read_text().strip() if (run / "setup.txt").exists() else "",
            "commit": (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else None,
            "opened": opened, "file": str(doc.relative_to(run / "deliverables")) if doc else "",
            "zi": mech["zi"] if mech else 0, "checks": checks, "passed": sum(scored.values()), "of": len(scored),
            "ran": opened != "failed" and all(scored.values()), "stops": max(len(turns) - 1, 0),
            "minutes": fixed.get("minutes", round(phases.get("build", 0) / 60, 1)), "paused_seconds": phases.get("paused", 0),
            "run_minutes": round(meta.get("seconds", 0) / 60, 1),
            "usage": vibe.usage(run), "setup_usd": _cost(run / "setup.jsonl"), "tester_usd": _cost(run / "test.jsonl"),
            "found": {"coverage": found("coverage", lambda r: r["found"]), "problems": found("problems", lambda r: r["found"] and not r["spin"]),
                      "extra_numbers": len(m.get("numbers", {}).get("extra", [])), "stale": len(m.get("numbers", {}).get("stale", [])),
                      "worked_out": sum(1 for r in m.get("numbers", {}).get("extra", []) if r["worked_out"] not in ("", "清单里找不到来源")),
                      "tone": m.get("tone", {}).get("count", 0), "tone_per_1000": m.get("tone", {}).get("per_1000", 0),
                      "parallel": m.get("parallel", {}).get("count", 0), "key_numbers": len(mech["key_numbers"]) if mech else 0},
            "observed": {c: m[c]["observed"] for c in m}, "invented": report.get("invented", []), "worst": report.get("worst", []),
            "info": mech["info"] if mech else {},
            "disagree": disagree, "doubts": {c["id"]: c["doubt"] for c in report.get("checks", []) if c.get("doubt")},
            "tester_notes": report.get("notes", ""), "review_note": fixed.get("note", ""), "review_note_zh": fixed.get("note_zh", "")}


def table(rows: list, task: str) -> str:
    rs = [r for r in rows if r["task"] == task]
    if not rs:
        return ""
    head = " | ".join(LABEL[c] for c in CHECKS)
    out = [f"## {task}: {(HERE / 'in' / f'brief-{task}.txt').read_text().strip()}", "",
           f"| Tool | ★ | Opened | 字 | {head} | Passed | Stops | Build min | Run min | Usage $ | × control | Install + tester $ | Ending |",
           "|---|---:|---|---:|" + "---|" * len(CHECKS) + "---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in rs:
        marks = " | ".join("✓" if r["checks"][c] else "✗" for c in CHECKS)
        out.append(f"| {r['repo']} | {r['stars']} | {r['opened']} | {r['zi']} | {marks} | {r['passed']}/{r['of']} | {r['stops']} | "
                   f"{r['minutes']} | {r['run_minutes']} | {r['usage']['usd']} | {r.get('usage_x', '-')} | "
                   f"{round(r['setup_usd'] + r['tester_usd'], 2)} | {r['ending']} |")
    return "\n".join(out) + "\n"


def findings(rows: list) -> str:
    out = ["## What the scripted checks found", "",
           "| Brief | Tool | 字 | 项目计划 8 | 问题写实 4 | 清单没有的数字 | 其中算出来的 | 旧数字当现在 | 套话和拔高 | 每千字 | 排比 | 编的事实（测试员） |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        f = r["found"]
        out.append(f"| {r['task']} | {r['repo']} | {r['zi']} | {f['coverage']} | {f['problems']} | {f['extra_numbers']} | {f['worked_out']} | "
                   f"{f['stale']} | {f['tone']} | {f['tone_per_1000']} | {f['parallel']} | {len(r['invented'])} |")
    return "\n".join(out) + "\n"


HEADER = """# Quarterly-report test (第二十五期 AI 写作)

Each tool was cloned and installed from its README in a throwaway sandbox (ops/ppt-runs/sandbox, entrypoint
in/writing.py), then Claude Code (Claude Opus) wrote a team's third-quarter work report from a made-up fact list
(in/fixtures/季度事实清单.md, see in/fixtures/README.md), from two requests in the person's words (in/brief-t1.txt,
in/brief-t2.txt; in/prompt.txt). Whenever a build stopped short of a finished report it got the reply in
in/reply.txt, up to 10 times, within 30 minutes. A tester session with no tool loaded then checked the document
against the checklist in in/test.md, the same for every tool and both requests and fixed before the runs: seven
checks scripted in in/kit.py against the answer key and tone lists in in/truth.json, one (facts) read by the
tester. octocat/Hello-World is the control: no tool installed. Usage is every Claude Code session a build started,
priced at API rates (score.py); "× control" divides by the control's usage on the same request.
"""


def notes(review: dict, rows: list) -> str:
    out = ["## Notes", ""]
    out += [f"- **{k}**: {v['note']}" for k, v in review.items() if not k.startswith("_") and v.get("note")]
    out += [f"- **{r['task']}/{r['repo']}**: the Mac slept {r['paused_seconds']} s during the build; that time is not counted"
            for r in rows if r.get("paused_seconds")]
    out += [f"- **{r['task']}/{r['repo']}**: the tester's copy of {', '.join(r['disagree'])} differs from the script's verdict here (the tester ran the script before one of the script fixes listed below; the table uses the fixed script)"
            for r in rows if r["disagree"]]
    out += [f"- **{r['task']}/{r['repo']}** doubt on {c}: {d}" for r in rows for c, d in r["doubts"].items()]
    out += [f"- **{r['task']}/{r['repo']}** recorded, not scored: {json.dumps(r['info'], ensure_ascii=False)}" for r in rows if r["info"]]
    return "\n".join(out) + "\n"


def main() -> None:
    if TWIN.exists() and hashlib.sha1(TWIN.read_bytes()).digest() != hashlib.sha1((HERE / "in" / "textcheck.py").read_bytes()).digest():
        print(f"note: in/textcheck.py differs from {TWIN}; they are meant to be the same file", file=sys.stderr)
    review = json.loads((HOME / "review.json").read_text()) if (HOME / "review.json").exists() else {}
    cands = json.loads((HERE / "candidates.json").read_text())
    rows = [r for t in SCORED for c in cands if (r := row(t, c, review))]
    for task in SCORED:
        ctrl = next((r for r in rows if r["task"] == task and r["repo"] == CONTROL), None)
        for r in rows:
            if ctrl and r["task"] == task and ctrl["usage"]["usd"]:
                r["usage_x"] = round(r["usage"]["usd"] / ctrl["usage"]["usd"], 1)
    (HOME / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    tables = "\n".join(table(rows, t) for t in SCORED)
    aborted = ["## Runs that do not count (redone; their files are in out/aborted/)", "", *[f"- {x}" for x in review.get("_aborted", [])], ""] \
        if review.get("_aborted") else []
    aborted += ["## Script fixes made during the runs (the rules unchanged; every run rescored with the fixed script)", "",
                *[f"- {x}" for x in review.get("_kit_fixes", [])], ""] if review.get("_kit_fixes") else []
    (HOME / "RESULTS.md").write_text(f"{HEADER}\n{tables}\n{findings(rows)}\n{notes(review, rows)}\n" + "\n".join(aborted))
    print(tables)


if __name__ == "__main__":
    main()
