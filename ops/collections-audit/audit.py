"""What you get if you install a whole skill collection: a count from the files, no model involved.

  python ops/collections-audit/audit.py     # clones the repos in candidates.json (shallow), writes results.json and RESULTS.md

For every SKILL.md in a collection: does its frontmatter meet the Agent Skills format (a name of
at most 64 lowercase letters, digits and hyphens; a description of 1 to 1,024 characters), is
the body within the 500 lines the format's guidance recommends, and does the name repeat inside
the collection. Then the combined length of distinct names and descriptions, at four
characters per token: an upper bound on what listing them all would take. Claude Code does not
list them all (see ops/codex-runs: past a budget it shows names only).
Nothing is executed.
"""
import json
import re
import statistics
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
CLONES = HERE / "clones"
NAME_OK = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX, DESC_MAX, BODY_LINES_MAX, CHARS_PER_TOKEN = 64, 1024, 500, 4
SKIP = {"node_modules", ".git"}


def clone(repo: str) -> Path:
    dest = CLONES / repo.replace("/", "__")
    if not dest.exists():
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"https://github.com/{repo}.git", str(dest)], check=True, timeout=900)
    return dest


def frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fields, key = {}, None
    for line in m.group(1).splitlines():
        top = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if top:
            key = top.group(1); fields[key] = top.group(2).strip().strip("|>").strip()
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return {k: v.strip("\"'") for k, v in fields.items()}, m.group(2)


def skill(path: Path) -> dict:
    fields, body = frontmatter(path.read_text(errors="ignore"))
    name, desc = fields.get("name", ""), fields.get("description", "")
    problems = [p for p, bad in (("no frontmatter", not fields), ("no name", bool(fields) and not name), ("no description", bool(fields) and not desc),
                                 ("name not lowercase-hyphen", bool(name) and not NAME_OK.match(name)), ("name over 64", len(name) > NAME_MAX),
                                 ("description over 1,024", len(desc) > DESC_MAX)) if bad]
    return {"name": name or path.parent.name, "desc_chars": len(desc), "body_lines": body.count("\n") + 1, "problems": problems,
            "has_scripts": (path.parent / "scripts").is_dir()}


def audit(c: dict) -> dict:
    root = clone(c["repo"])
    files = [f for f in root.rglob("SKILL.md") if not (set(f.relative_to(root).parts) & SKIP)]
    skills = [skill(f) for f in files]
    count = lambda pred: sum(1 for s in skills if pred(s))   # noqa: E731
    names = Counter(s["name"] for s in skills)
    # A name can be installed once: copies of a skill kept for other agents or plugins do not add to the cost.
    first = {s["name"]: s for s in reversed(skills)}
    listed = sum(len(s["name"]) + min(s["desc_chars"], DESC_MAX) for s in first.values())
    extras = {k: sum(1 for f in root.rglob("*.md") if k in f.parts and not (set(f.relative_to(root).parts) & SKIP)) for k in ("commands", "agents")}
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()[:12]
    return {**c, "skills": len(skills), "unique": len(first), **extras, "valid": count(lambda s: not s["problems"]), "problems": dict(Counter(p for s in skills for p in s["problems"])),
            "long_bodies": count(lambda s: s["body_lines"] > BODY_LINES_MAX), "repeated_names": sum(n - 1 for n in names.values() if n > 1),
            "with_scripts": count(lambda s: s["has_scripts"]), "median_desc_chars": round(statistics.median(s["desc_chars"] for s in skills)) if skills else 0,
            "standing_tokens": round(listed / CHARS_PER_TOKEN), "commit": head}


def markdown(rows: list[dict]) -> str:
    out = ["| Collection | ★ | Skill files | Distinct skills | Meet the format | Repeated names | Over 500 lines | With scripts | Names and descriptions, tokens (estimate) | Commands | Agents |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in sorted(rows, key=lambda r: -r["skills"]):
        share = f"{r['valid']}/{r['skills']}" if r["skills"] else "-"
        out.append(f"| {r['repo']} | {r['stars']:,} | {r['skills']} | {r['unique']} | {share} | {r['repeated_names']} | {r['long_bodies']} | {r['with_scripts']} | {r['standing_tokens']:,} | {r['commands']} | {r['agents']} |")
    out += ["", "Format problems:", ""] + [f"- {r['repo']}: {r['problems']}" for r in rows if r["problems"]]
    return "\n".join(out) + "\n"


def main() -> None:
    CLONES.mkdir(exist_ok=True)
    rows = [audit(c) for c in json.loads((HERE / "candidates.json").read_text())]
    (HERE / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    (HERE / "RESULTS.md").write_text(markdown(rows))
    print(markdown(rows))


if __name__ == "__main__":
    main()
