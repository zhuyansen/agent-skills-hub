"""Runs inside the sandbox: all skills installed for one agent, every prompt asked once, and
the run stopped as soon as the agent opens a skill (the question is which skill it reaches for,
not whether it finishes the job). Usage: [FILLERS=100] python3 /in/trigger.py codex|claude
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

AGENT = sys.argv[1]
FILLERS = int(os.environ.get("FILLERS", 0))     # crowding level: this many other real skills installed beside the 12
HOME = Path.home()
SKILL_DIR = HOME / (".codex" if AGENT == "codex" else ".claude") / "skills"
OUT = Path("/out") / (AGENT + (f"-{FILLERS}" if FILLERS else ""))
LIMIT_SECONDS = 150
CODEX_CONFIG = """model = "gpt-6-astra"
model_provider = "flatrouter"
[model_providers.flatrouter]
name = "FlatRouter"
base_url = "https://api.flatrouter.com/v1"
env_key = "FLATROUTER_API_KEY"
wire_api = "responses"
"""


def setup() -> list[str]:
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    for d in Path("/in/skills").iterdir():
        shutil.copytree(d, SKILL_DIR / d.name, dirs_exist_ok=True)
    for name in json.loads(Path("/in/fillers.json").read_text())[:FILLERS]:
        shutil.copytree(Path("/in/fillers") / name, SKILL_DIR / name, dirs_exist_ok=True)
    if AGENT == "codex":
        (HOME / ".codex" / "config.toml").write_text(CODEX_CONFIG)
        subprocess.run(["npm", "i", "-g", "--prefix", str(HOME / ".npm-global"), "@openai/codex"], capture_output=True)
        os.environ["PATH"] = f"{HOME}/.npm-global/bin:" + os.environ["PATH"]
    return sorted(d.name for d in SKILL_DIR.iterdir())


def command(prompt: str) -> list[str]:
    if AGENT == "codex":
        return ["codex", "exec", "--json", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox", prompt]
    return ["claude", "-p", prompt, "--model", os.environ.get("CLAUDE_MODEL", "opus"), "--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose"]


def opened(line: str, skills: list[str]) -> str | None:
    """The skill this event opens, if any: its folder is read, or (Claude Code) the Skill tool names it."""
    try:
        e = json.loads(line)
    except ValueError:
        return None
    if AGENT == "codex":
        item = e.get("item") or {}
        text = item.get("command", "") if item.get("type") == "command_execution" else ""
    else:
        if e.get("type") != "assistant":
            return None
        uses = [c for c in e["message"].get("content", []) if c.get("type") == "tool_use"]
        text = " ".join(json.dumps(c.get("input", {})) + (" SKILLTOOL" if c["name"] == "Skill" else "") for c in uses)
    for s in skills:
        if f"skills/{s}/" in text or ("SKILLTOOL" in text and f'"{s}"' in text):
            return s
    return None


def run(p: dict, skills: list[str]) -> dict:
    work = Path("/tmp/work") / p["id"].replace(":", "_"); work.mkdir(parents=True, exist_ok=True)
    log = OUT / (p["id"].replace(":", "_") + ".jsonl")
    t0, hit = time.time(), None
    with log.open("w") as f:
        proc = subprocess.Popen(command(p["prompt"]), cwd=work, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        os.set_blocking(proc.stdout.fileno(), False)
        while proc.poll() is None and time.time() - t0 < LIMIT_SECONDS and not hit:
            line = proc.stdout.readline()
            if not line:
                time.sleep(0.2); continue
            f.write(line)
            hit = opened(line, skills)
        ended = "opened a skill" if hit else "finished" if proc.poll() is not None else "time limit"
        proc.kill()
    return {**p, "agent": AGENT, "opened": hit, "ended": ended, "seconds": round(time.time() - t0)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    skills = setup()
    results = []
    for p in json.loads(Path("/in/prompts.json").read_text()):
        r = run(p, skills)
        results.append(r)
        print(f"{AGENT} {p['id']:48} -> {r['opened'] or '-':38} {r['ended']} {r['seconds']}s", flush=True)
        (OUT / "results.json").write_text(json.dumps(results, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
