"""Copy the paper-based scores from results.json into the PPT page's run data
(frontend/scripts/scenario-runs.json): PEI level, rubric score and its dimensions.

  python ops/ppt-runs/to_page.py      # after table.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
RUNS = HERE.parents[1] / "frontend/scripts/scenario-runs.json"
FIELDS = ("pei", "checklist", "checklist_dims", "rework")


def main() -> None:
    results = {r["repo"]: r for r in json.loads((HERE / "results.json").read_text())}
    data = json.loads(RUNS.read_text())
    entries = data["ppt-presentation"]["runs"]
    for repo, entry in entries.items():
        r = results.get(repo) or {}
        entry.update({k: r[k] for k in FIELDS if k in r})
        entry.pop("design", None)   # the holistic 1-5 rating, replaced by the rubric
    data["ppt-presentation"]["method"] = {"rubric": "https://arxiv.org/abs/2603.07244", "pei": "https://arxiv.org/abs/2601.09487"}
    RUNS.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"{sum('checklist' in e for e in entries.values())} of {len(entries)} entries scored")


if __name__ == "__main__":
    main()
