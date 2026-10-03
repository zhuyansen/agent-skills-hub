"""Jev decisions, the one call the scenario review needs.

TypeSafe's own API when TYPESAFE_API_KEY is set (since 10-03, when the OpenRouter credit
ran out mid-review), else OpenRouter. Same questions, same answers. Started as a copy of
the decisions part of jev-search-rerank-eval's client, so the review runs in CI without
that repo. Standard library only. Keys come from the environment.
"""
from __future__ import annotations

import http.client
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

BASE = "https://openrouter.ai/api"
JEV_MODEL = "~typesafe/jev-latest"   # the resolved model id is recorded per response
TYPESAFE_URL = "https://api.typesafe.ai/v1/systemone"   # docs.typesafe.ai/introduction/quickstart
TYPESAFE_MODEL = "jev-latest"
RETRIES = 5
TIMEOUT = 120


@dataclass
class Decision:
    answers: dict
    model: str
    cost: float


class OpenRouter:
    def __init__(self) -> None:
        self.official = bool(os.environ.get("TYPESAFE_API_KEY"))
        self.key = os.environ["TYPESAFE_API_KEY" if self.official else "OPENROUTER_API_KEY"]
        self.tokens = 0   # the official API reports tokens, not cost
        self.total_cost = 0.0
        self.models_seen: set[str] = set()

    def _post(self, url: str, body: dict) -> dict:
        last: Exception | None = None
        for attempt in range(RETRIES):
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
                "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
                    out = json.load(res)
            except urllib.error.HTTPError as exc:
                if exc.code != 429 and exc.code < 500:
                    raise
                last = exc
            except (urllib.error.URLError, http.client.HTTPException, OSError) as exc:  # transient network errors
                # http.client.RemoteDisconnected is neither a URLError nor a timeout; it stopped
                # the type step after 57 of 205 repos on 10-03.
                last = exc
            else:
                usage = out.get("usage") or {}
                self.total_cost += float(usage.get("cost") or 0)
                self.tokens += int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
                if out.get("model"):
                    self.models_seen.add(out["model"])
                return out
            time.sleep(2 ** attempt)
        raise last or RuntimeError("jev: exhausted retries")

    def decisions(self, state: str, questions: dict) -> Decision:
        if self.official:
            out = self._post(TYPESAFE_URL, {"model": TYPESAFE_MODEL, "state": state, "questions": questions})
        else:
            out = self._post(f"{BASE}/alpha/decisions", {"model": JEV_MODEL, "state": state, "questions": questions})
        return Decision(out.get("answers", {}), out.get("model", ""), float((out.get("usage") or {}).get("cost") or 0))
