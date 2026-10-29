"""Shadow record of CapCut's Most Used templates (migration 033): each 8-hourly source run stores the
newest finished hourly snapshot GoAnyAPI keeps of the listing, one row per template (best position,
title, use count). Nothing shows it. 2026-10-29: the user chose this (option A) over feeding the
listing into the AI video trends signal (memes.py) at once. A template's use count is how many people
already made their own version, and hotel lobby and Bulin 47 both sold while CapCut templates for them
existed; whether the listing shows such trends before their posts do is not known. A review two weeks
on checks that, and the trends it holds that memes.py never found; only then may it replace memes.py's
X search, which supplied none of the posts kept for the 16 trends found from 10-22 to 10-28.

The listing (goanyapi.com/docs/tiktok-capcut-trending-templates-api): up to 20 pages of about 24 cards,
repeats kept; GoAnyAPI snapshots it every hour (Asia/Shanghai hours) and keeps 30 days. 2 credits
($0.002) a page with cards, so about $0.04 a snapshot and $3.60 a month at three runs a day; the list
of hours is free. Which market it covers is not stated.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import goanyapi

SHANGHAI = timezone(timedelta(hours=8))   # GoAnyAPI's days and hours; China keeps no summer time
PAGES = 20                                # pages 0-19
WORKERS = 5
TIMEOUT = 45                              # per try: this runs inside the 8-hourly source job
HOURS_TRIED = 3                           # the newest hour may still be collecting (status RUNNING)
SEEN = "SELECT 1 FROM radar_capcut_templates WHERE day = :day AND hour = :hour LIMIT 1"
INSERT = """
INSERT INTO radar_capcut_templates (day, hour, template_id, position, title, slug, use_count_text,
                                    use_count, template_url)
VALUES (:day, :hour, :template_id, :position, :title, :slug, :use_count_text, :use_count, :template_url)
ON CONFLICT (day, hour, template_id) DO NOTHING
"""


def hours(now: datetime) -> list[tuple[str, int]]:
    """The newest hours GoAnyAPI holds a snapshot of, newest first: today's, then yesterday's."""
    out: list[tuple[str, int]] = []
    for back in (0, 1):
        day = (now.astimezone(SHANGHAI) - timedelta(days=back)).strftime("%Y%m%d")
        data, _ = goanyapi.call("capcut-most-used/times", timeout=TIMEOUT, day=day)
        out += [(day, int(t)) for t in sorted(data.get("times") or [], reverse=True)]
        if len(out) >= HOURS_TRIED:
            break
    return out[:HOURS_TRIED]


def page(day: str, hour: int, n: int) -> tuple[dict, int]:
    return goanyapi.call("capcut-most-used/history", timeout=TIMEOUT, day=day, time=hour, page=n)


def snapshot(day: str, hour: int) -> tuple[list[dict], int]:
    """One finished snapshot's cards and what the read cost; no cards while it is not finished. A page
    that fails fails the snapshot: a gap would read as templates arriving later than they did."""
    first, cost = page(day, hour, 0)
    if first.get("status") != "SUCCESS" or not first.get("items"):
        return [], cost
    with ThreadPoolExecutor(WORKERS) as pool:
        rest = list(pool.map(lambda n: page(day, hour, n), range(1, PAGES)))
    cards = list(first["items"]) + [c for data, _ in rest for c in data.get("items") or []]
    return cards, cost + sum(c for _, c in rest)


def _date(day: str) -> date:
    return datetime.strptime(day, "%Y%m%d").date()


def _row(day: str, hour: int, card: dict, position: int) -> dict:
    uses = card.get("useCountEstimate")
    return {"day": _date(day), "hour": hour, "template_id": str(card["templateId"]),
            "position": position, "title": card.get("title") or "", "slug": card.get("slug") or "",
            "use_count_text": card.get("useCountText") or "", "template_url": card.get("templateUrl") or "",
            "use_count": int(uses) if isinstance(uses, (int, float)) else None}


def rows_of(day: str, hour: int, cards: list[dict]) -> list[dict]:
    """One row per template, at its best place: the listing repeats cards."""
    best: dict[str, dict] = {}
    for i, card in enumerate(cards, 1):
        position = int(card.get("position") or i)
        tid = str(card.get("templateId") or "")
        if tid and (tid not in best or position < best[tid]["position"]):
            best[tid] = _row(day, hour, card, position)
    return list(best.values())


def _seen(engine, day: str, hour: int) -> bool:
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL statement_timeout = '30s'"))
        return conn.execute(text(SEEN), {"day": _date(day), "hour": hour}).first() is not None


def _write(engine, rows: list[dict]) -> None:
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL statement_timeout = '60s'"))
        conn.execute(text(INSERT), rows)


def record(now: datetime | None = None) -> dict:
    """Writes the newest finished snapshot not kept yet. Called with the radar's --skip-db honoured."""
    if not goanyapi.key():
        return {"skipped": True, "why": "没有 GOANYAPI_API_KEY"}
    import review
    engine = review._engine()
    try:
        return _record(engine, hours(now or datetime.now(timezone.utc)))
    finally:
        engine.dispose()


def _record(engine, newest: list[tuple[str, int]]) -> dict:
    spent = 0
    for day, hour in newest:
        if _seen(engine, day, hour):
            return {"day": day, "hour": hour, "already": True, "cost_micros": spent}
        cards, cost = snapshot(day, hour)
        spent += cost
        if cards:
            rows = rows_of(day, hour, cards)
            _write(engine, rows)
            return {"day": day, "hour": hour, "templates": len(rows), "cards": len(cards), "cost_micros": spent}
    return {"none": True, "cost_micros": spent}


def status(block: dict) -> str:
    """One line for the run's log, numbers only: the Actions log is public."""
    head = "- CapCut 模板榜(影子记录,不进邮件)"
    if block.get("error"):
        return f"{head}:没记录({block['error']})"
    if block.get("skipped"):
        return f"{head}:这轮不记({block.get('why') or '跳过数据库'})"
    if block.get("none"):
        return f"{head}:这两天没有抓完的快照"
    when = f"{block['day'][4:6]}-{block['day'][6:]} {block['hour']} 点(北京时间)"
    if block.get("already"):
        return f"{head}:{when}那张已经记过"
    return f"{head}:{when}那张,{block['templates']} 个模板({block['cards']} 张卡),${block['cost_micros'] / 1e6:.3f}"
