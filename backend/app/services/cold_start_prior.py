"""Day-one Jev prior for a new repo: one Jev decisions call, typed questions only.

Mirrors the question set of the public retrospective study (github.com/zhuyansen/
jev-cold-start-prior) so the prospective data is directly comparable. Star counts are kept
OUT of the state, and README lines rendering live star badges are stripped, so the prior is
a pure semantic signal and never leaks the popularity baseline it is compared against.

The call goes to TypeSafe's own API when TYPESAFE_API_KEY is set, else to OpenRouter (same
questions, same answers; ops/jev-review/jev_client.py made the same switch on 10-03). The
OpenRouter credit ran out around 2026-10-07 and every prior after that failed with HTTP 402."""

import json
import os
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass, field

import httpx

DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "~typesafe/jev-latest"
TYPESAFE_URL = "https://api.typesafe.ai/v1/systemone"   # docs.typesafe.ai/introduction/quickstart
TYPESAFE_MODEL = "jev-latest"
README_CHARS = 3000
TIMEOUT_S = 120
RETRIES = 4
BACKOFF_S = 1   # doubled per retry, as in ops/jev-review/jev_client.py
_BADGE = re.compile(r"^.*(shields\.io|star-history|stargazers|badge\.fury|img\.shields).*$", re.I | re.M)

QUESTIONS = {
    "will_gain": {"type": "score",
                  "instructions": "How many GitHub stars is this repository likely to gain in its first two weeks after this snapshot?",
                  "criteria": ["Almost none (under 5)", "A few (5-50)", "Many (50-500)", "A lot (over 500)"]},
    "maturity": {"type": "score", "instructions": "How complete and production-ready does the project look?",
                 "criteria": ["Placeholder or stub", "Working prototype", "Solid and usable", "Polished, production-grade"]},
    "clarity": {"type": "score", "instructions": "How clear and compelling is what it does and who it is for?",
                "criteria": ["Unclear", "Somewhat clear", "Clear", "Instantly obvious and compelling"]},
    "install": {"type": "score", "instructions": "How easy does it look to install and try?",
                "criteria": ["Hard or unclear", "Several manual steps", "Simple", "One command"]},
    "audience": {"type": "choice", "instructions": "Who is the audience?",
                 "criteria": {"personal": "The author's own setup or a single team",
                              "ecosystem": "Users of one specific tool or platform",
                              "developers": "A broad developer audience",
                              "everyone": "General users, non-developers included"}},
    "rides_trend": {"type": "noul", "instructions": "Is it built on or for a tool/model that is currently very popular (e.g. Claude Code, Codex, MCP, OpenClaw, a new frontier model)?",
                    "criteria": {"true": "Yes, it rides a current wave", "false": "No"}},
    "novel": {"type": "noul", "instructions": "Does it offer something not already widely available?",
              "criteria": {"true": "Genuinely new capability or approach", "false": "Another take on a common idea"}},
    "showcase": {"type": "noul", "instructions": "Does the README include a demo, screenshots, GIF, video or worked example?",
                 "criteria": {"true": "Yes", "false": "No"}},
}


@dataclass(frozen=True)
class JevEndpoint:
    name: str
    url: str
    model: str
    key: str = field(repr=False)


def endpoint_from_env(env: Mapping[str, str] | None = None) -> JevEndpoint | None:
    """TypeSafe's own API when TYPESAFE_API_KEY is set, else OpenRouter; None when neither key is."""
    env = os.environ if env is None else env
    if env.get("TYPESAFE_API_KEY"):
        return JevEndpoint("typesafe", TYPESAFE_URL, TYPESAFE_MODEL, env["TYPESAFE_API_KEY"])
    if env.get("OPENROUTER_API_KEY"):
        return JevEndpoint("openrouter", DECISIONS_URL, MODEL, env["OPENROUTER_API_KEY"])
    return None


def build_state(row: dict) -> str:
    age_days = max((row["first_seen"] - row["created_at"]).days, 0)
    readme = _BADGE.sub("", row.get("readme") or "")[:README_CHARS]
    return (f"GitHub repository snapshot, taken {age_days} day(s) after the repository was created.\n"
            f"Name: {row['repo_full_name']}\nAuthor: {row.get('author_name') or ''}\n"
            f"Category: {row.get('category') or ''}\nDescription: {row.get('description') or ''}\n\n"
            f"README (excerpt):\n{readme}")


def flatten(answers: dict) -> dict:
    out: dict = {}
    for key, ans in answers.items():
        if ans["type"] == "noul":
            out[key] = ans["noul"]
        elif ans["type"] == "score":
            out[key] = ans["score"]
        else:
            out[key] = ans["choice"]
            out.update({f"{key}={c}": p for c, p in ans["probabilities"].items()})
    return out


def score_prior(row: dict, endpoint: JevEndpoint, client: httpx.Client) -> tuple[dict, str]:
    """Return (flattened prior, resolved model id). Raises after RETRIES transient failures."""
    body = {"model": endpoint.model, "state": build_state(row), "questions": QUESTIONS}
    headers = {"Authorization": f"Bearer {endpoint.key}", "Content-Type": "application/json"}
    last_error = ""
    for attempt in range(RETRIES):
        resp = client.post(endpoint.url, headers=headers, content=json.dumps(body), timeout=TIMEOUT_S)
        if resp.status_code == 429 or resp.status_code >= 500:
            last_error = f"HTTP {resp.status_code}"
            time.sleep(BACKOFF_S * 2 ** attempt)
            continue
        resp.raise_for_status()
        data = resp.json()
        return flatten(data["answers"]), data.get("model", "")
    raise RuntimeError(f"Jev decisions failed for {row['repo_full_name']}: {last_error}")
