"""Jev decisions over OpenRouter, the one call the scenario review needs.

A copy of the decisions part of jev-search-rerank-eval's client, so the review runs
in CI without that repo. Standard library only. The key comes from the environment.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

BASE = "https://openrouter.ai/api"
JEV_MODEL = "~typesafe/jev-latest"   # the resolved model id is recorded per response
RETRIES = 5
TIMEOUT = 120


@dataclass
class Decision:
    answers: dict
    model: str
    cost: float


class OpenRouter:
    def __init__(self) -> None:
        self.key = os.environ["OPENROUTER_API_KEY"]
        self.total_cost = 0.0
        self.models_seen: set[str] = set()

    def _post(self, path: str, body: dict) -> dict:
        last: Exception | None = None
        for attempt in range(RETRIES):
            req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode(), headers={
                "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
                    out = json.load(res)
            except urllib.error.HTTPError as exc:
                if exc.code != 429 and exc.code < 500:
                    raise
                last = exc
            except (urllib.error.URLError, TimeoutError) as exc:  # transient network errors
                last = exc
            else:
                self.total_cost += float((out.get("usage") or {}).get("cost") or 0)
                if out.get("model"):
                    self.models_seen.add(out["model"])
                return out
            time.sleep(2 ** attempt)
        raise last or RuntimeError("openrouter: exhausted retries")

    def decisions(self, state: str, questions: dict) -> Decision:
        out = self._post("/alpha/decisions", {"model": JEV_MODEL, "state": state, "questions": questions})
        return Decision(out.get("answers", {}), out.get("model", ""), float((out.get("usage") or {}).get("cost") or 0))
