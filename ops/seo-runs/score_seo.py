"""Score the SEO audit runs against the test site's ground truth.

  python ops/seo-runs/score_seo.py [owner/repo|control ...]   # default: runs without score.json

A judge (Claude Opus 5.5 through `claude -p`, on the subscription: no API spend) gets the whole test
site (every page's HTML, robots.txt, sitemap.xml, the server's redirects and 404s), the 12 planted
defects (truth.json) and one run's report. It answers: which planted defects the report names, how
many separate problems the report raises, and which of them are false about the site (a page said to
lack something it has, or a clean bill for a check the site fails). Three passes: majority for each
defect, and a claim counts as false when two of three passes call it false. The false claims are then
read by hand (marks.json overrides the judge where it erred). Writes out/<run>/score.json.
"""
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
SITE = HERE / "in/site"
TRUTH = json.loads((HERE / "truth.json").read_text())
MARKS = json.loads((HERE / "marks.json").read_text()) if (HERE / "marks.json").exists() else {}
PASSES, WORKERS, REPORT_MAX = 3, 3, 60000

PROMPT = """You score an SEO audit of a small test website. Return JSON only, no prose, no code fence.

THE SITE (served at http://lumentea.test/; this is everything on it):
{site}

Server behaviour (Python's http.server): /shop/ answers 301 -> /store/, which answers 301 -> /teas/. /teas/bai-mudan/ is
sent with the response header X-Robots-Tag: noindex; no other page has that header. Each page is also served at its
index.html path (/index.html, /teas/index.html ...) with 200 and the same HTML, and a directory path without the trailing
slash (/about, /teas) answers 301 -> the slash version. /img/*.png images answer 200. Any other path answers 404
(including /teas/white-peony/, /teas/dragon-well/, /zh/, /llms.txt, /favicon.ico). Every 404 response carries the body of
/404.html (a small page with <title>Not found | Lumen Tea</title> and <meta name="robots" content="noindex">). Responses carry Content-Type with
charset=utf-8, no compression, no cache headers, HTTP/1.0. Only lumentea.test resolves (no www host).
Plain HTTP only (no HTTPS) because it is a sandbox; the auditor was told to ignore HTTPS.

PLANTED DEFECTS (the answer key):
{defects}

THE AUDIT REPORT:
<<<
{report}
>>>

Return {{"found": {{"D1": {{"hit": true|false, "quote": "<the report's words that name it, or empty>"}}, ... one entry for each of {ids}}},
"problems": <int: separate problems/issues/recommendations the report raises, counting each distinct problem once even if repeated>,
"false_claims": [{{"claim": "<the report's claim, quoted or closely paraphrased>", "why": "<what the site shows instead>"}}]}}

Rules:
- "hit" is true only when the report states that specific defect on the right page or file (for D11, the redirect chain
  from /shop/; for D5, the duplicate description of /teas/ and /blog/). A neighbouring remark is not a hit (e.g. "add more
  structured data" is not D8; "sitemap could include lastmod" is not D7).
- A false claim is one of two kinds, and only these count:
  (a) a problem the site does not have: a page said to lack a title, H1, description, canonical, viewport, lang, alt text,
      Open Graph tags, author/byline or structured data that it has; a link or URL said to be broken, redirected,
      noindexed or blocked that is not; a duplicate that is not a duplicate;
  (b) a clean bill for something the site fails: a statement that a check passes or that something is fine when the
      site shows otherwise (e.g. "every page has a viewport tag", "no broken links", "no redirect chains", "robots.txt
      allows all crawlers", "titles are unique").
  Not false claims: wrong counts, sizes or other incidental details that neither report a problem nor clear a check;
  opinions and advice (thin content, keyword use, adding llms.txt, adding FAQ schema, a title could be better, missing
  HTTPS/HSTS/security headers, no compression, no favicon.ico); anything true about the site even if not planted (no
  llms.txt, no BreadcrumbList, the blog has one post). A report that says the tool could not run is not a false claim.
- Score the report's text only; do not infer what the tool might have meant."""


def site_text() -> str:
    parts = []
    for f in sorted(SITE.rglob("*")):
        if f.is_file() and f.suffix in (".html", ".txt", ".xml") and f.name != "404.html":
            rel = "/" + str(f.relative_to(SITE)).replace("index.html", "")
            parts.append(f"=== {rel} ===\n{f.read_text()}")
    return "\n".join(parts)


def defects() -> str:
    return "\n".join(f"{d['id']} ({d['where']}): {d['defect']}" for d in TRUTH["defects"])


def report_text(run: Path) -> str:
    """The run's report.md, plus any other text file it wrote (a tool's own report), up to REPORT_MAX."""
    deliver = run / "deliverables"
    if not deliver.exists():
        return ""
    files = sorted(deliver.rglob("*"), key=lambda f: (f.name != "report.md", str(f)))
    out = ""
    for f in files:
        if f.is_file() and f.suffix in (".md", ".txt", ".json", ".html", ".csv") and f.stat().st_size < 400_000:
            out += f"\n--- file: {f.relative_to(deliver)} ---\n" + f.read_text(errors="ignore")
    return out[:REPORT_MAX]


def token() -> str:
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if line.startswith("CLAUDE_CODE_OAUTH_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"')
    sys.exit("CLAUDE_CODE_OAUTH_TOKEN missing from ~/.claude/.env")


def ask(text: str) -> dict:
    # In the sandbox image, with only the subscription token: this machine's own Claude Code settings route
    # elsewhere. One turn, no tools: the judge reads, it does not fetch.
    p = subprocess.run(["docker", "run", "--rm", "-i", "-e", "CLAUDE_CODE_OAUTH_TOKEN", "--entrypoint", "claude", "pptrun:1",
                        "-p", "--model", "opus", "--output-format", "json", "--max-turns", "1"],
                       input=text, capture_output=True, text=True, env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": token()}, timeout=900)
    result = json.loads(p.stdout)["result"]
    m = re.search(r"\{.*\}", result, re.S)
    return json.loads(m.group(0)) if m else {}


def score(run: Path) -> dict:
    report = report_text(run)
    if not report.strip():
        result = {"reported": False, "run": json.loads((run / "run.json").read_text())}
        (run / "score.json").write_text(json.dumps(result, indent=1))
        return result
    prompt = PROMPT.format(site=site_text(), defects=defects(), report=report,
                           ids=", ".join(d["id"] for d in TRUTH["defects"]))
    votes = [ask(prompt) for _ in range(PASSES)]
    found = {}
    for d in TRUTH["defects"]:
        hits = [bool(((v.get("found") or {}).get(d["id"]) or {}).get("hit")) for v in votes]
        quote = next((((v.get("found") or {}).get(d["id"]) or {}).get("quote") for v in votes
                      if ((v.get("found") or {}).get(d["id"]) or {}).get("hit")), "")
        found[d["id"]] = {"hit": sum(hits) * 2 > len(hits), "votes": hits, "quote": quote}
    problems = sorted(int(v.get("problems") or 0) for v in votes)[len(votes) // 2]
    # The false claims of the median pass by count; marks.json then corrects them by hand.
    fc = sorted((v.get("false_claims") or [] for v in votes), key=len)[len(votes) // 2]
    mk = MARKS.get(run.name, {})
    for d, hit in (mk.get("found") or {}).items():
        found[d]["hit"], found[d]["by_hand"] = hit, True
    if "false_claims" in mk:
        fc = mk["false_claims"]
    result = {"reported": True, "found": sum(v["hit"] for v in found.values()), "planted": len(TRUTH["defects"]),
              "problems": problems, "false_claims": fc, "defects": found, "run": json.loads((run / "run.json").read_text())}
    (run / "score.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result


def main() -> None:
    names = [r.replace("/", "__") for r in sys.argv[1:]]
    runs = [OUT / n for n in names] if names else [p for p in sorted(OUT.iterdir()) if (p / "run.json").exists() and not (p / "score.json").exists()]

    def one(run: Path) -> None:
        r = score(run)
        if not r["reported"]:
            print(f"{run.name}: no report", flush=True)
            return
        miss = [d for d, v in r["defects"].items() if not v["hit"]]
        print(f"{run.name}: found {r['found']}/{r['planted']}, {r['problems']} problems, {len(r['false_claims'])} false claims; missed {', '.join(miss) or '-'}", flush=True)

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(one, runs))


if __name__ == "__main__":
    main()
