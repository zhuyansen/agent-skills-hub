"""Keep GitHub traffic beyond the 14 days GitHub shows.

  python ops/github_traffic/export.py

For the site repo and every awesome list: daily views and clones, and the top referrers
and paths as of this run. Each repo has one file, ops/github_traffic/data/<repo>.json;
a run merges into it (a day already stored is overwritten with GitHub's newer count), so
weekly runs lose nothing. Runs weekly from .github/workflows/github-traffic.yml.

Needs a token that can read traffic: classic `repo` scope, or fine-grained with
Administration read-only on these repos (GH_TOKEN env, else the gh CLI's own login).
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
OWNER = "zhuyansen"
SITE_REPO = "agent-skills-hub"


def repos() -> list[str]:
    sys.path.insert(0, str(ROOT / "ops/awesome"))
    from check_consistency import LISTS
    return [SITE_REPO, *sorted({r.split("/", 1)[1] for r in LISTS.values()})]


def api(path: str) -> dict | list:
    out = subprocess.run(["gh", "api", f"repos/{OWNER}/{path}"], capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr.strip()[:200])
    return json.loads(out.stdout)


def merge_days(stored: dict, fresh: list[dict]) -> dict:
    for day in fresh:
        stored[day["timestamp"][:10]] = {"count": day["count"], "uniques": day["uniques"]}
    return dict(sorted(stored.items()))


def export(repo: str) -> str:
    path = DATA / f"{repo}.json"
    rec = json.loads(path.read_text()) if path.exists() else {"views": {}, "clones": {}, "referrers": {}, "paths": {}}
    rec["views"] = merge_days(rec["views"], api(f"{repo}/traffic/views")["views"])
    rec["clones"] = merge_days(rec["clones"], api(f"{repo}/traffic/clones")["clones"])
    today = date.today().isoformat()   # referrers and paths are 14-day totals: kept per run
    rec["referrers"][today] = api(f"{repo}/traffic/popular/referrers")
    rec["paths"][today] = [{k: p[k] for k in ("path", "count", "uniques")} for p in api(f"{repo}/traffic/popular/paths")]
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    views = sum(v["count"] for v in rec["views"].values())
    return f"{repo}: {len(rec['views'])} days stored, {views:,} views"


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    failed = 0
    for repo in repos():
        try:
            print(export(repo))
        except Exception as exc:  # noqa: BLE001 — one repo failing must not lose the others
            failed += 1
            print(f"{repo}: FAILED {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
