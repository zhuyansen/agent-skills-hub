"""Filler skills for the crowding levels of the trigger test: in/fillers/<name>/SKILL.md.

  python ops/codex-runs/make_fillers.py     # needs ops/collections-audit/clones (run that audit first)

Real skills from two large public collections (alirezarezvani/claude-skills, then
davila7/claude-code-templates), one per name, only those whose frontmatter meets the format,
SKILL.md alone. They are what an agent has installed after "install everything": the test asks
whether the 12 skills under test are still found among 100 or 500 others.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "collections-audit"))
from audit import CLONES, SKIP, frontmatter, skill  # noqa: E402

SOURCES = ["alirezarezvani__claude-skills", "davila7__claude-code-templates"]
WANT = 500


def main() -> None:
    dest = HERE / "in" / "fillers"
    shutil.rmtree(dest, ignore_errors=True)
    taken = {p["skill"] for p in json.loads((HERE / "in" / "prompts.json").read_text()) if p["skill"]}
    order = []
    for src in SOURCES:
        root = CLONES / src
        for f in sorted(root.rglob("SKILL.md")):
            if set(f.relative_to(root).parts) & SKIP or skill(f)["problems"]:
                continue
            name = frontmatter(f.read_text(errors="ignore"))[0]["name"]
            if name in taken or len(order) >= WANT:
                continue
            taken.add(name); order.append(name)
            (dest / name).mkdir(parents=True)
            shutil.copy2(f, dest / name / "SKILL.md")
    (HERE / "in" / "fillers.json").write_text(json.dumps(order, indent=1))   # the first N of this list are level N
    print(len(order), "fillers")


if __name__ == "__main__":
    main()
