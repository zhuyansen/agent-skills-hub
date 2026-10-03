"""The radar's review: keep every lead, check it in Google Trends two weeks later.

record()   upserts today's leads into radar_leads (migration 026).
review()   takes up to PER_DAY leads first seen REVIEW_AFTER days ago or earlier and not
           yet checked, asks DataForSEO Trends (via AIsa) about each search variant,
           and stores hit / miss / no_data plus how many days the radar was ahead.
summary()  hit rate and median lead per signal over the last WINDOW days of verdicts.

Each variant is its own Trends task: in one shared task the values share a 0-100 scale
and a small term next to a big one reads 0. A variant "rose" when its peak after
first_seen clears its own baseline (mean before first_seen) by RISE_FACTOR and
RISE_MIN; a word with an older meaning ("strata": strata rock, strata title) has a
high baseline and does not rise, while "niko1221 strata" goes from 0 to something.
"""
from __future__ import annotations

import statistics
from datetime import date, timedelta

import aisa

REVIEW_AFTER = 14
BEFORE_DAYS = 30
PER_DAY = 5           # leads; each costs one Trends task per variant (1200 micro-USD)
MAX_VARIANTS = 3
RISE_FACTOR, RISE_MIN = 2.0, 10
RISE_SHARE = 0.25     # the rise starts where a series first covers this share of base -> peak
WINDOW = 60
TOOL = "post_dataforseo_keywords_trends_explore_live"


def _engine():
    from sqlalchemy import create_engine
    from signals import db_url
    return create_engine(db_url().replace("postgres://", "postgresql://", 1), pool_pre_ping=True)


def record(rows: list[dict], today: date | None = None) -> int:
    """rows: report leads with term, kinds (signal names), signals (report lines),
    optional named and variants."""
    from sqlalchemy import text
    today = today or date.today()
    sql = text("""
        INSERT INTO radar_leads (term, first_seen, last_seen, signals, notes, named, variants)
        VALUES (:term, :today, :today, :kinds, :notes, :named, :variants)
        ON CONFLICT (term) DO UPDATE SET
          last_seen = EXCLUDED.last_seen,
          signals   = ARRAY(SELECT DISTINCT unnest(radar_leads.signals || EXCLUDED.signals)),
          notes     = (radar_leads.notes || EXCLUDED.notes)[greatest(1, cardinality(radar_leads.notes) + cardinality(EXCLUDED.notes) - 9):],
          named     = coalesce(EXCLUDED.named, radar_leads.named),
          variants  = ARRAY(SELECT DISTINCT unnest(radar_leads.variants || EXCLUDED.variants))
    """)
    engine = _engine()
    with engine.begin() as conn:
        conn.execute(text("SET statement_timeout = '60s'"))
        for r in rows:
            conn.execute(sql, {"term": r["term"], "today": today, "kinds": sorted(set(r["kinds"])),
                               "notes": r["signals"], "named": r.get("named"), "variants": r.get("variants", [])})
    engine.dispose()
    return len(rows)


def rose(points: list[tuple[date, int]], first_seen: date) -> dict:
    """One variant's Trends series judged against its own baseline."""
    values = [v for _, v in points]
    if not values or max(values) == 0:
        return {"rose": False, "no_data": True}
    before = [v for d, v in points if d < first_seen]
    after = [v for d, v in points if d >= first_seen]
    base = statistics.mean(before) if before else 0.0
    peak_after = max(after, default=0)
    peak = max(values)
    out = {"base": round(base, 1), "peak_after": peak_after, "no_data": False,
           "rose": peak_after >= max(base * RISE_FACTOR, base + RISE_MIN)}
    if out["rose"]:
        line = base + RISE_SHARE * (peak - base)
        out["first_rise"] = next(d for d, v in points if v >= max(line, 1) and v > base).isoformat()
    return out


def verdict(per_variant: dict[str, dict], first_seen: date) -> tuple[str, int | None]:
    risen = [v for v in per_variant.values() if v.get("rose")]
    if risen:
        first = min(date.fromisoformat(v["first_rise"]) for v in risen)
        return "hit", (first - first_seen).days
    if all(v.get("no_data") for v in per_variant.values()):
        return "no_data", None
    return "miss", None


def _series(task: dict) -> list[tuple[date, int]]:
    try:
        item = task["result"][0]["items"][0]
    except (KeyError, IndexError, TypeError):
        return []
    return [(date.fromisoformat(p["date_from"]), int((p.get("values") or [0])[0] or 0)) for p in item.get("data", [])]


def review(today: date | None = None) -> dict:
    from sqlalchemy import text
    today = today or date.today()
    engine = _engine()
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = '60s'"))
        due = conn.execute(text("""
            SELECT term, first_seen, variants FROM radar_leads
            WHERE reviewed_at IS NULL AND first_seen <= :cutoff ORDER BY first_seen LIMIT :n
        """), {"cutoff": today - timedelta(days=REVIEW_AFTER), "n": PER_DAY}).fetchall()
    if not due:
        engine.dispose()
        return {"checked": [], "cost_micros": 0}
    calls, plan = [], []
    for i, (term, first_seen, variants) in enumerate(due):
        keys = (list(variants) or [term])[:MAX_VARIANTS]
        body = [{"keywords": [k], "date_from": (first_seen - timedelta(days=BEFORE_DAYS)).isoformat(),
                 "date_to": min(first_seen + timedelta(days=REVIEW_AFTER), today).isoformat()} for k in keys]
        calls.append({"call_id": f"r{i}", "tool": TOOL, "arguments": {"body": body}})
        plan.append((f"r{i}", term, first_seen, keys))
    data, cost = aisa.call_all(calls)
    checked = []
    with engine.begin() as conn:
        for cid, term, first_seen, keys in plan:
            if cid not in data:
                continue   # stays due; tomorrow's run takes it again
            tasks = data[cid].get("tasks") or []
            per = {k: rose(_series(t), first_seen) for k, t in zip(keys, tasks)}
            v, lead = verdict(per, first_seen)
            conn.execute(text("""
                UPDATE radar_leads SET reviewed_at = now(), verdict = :v, lead_days = :lead,
                       trends = CAST(:trends AS jsonb) WHERE term = :term
            """), {"v": v, "lead": lead, "trends": __import__("json").dumps(per), "term": term})
            checked.append({"term": term, "first_seen": first_seen.isoformat(), "verdict": v, "lead_days": lead})
    engine.dispose()
    return {"checked": checked, "cost_micros": cost}


def summary(today: date | None = None) -> dict:
    from sqlalchemy import text
    today = today or date.today()
    engine = _engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT signals, verdict, lead_days FROM radar_leads
            WHERE reviewed_at >= :since AND verdict IS NOT NULL
        """), {"since": today - timedelta(days=WINDOW)}).fetchall()
        pending = conn.execute(text("SELECT count(*) FROM radar_leads WHERE reviewed_at IS NULL")).scalar()
    engine.dispose()
    by: dict[str, dict] = {}
    for kinds, v, lead in rows:
        for k in kinds or ["?"]:
            s = by.setdefault(k, {"checked": 0, "hit": 0, "leads": []})
            s["checked"] += 1
            if v == "hit":
                s["hit"] += 1
                s["leads"].append(lead)
    for s in by.values():
        s["median_lead"] = statistics.median(s.pop("leads")) if s["hit"] else None
    return {"by_signal": by, "pending": pending, "window_days": WINDOW}
