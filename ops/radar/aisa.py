"""Client for AIsa's tool router, the radar's paid data source.

Used for signal ① (X posts of labs and AI bloggers) and the review (Google Trends via
DataForSEO). Posts to the same endpoint as `aisa call`, directly: the CLI gives each
request about 30 s and the router runs a batch's calls one by one, about 10 s each,
so a batch of four already timed out through the CLI (2026-10-03). Here the timeout is
ours, and CI needs no Node. Key: AISA_API_KEY in CI; locally the CLI's stored key.
Every call is billed: callers keep their batches small and fixed. A batch is sent again
only when the gateway in front of the router answers 502, 503 or 504 (2026-10-16: the
fourth batch of five got nginx's 504 after about a minute); the router may have run it
anyway, so one bad day costs two batches at most. Any other failure is not retried.

Prices seen on 2026-10-03: an account's last 20 posts 3000 micro-USD, one Trends
explore task 1200 micro-USD.
"""
from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = os.environ.get("AISA_ROUTER_BASE_URL", "https://tools.aisa.one") + "/v1/tool-router/aisa-batch-use"
MAX_CALLS = 20      # the router's own limit per batch (1–20 calls)
BATCH = 3           # what call_all sends at once, about 30 s a batch: the gateway gives up near 60 s
TIMEOUT = 240
GATEWAY = {502, 503, 504}   # answered by the gateway, not the router: worth one more try
RETRY_AFTER = 10            # seconds


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


def send(req: urllib.request.Request, timeout: int, tries: int = 2) -> dict:
    """The JSON answer to one request. A 5xx from the gateway is sent once more after a
    pause; anything else raises at once."""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.load(res)
    except urllib.error.HTTPError as exc:
        if exc.code in GATEWAY and tries > 1:
            time.sleep(RETRY_AFTER)
            return send(req, timeout, tries - 1)
        raise AisaError(http_error(exc)) from exc
    except (OSError, ValueError) as exc:
        raise AisaError(f"{type(exc).__name__}: {exc}") from exc


def http_error(exc: urllib.error.HTTPError) -> str:
    """'HTTP 504 Gateway Time-out' for a gateway's HTML page, else the start of the body
    as plain text: the report mail renders markdown, so a page's tags would become HTML."""
    body = exc.read().decode("utf-8", "replace")
    title = re.search(r"<title>(.*?)</title>", body, re.I | re.S)
    if title:
        name = re.sub(rf"^{exc.code}\s*", "", " ".join(html.unescape(title.group(1)).split()))
        return f"HTTP {exc.code} {name}".strip()[:200]
    text = " ".join(re.sub(r"<[^>]*>?", " ", body).split())[:200]
    return f"HTTP {exc.code}: {text}" if text else f"HTTP {exc.code}"


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
    body = send(req, TIMEOUT)
    if "error" in body:
        raise AisaError(str(body["error"].get("message") or body["error"])[:200])
    out, cost = {}, 0
    for r in body.get("results", []):
        cost += int(r.get("customer_cost_micros_usd") or 0)
        if r.get("successful"):
            out[r["call_id"]] = r.get("data") or {}
    return out, cost


CHAT = os.environ.get("AISA_API_BASE_URL", "https://api.aisa.one") + "/v1/chat/completions"


def chat(model: str, system: str, user: str, max_tokens: int = 1500) -> str:
    """AIsa's OpenAI-compatible chat endpoint, same key as the tool router."""
    req = urllib.request.Request(CHAT, data=json.dumps({"model": model, "temperature": 0, "max_tokens": max_tokens, "messages": [
        {"role": "system", "content": system}, {"role": "user", "content": user}]}).encode(), method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key()}", "User-Agent": "agentskillshub-radar/1.0"})
    try:
        return send(req, 90)["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise AisaError(f"{type(exc).__name__}: {exc}") from exc
