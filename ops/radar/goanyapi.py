"""Optional second data source: GoAnyAPI (goanyapi.com), for what AIsa's tools do not give.

Used for three things: Google Trends' *related queries* for a name, the terms real people
searched together with it, and a 30-day daily Trends series for one country, which
arrives settled up to yesterday (DataForSEO's worldwide series does not); and where a new
site's visits come from (`traffic`, social_sites.py). Key: GOANYAPI_API_KEY. Without it every caller skips
this source and the radar runs as before.

One credit is $0.001; a related-queries lookup costs 6 (October 2026). Calls take 20 to
55 seconds and about one in ten fails with a timeout or a 502, so a call is tried twice
and a failure is reported, never fatal. The service is young (first released August
2026): treat it as an enhancement, not a dependency.
"""
from __future__ import annotations

import http.client
import json
from datetime import date, datetime, timezone
import os
import urllib.error
import urllib.parse
import urllib.request

UA = "agentskillshub-radar/1.0"

BASE = os.environ.get("GOANYAPI_BASE_URL", "https://api.goanyapi.com") + "/api/v1/"
TIMEOUT = 90
TRIES = 2
MICROS_PER_CREDIT = 1000


class GoAnyError(RuntimeError):
    pass


def key() -> str:
    return os.environ.get("GOANYAPI_API_KEY", "").strip()


def call(path: str, *, timeout: int = TIMEOUT, **params) -> tuple[dict, int]:
    """One GET. Returns (data, cost in micro-USD). `timeout` is per try: a caller in a hurry
    (the 8-hourly source run, social_sites.py) passes a shorter one."""
    req = urllib.request.Request(BASE + path + "?" + urllib.parse.urlencode(params), headers={
        "authorization": f"Bearer {key()}", "accept": "application/json", "user-agent": UA})
    error = ""
    for _ in range(TRIES):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                body = json.load(res)
        except urllib.error.HTTPError as exc:
            error = f"HTTP {exc.code}"
            if exc.code < 500:
                break
            continue
        except (OSError, ValueError, http.client.HTTPException) as exc:   # IncompleteRead is none of the others
            error = f"{type(exc).__name__}: {exc}"
            continue
        data = body.get("data") or {}
        if body.get("code") != "ok":
            raise GoAnyError(str(body.get("message") or body)[:160])
        return data, int(data.get("costCredits") or 0) * MICROS_PER_CREDIT
    raise GoAnyError(error[:160])


def related_queries(term: str, geo: str = "US", window: str = "today 1-m") -> tuple[dict[str, list[str]], int]:
    """{"rising": [...], "top": [...]}: what people searched on Google together with `term`."""
    data, cost = call("google-trends", q=term, date=window, geo=geo, data_type="RELATED_QUERIES")
    rq = data.get("relatedQueries") or {}
    return {k: [" ".join(str(x.get("query", "")).lower().split()) for x in rq.get(k) or []] for k in ("rising", "top")}, cost


def daily_series(term: str, geo: str = "US", window: str = "today 1-m") -> tuple[list[tuple[date, int]], int]:
    """[(day, value)] for `term` in one country, the last month by day."""
    data, cost = call("google-trends", q=term, date=window, geo=geo, data_type="TIMESERIES")
    out = []
    for p in (data.get("interestOverTime") or {}).get("timeline_data") or []:
        try:
            day = datetime.fromtimestamp(int(p["timestamp"]), timezone.utc).date()
            out.append((day, int(p["values"][0]["extracted_value"])))
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return out, cost
