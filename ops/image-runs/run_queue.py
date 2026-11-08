"""The image test's queue: every candidate without a finished run, one at a time, then the judge.

  python3 ops/image-runs/run_queue.py

The owner asked on 2026-11-07 for all 132 candidates, on APIMart for images and text: about eight
hours on the Claude subscription. A run that ends on the subscription's usage limit says nothing
about the skill, so it is moved to out-limited/ and retried once the limit resets (at most three
times). A run Docker never started stops the queue rather than being recorded as the skill's
failure, and so does an APIMart balance under BALANCE_FLOOR.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT, LIMITED = HERE / "out", HERE / "out-limited"
# IMAGE_FORCE_NEWEST (owner, 11-07): every image call on the newest model of its family (GPT Image 2.6,
# Nano Banana 2.1, FLUX 3), so skills compare on their prompts and workflow.
ENV = {"RUNS_DIR": "ops/image-runs", "IMAGE_ROUTES": "1", "IMAGE_FORCE_NEWEST": "1", "IMAGE_KEY_NAME": "APIMART_MULTI_KEY",
       "TEXT_PROXY": "1", "TEXT_VIA": "image", "NO_RENDER": "1", "RUN_MINUTES": "20"}
LIMIT = re.compile(r"usage limit|hit your (usage )?limit|limit reached|rate_limit_error|overloaded_error|resets? (at|in) ", re.I)
DOCKER_DOWN = re.compile(r"Cannot connect to the Docker daemon|docker: command not found|Is the docker daemon running", re.I)
RETRIES, LIMIT_WAIT_SECONDS, BALANCE_FLOOR, BALANCE_EVERY = 3, 30 * 60, 5.0, 10


def log(msg: str) -> None:
    print(f"{datetime.now().strftime('%m-%d %H:%M')} {msg}", flush=True)


def env_file() -> dict:
    vals = {}
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); vals[k.strip()] = v.strip().strip('"')
    return vals


def balance(e: dict) -> float | None:
    try:
        r = requests.get("https://api.apimart.ai/v1/user/balance", timeout=25,
                         headers={"Authorization": f"Bearer {e['APIMART_MULTI_KEY']}"})
        return float(r.json().get("remain_balance"))
    except Exception:  # noqa: BLE001 (a failed check does not stop the queue)
        return None


def pending() -> list[str]:
    repos = [c["repo"] for c in json.loads((HERE / "candidates.json").read_text())]
    return [r for r in repos if not (OUT / r.replace("/", "__") / "run.json").exists()]


def run_text(folder: Path) -> str:
    """What the run said at the end: the agent's result and Claude Code's stderr."""
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
    proc = subprocess.run([sys.executable, "ops/ppt-runs/run.py", repo], cwd=ROOT, env={**os.environ, **ENV},
                          capture_output=True, text=True)
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
    e, done, tries = env_file(), 0, {}
    while (todo := pending()):
        repo = todo[0]
        if done % BALANCE_EVERY == 0 and (b := balance(e)) is not None:
            log(f"APIMart balance ${b:.2f}")
            if b < BALANCE_FLOOR:
                log("balance under the floor: stopping"); break
        outcome = run_one(repo)
        if outcome == "docker":
            log("Docker is not running: stopping"); break
        if outcome == "limit":
            tries[repo] = tries.get(repo, 0) + 1
            if tries[repo] >= RETRIES:
                log(f"{repo}: usage limit {RETRIES} times: stopping"); break
            log(f"usage limit; waiting {LIMIT_WAIT_SECONDS // 60} min"); time.sleep(LIMIT_WAIT_SECONDS)
            continue
        done += 1
    log(f"{done} runs this pass; {len(pending())} still to run")
    subprocess.run([sys.executable, "ops/image-runs/score_image.py"], cwd=ROOT)


if __name__ == "__main__":
    main()
