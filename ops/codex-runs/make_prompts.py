"""Build the trigger test's inputs from the cloned skills: in/skills/<name>/ and in/prompts.json.

  python ops/codex-runs/make_prompts.py     # needs clones/ (see candidates.json) and FLATROUTER_* in ~/.claude/.env

For each skill a model (gpt-6-astra) writes three requests a user might type, from the skill's
own description: one that names the task plainly, one that describes the need without the
skill's name or its coined words, and one in the other language (English or Chinese). Six
unrelated requests are fixed below. Every prompt was read by hand afterwards; edits live in
in/prompts.json, so rerunning this overwrites them on purpose only.
"""
import json
import re
import shutil
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
SKILLS = HERE / "in" / "skills"
MAX_FILE = 300_000      # the test is about triggering: big assets are left out of the copy
NEGATIVES = [
    "Write a Python function that checks whether a string is a palindrome, ignoring case and punctuation.",
    "What is the difference between a process and a thread? Two or three sentences.",
    "Give me a regular expression that matches an ISO 8601 date like 2026-10-11.",
    "把这句话翻译成英文：今天下午三点开会，请带上上周的销售数据。",
    "List three common causes of a memory leak in a Node.js server.",
    "Rename the variable `tmp` to `total` in this snippet and return it: `tmp = 0\\nfor x in xs:\\n    tmp += x`",
]
ASK = """A user has an AI coding agent with many skills installed. Below is one skill's name and description.
Write three requests this user might type that this skill is meant for. Return JSON only:
{{"direct": "...", "indirect": "...", "other_language": "..."}}
- direct: asks for the task plainly, in the language of the description, without naming the skill.
- indirect: a realistic request for the same need that avoids the skill's name and any coined or brand words in the description (style names, mascots, product names); describe the outcome wanted instead.
- other_language: the direct request in the other language (Chinese if the description is English, English if it is Chinese).
Each is one or two sentences, self-contained (include a line of made-up material if the task needs input), and does not mention skills, plugins or tools.

Name: {name}
Description: {desc}"""


def env() -> dict:
    vals = {}
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); vals[k.strip()] = v.strip().strip('"')
    return vals


def ask(e: dict, text: str) -> dict:
    body = {"model": e.get("FLATROUTER_MODEL", "gpt-6-astra"), "temperature": 0, "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": text}]}
    req = urllib.request.Request(e["FLATROUTER_BASE_URL"] + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + e["FLATROUTER_API_KEY"], "Content-Type": "application/json"})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=300) as r:
        return json.loads(json.load(r)["choices"][0]["message"]["content"])


def front(skill_md: Path) -> tuple[str, str]:
    fm = re.search(r"^---\n(.*?)\n---", skill_md.read_text(errors="ignore"), re.S).group(1)
    name = re.search(r"^name:\s*(.+)$", fm, re.M).group(1).strip().strip("\"'")
    desc = re.search(r"^description:\s*(.*(?:\n[ \t]+.+)*)", fm, re.M).group(1)
    return name, " ".join(desc.replace("|", " ").split()).strip("\"'")


def copy_skill(src: Path, dest: Path) -> None:
    for f in src.rglob("*"):
        if f.is_file() and ".git" not in f.parts and "node_modules" not in f.parts and f.stat().st_size <= MAX_FILE:
            out = dest / f.relative_to(src)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)


def main() -> None:
    e = env()
    shutil.rmtree(SKILLS, ignore_errors=True)
    prompts = []
    for c in json.loads((HERE / "candidates.json").read_text()):
        clone = HERE / "clones" / c["repo"].replace("/", "__")
        skill_md = next(f for f in clone.rglob("SKILL.md") if "node_modules" not in f.parts)
        name, desc = front(skill_md)
        copy_skill(skill_md.parent, SKILLS / name)
        made = ask(e, ASK.format(name=name, desc=desc))
        prompts += [{"id": f"{name}:{k}", "skill": name, "repo": c["repo"], "kind": k, "prompt": made[k]} for k in ("direct", "indirect", "other_language")]
        print(name, "ok", flush=True)
    prompts += [{"id": f"none:{n}", "skill": None, "repo": None, "kind": "unrelated", "prompt": p} for n, p in enumerate(NEGATIVES, 1)]
    (HERE / "in" / "prompts.json").write_text(json.dumps(prompts, indent=1, ensure_ascii=False))
    print(len(prompts), "prompts")


if __name__ == "__main__":
    main()
