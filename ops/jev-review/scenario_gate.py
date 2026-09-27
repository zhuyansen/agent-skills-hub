"""Jev as the gate for a scenario page's repos under the 50-star floor.

A scenario page lists repos with >= 50 stars. Below that, stars say little (a repo
from last week has had no time to collect them), so the page admits a repo on what
its README shows instead. The questions, weights and cut-offs are the ones used on
2026-09-27 for the >= 50-star candidates of /best/opus-5-5-video/, fixed before any
answer here was seen.

  collect  GitHub search under the floor, then the page's own keyword matcher
  judge    README + two Jev calls per repo (relevance, quality); cached on disk
  report   table + the list for `match.admit_below_floor`
  audit    the same relevance questions for repos already on the page (names from a
           JSON list); off-topic ones go to `match.exclude_repos`

Usage: python ops/jev-review/scenario_gate.py <collect|judge|report> [slug]
       python ops/jev-review/scenario_gate.py audit <slug> <names.json>
Env:   OPENROUTER_API_KEY (judge); gh CLI signed in (collect, judge)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCENARIOS = ROOT / "frontend/scripts/scenario-keywords.json"

PAGE_FLOOR = 50          # frontend/scripts/shared-utils.mjs shouldIndex()
GATE_FLOOR = 5           # below this a search returns thousands of empty repos
WAVE_FLOOR = 1           # a repo that names the model needs only one star
STAR_BANDS = ("stars:20..49", "stars:5..19")
WAVE_BAND = "stars:1..4"
SEARCH_PAUSE = 2.2       # GitHub search: 30 requests a minute
PAGE_SIZE = 100
MAX_PAGES = 4
README_RELEVANCE = 3500  # characters of README each question set reads
README_QUALITY = 5000
RELEVANT = 0.5
HIGH, MID = 0.75, 0.50

QUERIES = {
    "opus-5-5-video": {
        "wave": ['"opus 5.5" video in:name,description'],
        "topic": [
            "hyperframes in:name,description,topics",
            "remotion skill in:name,description,topics",
            "claude video skill in:name,description",
            "claude code video in:name,description",
            "codex video skill in:name,description",
            "motion graphics skill in:name,description",
            "music video claude in:name,description",
        ],
        "names_model": r"opus[\s-]?5\.5",
    },
}

RELEVANCE = {
    "makes_video": {"type": "noul", "instructions": {
        "question": "Is the main purpose of `repo` to produce or edit video or motion graphics?",
        "focus": "The output is a video file or an animation meant to be watched, not images, slides or a web page."}},
    "agent_driven": {"type": "noul", "instructions": {
        "question": "Is `repo` meant to be operated by an AI coding agent such as Claude Code or Codex?",
        "focus": "A skill, a plugin, an MCP server, or a toolkit whose instructions are written for the agent."}},
    "code_rendered": {"type": "noul", "instructions": {
        "question": "Does `repo` render its video from code the agent writes (HTML, React, canvas, Remotion, HyperFrames, p5.js)?",
        "focus": "As opposed to sending a prompt to a video-generation model or an avatar service."}},
    "reusable_tool": {"type": "noul", "instructions": {
        "question": "Is `repo` a reusable tool or skill someone installs, rather than the source of one finished video?"}},
    "names_opus": {"type": "noul", "instructions": {
        "question": "Does `repo.readme` say it was made with, or for, a Claude Opus model specifically?"}},
}
QUALITY = {
    "shows_result": {"type": "noul", "instructions": {
        "question": "Does `repo.readme` show the finished output — a video, GIF, screenshot or a link to one?"}},
    "one_command_start": {"type": "noul", "instructions": {
        "question": "Can a reader start using `repo` from a single install or run command given in the README?"}},
    "specific_outcome": {"type": "noul", "instructions": {
        "question": "Does `repo.readme` state a concrete result the user gets, rather than general capability claims?",
        "focus": "For example '9:16 hand-drawn explainer from a markdown script', not 'powerful video automation'."}},
    "complete_docs": {"type": "noul", "instructions": {
        "question": "Is `repo.readme` organized and complete: install, usage and at least one worked example?"}},
    "novel_angle": {"type": "noul", "instructions": {
        "question": "Does `repo` do something visibly different from a generic Remotion or HyperFrames template or wrapper?",
        "focus": "A distinct visual style, a new input-to-video format, or a workflow other repos in this space do not offer."}},
    "shareable_output": {"type": "noul", "instructions": {
        "question": "Is the output of `repo` the kind of thing people post publicly — a striking style, a recognizable format, a music video?"}},
}
QUALITY_KEYS = ("shows_result", "one_command_start", "specific_outcome", "complete_docs")
HIT_KEYS = ("novel_angle", "shareable_output", "shows_result")


def out_dir(slug: str) -> Path:
    path = HERE / "out" / f"gate-{slug}"
    (path / "readme").mkdir(parents=True, exist_ok=True)
    return path


def gh(args: list[str]) -> str:
    return subprocess.run(["gh", "api", *args], capture_output=True, text=True).stdout


def search(query: str) -> list[dict]:
    found = []
    for page in range(1, MAX_PAGES + 1):
        raw = gh(["-X", "GET", "search/repositories", "-f", f"q={query} fork:false archived:false",
                  "-f", "sort=stars", "-f", f"per_page={PAGE_SIZE}", "-f", f"page={page}"])
        items = (json.loads(raw or "{}")).get("items") or []
        found += items
        time.sleep(SEARCH_PAUSE)
        if len(items) < PAGE_SIZE:
            break
    return found


def matches_page(repo: dict, match: dict) -> bool:
    """The page's keyword matcher (generate-scenario-pages.mjs matchSkills), minus the star gate."""
    name, desc = (repo.get("name") or "").lower(), (repo.get("description") or "").lower()
    topics = [t.lower() for t in repo.get("topics") or []]
    text = f"{desc} {name} {' '.join(topics)}"
    if any(k.lower() in text for k in match.get("exclude_keywords", [])):
        return False
    required = match.get("required_keywords", [])
    if required and not any(k.lower() in f"{desc} {name}" for k in required):
        return False
    keyword = any(k.lower() in text for k in match.get("primary_keywords", []))
    return keyword or any(t.lower() in topics for t in match.get("topic_matches", []))


def slim(repo: dict, source: str) -> dict:
    return {"repo": repo["full_name"], "name": repo["name"], "stars": repo["stargazers_count"],
            "description": repo.get("description") or "", "topics": repo.get("topics") or [],
            "created": (repo.get("created_at") or "")[:10], "pushed": (repo.get("pushed_at") or "")[:10],
            "source": source}


def collect(slug: str) -> None:
    match = next(s for s in json.loads(SCENARIOS.read_text()) if s["slug"] == slug)["match"]
    plan = [(q, band, "topic") for q in QUERIES[slug]["topic"] for band in STAR_BANDS]
    plan += [(q, band, "wave") for q in QUERIES[slug]["wave"] for band in (*STAR_BANDS, WAVE_BAND)]
    seen, raw = {}, 0
    for query, band, source in plan:
        for repo in search(f"{query} {band}"):
            raw += 1
            if source == "wave" or matches_page(repo, match):
                seen.setdefault(repo["full_name"].lower(), slim(repo, source))
    rows = sorted(seen.values(), key=lambda r: -r["stars"])
    (out_dir(slug) / "candidates.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print(f"{raw} search results -> {len(rows)} distinct repos pass the page's keyword matcher")


def readme_of(slug: str, repo: str) -> str:
    path = out_dir(slug) / "readme" / (repo.replace("/", "__") + ".md")
    if not path.exists():
        path.write_text(gh([f"repos/{repo}/readme", "-H", "Accept: application/vnd.github.raw"]))
    text = path.read_text()
    return "" if text.lstrip().startswith('{"message"') else text


def ask(client, row: dict, readme: str, limit: int, questions: dict, full: bool) -> dict:
    repo = {"name": row["repo"], "description": row["description"], "readme": readme[:limit]}
    if full:
        repo.update(created=row["created"], topics=row["topics"])
    res = client.decisions(json.dumps({"repo": repo}, ensure_ascii=False), questions)
    return {k: float(v.get("noul", 0)) for k, v in res.answers.items()}


def verdict(row: dict) -> str:
    if not row["readme_chars"]:
        return "no_readme"
    if row["stars"] < GATE_FLOOR and not row["names_model"]:
        return "below_gate_floor"
    # Both must hold. A video made with the model but not operated by an agent (a
    # finished music video, a demo) stays off the page: owner's rule, 2026-09-27.
    if row["makes_video"] < RELEVANT or row["agent_driven"] < RELEVANT:
        return "off_topic"
    return "admit" if row["quality"] >= MID else "low_quality"


def judge_one(client, slug: str, row: dict, today: date) -> dict:
    readme = readme_of(slug, row["repo"])
    out = {**row, "readme_chars": len(readme),
           "names_model": bool(re.search(QUERIES[slug]["names_model"], readme.lower()))}
    if readme:
        out.update(ask(client, row, readme, README_RELEVANCE, RELEVANCE, full=True))
        out.update(ask(client, row, readme, README_QUALITY, QUALITY, full=False))
    quality = sum(out.get(k, 0.0) for k in QUALITY_KEYS) / len(QUALITY_KEYS)
    days = max((today - date.fromisoformat(row["created"])).days, 1)
    out.update(quality=quality, tier="高" if quality >= HIGH else "中" if quality >= MID else "低",
               hit_prior=sum(out.get(k, 0.0) for k in HIT_KEYS) / len(HIT_KEYS),
               days=days, stars_per_day=row["stars"] / days)
    for key in RELEVANCE:
        out.setdefault(key, 0.0)
    out["verdict"] = verdict(out)
    return out


def judge(slug: str, prefix: str = "") -> None:
    sys.path.insert(0, str(Path.home() / "content/jev-search-rerank-eval/src"))
    from jse.openrouter import OpenRouter  # noqa: E402
    client, path = OpenRouter(), out_dir(slug) / f"{prefix}judged.json"
    done = {r["repo"]: r for r in json.loads(path.read_text())} if path.exists() else {}
    rows = json.loads((out_dir(slug) / f"{prefix}candidates.json").read_text())
    for i, row in enumerate(rows, 1):
        if row["repo"] in done:
            continue
        try:
            done[row["repo"]] = judge_one(client, slug, row, date.today())
        except Exception as exc:  # noqa: BLE001 — one bad repo must not lose the rest
            print(f"  skipped {row['repo']}: {str(exc)[:100]}", file=sys.stderr)
        if i % 20 == 0:
            path.write_text(json.dumps(list(done.values()), ensure_ascii=False, indent=1))
            print(f"  [{i}/{len(rows)}] cost ${client.total_cost:.4f}", flush=True)
    path.write_text(json.dumps(list(done.values()), ensure_ascii=False, indent=1))
    print(f"{len(done)} judged · models {sorted(client.models_seen)} · cost ${client.total_cost:.4f}")


def report(slug: str) -> None:
    rows = json.loads((out_dir(slug) / "judged.json").read_text())
    counts: dict[str, int] = {}
    for r in rows:
        r["verdict"] = verdict(r)
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    (out_dir(slug) / "judged.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print("verdicts:", counts)
    admitted = sorted((r for r in rows if r["verdict"] == "admit"), key=lambda r: -r["stars"])
    print(f"\n{'repo':50s} {'★':>3} {'created':10s} 档 质量 爆款 | video agent code tool | model")
    for r in admitted:
        print(f"{r['repo'][:50]:50s} {r['stars']:>3} {r['created']} {r['tier']} {r['quality']:.2f} {r['hit_prior']:.2f} | "
              f"{r['makes_video']:.2f}  {r['agent_driven']:.2f}  {r['code_rendered']:.2f} {r['reusable_tool']:.2f} | "
              f"{'names it' if r['names_model'] else ''}")
    (out_dir(slug) / "admitted.json").write_text(json.dumps([r["repo"] for r in admitted], indent=1))


def audit(slug: str, names_file: str) -> None:
    rows = []
    for name in json.loads(Path(names_file).read_text()):
        meta = json.loads(gh([f"repos/{name}"]) or "{}")
        if meta.get("full_name"):
            rows.append(slim(meta, "page"))
    (out_dir(slug) / "page-candidates.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    judge(slug, prefix="page-")
    judged = json.loads((out_dir(slug) / "page-judged.json").read_text())
    off = sorted((r for r in judged if r["verdict"] in ("off_topic", "no_readme")), key=lambda r: -r["stars"])
    print(f"\n{len(judged)} on the page · {len(off)} off-topic")
    for r in off:
        print(f"  {r['repo'][:46]:46s} {r['stars']:>6}★ video {r['makes_video']:.2f} agent {r['agent_driven']:.2f} "
              f"| {r['description'][:70]}")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "report"
    slug = sys.argv[2] if len(sys.argv) > 2 else "opus-5-5-video"
    if step == "audit":
        audit(slug, sys.argv[3])
    else:
        {"collect": collect, "judge": judge, "report": report}[step](slug)
