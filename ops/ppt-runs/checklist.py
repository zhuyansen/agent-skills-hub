"""Rubric scoring of the decks, after PresentBench (Chen et al., arXiv 2603.07244): five
dimensions, each a list of yes/no items, the deck's score the mean of the dimension scores.
A holistic 1-5 rating agrees with human rankings far less (rho 0.26 vs 0.53 in that paper;
0.57 vs 0.71 in SlidesGen-Bench), so items are atomic and one dimension is asked per call.

  python ops/ppt-runs/checklist.py [--passes N] [owner/repo ...]   # default: every run that ran, 3 passes

Each pass is saved (checklist.pass<k>.json); checklist.json holds the majority answer per
item over the passes. One pass flipped 4 of 150 answers on a rerun, all on the most
subjective items (sweeping claims, legibility), enough to move a deck 4-7 points.

Items for completeness, correctness and fidelity are written from our brief (in/brief.md),
as PresentBench writes material-specific items; fundamentals and design are generic. One
item, every slide title states a takeaway, comes from the assertion-evidence studies
(Garner and Alley 2013). Writes out/<run>/checklist.json.
"""
from __future__ import annotations

import base64
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
BRIEF = (HERE / "in" / "brief.md").read_text()
MAX_PAGES = 12
WORKERS, RETRIES, RETRY_SECONDS = 4, 3, 20

DIMENSIONS = {
    "fundamentals": [
        "The deck has 8 to 10 slides (not counting an appendix).",
        "Every slide has a title, and each title matches what is on that slide.",
        "The slides follow the brief's order: the problem, what the Hub does, the PPT example, how to choose, the call to action.",
        "No slide is a wall of text: each slide can be read in under a minute (roughly 80 words or fewer).",
        "Each slide title states a takeaway as a sentence (e.g. \"Most skills are installed after a glance\"), not a topic label (e.g. \"The problem\"), on at least most slides.",
    ],
    "design": [
        "One visual system across the slides: the same fonts, colour palette and layout grid.",
        "No text is cut off, overflowing its box or the slide, or overlapping other text or images, on any slide.",
        "Body text is large enough to read when presented (no tiny print except footnotes or sources).",
        "The deck shows something visually beyond bullets on at least two slides (a table, chart, diagram or icon set) and the visual carries information.",
        "No slide is cluttered: there is clear hierarchy and white space on every slide.",
        "Contrast between text and background is sufficient everywhere (no light grey on white, no text over a busy image).",
    ],
    "completeness": [
        "It explains the problem: skills run with the agent's permissions but are installed after a glance at the README.",
        "It says the Hub indexes 186,000+ repositories, refreshed every 8 hours.",
        "It names the grades (SAFE, CAUTION, UNSAFE, UNAUDITED) and the 11 red-flag categories, with at least one example category.",
        "It gives the coverage figures (93% of skills over 100 stars, 98% over 1,000 stars graded).",
        "It shows the PPT example with the three routes and their counts (98 native PPTX, 55 web slides, 7 image-first) out of 205.",
        "It says all 9 flagged PPT skills are flagged for how they install, none for what they do while making slides.",
        "It gives the three steps to choose a skill (who touches the output next; the four checks; the security grade).",
        "It ends with the call to action: look up a skill at agentskillshub.top, or paste a GitHub URL for a free check.",
    ],
    "correctness": [
        "Every mention of the number of repositories says 186,000+ (or 186K+), or the deck does not mention it.",
        "Every mention of the refresh interval says every 8 hours, or the deck does not mention it.",
        "Every mention of the grades uses exactly SAFE, CAUTION, UNSAFE, UNAUDITED, and of the categories says 11, or the deck does not mention them.",
        "The coverage figures, where shown, are 93% (over 100 stars) and 98% (over 1,000 stars), not swapped or altered.",
        "The route counts, where shown, are 98, 55 and 7, of 205 PPT skills, each with the right route.",
        "The flagged count, where shown, is 9, and the reason is installation (sudo, curl | sh), not slide-making behaviour.",
    ],
    "fidelity": [
        "No number appears that is neither in the brief nor derived from it by simple arithmetic (a sum such as 98 + 55 + 7 = 160 is fine); slide numbers, dates and chart axis labels such as 0% or 100% do not count.",
        "No customers, testimonials, quotes, case studies or company names are invented.",
        "No product features are claimed that the brief does not state (e.g. sandbox execution, automatic blocking, enterprise plans).",
        "No sweeping claim goes beyond the brief (e.g. \"every skill is graded\", \"guaranteed safe\", \"no risk\").",
        "No sources, logos, partnerships or awards are invented.",
    ],
}

PROMPT = """You check a slide deck an AI agent made from the brief below, one yes/no item at a time.
Answer each item from the slide images only. "yes" means the deck satisfies the item. When an item says
"or the deck does not mention it", absence counts as yes. Be strict: partial counts as no.

=== BRIEF ===
{brief}
=== END BRIEF ===

Items ({dim}):
{items}

Return JSON only: {{"items": [{{"n": <item number>, "answer": "yes"|"no", "slide": <slide number or null>, "evidence": "<one sentence>"}}]}}"""


def env() -> dict:
    vals = {}
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); vals[k.strip()] = v.strip().strip('"')
    return vals


def ask(e: dict, text: str, pages: list[Path]) -> dict:
    content = [{"type": "text", "text": text}] + [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()}}
        for p in pages[:MAX_PAGES]]
    body = {"model": e.get("FLATROUTER_MODEL", "gpt-6-astra"), "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"}, "temperature": 0}
    req = urllib.request.Request(e["FLATROUTER_BASE_URL"] + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + e["FLATROUTER_API_KEY"], "Content-Type": "application/json"})
    for attempt in range(RETRIES):
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=300) as r:
                return json.loads(json.load(r)["choices"][0]["message"]["content"])
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as err:
            if attempt == RETRIES - 1 or (isinstance(err, urllib.error.HTTPError) and err.code < 500):
                raise
            time.sleep(RETRY_SECONDS * (attempt + 1))
    return {}


def dimension(e: dict, dim: str, pages: list[Path]) -> dict:
    items = DIMENSIONS[dim]
    listed = "\n".join(f"{i}. {q}" for i, q in enumerate(items, 1))
    got = {a.get("n"): a for a in ask(e, PROMPT.format(brief=BRIEF, dim=dim, items=listed), pages).get("items", [])}
    answers = [{"item": q, **{k: got.get(i, {}).get(k) for k in ("answer", "slide", "evidence")}} for i, q in enumerate(items, 1)]
    yes = sum(a["answer"] == "yes" for a in answers)
    return {"score": round(yes / len(items), 3), "yes": yes, "of": len(items), "answers": answers}


def slides(run: Path) -> list[Path]:
    """The rendered slides in order; sheet.png (the contact sheet of all of them) is not a slide."""
    return sorted((p for p in (run / "pages").glob("*.png") if p.stem != "sheet"),
                  key=lambda p: int("".join(filter(str.isdigit, p.stem)) or 0))


def one_pass(run: Path, e: dict, k: int) -> None:
    pages = slides(run)
    dims = {d: dimension(e, d, pages) for d in DIMENSIONS}
    (run / f"checklist.pass{k}.json").write_text(json.dumps(
        {"dimensions": dims, "pages": len(pages), "judge": e.get("FLATROUTER_MODEL", "gpt-6-astra")}, indent=1, ensure_ascii=False))


def majority(run: Path) -> dict:
    """Per item, the answer most passes gave (ties count as no); the evidence of a pass that agrees."""
    passes = [json.loads(p.read_text()) for p in sorted(run.glob("checklist.pass*.json"))]
    dims = {}
    for d, items in DIMENSIONS.items():
        answers = []
        for i, q in enumerate(items):
            votes = [p["dimensions"][d]["answers"][i] for p in passes]
            yes = sum(v["answer"] == "yes" for v in votes)
            pick = "yes" if yes * 2 > len(votes) else "no"
            agree = next(v for v in votes if (v["answer"] == "yes") == (pick == "yes")) if any((v["answer"] == "yes") == (pick == "yes") for v in votes) else votes[0]
            answers.append({"item": q, "answer": pick, "votes": f"{yes}/{len(votes)}", "slide": agree.get("slide"), "evidence": agree.get("evidence")})
        n = sum(a["answer"] == "yes" for a in answers)
        dims[d] = {"score": round(n / len(items), 3), "yes": n, "of": len(items), "answers": answers}
    reviewed = review(run, dims)
    result = {"overall": round(sum(v["score"] for v in dims.values()) / len(dims), 3), "dimensions": dims,
              "passes": len(passes), "reviewed": reviewed, "judge": passes[0]["judge"] if passes else None}
    (run / "checklist.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result


def review(run: Path, dims: dict) -> int:
    """Apply a person's corrections (checklist_review.json) after the vote; returns how many."""
    path = HERE / "checklist_review.json"
    fixes = [o for o in json.loads(path.read_text())["overrides"] if o["run"] == run.name] if path.exists() else []
    for o in fixes:
        a = dims[o["dimension"]]["answers"][o["item"] - 1]
        a.update(answer=o["answer"], reviewed=o["why"])
    for d in {o["dimension"] for o in fixes}:
        n = sum(a["answer"] == "yes" for a in dims[d]["answers"])
        dims[d].update(score=round(n / dims[d]["of"], 3), yes=n)
    return len(fixes)


def score(run: Path, e: dict, passes: int) -> dict:
    for k in range(1, passes + 1):
        if not (run / f"checklist.pass{k}.json").exists():
            one_pass(run, e, k)
    return majority(run)


def main() -> None:
    e = env()
    args = sys.argv[1:]
    passes = int(args.pop(args.index("--passes") + 1)) if "--passes" in args else 3
    args = [a for a in args if a != "--passes"]
    names = [r.replace("/", "__") for r in args]
    ran = [r["repo"].replace("/", "__") for r in json.loads((HERE / "results.json").read_text()) if r["ran"]]
    runs = [OUT / n for n in (names or ran) if slides(OUT / n)]

    def one(run: Path) -> None:
        r = score(run, e, passes)
        print(run.name, r["overall"], {d: f"{v['yes']}/{v['of']}" for d, v in r["dimensions"].items()}, flush=True)

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(one, runs))


if __name__ == "__main__":
    main()
