"""Jev as the gate for a scenario page's repos under the 50-star floor.

A scenario page lists repos with >= 50 stars. Below that, stars say little (a repo
from last week has had no time to collect them), so the page admits a repo on what
its README shows instead. The questions, weights and cut-offs are the ones used on
2026-09-27 for the >= 50-star candidates of /best/claude-video-skills/, fixed before any
answer here was seen.

  collect  GitHub search under the floor, then the page's own keyword matcher
  judge    README + two Jev calls per repo (relevance, quality); cached on disk
  report   table + the list for `match.admit_reviewed`
  audit    the same relevance questions for repos already on the page (names from a
           JSON list); off-topic ones go to `match.exclude_repos`

  types    what kind of video each repo on the page produces

  add      review one repo the owner names and put it with the page's rows

Usage: python ops/jev-review/scenario_gate.py <collect|judge|report|types> [slug]
       python ops/jev-review/scenario_gate.py add <slug> <owner/repo>
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
sys.path.insert(0, str(HERE))
SCENARIOS = ROOT / "frontend/scripts/scenario-keywords.json"
KINDS_FILE = ROOT / "frontend/scripts/scenario-kinds.json"

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

# Scripts, shot analysis and learning material: they make no video, the owner lists them.
CRAFT = [
    "eternityspring/reelbench-skills",
    "jtydhr88/screenwriting-skills",
    "wyuzhi/qisi-video-remix",
    "adityaarsharma/youtube-marketing-skills",
    "wocha-xiaoli/video-shot-analysis-feishu",
    "liuliu-66-create/ll-video-decomposer",
    "erduo1998-cell/video-script-builder",
    "chenmisss/laoxu-video-script",
    "sharon-laicc/viral-video-decomposer",
    "gnipbao/minimax-h3-video-reverse-skill",
]

# Named by the owner although the review puts them under the line: creative code that is
# not video in the strict sense (a real-time 3D scroll, hand-drawn art with films among its
# outputs) and an editing skill whose README leads with subtitles (makes video 0.40).
# Filed under the nearest type.
CREATIVE = {"JimLiu/taohuayuan": "story", "alexgreensh/anidoodle": "motion", "JimLiu/baocut": "editing"}

QUERIES = {
    "claude-video-skills": {
        "wave": ['"opus 5.5" video in:name,description'],
        "topic": [
            "hyperframes in:name,description,topics",
            "remotion skill in:name,description,topics",
            "claude video skill in:name,description",
            "claude code video in:name,description",
            "codex video skill in:name,description",
            "motion graphics skill in:name,description",
            "music video claude in:name,description",
            # Added 2026-09-30: repos that say film or animation, not video, were never searched.
            "claude animation skill in:name,description",
            "claude film in:name,description",
            "agent video skill in:name,description",
            "remotion claude in:name,description,topics",
        ],
        "names_model": r"opus[\s-]?5\.5",
        # Decided by the owner, repo by repo (2026-09-27). The questions below turn these
        # away (a music video is not an agent tool; a screenwriting skill makes no video);
        # this is a list of names, not a rule, and nothing joins it without the owner
        # saying so.
        "owner_admitted": ["ledbetterljoshua/functional-emotions-video", *CRAFT, *CREATIVE],
        # Their type is the owner's too: what comes before the video, not the video.
        "owner_kinds": {**{name: "craft" for name in CRAFT}, **CREATIVE},
        # Skills that live in a folder of a larger repo; reviewed from the folder's README.
        "sub_skill_kinds": {"EverMind-AI/Raven/skills/git-story-film": "explainer"},
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
# What kind of video comes out. Descriptive, one kind per question; a repo may score on
# several, and its type is the highest score (TYPE_MIN or more), else "general".
def _kind(question: str, focus: str) -> dict:
    return {"type": "noul", "instructions": {"question": question, "focus": focus}}


TYPES = {
    "promo": _kind("Is the video `repo` produces a promotional video for a product, a brand or a launch?",
                   "Product launch films, brand videos, ads, trailers for an app or a company."),
    "explainer": _kind("Is the video `repo` produces an explainer or educational video?",
                       "It teaches a topic or explains a concept: knowledge videos, tutorials, narrated lessons."),
    "music": _kind("Is the video `repo` produces a music video, a lyric video or visuals set to a song?",
                   "The soundtrack is a song and the picture follows it."),
    "motion": _kind("Does `repo` produce short motion graphics rather than a full video?",
                    "Animated logos, titles, UI animations, animated diagrams, GIFs, stickers."),
    "shorts": _kind("Is the video `repo` produces a short social video for Reels, Shorts, TikTok or Douyin?",
                    "Vertical format, talking-head or faceless channel videos, hooks and captions for a feed."),
    "editing": _kind("Does `repo` edit footage that already exists rather than create video from nothing?",
                     "Cutting, trimming, removing silences, adding b-roll or captions, recaps of a longer recording."),
    "demo": _kind("Is the video `repo` produces a demo or walkthrough of software?",
                  "App store previews, screen-recording walkthroughs, onboarding videos, code walkthroughs."),
    "story": _kind("Is the video `repo` produces a story: an animated tale, a short drama or a cinematic scene?",
                   "Characters, a plot, storyboards, shots; fiction rather than information."),
    "avatar": _kind("Does the video `repo` produces show a digital human: an AI avatar or a virtual presenter?",
                    "HeyGen-style avatars, lip-sync, talking photos, virtual anchors, cloned presenters."),
    "general": _kind("Is `repo` a general-purpose video framework or skill collection, not tied to one kind of video?",
                     "A rendering framework, a base toolkit, a bundle of many unrelated video skills."),
}
TYPE_MIN = 0.5

QUALITY_KEYS = ("shows_result", "one_command_start", "specific_outcome", "complete_docs")
HIT_KEYS = ("novel_angle", "shareable_output", "shows_result")


def state_dir(slug: str) -> Path:
    """Review results kept in git: what was judged, the page's own rows, the types.
    The daily job (ops/awesome/daily_video_pass.py) reads them to review only new repos."""
    path = HERE / "state" / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


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


_BADGE = re.compile(r"\[?!\[[^\]]*\]\([^)]*(?:shields\.io|badge|badgen)[^)]*\)(?:\]\([^)]*\))?|<img[^>]*(?:shields\.io|badge)[^>]*>", re.I)
_VIDEO = re.compile(r"<video[^>]*>|<source[^>]*>|https?://\S+\.(?:mp4|mov|webm)\b\S*|https?://github\.com/user-attachments/assets/\S+", re.I)
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)|<img[^>]*?(?:alt=\"([^\"]*)\")?[^>]*>", re.I)
_TAG = re.compile(r"<!--.*?-->|<[^>]+>|&[a-z]+;", re.S)


def prose(readme: str) -> str:
    """The README as a reader sees it: no badges, no HTML, media kept as [video] / [image].
    A window cut from the raw file can be mostly markup: hypit-ai/hypit's first 3,500
    characters were 63% tags, the questions never reached the line that says it is an
    agent skill, and it was judged off-topic. Media stays as a token because removing it
    took away the evidence for "shows the finished output" (-0.15 on average)."""
    text = _VIDEO.sub(" [video] ", _BADGE.sub(" ", readme))
    text = _IMAGE.sub(lambda m: f" [image: {(m.group(1) or m.group(2) or '').strip()}] ", text)
    text = re.sub(r"[ \t]+", " ", _TAG.sub(" ", text))
    return re.sub(r" *\n\s*\n\s*", "\n\n", text).strip()


def ask(client, row: dict, readme: str, limit: int, questions: dict, full: bool) -> dict:
    repo = {"name": row["repo"], "description": row["description"], "readme": prose(readme)[:limit]}
    if full:
        repo.update(created=row["created"], topics=row["topics"])
    res = client.decisions(json.dumps({"repo": repo}, ensure_ascii=False), questions)
    return {k: float(v.get("noul", 0)) for k, v in res.answers.items()}


def verdict(row: dict, slug: str = "claude-video-skills") -> str:
    if row["repo"] in QUERIES[slug].get("owner_admitted", []):
        return "admit"
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
    out["verdict"] = verdict(out, slug)
    return out


def judge(slug: str, prefix: str = "") -> None:
    from jev_client import OpenRouter  # noqa: E402  (ops/jev-review/jev_client.py)
    client, path = OpenRouter(), state_dir(slug) / f"{prefix}judged.json"
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


def keyword_blocked(slug: str) -> list[dict]:
    """Repos above the floor that the review admits but the page's keywords turn away
    (lemomo-ai/lemo-opuscar: "style prompt" in its description hit the exclude word
    "prompt"). They need the admitted list to reach the page."""
    path = state_dir(slug) / "page-judged.json"
    if not path.exists():
        return []
    match = next(x for x in json.loads(SCENARIOS.read_text()) if x["slug"] == slug)["match"]
    return [r for r in json.loads(path.read_text())
            if verdict(r, slug) == "admit" and not matches_page(r, match)]


def report(slug: str) -> None:
    rows = json.loads((state_dir(slug) / "judged.json").read_text())
    counts: dict[str, int] = {}
    for r in rows:
        r["verdict"] = verdict(r, slug)
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    (state_dir(slug) / "judged.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print("verdicts:", counts)
    admitted = sorted((r for r in rows if r["verdict"] == "admit"), key=lambda r: -r["stars"])
    print(f"\n{'repo':50s} {'★':>3} {'created':10s} 档 质量 爆款 | video agent code tool | model")
    for r in admitted:
        print(f"{r['repo'][:50]:50s} {r['stars']:>3} {r['created']} {r['tier']} {r['quality']:.2f} {r['hit_prior']:.2f} | "
              f"{r['makes_video']:.2f}  {r['agent_driven']:.2f}  {r['code_rendered']:.2f} {r['reusable_tool']:.2f} | "
              f"{'names it' if r['names_model'] else ''}")
    names = [r["repo"] for r in admitted] + [r["repo"] for r in keyword_blocked(slug)]
    (out_dir(slug) / "admitted.json").write_text(json.dumps(names, indent=1))


def on_page(slug: str) -> list[dict]:
    """Every repo the page will list: on-topic ones above the floor, admitted ones below."""
    match = next(x for x in json.loads(SCENARIOS.read_text()) if x["slug"] == slug)["match"]
    keep = {n.lower() for n in match.get("featured", [])}
    above = json.loads((state_dir(slug) / "page-judged.json").read_text())
    below = json.loads((state_dir(slug) / "judged.json").read_text())
    rows = [r for r in above if verdict(r, slug) not in ("off_topic", "no_readme") or r["repo"].lower() in keep]
    rows += [r for r in below if verdict(r, slug) == "admit"]
    dropped = {k.lower() for k in match.get("exclude_repos", [])}   # off-topic, renamed or gone from GitHub
    return [r for r in rows if r["repo"].lower() not in dropped]


GENERAL_MIN = 0.6
# A kind too small to stand alone is filed under a neighbour: of 13 "demo" winners about
# 5 make demo videos. Avatars are only 4 repos but keep their own chip (owner's decision,
# 2026-09-27): people look for digital-human tools by that name.
MERGED = {"demo": "promo"}
# Two questions fire too easily at 0.5. "Set to a song" fits any video with background
# music (half the music bucket was general Remotion skills); "a walkthrough of software"
# fits most tools whose README walks through itself (manim_skill scored 0.68).
STRICT = {"music": 0.8, "demo": 0.85}
# Display order of the chips on the page.
KIND_LABELS = [
    {"id": "general", "icon": "🧱", "en": "Frameworks & toolkits", "zh": "框架与通用工具包"},
    {"id": "promo", "icon": "📣", "en": "Promo & demos", "zh": "产品宣传与演示"},
    {"id": "explainer", "icon": "🎓", "en": "Explainers", "zh": "讲解科普"},
    {"id": "editing", "icon": "✂️", "en": "Editing", "zh": "剪辑与后期"},
    {"id": "shorts", "icon": "📱", "en": "Shorts & social", "zh": "短视频与口播"},
    {"id": "avatar", "icon": "🧑‍💼", "en": "Avatars", "zh": "数字人"},
    {"id": "story", "icon": "📖", "en": "Stories & animation", "zh": "故事与动画"},
    {"id": "motion", "icon": "🎞", "en": "Motion graphics", "zh": "动效与 Logo"},
    {"id": "craft", "icon": "📝", "en": "Scripts & learning", "zh": "剧本与学习"},
    {"id": "music", "icon": "🎵", "en": "Music videos", "zh": "音乐视频"},
]


def kind_of(scores: dict) -> str:
    """One type per repo. A framework serves every kind of video, so it is filed as
    general even when one kind also scores."""
    if scores["general"] >= GENERAL_MIN:
        return "general"
    passed = {k: v for k, v in scores.items() if k != "general" and v >= STRICT.get(k, TYPE_MIN)}
    if not passed:
        return "general"
    best = max(passed, key=passed.get)
    return MERGED.get(best, best)


def types(slug: str) -> None:
    from jev_client import OpenRouter  # noqa: E402  (ops/jev-review/jev_client.py)
    client, path = OpenRouter(), state_dir(slug) / "types.json"
    done = {r["repo"]: r for r in json.loads(path.read_text())} if path.exists() else {}
    for row in on_page(slug):
        if row["repo"] in done:
            done[row["repo"]]["kind"] = kind_of(done[row["repo"]]["scores"])
            continue
        scores = ask(client, row, readme_of(slug, row["repo"]), README_RELEVANCE, TYPES, full=True)
        done[row["repo"]] = {"repo": row["repo"], "stars": row["stars"], "description": row["description"],
                             "scores": scores, "kind": kind_of(scores)}
        path.write_text(json.dumps(list(done.values()), ensure_ascii=False, indent=1))
    print(f"{len(done)} typed · cost ${client.total_cost:.4f}")
    listed = {r["repo"] for r in on_page(slug)}
    kinds = json.loads(KINDS_FILE.read_text()) if KINDS_FILE.exists() else {}
    repos = {k: v["kind"] for k, v in sorted(done.items()) if k in listed}
    repos.update({k: v for k, v in QUERIES[slug].get("owner_kinds", {}).items() if k in listed})
    repos.update(QUERIES[slug].get("sub_skill_kinds", {}))  # keyed by repo + folder
    kinds[slug] = {"kinds": KIND_LABELS, "repos": repos}
    KINDS_FILE.write_text(json.dumps(kinds, ensure_ascii=False, indent=1) + "\n")


def add(slug: str, name: str) -> None:
    """Review one repo and put it with the page's rows (for repos the owner names)."""
    from jev_client import OpenRouter  # noqa: E402  (ops/jev-review/jev_client.py)
    meta = json.loads(gh([f"repos/{name}"]) or "{}")
    row = judge_one(OpenRouter(), slug, slim(meta, "owner"), date.today())
    path = state_dir(slug) / "page-judged.json"
    rows = [r for r in json.loads(path.read_text()) if r["repo"] != row["repo"]] + [row]
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print(f"{row['repo']} {row['stars']} stars: video {row['makes_video']:.2f} agent {row['agent_driven']:.2f} "
          f"quality {row['quality']:.2f} -> {row['verdict']}")


def audit(slug: str, names_file: str) -> None:
    rows = []
    for name in json.loads(Path(names_file).read_text()):
        meta = json.loads(gh([f"repos/{name}"]) or "{}")
        if meta.get("full_name"):
            rows.append(slim(meta, "page"))
    (out_dir(slug) / "page-candidates.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    judge(slug, prefix="page-")
    judged = json.loads((state_dir(slug) / "page-judged.json").read_text())
    off = sorted((r for r in judged if r["verdict"] in ("off_topic", "no_readme")), key=lambda r: -r["stars"])
    print(f"\n{len(judged)} on the page · {len(off)} off-topic")
    for r in off:
        print(f"  {r['repo'][:46]:46s} {r['stars']:>6}★ video {r['makes_video']:.2f} agent {r['agent_driven']:.2f} "
              f"| {r['description'][:70]}")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "report"
    slug = sys.argv[2] if len(sys.argv) > 2 else "claude-video-skills"
    if step in ("audit", "add"):
        {"audit": audit, "add": add}[step](slug, sys.argv[3])
    else:
        {"collect": collect, "judge": judge, "report": report, "types": types}[step](slug)
