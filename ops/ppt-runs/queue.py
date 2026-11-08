"""Run a test project's candidates one at a time through run.py, surviving the subscription's usage limit.

  RUNS_DIR=ops/slop-ui-runs NO_RENDER=1 RUN_MINUTES=20 python3 ops/ppt-runs/queue.py
  RUNS_DIR=ops/3d-runs SANDBOX_IMAGE=pptrun-3d:1 FORCE_SETUP=1 NO_RENDER=1 RUN_MINUTES=25 python3 ops/ppt-runs/queue.py

The image test's queue (ops/image-runs/run_queue.py) made general: the project and its settings come from the
environment, as run.py reads them. A run that ends on the usage limit says nothing about the skill, so it is moved
to out-limited/ and retried after a wait (at most three times); a run Docker never started stops the queue.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = (ROOT / os.environ["RUNS_DIR"]).resolve()
OUT, LIMITED = PROJECT / "out", PROJECT / "out-limited"
LIMIT = re.compile(r"usage limit|hit your (usage )?limit|limit reached|rate_limit_error|overloaded_error|resets? (at|in) ", re.I)
DOCKER_DOWN = re.compile(r"Cannot connect to the Docker daemon|docker: command not found|Is the docker daemon running", re.I)
RETRIES, LIMIT_WAIT_SECONDS = 3, 30 * 60


def log(msg: str) -> None:
    print(f"{datetime.now().strftime('%m-%d %H:%M')} {msg}", flush=True)


def pending() -> list[str]:
    repos = [c["repo"] for c in json.loads((PROJECT / "candidates.json").read_text())]
    return [r for r in repos if not (OUT / r.replace("/", "__") / "run.json").exists()]


def run_text(folder: Path) -> str:
    """What the run said at the end: Claude Code's stderr and the agent's result when it was an error."""
    parts = [(folder / "claude.err").read_text(errors="ignore")[-3000:] if (folder / "claude.err").exists() else ""]
    lines = (folder / "transcript.jsonl").read_text(errors="ignore").splitlines() if (folder / "transcript.jsonl").exists() else []
    for line in reversed(lines):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "result":
            parts.append(str(ev.get("result") or "") if ev.get("is_error") or ev.get("subtype") != "success" else "")
            break
    return "\n".join(parts)


def run_one(repo: str) -> str:
    """Run one repo; returns "ok", "limit" (moved aside, retry later) or "docker" (stop)."""
    proc = subprocess.run([sys.executable, "ops/ppt-runs/run.py", repo], cwd=ROOT, capture_output=True, text=True)
    log(f"{repo}: {(proc.stdout.strip().splitlines() or ['?'])[-1]}")
    folder = OUT / repo.replace("/", "__")
    said = run_text(folder) + proc.stderr
    if DOCKER_DOWN.search(said):
        shutil.rmtree(folder, ignore_errors=True)
        return "docker"
    if LIMIT.search(said):
        LIMITED.mkdir(exist_ok=True)
        shutil.move(str(folder), str(LIMITED / f"{folder.name}-{int(time.time())}"))
        return "limit"
    return "ok"


def main() -> None:
    done, tries = 0, {}
    while (todo := pending()):
        repo = todo[0]
        outcome = run_one(repo)
        if outcome == "docker":
            log("Docker is not running: stopping")
            break
        if outcome == "limit":
            tries[repo] = tries.get(repo, 0) + 1
            if tries[repo] >= RETRIES:
                log(f"{repo}: usage limit {RETRIES} times: stopping")
                break
            log(f"usage limit; waiting {LIMIT_WAIT_SECONDS // 60} min")
            time.sleep(LIMIT_WAIT_SECONDS)
            continue
        done += 1
    log(f"{done} runs this pass; {len(pending())} still to run")


if __name__ == "__main__":
    main()
