"""Run the vibe coding test: one fresh sandbox per tool and task, strictly serial.

  python3 ops/vibe-coding-runs/run.py t1 owner/repo [owner/repo ...]
  python3 ops/vibe-coding-runs/run.py t1 --next 4        # the next 4 candidates without a finished run
  python3 ops/vibe-coding-runs/run.py t1 --retest owner/repo ...   # the tester again on builds already made
  python3 ops/vibe-coding-runs/run.py --login-check      # a tool's own `claude` is signed in?

Each run is a pptrun container (ops/ppt-runs/sandbox) with in/ mounted and in/vibe.py as its
entrypoint; results land in out/<task>/<owner__repo>/. Needs CLAUDE_CODE_OAUTH_TOKEN in
~/.claude/.env. Serial because every run draws on the same subscription: check its usage
between batches, and stop at the limits rather than spill into paid extra usage.
"""
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ppt_run", HERE.parent / "ppt-runs" / "run.py")
ppt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ppt)
MINUTES = {"t1": (30, 15), "t2": (45, 25)}      # the build's limit, the tester's limit
SETUP_MINUTES, GRACE_MINUTES = 15, 10
# Why a build was tested again (--retest): the tester's "reopen" step first quit Chromium, which
# loses localStorage writes still on their way to disk, then reopened in a second tab, which races
# with apps that save as they load. Now the checks use index.html from a local address (the test
# browser's localStorage for file:// pages is unreliable) and reopen by closing every tab first.
RETEST_WHY = "tester kit v3: checks on a local address, reopen = close every tab, then open a new one"


def docker(name: str, token: str, out: Path, extra: list[str], args: list[str]) -> list[str]:
    return ["docker", "run", "--rm", "--name", name, "-e", f"CLAUDE_CODE_OAUTH_TOKEN={token}", *extra,
            "-v", f"{HERE / 'in'}:/in:ro", "-v", f"{out}:/out", "--entrypoint", "python3", ppt.IMAGE, "/in/vibe.py", *args]


def run(task: str, repo: str, token: str) -> dict:
    out = HERE / "out" / task / repo.replace("/", "__"); out.mkdir(parents=True, exist_ok=True)
    build, test = MINUTES[task]
    name = f"vibe-{task}-{out.name.lower()[:40]}"
    env = ["-e", f"TASK={task}", "-e", f"RUN_MINUTES={build}", "-e", f"TEST_MINUTES={test}"]
    t0 = time.time()
    try:
        p = subprocess.run(docker(name, token, out, env, [repo]), capture_output=True, text=True,
                           timeout=(SETUP_MINUTES + build + test + GRACE_MINUTES) * 60)
        status = "done" if p.returncode == 0 else f"exit {p.returncode}"
        (out / "docker.log").write_text(p.stdout[-20000:] + p.stderr[-20000:])
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        status = "timeout"
    meta = {"repo": repo, "task": task, "status": status, "seconds": round(time.time() - t0), "finished": time.strftime("%Y-%m-%d %H:%M")}
    (out / "run.json").write_text(json.dumps(meta, indent=1))
    return meta


def pending(task: str) -> list[str]:
    repos = [c["repo"] for c in json.loads((HERE / "candidates.json").read_text())]
    return [r for r in repos if not (HERE / "out" / task / r.replace("/", "__") / "run.json").exists()]


def main() -> None:
    token = ppt.env_file().get("CLAUDE_CODE_OAUTH_TOKEN")
    if not token:
        sys.exit("CLAUDE_CODE_OAUTH_TOKEN missing from ~/.claude/.env (run `claude setup-token`)")
    if sys.argv[1:] == ["--login-check"]:
        check = HERE / "out" / "login-check"; check.mkdir(parents=True, exist_ok=True)
        subprocess.run(docker("vibe-login-check", token, check, [], ["--login-check"]))
        return
    task, rest = sys.argv[1], sys.argv[2:]
    if rest[:1] == ["--retest"]:
        for repo in rest[1:]:
            out = HERE / "out" / task / repo.replace("/", "__")
            env = ["-e", f"TASK={task}", "-e", f"TEST_MINUTES={MINUTES[task][1]}", "-e", f"RETEST_WHY={RETEST_WHY}"]
            p = subprocess.run(docker(f"vibe-retest-{task}-{out.name.lower()[:30]}", token, out, env, ["--retest", repo]), capture_output=True, text=True)
            print(f"{time.strftime('%Y-%m-%d %H:%M')} {task} {repo}: retest exit {p.returncode}", flush=True)
        return
    repos = pending(task)[:int(rest[1])] if rest[:1] == ["--next"] else rest
    for repo in repos:
        meta = run(task, repo, token)
        print(f"{meta['finished']} {task} {repo}: {meta['status']} in {meta['seconds']}s", flush=True)


if __name__ == "__main__":
    main()
