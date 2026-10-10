"""Score the code-review runs against the fixture's ground truth.

  python ops/review-runs/score_review.py [owner/repo ...]   # default: runs without score.json

A judge (gpt-6-astra through FlatRouter) reads all 12 reviews of a run in one call (36
calls per run hit the rate limit) and answers per branch from truth.json: did it name the planted defect (8 branches have one), and
how many separate issues does it present as blocking, as worth fixing, as nits. Three
passes, majority for the yes/no and median for the counts (one pass flips a few answers).
Two numbers follow, as in SWR-Bench: defects found of 8, and blocking findings on the 4
clean branches (false alarms). Writes out/<run>/score.json.
"""
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
TRUTH = json.loads((HERE / "truth.json").read_text())
PASSES, WORKERS, RETRIES, RETRY_SECONDS = 3, 2, 6, 20

PROMPT = """You score an AI code review tool's reviews of 12 pull requests. Return JSON only.

For each pull request below you get its title, what is planted in it (or that it is clean), and the review the tool wrote.
Return {{"branches": {{"<branch name>": {{
  "found_planted": true|false|null,   // null when the pull request has no planted defect
  "blocking": <int>,   // separate issues the review presents as must-fix: blocking, critical, high, "request changes"
  "should_fix": <int>, // separate issues it presents as medium or "should fix"
  "nits": <int>,       // minor, low, style, optional
  "quote": "<the sentence that names the planted defect, or the first blocking finding, or empty>"}}, ...}}}}
Count an issue once even if the review repeats it. "found_planted" is true only when the review states that specific
defect (the same cause), not a neighbouring remark. A review that says "No findings" has all counts 0. Judge each
pull request on its own review only.

{items}"""
REVIEW_MAX = 6000


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
    for attempt in range(RETRIES):
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=300) as r:
                return json.loads(json.load(r)["choices"][0]["message"]["content"])
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as err:
            # 429 (rate limit) is worth waiting out like a 5xx; any other 4xx is our request's fault.
            if attempt == RETRIES - 1 or (isinstance(err, urllib.error.HTTPError) and err.code < 500 and err.code != 429):
                raise
            time.sleep(RETRY_SECONDS * (attempt + 1))
    return {}


def item(branch: str, review: str) -> str:
    t = TRUTH[branch]
    truth = (f"Planted defect: {t['defect']}" if t["defect"]
             else "No planted defect: a clean change (refactor, docs, a test, or correct validation).")
    return f"=== {branch} ===\nTitle: {t['title']}\n{truth}\n--- review ---\n{review[:REVIEW_MAX]}\n"


def branch_votes(votes: list[dict], branch: str) -> dict:
    mine = [(v.get("branches") or {}).get(branch) or {} for v in votes]
    planted = bool(TRUTH[branch]["defect"])
    found = None if not planted else sum(bool(v.get("found_planted")) for v in mine) * 2 > len(mine)
    med = lambda k: int(statistics.median(int(v.get(k) or 0) for v in mine))   # noqa: E731
    return {"planted": planted, "found": found, "found_votes": [v.get("found_planted") for v in mine],
            "blocking": med("blocking"), "should_fix": med("should_fix"), "nits": med("nits"),
            "quote": next((v.get("quote") for v in mine if v.get("quote")), "")}


def score(run: Path, e: dict) -> dict:
    deliver = run / "deliverables"
    reviews = {b: (deliver / f"{b}.md").read_text() for b in TRUTH if (deliver / f"{b}.md").exists()}
    votes = [ask(e, PROMPT.format(items="\n".join(item(b, r) for b, r in reviews.items()))) for _ in range(PASSES)] if reviews else []
    branches = {b: branch_votes(votes, b) for b in reviews}
    buggy = [b for b in branches.values() if b["planted"]]
    clean = [b for b in branches.values() if not b["planted"]]
    result = {"reviewed": len(branches), "found": sum(bool(b["found"]) for b in buggy), "planted_reviewed": len(buggy),
              "false_alarms": sum(b["blocking"] for b in clean), "clean_reviewed": len(clean),
              "clean_with_blocking": sum(b["blocking"] > 0 for b in clean),
              "findings_per_pr": round(sum(b["blocking"] + b["should_fix"] + b["nits"] for b in branches.values()) / max(len(branches), 1), 1),
              "branches": branches, "run": json.loads((run / "run.json").read_text())}
    (run / "score.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result


def main() -> None:
    e = env()
    names = [r.replace("/", "__") for r in sys.argv[1:]]
    runs = [OUT / n for n in names] if names else [p for p in sorted(OUT.iterdir()) if (p / "run.json").exists() and not (p / "score.json").exists()]

    def one(run: Path) -> None:
        r = score(run, e)
        print(f"{run.name}: reviewed {r['reviewed']}/12, found {r['found']}/{r['planted_reviewed']}, "
              f"false alarms {r['false_alarms']} on {r['clean_reviewed']} clean, {r['findings_per_pr']} findings per PR", flush=True)

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(one, runs))


if __name__ == "__main__":
    main()
