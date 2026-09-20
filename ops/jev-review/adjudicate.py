"""Second-pass adjudication of scanner flags: issued, or merely cited?

Each flag instance gets the same four atomic questions about the *textual role* of the
matched line — never "is this dangerous", which the decisions API answers poorly. Jev and
an independent judge (Haiku) see identical state; the heuristic baselines see the same
line. Answers are cached on disk so a rerun costs nothing.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CACHE = OUT / "cache"
sys.path.insert(0, str(Path.home() / "content/jev-search-rerank-eval/src"))
from jse.openrouter import OpenRouter  # noqa: E402

WORKERS = 8
MAX_LINE = 400
MAX_CTX = 900

QUESTIONS = {
    "issues_it": {"type": "noul", "instructions": {
        "question": "Does `readme.matched_line` tell the reader to run this, or say the project itself does it?",
        "focus": "An instruction, an install step, a config value the reader is meant to set, or a "
                 "description of what the project does when it runs."}},
    "is_documentation": {"type": "noul", "instructions": {
        "question": "Is `readme.matched_line` describing behaviour the project detects, blocks, warns about or scores?",
        "focus": "Security tools print the attacks they stop — rule tables, severity lists, "
                 "'blocked patterns', comparison rows, demo payloads."}},
    "is_negated": {"type": "noul", "instructions": {
        "question": "Does `readme.matched_line` tell the reader NOT to do this, or say the project prevents it?"}},
    "word_coincidence": {"type": "noul", "instructions": {
        "question": "Did `flag.trigger` land inside ordinary prose here — part of another word, a file "
                    "name, a URL, or an unrelated meaning — rather than a command or setting?"}},
}
# Fixed before any result was seen.
WEIGHTS = {"issues_it": 1.0, "is_documentation": -0.5, "is_negated": -0.5, "word_coincidence": -0.5}

JUDGE_SYSTEM = (
    "You adjudicate one line of a public README. A regex flagged it for a security claim. "
    "Decide whether the line ISSUES that behaviour (an instruction to run it, a config the reader "
    "sets, or the project describing what it does) or only CITES it (a rule table, a list of "
    "attacks the tool blocks, a warning against it, or a coincidental word match). "
    "Danger is irrelevant — a legitimate `sudo apt install` still ISSUES. "
    "Answer with exactly one word, ISSUED or CITED, then a space and your confidence 0-100."
)
_SECRET = re.compile(r"\b(sk-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9]{12,}|[A-Fa-f0-9]{32,})\b")


def state_of(item: dict, claims: dict) -> str:
    return json.dumps({
        "flag": {"name": item["flag"], "claim": claims.get(item["flag"], ""),
                 "trigger": _SECRET.sub("<redacted>", item["line"])[:MAX_LINE]},
        "readme": {"repo": item["repo"], "project_description": item["description"][:160],
                   "matched_line": _SECRET.sub("<redacted>", item["line"])[:MAX_LINE],
                   "surrounding_lines": _SECRET.sub("<redacted>", item["context"])[:MAX_CTX],
                   "inside_code_fence": item["in_fence"]},
    }, ensure_ascii=False)


def cached(kind: str, state: str, fetch):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{kind}-{hashlib.sha256(state.encode()).hexdigest()[:16]}.json"
    if path.exists():
        return json.loads(path.read_text())
    value = fetch()
    path.write_text(json.dumps(value, ensure_ascii=False))
    return value


def jev_one(client: OpenRouter, state: str) -> dict:
    def fetch():
        res = client.decisions(state, QUESTIONS)
        return {k: float(v.get("noul", 0.0)) for k, v in res.answers.items()}
    return cached("jev", state, fetch)


# Two independent judges from two families: agreement between them bounds how much of
# the disagreement with the hand labels is one model's idiosyncrasy.
JUDGES = {"haiku": "~anthropic/claude-haiku-latest", "gemini": "google/gemini-3.8-flash"}


def judge_one(client: OpenRouter, state: str, model: str) -> dict:
    def fetch():
        out = client._post("/v1/chat/completions", {
            "model": model, "temperature": 0, "max_tokens": 12,
            "messages": [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": state}]})
        text = (out["choices"][0]["message"]["content"] or "").strip()
        head = text.split()[0].upper() if text else ""
        conf = next((int(t) for t in re.findall(r"\d+", text)), 50)
        issued = head.startswith("ISSUED")
        return {"issued": issued, "score": (conf if issued else 100 - conf) / 100.0, "raw": text[:40]}
    return cached(f"judge-{model}", state, fetch)


def main() -> None:
    items = json.load(open(OUT / (sys.argv[1] if len(sys.argv) > 1 else "handlabels.json")))
    claims = json.load(open(OUT / "flag_desc.json"))
    client = OpenRouter()
    states = [state_of(it, claims) for it in items]

    with ThreadPoolExecutor(WORKERS) as pool:
        jev = list(pool.map(lambda s: jev_one(client, s), states))
    judges = {}
    for name, model in JUDGES.items():
        try:
            with ThreadPoolExecutor(WORKERS) as pool:
                judges[name] = list(pool.map(lambda s, m=model: judge_one(client, s, m), states))
        except Exception as exc:  # the Jev-scoped key blocks other models by guardrail
            print(f"judge {name} unavailable: {str(exc)[:90]}", file=sys.stderr)

    for i, (it, j) in enumerate(zip(items, jev)):
        it["jev"] = j
        it["jev_score"] = sum(WEIGHTS[k] * j.get(k, 0.0) for k in WEIGHTS)
        it["judges"] = {name: judges[name][i] for name in judges}
    name = "adjudicated-" + (sys.argv[1] if len(sys.argv) > 1 else "handlabels.json")
    (OUT / name).write_text(json.dumps(items, ensure_ascii=False, indent=1))
    print(f"{len(items)} items · models {sorted(client.models_seen)} · cost ${client.total_cost:.4f}")


if __name__ == "__main__":
    main()
