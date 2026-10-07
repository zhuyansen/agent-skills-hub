"""Run PPT skills end to end in the sandbox, one at a time.

  python ops/ppt-runs/run.py owner/repo [owner/repo ...]
  python ops/ppt-runs/run.py --all          # every repo in candidates.json without a finished run

Each run: a fresh pptrun container clones the repo, installs its SKILL.md folders into
Claude Code, builds a deck from in/brief.md with in/prompt.txt, and renders the result
(sandbox/render.py). Results land in out/<owner__repo>/. Needs CLAUDE_CODE_OAUTH_TOKEN
(from `claude setup-token`) and FLATROUTER_* in ~/.claude/.env; image-route skills reach
gpt-image-2 through FlatRouter's OpenAI-compatible endpoint. Strictly serial: the
subscription has a usage window, and parallel runs would only hit it sooner.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
IMAGE = "pptrun:1"
RUN_MINUTES = 30
GRACE_SECONDS = 600     # render + install time on top of the agent's limit


def env_file() -> dict:
    vals = {}
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); vals[k.strip()] = v.strip().strip('"')
    return vals


def docker_env(e: dict) -> list[str]:
    pairs = {"CLAUDE_CODE_OAUTH_TOKEN": e["CLAUDE_CODE_OAUTH_TOKEN"], "OPENAI_API_KEY": e["FLATROUTER_API_KEY"],
             "OPENAI_BASE_URL": e["FLATROUTER_BASE_URL"], "RUN_MINUTES": str(RUN_MINUTES)}
    return [x for k, v in pairs.items() for x in ("-e", f"{k}={v}")]


def run(repo: str, e: dict) -> dict:
    out = OUT / repo.replace("/", "__"); out.mkdir(parents=True, exist_ok=True)
    cmd = ["docker", "run", "--rm", "--name", f"pptrun-{out.name.lower()[:50]}", *docker_env(e),
           "-v", f"{HERE / 'in'}:/in:ro", "-v", f"{out}:/out", IMAGE, repo]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=RUN_MINUTES * 60 + GRACE_SECONDS)
        status = "done" if p.returncode == 0 else f"exit {p.returncode}"
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", f"pptrun-{out.name.lower()[:50]}"], capture_output=True)
        status = "timeout"
    meta = {"repo": repo, "status": status, "seconds": round(time.time() - t0), "finished": time.strftime("%Y-%m-%d %H:%M")}
    (out / "run.json").write_text(json.dumps(meta, indent=1))
    return meta


def pending() -> list[str]:
    repos = [c["repo"] for c in json.loads((HERE / "candidates.json").read_text())]
    return [r for r in repos if not (OUT / r.replace("/", "__") / "run.json").exists()]


def main() -> None:
    e = env_file()
    if not e.get("CLAUDE_CODE_OAUTH_TOKEN"):
        sys.exit("CLAUDE_CODE_OAUTH_TOKEN missing from ~/.claude/.env (run `claude setup-token`)")
    repos = pending() if sys.argv[1:] == ["--all"] else sys.argv[1:]
    for repo in repos:
        meta = run(repo, e)
        print(f"{meta['finished']} {repo}: {meta['status']} in {meta['seconds']}s", flush=True)


if __name__ == "__main__":
    main()
