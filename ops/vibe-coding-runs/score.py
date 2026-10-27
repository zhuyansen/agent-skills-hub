"""Score the vibe coding runs: what a person who cannot code gets from each tool.

  python3 ops/vibe-coding-runs/score.py      # after the runs in out/t1 and out/t2: writes results.json and RESULTS.md

Per tool and task, from out/<task>/<owner__repo>/ (see in/vibe.py):
- opened: how a person opens what was delivered: "file" (double-click index.html), "command"
  (the one command in START.txt) or "failed";
- checks: the tester's verdict on each check (test/report.json), corrected by review.json where
  the screenshots say otherwise (every correction carries its reason);
- ran: it opened and every check passed;
- stops: how many times the build stopped for the user (a question, an approval) and got the
  stock reply in in/reply.txt;
- minutes: the build, from the brief to its last turn (install and test not counted); review.json
  overrides it where the Mac slept during a run and the clock counted the pause;
- usage: every Claude Code session the build started, the tool's own included (the install
  session and the tester are not), priced at Anthropic's API rates per million tokens; and the
  same as a multiple of the control run's.
"""
import json
import tarfile
from pathlib import Path

HERE = Path(__file__).parent
CONTROL = "octocat/Hello-World"
TASKS = {"t1": ["open", "add", "total", "reopen"],
         "t2": ["open", "record", "month", "category", "by-month", "budget", "export", "reopen"]}
# USD per million tokens: input, output, cache read, cache write 5 min, cache write 1 h (claude-api reference, 2026-10).
PRICES = {"claude-opus-5-5": (4, 20, 0.2, 5, 8), "claude-opus-5": (5, 25, 0.5, 6.25, 10), "claude-sonnet-5-5": (2, 10, 0.2, 2.5, 4),
          "claude-sonnet-5": (2, 10, 0.2, 2.5, 4), "claude-haiku-5-5": (0.1, 0.5, 0.01, 0.125, 0.2), "claude-haiku-4-5": (1, 5, 0.1, 1.25, 2)}
FRAMEWORKS = ("next", "react", "vue", "svelte", "vite", "express", "tailwindcss")


def key(repo: str) -> str:
    return repo.replace("/", "__")


def price(model: str) -> tuple:
    return next((v for k, v in sorted(PRICES.items(), key=lambda kv: -len(kv[0])) if model.startswith(k)), PRICES["claude-opus-5-5"])


def session_id(log: Path) -> str | None:
    for line in log.read_text(errors="ignore").splitlines()[:5] if log.exists() else []:
        try:
            return json.loads(line).get("session_id")
        except ValueError:
            continue
    return None


def usage(run: Path) -> dict:
    """Tokens and API-rate cost of the build's sessions, each message counted once."""
    skip = session_id(run / "setup.jsonl")
    seen, cost, tokens, sessions = set(), 0.0, 0, set()
    for f in (run / "sessions").rglob("*.jsonl") if (run / "sessions").exists() else []:
        if skip and skip in str(f):
            continue
        for line in f.read_text(errors="ignore").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            m = e.get("message") or {}
            u = m.get("usage")
            if e.get("type") != "assistant" or not u or (m.get("id"), e.get("requestId")) in seen:
                continue
            seen.add((m.get("id"), e.get("requestId"))); sessions.add(e.get("sessionId"))
            cc = u.get("cache_creation") or {}
            w5, w1 = cc.get("ephemeral_5m_input_tokens"), cc.get("ephemeral_1h_input_tokens")
            if w5 is None and w1 is None:
                w5, w1 = u.get("cache_creation_input_tokens", 0), 0
            n = [u.get("input_tokens", 0), u.get("output_tokens", 0), u.get("cache_read_input_tokens", 0), w5 or 0, w1 or 0]
            cost += sum(a * b for a, b in zip(n, price(m.get("model", "")))) / 1e6
            tokens += sum(n)
    return {"usd": round(cost, 2), "tokens": tokens, "sessions": len(sessions)}


def framework(run: Path) -> list[str]:
    """What the app is built with, from the package.json files the build left (none: plain HTML/JS)."""
    deps = set()
    if not (run / "project.tgz").exists():
        return []
    with tarfile.open(run / "project.tgz") as tar:
        for m in tar.getmembers():
            if not m.name.endswith("package.json") or "node_modules" in m.name:
                continue
            try:
                pkg = json.load(tar.extractfile(m))
            except (ValueError, AttributeError):
                continue
            deps |= set(pkg.get("dependencies", {})) | set(pkg.get("devDependencies", {}))
    return sorted(d for d in deps if d in FRAMEWORKS)


def checks(task: str, repo: str, report: dict, review: dict) -> dict:
    """The tester's verdicts, by check id, with the reviewer's corrections applied."""
    got = {c.get("id"): bool(c.get("pass")) for c in report.get("checks", [])}
    fixed = review.get(f"{task}/{repo}", {}).get("checks", {})
    return {c: fixed[c]["pass"] if c in fixed else got.get(c, False) for c in TASKS[task]}


def row(task: str, cand: dict, review: dict) -> dict | None:
    run = HERE / "out" / task / key(cand["repo"])
    if not (run / "run.json").exists():
        return None
    load = lambda p, d: json.loads((run / p).read_text()) if (run / p).exists() else d   # noqa: E731
    report, phases, turns = load("test/report.json", {}), load("phases.json", {}), load("turns.json", [])
    opened = review.get(f"{task}/{cand['repo']}", {}).get("opened", report.get("opened_by", "failed"))
    got = checks(task, cand["repo"], report, review)
    return {**cand, "task": task, "status": load("run.json", {}).get("status"), "ending": phases.get("ending"),
            "setup": (run / "setup.txt").read_text().strip() if (run / "setup.txt").exists() else "",
            "commit": (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else None,
            "opened": opened, "start_command": report.get("start_command") or "", "checks": got,
            "passed": sum(got.values()), "of": len(got), "ran": opened != "failed" and all(got.values()),
            "stops": max(len(turns) - 1, 0), "usage": usage(run),
            "minutes": review.get(f"{task}/{cand['repo']}", {}).get("minutes", round(phases.get("build", 0) / 60, 1)),
            "packages": framework(run), "tester_notes": report.get("notes", ""),
            "review_note": review.get(f"{task}/{cand['repo']}", {}).get("note", "")}


def markdown(rows: list[dict]) -> str:
    out = []
    for task, ids in TASKS.items():
        rs = [r for r in rows if r["task"] == task]
        if not rs:
            continue
        out += [f"## {task}: {(HERE / 'in' / f'brief-{task}.txt').read_text().strip()}", "",
                "| Tool | ★ | Opened | " + " | ".join(ids) + " | Ran | Stops | Build min | Usage $ | × control | Ending |",
                "|---|---:|---|" + "---|" * len(ids) + "---|---:|---:|---:|---:|---|"]
        for r in rs:
            marks = " | ".join("✓" if r["checks"][c] else "✗" for c in ids)
            out.append(f"| {r['repo']} | {r['stars']} | {r['opened']} | {marks} | {'yes' if r['ran'] else 'no'} | {r['stops']} | "
                       f"{r['minutes']} | {r['usage']['usd']} | {r.get('usage_x', '-')} | {r['ending']} |")
        out.append("")
    return "\n".join(out)


def main() -> None:
    review = json.loads((HERE / "review.json").read_text()) if (HERE / "review.json").exists() else {}
    cands = json.loads((HERE / "candidates.json").read_text())
    rows = [r for t in TASKS for c in cands if (r := row(t, c, review))]
    for task in TASKS:
        ctrl = next((r for r in rows if r["task"] == task and r["repo"] == CONTROL), None)
        for r in rows:
            if ctrl and r["task"] == task and ctrl["usage"]["usd"]:
                r["usage_x"] = round(r["usage"]["usd"] / ctrl["usage"]["usd"], 1)
    (HERE / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    (HERE / "RESULTS.md").write_text(f"{HEADER}\n{markdown(rows)}\n{notes(review)}")
    print(markdown(rows))


HEADER = """# Vibe coding test, 2026-10-26 and 27

Each tool was cloned and installed from its README in a throwaway sandbox (ops/ppt-runs/sandbox, entrypoint
in/vibe.py), then Claude Code (Claude Opus 5.5) built two apps with it from requests in the words of someone
who cannot code (in/brief-t1.txt, in/brief-t2.txt; in/prompt.txt). Whenever a build stopped short of a finished
app, it got the reply in in/reply.txt, up to 10 times. Limits: 30 minutes (t1), 45 minutes (t2). A tester session
with no tool loaded opened the app and ran the checks in in/test-t1.md and in/test-t2.md through the browser
helpers in in/tester_kit.py; every screenshot was reviewed, and exported spreadsheets were read back.
octocat/Hello-World is the control: no tool installed. Usage is every Claude Code session a build started,
priced at API rates (score.py); "× control" divides by the control's usage on the same task.

Tester notes: the "open" check uses index.html as a local file (what double-clicking opens); the other checks
use the same file from a local address, and "reopen" closes every tab and opens a new one. The sandbox's test
browser loses localStorage for local files when a script closes it (a plain localStorage page lost its data in
1 to 4 of 8 tries), so the first version of the tester failed apps for the browser's sake; every t1 build was
tested again with the final tester (earlier verdicts in out/t1/*/test-prev-N/, not committed).
"""


def notes(review: dict) -> str:
    out = ["## Notes from the review", ""]
    out += [f"- **{k}**: {v['note']}" for k, v in review.items() if v.get("note")]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    main()
