"""Move a keyword-picked scenario page to a reviewed one (pages in page_profiles.PAGES).

  python ops/jev-review/upgrade_page.py collect <slug> <catalog.json>
  python ops/jev-review/scenario_gate.py judge <slug>
  python ops/jev-review/upgrade_page.py split <slug>
  python ops/jev-review/scenario_gate.py types <slug>
  python ops/jev-review/upgrade_page.py publish <slug> <catalog.json>

collect   candidates: GitHub search in every star band (50+, 20-49, 5-19) and the
          catalog's rows of 50 stars or more, both through the page's word filter.
          <catalog.json> is a REST export of skills with stars >= 50 (all columns).
split     repos of 50 stars or more go to page-judged.json, where on_page() lists them
          when on topic; the rest stay in judged.json and also need the quality bar.
publish   the page lists the reviewed repos only (reviewed_only), sorted by stars;
          Chinese descriptions for listed repos that have none; repos the catalog lacks
          are queued for the sync and graded (daily_video_pass.queue_and_grade).
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(HERE), str(ROOT / "backend"), str(ROOT / "ops/awesome")]
import scenario_gate as gate  # noqa: E402
from page_profiles import is_candidate  # noqa: E402

BANDS = ("stars:>=50", *gate.STAR_BANDS)
DESC_WORKERS = 10
DESC_SAVE = 10


def _topics(raw) -> list[str]:
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw) if raw and raw != "None" else []
    except ValueError:
        return []


def catalog_rows(path: str) -> list[dict]:
    return [{"full_name": r["repo_full_name"], "name": r["repo_name"], "stargazers_count": int(float(r["stars"])),
             "description": r.get("description") or "", "topics": _topics(r.get("topics")),
             "created_at": r.get("created_at") or "", "pushed_at": r.get("last_commit_at") or ""}
            for r in json.loads(Path(path).read_text())]


def live_cards(slug: str) -> set[str]:
    """owner/repo of every card on the live page."""
    req = urllib.request.Request(f"https://agentskillshub.top/best/{slug}/", headers={"User-Agent": "agentskillshub-upgrade"})
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            html = res.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:   # a new page: nothing live to keep
            return set()
        raise
    return {m.lower() for m in re.findall(r'class="bp-card-title" href="/skill/([^/"]+/[^/"]+)/"', html)}


def collect(slug: str, catalog: str) -> None:
    seen: dict[str, dict] = {}
    for query in gate.QUERIES[slug]["topic"]:
        for band in BANDS:
            for repo in gate.search(f"{query} {band}"):
                if is_candidate(slug, repo["name"], repo.get("description") or "", repo.get("topics") or []):
                    seen.setdefault(repo["full_name"].lower(), gate.slim(repo, "search"))
        print(f"  {query}: {len(seen)} so far", flush=True)
    # Every card the live page shows today is reviewed too: the upgrade only adds.
    live = live_cards(slug)
    for repo in catalog_rows(catalog):
        if is_candidate(slug, repo["name"], repo["description"], repo["topics"]) or repo["full_name"].lower() in live:
            seen.setdefault(repo["full_name"].lower(), gate.slim(repo, "catalog"))
    rows = sorted(seen.values(), key=lambda r: -r["stars"])
    (gate.out_dir(slug) / "candidates.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print(f"{len(rows)} candidates · {sum(r['stars'] >= gate.PAGE_FLOOR for r in rows)} with 50+ stars")


def split(slug: str) -> None:
    below_path, above_path = gate.state_dir(slug) / "judged.json", gate.state_dir(slug) / "page-judged.json"
    rows = json.loads(below_path.read_text()) + (json.loads(above_path.read_text()) if above_path.exists() else [])
    rows = list({r["repo"]: r for r in rows}.values())
    above = [r for r in rows if r["stars"] >= gate.PAGE_FLOOR]
    below = [r for r in rows if r["stars"] < gate.PAGE_FLOOR]
    above_path.write_text(json.dumps(above, ensure_ascii=False, indent=1))
    below_path.write_text(json.dumps(below, ensure_ascii=False, indent=1))
    listed = gate.on_page(slug)
    print(f"{len(above)} with 50+ stars, {len(below)} under · {len(listed)} would be listed "
          f"({sum(r['stars'] < gate.PAGE_FLOOR for r in listed)} under 50)")


def extra(slug: str) -> None:
    """Ask a page's `extra` topic questions of the rows that pass everything else, so a
    question added after the review costs one call per candidate, not a new review."""
    from concurrent.futures import ThreadPoolExecutor
    from jev_client import OpenRouter
    from page_profiles import PAGES
    questions = PAGES[slug].get("extra", {})
    p, jev = gate.profile(slug), OpenRouter()
    floor = p.get("topic_min", gate.RELEVANT)
    for name in ("judged.json", "page-judged.json"):
        path = gate.state_dir(slug) / name
        rows = json.loads(path.read_text())
        todo = [r for r in rows if any(k not in r for k in questions)
                and min(r.get("on_subject", 0), r.get("is_software", 0)) >= floor]
        ask = lambda r: gate.ask(jev, r, gate.readme_of(slug, r["repo"]), gate.README_RELEVANCE, questions, full=True)
        with ThreadPoolExecutor(gate.JUDGE_WORKERS) as pool:
            for row, answers in zip(todo, pool.map(ask, todo)):
                row.update(answers)
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"{name}: asked {len(todo)}")
    print(f"{len(gate.on_page(slug))} listed now · {jev.tokens} tokens")


def set_reviewed_only(slug: str, below: list[str]) -> None:
    """reviewed_only, sorted by stars, no cap; admit_reviewed holds the repos under 50 stars."""
    import daily_video_pass as dvp
    pages = json.loads(dvp.KEYWORDS.read_text())
    match = next(p for p in pages if p["slug"] == slug)["match"]
    match.update(reviewed_only=True, sort="stars", max_results=None)
    match["admit_reviewed"] = sorted(set(match.get("admit_reviewed", [])) | set(below))
    dvp.KEYWORDS.write_text(json.dumps(pages, ensure_ascii=False, indent=1) + "\n")


def describe_all(dvp, jev, rows: list[dict]) -> dict[str, str]:
    """Chinese descriptions, DESC_WORKERS at a time, saved every DESC_SAVE so an
    interrupted run keeps what it wrote."""
    from concurrent.futures import ThreadPoolExecutor
    zh: dict[str, str] = {}
    with ThreadPoolExecutor(DESC_WORKERS) as pool:
        for start in range(0, len(rows), DESC_SAVE):
            chunk = rows[start:start + DESC_SAVE]
            zh.update(zip((r["repo"] for r in chunk), (d for d, _ in pool.map(lambda r: dvp.describe_zh(r, jev), chunk))))
            have = json.loads(dvp.DESC_ZH.read_text())
            have.update({n: v for n, v in zh.items() if v})
            dvp.DESC_ZH.write_text(json.dumps(have, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
            print(f"  zh {min(start + DESC_SAVE, len(rows))}/{len(rows)}", flush=True)
    return zh


def describe(slug: str) -> None:
    """Chinese descriptions only, for pages published with --no-desc (10-03: FlatRouter gave
    6-8 a minute, so pages went live first with English text and Chinese followed)."""
    import daily_video_pass as dvp
    from jev_client import OpenRouter
    dvp.SLUG = slug
    have = json.loads(dvp.DESC_ZH.read_text())
    zh = describe_all(dvp, OpenRouter(), [r for r in gate.on_page(slug) if r["repo"] not in have])
    print(f"{slug}: {sum(bool(v) for v in zh.values())}/{len(zh)} new zh descriptions")


def publish(slug: str, catalog: str, with_desc: bool = True) -> None:
    import daily_video_pass as dvp
    from jev_client import OpenRouter
    dvp.SLUG = slug
    listed = gate.on_page(slug)
    set_reviewed_only(slug, [r["repo"] for r in listed if r["stars"] < gate.PAGE_FLOOR])
    jev = OpenRouter()
    todo = [r for r in listed if r["repo"] not in json.loads(dvp.DESC_ZH.read_text())]
    zh = describe_all(dvp, jev, todo) if with_desc else {}
    in_catalog = {r["full_name"].lower() for r in catalog_rows(catalog)}
    missing = [r["repo"] for r in listed if r["repo"].lower() not in in_catalog]
    db = dvp.queue_and_grade(missing) if missing else {"in_catalog": [], "queued_only": [], "graded": {}}
    print(f"{len(listed)} listed · {sum(bool(v) for v in zh.values())}/{len(zh)} new zh descriptions · "
          f"{len(missing)} not in the 50+ catalog: {len(db['in_catalog'])} already in the DB, "
          f"{len(db['queued_only'])} queued, {len(db['graded'])} graded · Jev ${jev.total_cost:.4f}")


if __name__ == "__main__":
    step, slug = sys.argv[1], sys.argv[2]
    {"collect": lambda: collect(slug, sys.argv[3]), "split": lambda: split(slug), "extra": lambda: extra(slug),
     "publish": lambda: publish(slug, sys.argv[3], "--no-desc" not in sys.argv),
     "describe": lambda: describe(slug)}[step]()
