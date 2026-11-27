"""Runs inside the sandbox for the meeting-summary test (ops/summary-runs): one tool, one brief.

  python3 /in/summary.py <owner/repo>       # TASK=t1|t2; octocat/Hello-World is the control (no tool)
  python3 /in/summary.py --login-check      # only checks that a `claude` started by a tool is signed in
  python3 /in/summary.py --retest <owner/repo>

The steps of the personal-site test (ops/site-runs/in/site.py), with these changes:
- the project folder starts with the meeting record, 会议记录.txt (in/fixtures), committed;
- ONLY=<path> (from candidates.json "only"): the tool is one folder of a large repository, cloned
  sparsely (that folder and the repository's top-level files), and its own install prompt in
  in/setup_prompts/<owner__repo>.txt says what to install;
- the build is finished when ~/work/output holds a document (textcheck.candidates: Markdown, text,
  Word, HTML or PDF) and the session printed its DELIVERABLE line;
- the tester has no browser: it reads the document against the record with /in/kit.py and the
  checklist in /in/test.md, the same for both briefs ({BRIEF} is filled in);
- output.json keeps which document is the deliverable and its 字数.
Ported from the resume test (ops/resume-runs/in/resume.py, 2026-11-08), after its runs:
- every Claude Code session is watched while it runs: a rate-limit event saying the subscription is
  using paid extra usage, has refused a request, or has a window at WATCH_LIMIT or more stops the
  session, and /out/LIMIT.json says why (run.py then stops the batch; the tester is skipped);
  every such event is kept in /out/limits.jsonl;
- the Mac's sleep does not count: a 3-second poll that returns SUSPEND_GAP or more later means the
  container was frozen, and that time is added to the session's and the build's deadlines
  (paused_seconds in turns.json, "paused" in phases.json);
- a clone that fails (no network) stops the run as "setup failed" instead of crashing in ~/src, and
  whatever happened, the run's files are collected and phases.json is written.

1. A git identity, the project folder ~/work (a git repository holding the record), and a login for
   any `claude` the tool starts itself: a user's machine is signed in to Claude Code, but a headless
   session does not pass its token on to the processes it starts.
2. The tool is cloned to ~/src and a separate session installs it from its README (setup.jsonl).
3. The build: the brief in the user's words. Whenever the session stops without a finished document
   (a question, an approval), it gets the same reply from a user who cannot code, up to MAX_REPLIES
   times, within RUN_MINUTES in all (build-<n>.jsonl, turns.json).
4. Everything the build left running is stopped. A tester session with its own, empty Claude Code
   config (no tool loaded) checks the document (test/).
5. Copied out: output/ (deliverables/), the project's file list, and every Claude Code session the
   build started, the tool's own included (sessions/), for counting tokens.
"""
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import kit                                     # fails here, before any session, if the answer key and the record disagree
import textcheck as tc

HOME = Path.home()
WORK, SRC, TESTER, OUT, IN = HOME / "work", HOME / "src", HOME / "tester", Path("/out"), Path("/in")
CONTROL = "octocat/Hello-World"
FIXTURES = ("会议记录.txt",)
TASK = os.environ.get("TASK", "t1")
ONLY = os.environ.get("ONLY", "")
RUN_SECONDS = int(os.environ.get("RUN_MINUTES", 20)) * 60
TEST_SECONDS = int(os.environ.get("TEST_MINUTES", 15)) * 60
SETUP_SECONDS = 15 * 60
MAX_REPLIES = int(os.environ.get("MAX_REPLIES", 10))
MODEL = os.environ.get("CLAUDE_MODEL", "opus")
MIN_TURN_SECONDS = 60          # do not start another turn with less time than this left
WATCH_LIMIT = float(os.environ.get("WATCH_LIMIT", 0.97))   # stop a session when a usage window reaches this
SUSPEND_GAP = 60               # a 3-second poll that returns this much later: the container was frozen (the Mac asleep)
SKIP = {"node_modules", ".git", ".next", "dist-cache", "__pycache__", ".venv", "venv", ".cache"}
LIMIT = re.compile(r"usage limit|rate limit|limit reached|resets at|out of extra usage|extra usage", re.I)
LOGIN_FILE = HOME / ".claude-login"
REAL_CLAUDE = shutil.which("claude") or "/usr/local/bin/claude"
WRAPPER = """#!/bin/sh
# A user's machine is signed in to Claude Code; a headless session does not pass its login on.
unset CLAUDECODE
CLAUDE_CODE_OAUTH_TOKEN="$(cat "$HOME/.claude-login")" exec {real} "$@"
"""


def sh(cmd: str, cwd: Path = HOME) -> str:
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True).stdout.strip()


def sign_in_children() -> None:
    """Tools that start `claude` themselves get the same login: on PATH through a wrapper, and in
    ~/.claude/.credentials.json for an SDK that runs its own copy of the binary."""
    token = os.environ["CLAUDE_CODE_OAUTH_TOKEN"]
    old = os.umask(0o077)
    LOGIN_FILE.write_text(token)
    (HOME / ".claude").mkdir(exist_ok=True)
    year = int((time.time() + 300 * 86400) * 1000)
    (HOME / ".claude" / ".credentials.json").write_text(json.dumps({"claudeAiOauth": {
        "accessToken": token, "refreshToken": "", "expiresAt": year, "scopes": ["user:inference"], "subscriptionType": "max"}}))
    os.umask(old)
    bin_dir = HOME / ".local" / "bin"; bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / "claude").write_text(WRAPPER.format(real=REAL_CLAUDE)); (bin_dir / "claude").chmod(0o755)
    os.environ["PATH"] = f"{bin_dir}:{os.environ['PATH']}"
    with (HOME / ".bashrc").open("a") as f:
        f.write(f'\nexport PATH="{bin_dir}:$PATH"\n')


def prepare() -> None:
    for k, v in (("user.name", "Summary Test"), ("user.email", "summary-test@example.com"), ("init.defaultBranch", "main")):
        sh(f"git config --global {k} '{v}'")
    WORK.mkdir(exist_ok=True)
    for name in FIXTURES:
        shutil.copy(IN / "fixtures" / name, WORK / name)
    sh("git init -q && git add -A && git commit -q -m 'the meeting record'", WORK)
    sign_in_children()


# ---- watching the subscription (as ops/resume-runs/in/resume.py) ---------------------------------

def _limit_reason(info: dict) -> str | None:
    if info.get("isUsingOverage"):
        return "the subscription is using paid extra usage"
    if info.get("status") not in (None, "allowed", "allowed_warning"):
        return f"rate limit status {info.get('status')}"
    for name, w in (info.get("unifiedWindows") or {}).items():
        if (w.get("utilization") or 0) >= WATCH_LIMIT:
            return f"{name} window at {w.get('utilization')}"
    return None


def scan(log: Path, pos: int) -> tuple:
    """Read the stream-json log from pos: keep every rate-limit event in /out/limits.jsonl and say
    why to stop, if a reason turns up. Returns the position after the last whole line."""
    try:
        with log.open("rb") as f:
            f.seek(pos)
            chunk = f.read()
    except FileNotFoundError:
        return pos, None
    end = chunk.rfind(b"\n") + 1
    why = None
    for raw in chunk[:end].splitlines():
        if b'"rate_limit_event"' not in raw and b'"result"' not in raw:
            continue
        try:
            e = json.loads(raw)
        except ValueError:
            continue
        if e.get("type") == "rate_limit_event":
            info = e.get("rate_limit_info") or {}
            with (OUT / "limits.jsonl").open("a") as f:
                f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "log": log.name, **info}) + "\n")
            why = why or _limit_reason(info)
        elif e.get("type") == "result" and e.get("is_error") and LIMIT.search(str(e.get("result") or "")):
            why = why or f"session ended on a limit: {str(e.get('result'))[:200]}"
    return pos + end, why


def result_of(log: Path) -> dict:
    """The last `result` event of a stream-json session, or {}."""
    last = {}
    for line in log.read_text(errors="ignore").splitlines() if log.exists() else []:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "result":
            last = e
    return last


def claude(args: list, log: Path, seconds: float, env: dict | None = None, cwd: Path = WORK) -> dict:
    """One headless Claude Code session, stopped at its time limit or when the subscription watch says
    so. Time the container spends frozen (the Mac asleep) moves the deadline on (paused_seconds)."""
    cmd = [REAL_CLAUDE, *args, "--model", MODEL, "--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose"]
    deadline, pos, why, paused = time.time() + max(seconds, 1), 0, None, 0.0
    with log.open("w") as f:
        p = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        last = time.time()
        while p.poll() is None:
            time.sleep(3)
            now = time.time()
            if now - last > SUSPEND_GAP:     # frozen while the Mac slept: that time is not the tool's
                paused += now - last - 3
                deadline += now - last - 3
            last = now
            pos, why = scan(log, pos)
            if why or now > deadline:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait()
                break
    pos, late = scan(log, pos)
    why = why or late
    res = {**result_of(log), "paused_seconds": round(paused)}
    if why:
        (OUT / "LIMIT.json").write_text(json.dumps({"why": why, "log": log.name, "at": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=1))
        return {**res, "usage_limit": why}
    if (p.returncode is not None and p.returncode < 0) or time.time() > deadline:
        return {**res, "timed_out": True}
    return res


def clone() -> None:
    url = f"https://github.com/{REPO}.git"
    if ONLY:                       # one folder of a large repository: that folder and the top-level files
        sh(f"git clone -q --depth 1 --filter=blob:none --sparse {url} {SRC}")
        sh(f"git sparse-checkout set '{ONLY}'", SRC)
    else:
        sh(f"git clone -q --depth 1 {url} {SRC}")
    if not (SRC / ".git").exists():
        (OUT / "setup.txt").write_text(f"SETUP: failed: could not clone {url}\n")
        raise SystemExit(f"stopped: could not clone {url}")
    (OUT / "commit.txt").write_text(sh("git rev-parse HEAD", SRC))


def setup() -> None:
    clone()
    own = IN / "setup_prompts" / f"{REPO.replace('/', '__')}.txt"
    prompt = (own if own.exists() else IN / "setup_prompt.txt").read_text()
    t0 = time.time()
    res = claude(["-p", prompt], OUT / "setup.jsonl", SETUP_SECONDS)
    line = next((x for x in (res.get("result") or "").splitlines() if x.startswith("SETUP:")), "SETUP: (no line)")
    (OUT / "setup.txt").write_text(line + "\n")
    (OUT / "installed.txt").write_text(sh(f"{REAL_CLAUDE} plugin list 2>&1; {REAL_CLAUDE} mcp list 2>&1; "
                                          "ls ~/.claude/skills ~/work/.claude/skills ~/.agents/skills 2>&1", WORK))
    PHASES["setup"] = round(time.time() - t0 - res.get("paused_seconds", 0))
    if res.get("usage_limit"):
        raise SystemExit(f"stopped: {res['usage_limit']}")


def finished(res: dict) -> bool:
    return bool(tc.candidates(WORK / "output")) and "DELIVERABLE:" in (res.get("result") or "")


def turn_record(n: int, res: dict, seconds: float) -> dict:
    return {"turn": n, "seconds": round(seconds), "paused_seconds": res.get("paused_seconds", 0),
            "cost_usd": res.get("total_cost_usd"), "is_error": res.get("is_error"),
            "timed_out": bool(res.get("timed_out")), "usage_limit": res.get("usage_limit"),
            "session_id": res.get("session_id"), "result": (res.get("result") or "")[:6000]}


def build() -> str:
    """The brief, then the same reply whenever the build stops short. Returns how it ended."""
    key = REPO.replace("/", "__")
    template = (IN / "prompts" / f"{key}.txt") if (IN / "prompts" / f"{key}.txt").exists() else IN / "prompt.txt"
    prompt = template.read_text().replace("{BRIEF}", (IN / f"brief-{TASK}.txt").read_text().strip())
    reply, deadline, turns = (IN / "reply.txt").read_text().strip(), time.time() + RUN_SECONDS, []
    args, ending = ["-p", prompt], "replies used up"
    while True:
        t0 = time.time()
        res = claude(args, OUT / f"build-{len(turns)}.jsonl", deadline - t0)
        deadline += res.get("paused_seconds", 0)          # the Mac's sleep does not count against the build
        turns.append(turn_record(len(turns), res, time.time() - t0 - res.get("paused_seconds", 0)))
        (OUT / "turns.json").write_text(json.dumps(turns, indent=1, ensure_ascii=False))
        if res.get("usage_limit") or (LIMIT.search(res.get("result") or "") and res.get("is_error")):
            ending = "usage limit"; break
        if finished(res):
            ending = "finished"; break
        if res.get("timed_out") or deadline - time.time() < MIN_TURN_SECONDS:
            ending = "out of time"; break
        if not res.get("session_id"):
            ending = "session crashed"; break
        if len(turns) > MAX_REPLIES:
            break
        args = ["-p", reply, "--resume", res["session_id"]]
    PHASES["build"] = round(sum(t["seconds"] for t in turns))
    PHASES["paused"] = round(sum(t["paused_seconds"] for t in turns))
    return ending


def stop_leftovers() -> None:
    """Everything but this script: servers, loops and watchers the build or the tester started."""
    me = os.getpid()
    for p in Path("/proc").iterdir():
        if p.name.isdigit() and int(p.name) not in (1, me):
            try:
                os.kill(int(p.name), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
    time.sleep(1)


def fingerprint() -> dict:
    """Hashes of the project's own files (dependencies, git and caches left out)."""
    out = {}
    for root, dirs, names in os.walk(WORK):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for n in names:
            f = Path(root) / n
            if f.is_file() and not f.is_symlink() and f.stat().st_size < 5_000_000:
                out[str(f.relative_to(WORK))] = hashlib.sha1(f.read_bytes()).hexdigest()
    return out


def test() -> None:
    TESTER.mkdir(exist_ok=True)
    if (OUT / "LIMIT.json").exists():
        (OUT / "test").mkdir(exist_ok=True)   # the subscription said stop: no tester session
        (OUT / "test" / "report.json").write_text(json.dumps({"opened_by": "skipped", "file": "", "checks": [],
                                                             "notes": "not tested: " + json.loads((OUT / "LIMIT.json").read_text())["why"]}))
        return
    if not tc.candidates(WORK / "output"):
        (OUT / "test").mkdir(exist_ok=True)   # nothing a person could open: no tester session
        (OUT / "test" / "report.json").write_text(json.dumps({"opened_by": "failed", "file": "", "checks": [], "notes": "no document in ~/work/output"}))
        return
    before = fingerprint()
    path = os.pathsep.join(x for x in os.environ["PATH"].split(os.pathsep) if ".local/bin" not in x)
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(HOME / ".tester-config"), "PATH": path}
    prompt = (IN / "test.md").read_text().replace("{BRIEF}", (IN / f"brief-{TASK}.txt").read_text().strip())
    t0 = time.time()
    res = claude(["-p", prompt], OUT / "test.jsonl", TEST_SECONDS, env=env, cwd=TESTER)
    PHASES["test"] = round(time.time() - t0 - res.get("paused_seconds", 0))
    PHASES["test_paused"] = res.get("paused_seconds", 0)
    if res.get("usage_limit"):
        PHASES["test_stopped"] = res["usage_limit"]
    stop_leftovers()
    after = fingerprint()
    touched = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    shutil.copytree(TESTER, OUT / "test", dirs_exist_ok=True)
    (OUT / "test" / "touched.json").write_text(json.dumps(touched, indent=1, ensure_ascii=False))


def output_info() -> dict:
    """What the person gets: the documents in output/, which one is the deliverable and how long it is."""
    files = [f for f in (WORK / "output").rglob("*") if f.is_file() and not SKIP.intersection(f.relative_to(WORK).parts)]
    doc = tc.deliverable(WORK / "output")
    return {"files": len(files), "bytes": sum(f.stat().st_size for f in files),
            "file": str(doc.relative_to(WORK)) if doc else "", "zi": tc.zi(tc.read(doc)) if doc else 0}


def collect() -> None:
    files = fingerprint()
    (OUT / "files.json").write_text(json.dumps(sorted(files), indent=1, ensure_ascii=False))
    if (WORK / "output").exists():
        shutil.copytree(WORK / "output", OUT / "deliverables", ignore=shutil.ignore_patterns(*SKIP), dirs_exist_ok=True)
        (OUT / "output.json").write_text(json.dumps(output_info(), indent=1, ensure_ascii=False))
    sh(f"tar czf {OUT / 'project.tgz'} " + " ".join(f"--exclude={x}" for x in SKIP) + " -C ~ work")
    if (HOME / ".claude" / "projects").exists():
        shutil.copytree(HOME / ".claude" / "projects", OUT / "sessions", dirs_exist_ok=True)


def retest() -> None:
    """The tester again, on a document already made, after a fix to the tester's kit (never to the
    document). Earlier verdicts stay in test-prev-<n>/."""
    if (OUT / "test").exists():
        n = 1 + sum(1 for d in OUT.glob("test-prev-*"))
        (OUT / "test").rename(OUT / f"test-prev-{n}")
    sh(f"tar xzf {OUT / 'project.tgz'} -C {HOME}")
    test()


def login_check() -> None:
    """Both ways a tool can start Claude Code, with the session's own token taken away."""
    sign_in_children()
    env = {**{k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_OAUTH_TOKEN"}, "CLAUDECODE": "1"}   # as inside a session's shell
    for label, exe in (("wrapper on PATH", "claude"), ("binary, credentials file", REAL_CLAUDE)):
        p = subprocess.run([exe, "-p", "Reply with the single word: ok", "--model", "haiku"], env=env, capture_output=True, text=True, timeout=180)
        print(f"{label}: exit {p.returncode}: {(p.stdout + p.stderr).strip()[:300]}", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "--login-check":
        login_check(); sys.exit(0)
    if sys.argv[1] == "--retest":
        REPO, PHASES = sys.argv[2], {}
        retest()
        (OUT / "retest.json").write_text(json.dumps({**PHASES, "why": os.environ.get("RETEST_WHY", "")}, indent=1))
        sys.exit(0)
    REPO, PHASES = sys.argv[1], {}
    OUT.mkdir(exist_ok=True)
    (OUT / "env.txt").write_text(f"task {TASK}\nclaude {sh(REAL_CLAUDE + ' --version')}\nmodel {MODEL}\nonly {ONLY or '-'}\n")
    prepare()
    ending = "setup failed"
    try:
        if REPO != CONTROL:
            setup()
        ending = build()
    except SystemExit as e:
        PHASES["stopped"] = str(e)
        ending = "usage limit" if (OUT / "LIMIT.json").exists() else ending
    finally:
        stop_leftovers()
        collect()
        (OUT / "phases.json").write_text(json.dumps({**PHASES, "ending": ending}, indent=1))
    if ending != "setup failed":
        test()
        (OUT / "phases.json").write_text(json.dumps({**PHASES, "ending": ending}, indent=1))
    print(f"{REPO} {TASK}: {ending}", flush=True)
