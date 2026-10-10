"""Score the Obsidian runs: answers to 15 questions about the test vault, against truth.json.

  python ops/obsidian-runs/score_obsidian.py      # writes results.json and RESULTS.md

A judge (gpt-6-astra through FlatRouter, three passes, majority) marks each answer right
or wrong against the expected answer; for the three questions the vault cannot answer,
right means the answer says so and gives no made-up value. Scores are reported by
LongMemEval's five abilities (arXiv 2410.10813). Cost is read from the transcript: how
many tool calls went through the tool under test (MCP tools, Skill) and how many through
plain file tools, the tokens the session used, and the minutes it took.
"""
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
TRUTH = json.loads((HERE / "truth.json").read_text())
ABILITIES = ["extraction", "multi-note", "temporal", "update", "abstain"]
CONTROL = "octocat/Hello-World"
PASSES, RETRIES, RETRY_SECONDS = 3, 6, 20
FILE_TOOLS = {"Read", "Grep", "Glob", "Bash", "LS"}

PROMPT = """You mark answers to 15 questions about a set of notes. Return JSON only:
{{"marks": {{"1": true|false, ..., "15": true|false}}}}
An answer is right when it states the expected fact (wording may differ; extra correct detail is fine). It is wrong when
it gives a different value, hedges between values, or is missing. For questions whose expected answer says the notes do
not hold it, the answer is right only if it says the notes do not say and offers no value of its own.

{items}"""


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
            if attempt == RETRIES - 1 or (isinstance(err, urllib.error.HTTPError) and err.code < 500 and err.code != 429):
                raise
            time.sleep(RETRY_SECONDS * (attempt + 1))
    return {}


def usage(transcript: Path) -> dict:
    """Tool calls by kind and tokens, from the session transcript."""
    tool, files, tokens = 0, 0, 0
    for line in transcript.read_text(errors="ignore").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") != "assistant":
            continue
        u = e["message"].get("usage") or {}
        tokens += u.get("output_tokens", 0) + u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        for c in e["message"].get("content", []):
            if c.get("type") == "tool_use":
                name = c["name"]
                tool += name.startswith("mcp__") or name in ("Skill", "SlashCommand")
                files += name in FILE_TOOLS
    return {"tool_calls": tool, "file_calls": files, "tokens": tokens}


def marks(e: dict, answers: str) -> dict[str, bool]:
    items = "\n".join(f"Question {t['n']}: {t['question']}\nExpected: {t['answer']}" for t in TRUTH) + "\n\n=== The answers ===\n" + answers[:8000]
    votes = [ask(e, PROMPT.format(items=items)).get("marks") or {} for _ in range(PASSES)]
    return {str(t["n"]): sum(bool(v.get(str(t["n"]))) for v in votes) * 2 > PASSES for t in TRUTH}


def row(c: dict, e: dict) -> dict:
    run = OUT / c["repo"].replace("/", "__")
    answers = run / "deliverables" / "answers.md"
    if not (run / "run.json").exists():
        return {**c, "ran": False, "reason": "not run"}
    meta = json.loads((run / "run.json").read_text())
    if not answers.exists():
        return {**c, "ran": False, "reason": meta.get("reason") or meta.get("status") or "no answers", "minutes": round(meta["seconds"] / 60, 1)}
    m = marks(e, answers.read_text())
    by = {a: sum(m[str(t["n"])] for t in TRUTH if t["ability"] == a) for a in ABILITIES}
    return {**c, "ran": True, "correct": sum(m.values()), "by_ability": by, "marks": m, **usage(run / "transcript.jsonl"),
            "minutes": round(meta["seconds"] / 60, 1), "commit": (run / "commit.txt").read_text().strip()[:12] if (run / "commit.txt").exists() else None}


def markdown(rows: list[dict]) -> str:
    out = ["| Tool | ★ | Right (of 15) | " + " | ".join(ABILITIES) + " | Calls through the tool | Plain file calls | Tokens | Min |", "|---|---:|---:|" + "---:|" * (len(ABILITIES) + 4)]
    for r in sorted((r for r in rows if r["ran"]), key=lambda r: (-r["correct"], r["tokens"])):
        out.append(f"| {r['repo']} | {r['stars']} | {r['correct']} | " + " | ".join(f"{r['by_ability'][a]}/3" for a in ABILITIES)
                   + f" | {r['tool_calls']} | {r['file_calls']} | {r['tokens']:,} | {r['minutes']} |")
    out += ["", "Not run:", ""] + [f"- {r['repo']}: {r['reason']}" for r in rows if not r["ran"]]
    return "\n".join(out) + "\n"


def main() -> None:
    e = env()
    cands = json.loads((HERE / "candidates.json").read_text())
    rows = [row({"repo": CONTROL, "kind": "control", "stars": 0, "grade": None}, e), *[row(c, e) for c in cands]]
    (HERE / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    (HERE / "RESULTS.md").write_text(markdown(rows))
    print(markdown(rows))


if __name__ == "__main__":
    main()
