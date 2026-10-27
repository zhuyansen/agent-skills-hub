"""Runs inside the sandbox for the vibe coding test (ops/vibe-coding-runs): one tool, one task.

  python3 /in/vibe.py <owner/repo>       # TASK=t1|t2; octocat/Hello-World is the control (no tool)
  python3 /in/vibe.py --login-check      # only checks that a `claude` started by a tool is signed in

1. A git identity, an empty project folder ~/work that is a git repository, and a login for any
   `claude` the tool starts itself: a user's machine is signed in to Claude Code, but a headless
   session does not pass its token on to the processes it starts.
2. The tool is cloned to ~/src and a separate session installs it from its README (setup.jsonl).
3. The build: the brief in the user's words. Whenever the session stops without a finished app
   (a question, an approval), it gets the same reply from a user who cannot code, up to
   MAX_REPLIES times, within RUN_MINUTES in all (build-<n>.jsonl, turns.json).
4. Everything the build left running is stopped. A tester session with its own, empty Claude Code
   config (no tool loaded) opens the app in a browser and runs the task's checks (test/).
5. Copied out: the deliverable, the project's file list, and every Claude Code session the build
   started, the tool's own included (sessions/), for counting tokens.
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

HOME = Path.home()
WORK, SRC, TESTER, OUT, IN = HOME / "work", HOME / "src", HOME / "tester", Path("/out"), Path("/in")
CONTROL = "octocat/Hello-World"
TASK = os.environ.get("TASK", "t1")
RUN_SECONDS = int(os.environ.get("RUN_MINUTES", 30)) * 60
TEST_SECONDS = int(os.environ.get("TEST_MINUTES", 15)) * 60
SETUP_SECONDS = 15 * 60
MAX_REPLIES = int(os.environ.get("MAX_REPLIES", 10))
MODEL = os.environ.get("CLAUDE_MODEL", "opus")
MIN_TURN_SECONDS = 60          # do not start another turn with less time than this left
SKIP = {"node_modules", ".git", ".next", "dist-cache", "__pycache__", ".venv", "venv", ".cache"}
LIMIT = re.compile(r"usage limit|rate limit|limit reached|resets at|out of extra usage", re.I)
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
    """Tools that start `claude` themselves (Ralph loops, Task Master's claude-code provider) get the
    same login: on PATH through a wrapper, and in ~/.claude/.credentials.json for an SDK that runs
    its own copy of the binary."""
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
    for k, v in (("user.name", "Vibe Test"), ("user.email", "vibe-test@example.com"), ("init.defaultBranch", "main")):
        sh(f"git config --global {k} '{v}'")
    WORK.mkdir(exist_ok=True)   # the image's working directory: empty
    sh("git init -q && git commit -q --allow-empty -m 'empty project'", WORK)
    sign_in_children()


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


def claude(args: list[str], log: Path, seconds: float, env: dict | None = None, cwd: Path = WORK) -> dict:
    cmd = [REAL_CLAUDE, *args, "--model", MODEL, "--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose"]
    with log.open("w") as f:
        try:
            subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT, timeout=max(seconds, 1), env=env)
        except subprocess.TimeoutExpired:
            return {**result_of(log), "timed_out": True}
    return result_of(log)


def setup() -> None:
    sh(f"git clone -q --depth 1 https://github.com/{REPO}.git {SRC}")
    (OUT / "commit.txt").write_text(sh("git rev-parse HEAD", SRC))
    t0 = time.time()
    res = claude(["-p", (IN / "setup_prompt.txt").read_text()], OUT / "setup.jsonl", SETUP_SECONDS)
    line = next((x for x in (res.get("result") or "").splitlines() if x.startswith("SETUP:")), "SETUP: (no line)")
    (OUT / "setup.txt").write_text(line + "\n")
    (OUT / "installed.txt").write_text(sh(f"{REAL_CLAUDE} plugin list 2>&1; {REAL_CLAUDE} mcp list 2>&1", WORK))
    PHASES["setup"] = round(time.time() - t0)


def finished(res: dict) -> bool:
    entry = (WORK / "output" / "index.html").exists() or (WORK / "output" / "START.txt").exists()
    return entry and "DELIVERABLE:" in (res.get("result") or "")


def turn_record(n: int, res: dict, seconds: float) -> dict:
    return {"turn": n, "seconds": round(seconds), "cost_usd": res.get("total_cost_usd"), "is_error": res.get("is_error"),
            "timed_out": bool(res.get("timed_out")), "session_id": res.get("session_id"), "result": (res.get("result") or "")[:6000]}


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
        turns.append(turn_record(len(turns), res, time.time() - t0))
        (OUT / "turns.json").write_text(json.dumps(turns, indent=1, ensure_ascii=False))
        if finished(res):
            ending = "finished"; break
        if LIMIT.search(res.get("result") or "") and res.get("is_error"):
            ending = "usage limit"; break
        if res.get("timed_out") or deadline - time.time() < MIN_TURN_SECONDS:
            ending = "out of time"; break
        if not res.get("session_id"):
            ending = "session crashed"; break
        if len(turns) > MAX_REPLIES:
            break
        args = ["-p", reply, "--resume", res["session_id"]]
    PHASES["build"] = round(sum(t["seconds"] for t in turns))
    return ending


def stop_leftovers() -> None:
    """Everything but this script: dev servers, loops and watchers the build or the tester started."""
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
    if not ((WORK / "output" / "index.html").exists() or (WORK / "output" / "START.txt").exists()):
        (OUT / "test").mkdir(exist_ok=True)   # nothing a user could open: no tester session
        (OUT / "test" / "report.json").write_text(json.dumps({"opened_by": "failed", "checks": [], "notes": "no deliverable in ~/work/output"}))
        return
    before = fingerprint()
    path = os.pathsep.join(x for x in os.environ["PATH"].split(os.pathsep) if ".local/bin" not in x)
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(HOME / ".tester-config"), "PATH": path}
    t0 = time.time()
    claude(["-p", (IN / f"test-{TASK}.md").read_text()], OUT / "test.jsonl", TEST_SECONDS, env=env, cwd=TESTER)
    PHASES["test"] = round(time.time() - t0)
    stop_leftovers()
    after = fingerprint()
    touched = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    shutil.copytree(TESTER, OUT / "test", ignore=shutil.ignore_patterns("profile"), dirs_exist_ok=True)
    (OUT / "test" / "touched.json").write_text(json.dumps(touched, indent=1))


def collect() -> None:
    files = fingerprint()
    (OUT / "files.json").write_text(json.dumps(sorted(files), indent=1, ensure_ascii=False))
    if (WORK / "output").exists():
        shutil.copytree(WORK / "output", OUT / "deliverables", ignore=shutil.ignore_patterns(*SKIP), dirs_exist_ok=True)
    sh(f"tar czf {OUT / 'project.tgz'} " + " ".join(f"--exclude={x}" for x in SKIP) + " -C ~ work")
    if (HOME / ".claude" / "projects").exists():
        shutil.copytree(HOME / ".claude" / "projects", OUT / "sessions", dirs_exist_ok=True)


def retest() -> None:
    """The tester again, on a build already made, after a fix to the tester's tools (never to the app).
    Earlier verdicts stay in test-prev-<n>/. Dependencies are not in project.tgz: every folder with a
    package.json gets `npm install` again, from its lockfile, as the build had left it."""
    if (OUT / "test").exists():
        n = 1 + sum(1 for d in OUT.glob("test-prev-*"))
        (OUT / "test").rename(OUT / f"test-prev-{n}")
    sh(f"tar xzf {OUT / 'project.tgz'} -C {HOME}")
    for pkg in WORK.rglob("package.json"):
        if not SKIP.intersection(pkg.relative_to(WORK).parts):
            sh("npm install --no-audit --no-fund", pkg.parent)
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
    (OUT / "env.txt").write_text(f"task {TASK}\nclaude {sh(REAL_CLAUDE + ' --version')}\nmodel {MODEL}\n")
    prepare()
    if REPO != CONTROL:
        setup()
    ending = build()
    stop_leftovers()
    collect()
    test()
    (OUT / "phases.json").write_text(json.dumps({**PHASES, "ending": ending}, indent=1))
    print(f"{REPO} {TASK}: {ending}", flush=True)
