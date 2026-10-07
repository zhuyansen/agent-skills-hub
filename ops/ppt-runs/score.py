"""Score finished runs: the four questions of the PPT page's method, with evidence.

  python ops/ppt-runs/score.py [owner/repo ...]     # default: every run without score.json

Inputs per run (out/<owner__repo>/): rendered pages (pages/*.png), render.json (pptx
editability counts), transcript.jsonl (what the agent did). The judge is gpt-6-astra
through FlatRouter (FLATROUTER_* in ~/.claude/.env); it sees the pages and a summary,
and must cite what it saw. Objective facts (editability, self-check commands, run
status) are computed here and passed in, so the model judges only what needs eyes.
"""
import base64
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
MAX_PAGES = 10
# Commands that show the agent looked at its own output before finishing.
SELF_CHECK = re.compile(r"pdftoppm|soffice[^\n]{0,80}--convert-to (pdf|png)|screenshot|--screenshot|playwright|Read[^\n]{0,40}\.png|render", re.I)

QUESTIONS = """You are reviewing a slide deck an AI agent made with one third-party "PPT skill" from a fixed brief.
The brief asked for 8-10 slides for engineering managers; it contains these facts: 186,000+ repositories,
refreshed every 8 hours, 11 red-flag categories, 93% of skills over 100 stars and 98% over 1,000 graded,
a table of PPT routes (Native PPTX 98, Web slides 55, Image-first 7), and 9 flagged PPT skills, all for install method.

Answer from the page images and the facts given. Return JSON only:
{
 "story": {"answer": "yes|partly|no", "evidence": "..."},          // a clear storyline: problem -> what -> example -> how to choose -> call to action
 "layout_system": {"answer": "yes|partly|no", "evidence": "..."},  // one consistent visual system across slides
 "fidelity": {"answer": "yes|partly|no", "evidence": "..."},       // numbers and claims match the brief; quote any wrong number
 "readability": {"answer": "yes|partly|no", "evidence": "..."},    // text legible, nothing cut off or overlapping
 "design": {"score": 1-5, "evidence": "..."},                       // visual quality a manager would accept
 "rework": {"minutes": <int>, "what": "..."}                        // honest estimate of fixing time before handing it over
}
Evidence must point at specific slides ("slide 3: ...")."""


def env() -> dict:
    vals = {}
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); vals[k.strip()] = v.strip().strip('"')
    return vals


def facts(run: Path) -> dict:
    render = json.loads((run / "render.json").read_text()) if (run / "render.json").exists() else {}
    transcript = (run / "transcript.jsonl").read_text(errors="ignore") if (run / "transcript.jsonl").exists() else ""
    stats = next(iter(render.get("pptx", {}).values()), None)
    if stats and "slides" in stats:
        editable = "image" if stats["full_image_slides"] >= max(1, stats["slides"] // 2) else "native"
    else:
        editable = "browser" if (render.get("rendered_from") or "").endswith(".html") else "unknown"
    return {"run": json.loads((run / "run.json").read_text()), "rendered_from": render.get("rendered_from"),
            "files": render.get("files", []), "pptx": stats, "editability": editable,
            "self_check": bool(SELF_CHECK.search(transcript)), "pages": render.get("pages", [])}


def ask(e: dict, f: dict, pages: list[Path]) -> dict:
    content = [{"type": "text", "text": QUESTIONS + "\n\nComputed facts: " + json.dumps(f)[:3000]}]
    for p in pages[:MAX_PAGES]:
        content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()}})
    body = {"model": e.get("FLATROUTER_MODEL", "gpt-6-astra"), "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"}, "temperature": 0}
    req = urllib.request.Request(e["FLATROUTER_BASE_URL"] + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + e["FLATROUTER_API_KEY"], "Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # FlatRouter is reached directly
    with opener.open(req, timeout=300) as r:
        return json.loads(json.load(r)["choices"][0]["message"]["content"])


def score(run: Path, e: dict) -> dict:
    f = facts(run)
    pages = sorted((run / "pages").glob("*.png")) if (run / "pages").exists() else []
    result = {"facts": f, "judge": ask(e, f, pages) if pages else None,
              "note": None if pages else "no rendered pages: nothing for the judge to see"}
    (run / "score.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result


def main() -> None:
    e = env()
    names = [r.replace("/", "__") for r in sys.argv[1:]]
    runs = [OUT / n for n in names] if names else [p for p in OUT.iterdir() if (p / "run.json").exists() and not (p / "score.json").exists()]
    for run in runs:
        r = score(run, e)
        j = r["judge"] or {}
        print(run.name, r["facts"]["run"]["status"], r["facts"]["editability"], "self-check" if r["facts"]["self_check"] else "-",
              {k: (v.get("answer") or v.get("score") or v.get("minutes")) for k, v in j.items() if isinstance(v, dict)}, flush=True)


if __name__ == "__main__":
    main()
