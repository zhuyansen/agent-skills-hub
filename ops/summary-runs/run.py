"""Run the meeting-summary test (第二十四期 AI 总结): one fresh sandbox per tool and brief, strictly serial.

  cd ~/content/agent-skills-hub
  python3 ops/summary-runs/run.py --login-check                         # the sandbox's `claude` is signed in? (two tiny haiku calls)
  caffeinate -i python3 ops/summary-runs/run.py t1 octocat/Hello-World  # the control first: read its summary and report
  caffeinate -i python3 ops/summary-runs/run.py t1 --next 6             # then the other 6, in candidates.json order
  caffeinate -i python3 ops/summary-runs/run.py t2 --next 7             # after checking the subscription's usage
  python3 ops/summary-runs/run.py t1 --retest owner/repo ...            # the tester again on summaries already made
  python3 ops/summary-runs/run.py t1 --abort owner/repo mac-sleep       # move a run that does not count to out/aborted/
  python3 ops/summary-runs/score.py && python3 ops/summary-runs/render.py   # results.json, RESULTS.md, evidence PNGs

Append `2>&1 | tee -a ops/summary-runs/run.log` to keep the one-line log of each run.

Each run is a container of resumerun:1 (ops/resume-runs/sandbox: pptrun:1, the image of the personal-site
test, plus LibreOffice Writer, so a tool that makes a Word file can open and convert it) with in/ mounted
and in/summary.py as its entrypoint; results land in out/<task>/<owner__repo>/. A candidate with "only"
in candidates.json is one folder of a large repository: the sandbox clones just that folder (ONLY).
Needs CLAUDE_CODE_OAUTH_TOKEN in ~/.claude/.env (read here, never printed). Serial because every run
draws on the same subscription, and other tests share it. Keep the Mac on power.

Ported from the resume test (ops/resume-runs/run.py, 2026-11-08), after its runs:
- Network: this Mac reaches the internet through a local proxy (HTTPS_PROXY, 127.0.0.1:7897), and
  direct connections from a container broke on GitHub (TLS handshakes cut, a clone at 3 KB/s), so
  every container gets the same proxy at host.docker.internal (proxy_env). No proxy on the host: none
  in the container.
- Sleep: caffeinate -i stops idle sleep only; a closed lid on battery still puts the Mac to sleep (the
  resume test lost a run to a 4-hour clamshell sleep). The clocks stop while it sleeps: in/summary.py
  moves its deadlines on by the time its container was frozen (paused_seconds in turns.json), and
  container times here use time.monotonic(), which on macOS does not count sleep. A run cut short by
  sleep is still redone and not scored: `--abort <task> <owner/repo> mac-sleep` moves it to
  out/aborted/, then run it again (and note it in review.json "_aborted").
- Usage guard: before each run the latest rate-limit event of this test's own sessions is read; the
  batch stops when a window is at STOP_AT or more, when the subscription says it is using paid extra
  usage, or when a run left LIMIT.json (in/summary.py stops a session that crosses into extra usage,
  is refused, or reaches 0.97 of a window). Paid extra usage is never to be used for this test.

The material is made up: in/fixtures/会议记录.txt (see in/fixtures/README.md) and its answer key
in/truth.json, written before any run.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ppt_run", HERE.parent / "ppt-runs" / "run.py")
ppt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ppt)
IMAGE = "resumerun:1"   # pinned: pptrun:1 plus LibreOffice Writer (ops/resume-runs/sandbox); ppt-runs/run.py reads SANDBOX_IMAGE
# The build's limit and the tester's, in minutes. Episode 21 (ops/site-runs) gave the build 45 and
# the tester 20, and its builds took 3 to 6 minutes (one 25). A summary of a 5,000-字 record takes
# Claude Code a minute or two: 20 minutes leaves room for a skill that stops to ask (meeting-minutes
# asks up to three questions first) and for one that runs its own command-line tool (summarize).
# The tester reads two documents and runs one script: 15.
MINUTES = {"t1": (20, 15), "t2": (20, 15)}
SETUP_MINUTES, GRACE_MINUTES = 15, 10
STOP_AT = 0.85
RETEST_WHY = "tester kit changed (say what) before the rerun"
PREFIX = "sum"
ENTRY = "/in/summary.py"


def candidates() -> list:
    return json.loads((HERE / "candidates.json").read_text())


def proxy_env() -> list:
    """The host's proxy for the container, with 127.0.0.1 or localhost replaced by host.docker.internal."""
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if not proxy:
        return []
    proxy = re.sub(r"//(127\.0\.0\.1|localhost)(?=[:/]|$)", "//host.docker.internal", proxy)
    no = "localhost,127.0.0.1,::1"
    return [x for k, v in (("HTTPS_PROXY", proxy), ("HTTP_PROXY", proxy), ("https_proxy", proxy), ("http_proxy", proxy),
                           ("NO_PROXY", no), ("no_proxy", no)) for x in ("-e", f"{k}={v}")]


def docker(name: str, token: str, out: Path, extra: list, args: list) -> list:
    return ["docker", "run", "--rm", "--name", name, "-e", f"CLAUDE_CODE_OAUTH_TOKEN={token}", *proxy_env(), *extra,
            "-v", f"{HERE / 'in'}:/in:ro", "-v", f"{out}:/out", "--entrypoint", "python3", IMAGE, ENTRY, *args]


def contained(cmd: list, name: str, minutes: int, log: Path) -> tuple:
    t0 = time.monotonic()        # on macOS this does not count sleep, like subprocess.run's own timeout
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=minutes * 60)
        status = "done" if p.returncode == 0 else f"exit {p.returncode}"
        log.write_text(p.stdout[-20000:] + p.stderr[-20000:])
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        status = "timeout"
    return status, round(time.monotonic() - t0)


def run(task: str, cand: dict, token: str) -> dict:
    repo = cand["repo"]
    out = HERE / "out" / task / repo.replace("/", "__"); out.mkdir(parents=True, exist_ok=True)
    build, test = MINUTES[task]
    name = f"{PREFIX}-{task}-{out.name.lower()[:40]}"
    env = ["-e", f"TASK={task}", "-e", f"RUN_MINUTES={build}", "-e", f"TEST_MINUTES={test}", "-e", f"ONLY={cand.get('only', '')}"]
    status, seconds = contained(docker(name, token, out, env, [repo]), name, SETUP_MINUTES + build + test + GRACE_MINUTES, out / "docker.log")
    meta = {"repo": repo, "task": task, "status": status, "seconds": seconds, "finished": time.strftime("%Y-%m-%d %H:%M")}
    (out / "run.json").write_text(json.dumps(meta, indent=1))
    return meta


def latest_limits() -> dict | None:
    """The most recent rate-limit event any run of this test recorded."""
    events = []
    for f in (HERE / "out").glob("t*/*/limits.jsonl"):
        for line in f.read_text().splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                continue
    return max(events, key=lambda e: e.get("t", "")) if events else None


def guard() -> str | None:
    """Why the batch must stop before the next run, or None."""
    hit = sorted((HERE / "out").glob("t*/*/LIMIT.json"))
    if hit:
        return f"{hit[-1].parent.name}: {json.loads(hit[-1].read_text())['why']}"
    e = latest_limits()
    if not e:
        return None
    if e.get("isUsingOverage"):
        return "the subscription reports paid extra usage in use"
    if e.get("status") not in (None, "allowed", "allowed_warning"):
        return f"rate limit status {e.get('status')}"
    full = {k: w.get("utilization") for k, w in (e.get("unifiedWindows") or {}).items() if (w.get("utilization") or 0) >= STOP_AT}
    return f"usage windows at {full}" if full else None


def usage_line() -> str:
    e = latest_limits() or {}
    return ", ".join(f"{k} {w.get('utilization')}" for k, w in (e.get("unifiedWindows") or {}).items()) or "no rate-limit event yet"


def phases(task: str, repo: str) -> dict:
    f = HERE / "out" / task / repo.replace("/", "__") / "phases.json"
    return json.loads(f.read_text()) if f.exists() else {}


def pending(task: str) -> list:
    return [c for c in candidates() if not (HERE / "out" / task / c["repo"].replace("/", "__") / "run.json").exists()]


def abort(task: str, repo: str, why: str) -> None:
    """Move a run that does not count (cut short by sleep, a broken network) to out/aborted/<task>-<owner__repo>-<why>."""
    src = HERE / "out" / task / repo.replace("/", "__")
    dst = HERE / "out" / "aborted" / f"{task}-{repo.replace('/', '__')}-{why}"
    if not src.exists():
        sys.exit(f"no run at {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    print(f"{time.strftime('%Y-%m-%d %H:%M')} {task} {repo}: moved to {dst.relative_to(HERE)}; run it again, and note it in review.json \"_aborted\"", flush=True)


def main() -> None:
    sys.path.insert(0, str(HERE / "in"))
    import kit   # noqa: F401  (stops here, before any container, if truth.json and the record disagree)
    args = sys.argv[1:]
    if len(args) == 4 and args[1] == "--abort":
        abort(args[0], args[2], args[3])
        return
    token = ppt.env_file().get("CLAUDE_CODE_OAUTH_TOKEN")
    if not token:
        sys.exit("CLAUDE_CODE_OAUTH_TOKEN missing from ~/.claude/.env (run `claude setup-token`)")
    if args == ["--login-check"]:
        check = HERE / "out" / "login-check"; check.mkdir(parents=True, exist_ok=True)
        subprocess.run(docker(f"{PREFIX}-login-check", token, check, [], ["--login-check"]))
        return
    task, rest = args[0], args[1:]
    if task not in MINUTES:
        sys.exit(f"task is t1 or t2, not {task}")
    by_repo = {c["repo"]: c for c in candidates()}
    if rest[:1] == ["--retest"]:
        for repo in rest[1:]:
            out = HERE / "out" / task / repo.replace("/", "__")
            env = ["-e", f"TASK={task}", "-e", f"TEST_MINUTES={MINUTES[task][1]}", "-e", f"RETEST_WHY={RETEST_WHY}"]
            name = f"{PREFIX}-retest-{task}-{out.name.lower()[:30]}"
            status, sec = contained(docker(name, token, out, env, ["--retest", repo]), name, MINUTES[task][1] + GRACE_MINUTES, out / "docker-retest.log")
            print(f"{time.strftime('%Y-%m-%d %H:%M')} {task} {repo}: retest {status} in {sec}s", flush=True)
        return
    if rest[:1] == ["--next"]:
        cands = pending(task)[:int(rest[1])]
    else:
        unknown = [r for r in rest if r not in by_repo]
        if unknown:
            sys.exit(f"not in candidates.json: {unknown}")
        cands = [by_repo[r] for r in rest]
    for cand in cands:
        why = guard()
        if why:
            print(f"{time.strftime('%Y-%m-%d %H:%M')} STOP before {task} {cand['repo']}: {why}", flush=True)
            sys.exit(2)
        meta = run(task, cand, token)
        ph = phases(task, cand["repo"])
        slept = f"; the Mac slept {ph['paused']}s during the build: check it, and --abort it if it was cut short" if ph.get("paused") else ""
        print(f"{meta['finished']} {task} {cand['repo']}: {meta['status']}, {ph.get('ending', 'no phases.json')} in {meta['seconds']}s; "
              f"usage {usage_line()}{slept}", flush=True)
    why = guard()
    if why:
        print(f"{time.strftime('%Y-%m-%d %H:%M')} STOP after the batch: {why}", flush=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
