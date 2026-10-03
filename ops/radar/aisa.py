"""Client for AIsa's tool router, the radar's paid data source.

Used for signal ① (X posts of labs and AI bloggers) and the review (Google Trends via
DataForSEO). Posts to the same endpoint as `aisa call`, directly: the CLI gives each
request about 30 s and the router runs a batch's calls one by one, about 10 s each,
so a batch of four already timed out through the CLI (2026-10-03). Here the timeout is
ours, and CI needs no Node. Key: AISA_API_KEY in CI; locally the CLI's stored key.
Every call is billed: callers keep their batches small and fixed, and a failed batch is
never retried here, so one bad day costs one batch at most.

Prices seen on 2026-10-03: an account's last 20 posts 3000 micro-USD, one Trends
explore task 1200 micro-USD.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

URL = os.environ.get("AISA_ROUTER_BASE_URL", "https://tools.aisa.one") + "/v1/tool-router/aisa-batch-use"
MAX_CALLS = 20      # the router's own limit per batch (1–20 calls)
BATCH = 5           # what call_all sends at once, about 50 s a batch
TIMEOUT = 240


class AisaError(RuntimeError):
    pass


def key() -> str:
    if os.environ.get("AISA_API_KEY"):
        return os.environ["AISA_API_KEY"].strip()
    home = Path.home() / ".aisa"
    if (home / "key").exists():
        return (home / "key").read_text().strip()
    if (home / "tokens.json").exists():
        return json.loads((home / "tokens.json").read_text()).get("accessToken", "")
    raise AisaError("no AIsa key: set AISA_API_KEY")


def call_all(calls: list[dict]) -> tuple[dict[str, dict], int]:
    """call() in batches of BATCH. A failed batch raises and stops the rest."""
    out, cost = {}, 0
    for i in range(0, len(calls), BATCH):
        data, c = call(calls[i:i + BATCH])
        out.update(data)
        cost += c
    return out, cost


def call(calls: list[dict]) -> tuple[dict[str, dict], int]:
    """Run one batch. Returns ({call_id: data}, cost in micro-USD). Calls that failed are
    left out of the dict; the batch as a whole only raises when the request fails."""
    if not calls:
        return {}, 0
    if len(calls) > MAX_CALLS:
        raise AisaError(f"{len(calls)} calls in one batch, the cap is {MAX_CALLS}")
    req = urllib.request.Request(URL, data=json.dumps({"calls": calls}).encode(), method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key()}", "x-aisa-source": "agentskillshub-radar"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            body = json.load(res)
    except urllib.error.HTTPError as exc:
        raise AisaError(f"HTTP {exc.code}: {' '.join(exc.read().decode('utf-8', 'replace').split())[:200]}") from exc
    except (OSError, ValueError) as exc:
        raise AisaError(f"{type(exc).__name__}: {exc}") from exc
    if "error" in body:
        raise AisaError(str(body["error"].get("message") or body["error"])[:200])
    out, cost = {}, 0
    for r in body.get("results", []):
        cost += int(r.get("customer_cost_micros_usd") or 0)
        if r.get("successful"):
            out[r["call_id"]] = r.get("data") or {}
    return out, cost
