"""The radar's review: keep every lead, check it in Google Trends two weeks later.

record()   upserts today's leads into radar_leads (migration 026), each with its evidence
           (migration 027; the shape is below) once the table has that column.
record_new()  the same for leads that must not show (shadow mode): it never touches a lead
           another signal holds, beyond merging the evidence into it.
add_evidence()  merges more evidence into leads already kept: the keyword table's reading
           of a name (usecases.name_evidence).
review()   takes up to PER_DAY leads first seen REVIEW_AFTER days ago or earlier and not
           yet checked, those of retired signals (RETIRED_SIGNALS) after all the others,
           asks DataForSEO Trends (via AIsa) about each search variant,
           and stores hit / miss / no_data plus how many days the radar was ahead.
summary()  per signal over the last WINDOW days of verdicts (tally): early hits, late hits,
           unclear hits, no rise, no data, and the median lead of the early hits. A hit is early
           when Trends rose EARLY_DAYS or more after the radar first saw the term, late when it
           rose before; unclear when neither can be told (unclear()): the lead was first seen on
           RECORDING_START, or its rise began before the repository it came from existed. The
           stored verdict stays "hit" in every case.

Each variant is its own call: in one shared task the values share a 0-100 scale and a
small term next to a big one reads 0, and the live endpoint runs only the first task of
a request's body (seen 2026-10-03), so tasks cannot be batched into one call either. A variant "rose" when its peak after
first_seen clears its own baseline (mean before first_seen) by RISE_FACTOR and
RISE_MIN; a word with an older meaning ("strata": strata rock, strata title) has a
high baseline and does not rise, while "niko1221 strata" goes from 0 to something.

The evidence, radar_leads.evidence (JSONB). Another project reads it to draft a page, so
these keys stay as they are: a key may be added, none renamed or retyped. A key is there
only when the lead has something for it.
  {"v": 1, "updated": "YYYY-MM-DD",
   "posts": [{"url", "account", "text", "likes", "date", "platform"}],
       up to 10, most-liked first. url: the post ("" when the source gives none); account:
       who posted it; text: at most 280 characters; likes: int; date: "YYYY-MM-DD" or "";
       platform: "x", "bluesky", "tiktok", "instagram", "youtube"... Optional: "views" (int)
       and "link" (the URL the post linked: new sites).
   "examples": [str],  the report's example lines, up to 10
   "variants": [str],  the search terms
   "meme": {"what", "checks", "earliest": "YYYY-MM-DD" or "", "earliest_is_floor": bool,
            "window": {"peak_days", "age_days", "days_left"},                AI video trends
            "slots": {"head": page, "tool": page with "ads": bool, "taken": bool}},
       a page: {"results", "platforms", "tools": int, "blocks": [str]}, Google's first page for
       the trend's name (head) and its search term (tool), US English. From 2026-10-31, and only
       for leads that had the competition check (meme_checks.slots, shadow: shown nowhere).
   "keywords": {"rows": [{"phrase", "kind", "per_day", "decision", "now"}],
                "tails": [str], "cosearch": [str]},          names the keyword table read
   "site": {"domain", "registered", "age_days", "authors", "by": {network: people},
            "traffic": {"driven", "shares", "visits", "month", "registered"} or null},
                                                                 new sites people link
   "born": "YYYY-MM-DD",  the day the repository a breakout lead came from was created (from 2026-10-27)
   "first_by": {signal: "YYYY-MM-DD"}}  the day each signal first reported the lead: which one
                                        came first. Kept from FIRST_BY_SINCE on: a lead first
                                        seen before it has it only for the signals since.
A lead recorded again merges (merge_evidence): posts are the union by URL, the 10
most-liked kept; first_by keeps each signal's earliest day; every other key takes the
newest value.
"""
from __future__ import annotations

import json
import re
import statistics
from datetime import date, timedelta

import aisa

REVIEW_AFTER = 14
BEFORE_DAYS = 30
# Leads a day; each costs one Trends task per variant (1200 micro-USD). It was 5 while about 33
# leads came in a day, so a lead waited about 84 days for its review (2026-10-21); 40 keeps up.
PER_DAY = 40
MAX_VARIANTS = 3
# Trends tasks a run, about 10 minutes (the gateway takes 3 a batch, about 30 s) and $0.072; a lead that does
# not fit stays due for tomorrow. Leads averaged 1.26 tasks on 2026-10-21, so 40 fit in about 50.
REVIEW_CALLS_MAX = 60
RISE_FACTOR, RISE_MIN = 2.0, 10
# A hit is early only when Trends rose at least this many days after the radar first saw the term. 16 of the
# 17 hits by 2026-10-21 had risen before or on that day; most of them were unclear (below), not late.
EARLY_DAYS = 1
OUTCOMES = ("early", "late", "unclear", "miss", "no_data")
# radar_leads' first day (migration 026). A lead first seen then may have been reported in the days before it, so
# how early it was cannot be told: 12 of the 54 hits reviewed by 2026-10-27, all of them "late".
RECORDING_START = date(2026, 10, 3)
# A rise that began more than this many days before the repository a lead came from existed is the word's older
# use or noise, not the repository's: 6 of the 29 breakout hits by 2026-10-27 (coucou, opendots, removemacai).
PRE_EXISTING_DAYS = 1
# breakout's note, for the leads kept before evidence had "born": stars over stars a day is the repository's age,
# to the day for 27 of those 29 hits and a day late for 2.
BORN_NOTE = re.compile(r"GitHub 爆发 \S+ ★(\d+)\(均 (\d+)/天")
RISE_SHARE = 0.25     # the rise starts where a series first covers this share of base -> peak
WINDOW = 60
TOOL = "post_dataforseo_keywords_trends_explore_live"
# Google has not settled the last two days of a daily series: they come back as 0 and
# then 100 for unrelated terms ("ai image detector": ..., 5, 5, 0, 100 on 2026-10-12),
# which reads as a rise. Every reader drops them (settled()). Found before the first
# leads came due (10-17), so no stored verdict was made from those days.
UNSETTLED_DAYS = 2
# The ① leads the daily report lists from the last day (recent_sources); radar.py adds the
# new sites people link once social_sites.SOCIAL_SHOW is on.
SOURCE_KINDS = ("x", "hf", "meme", "appstore")
# Signals the radar stopped reading on 2026-10-21 (radar.RETIRED labels them). Their leads, about 37% of those
# due that day, are still reviewed, but only with the day's places left over: the signals still running come first.
RETIRED_SIGNALS = ("sitemap", "newsite")
DUE_SQL = """
    SELECT term, first_seen, variants FROM radar_leads
    WHERE reviewed_at IS NULL AND first_seen <= :cutoff
    ORDER BY signals <@ CAST(:retired AS text[]), first_seen LIMIT :n
"""
EVIDENCE_V = 1
EVIDENCE_POSTS = 10
EVIDENCE_EXAMPLES = 10
POST_CHARS = 280
EVIDENCE_PARTS = ("meme", "keywords", "site", "born")   # kept as the signal built them
FIRST_BY_SINCE = date(2026, 10, 27)             # the day evidence began to keep which signal reported a lead first
_EVIDENCE_COLUMN: bool | None = None            # radar_leads.evidence exists (migration 027); asked once a run
_UPSERT = """
    INSERT INTO radar_leads (term, first_seen, last_seen, signals, notes, named, variants{col})
    VALUES (:term, :today, :today, :kinds, :notes, :named, :variants{val})
    ON CONFLICT (term) DO UPDATE SET
      last_seen = EXCLUDED.last_seen,
      signals   = ARRAY(SELECT DISTINCT unnest(radar_leads.signals || EXCLUDED.signals)),
      notes     = (radar_leads.notes || EXCLUDED.notes)[greatest(1, cardinality(radar_leads.notes) + cardinality(EXCLUDED.notes) - 9):],
      named     = coalesce(EXCLUDED.named, radar_leads.named),
      variants  = ARRAY(SELECT DISTINCT unnest(radar_leads.variants || EXCLUDED.variants)){set}
"""
UPSERT = _UPSERT.format(col="", val="", set="")
UPSERT_EVIDENCE = _UPSERT.format(col=", evidence", val=", CAST(:evidence AS jsonb)", set=",\n      evidence  = EXCLUDED.evidence")


def settled(points: list[tuple], today: date) -> list[tuple]:
    """A daily Trends series without its last UNSETTLED_DAYS days. Rows are (day, value, ...)."""
    cut = today - timedelta(days=UNSETTLED_DAYS)
    return [p for p in points if p[0] < cut]


def _engine():
    from sqlalchemy import create_engine
    from signals import db_url
    return create_engine(db_url().replace("postgres://", "postgresql://", 1), pool_pre_ping=True)


def record(rows: list[dict], today: date | None = None) -> int:
    """rows: report leads with term, kinds (signal names), signals (report lines), optional
    named and variants, and what evidence() reads. The evidence is merged into what the lead
    holds; until migration 027 adds the column it is left out and the rest is written as before."""
    if not rows:
        return 0
    from sqlalchemy import text
    today = today or date.today()
    engine = _engine()
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL statement_timeout = '60s'"))
        with_evidence = _has_evidence(conn)
        held = _held(conn, [r["term"] for r in rows], with_evidence) if with_evidence else None
        _upsert(conn, rows, today, held)
    engine.dispose()
    return len(rows)


def record_new(rows: list[dict], today: date | None = None) -> dict:
    """Leads that must not show (social_sites.py's shadow mode): a term that is no lead yet is
    written as record() writes it; a term another signal holds keeps its lead as it is, since its
    last note and last_seen are what the reports show, and only takes the evidence (once the
    column exists). Returns {"recorded": written, "merged": evidence added to leads held}."""
    if not rows:
        return {"recorded": 0, "merged": 0}
    from sqlalchemy import text
    today = today or date.today()
    engine = _engine()
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL statement_timeout = '60s'"))
        with_evidence = _has_evidence(conn)
        held = _held(conn, [r["term"] for r in rows], with_evidence)
        fresh, kept = [r for r in rows if r["term"] not in held], [r for r in rows if r["term"] in held]
        _upsert(conn, fresh, today, {} if with_evidence else None)
        if with_evidence:
            _merge_into(conn, kept, held, today)
    engine.dispose()
    return {"recorded": len(fresh), "merged": len(kept) if with_evidence else 0}


def _upsert(conn, rows: list[dict], today: date, held: dict | None) -> None:
    from sqlalchemy import text
    sql = text(UPSERT if held is None else UPSERT_EVIDENCE)
    for r in rows:
        conn.execute(sql, _params(r, today, held))


def _params(r: dict, today: date, held: dict | None) -> dict:
    """One row's values. `held` is {term: evidence} with the column, None without; a term twice
    in one batch merges into its first row's evidence."""
    params = {"term": r["term"], "today": today, "kinds": sorted(set(r["kinds"])), "notes": r["signals"],
              "named": r.get("named"), "variants": r.get("variants", [])}
    if held is not None:
        held[r["term"]] = merge_evidence(held.get(r["term"]), evidence(r, today))
        params["evidence"] = json.dumps(held[r["term"]], ensure_ascii=False)
    return params


def add_evidence(rows: list[dict], today: date | None = None) -> int:
    """More evidence for leads already kept (rows: term and the parts evidence() reads), merged
    in. A term that is no lead yet is left alone, and nothing is written without the column.
    Returns how many leads took it."""
    if not rows:
        return 0
    from sqlalchemy import text
    today = today or date.today()
    engine = _engine()
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL statement_timeout = '60s'"))
        held = _held(conn, [r["term"] for r in rows], True) if _has_evidence(conn) else {}
        mine = [r for r in rows if r["term"] in held]
        _merge_into(conn, mine, held, today)
    engine.dispose()
    return len(mine)


def _merge_into(conn, rows: list[dict], held: dict, today: date) -> None:
    """Each row's evidence merged into the lead `held` has for it; nothing else of the lead changes."""
    from sqlalchemy import text
    for r in rows:
        held[r["term"]] = merge_evidence(held[r["term"]], evidence(r, today))
        conn.execute(text("UPDATE radar_leads SET evidence = CAST(:ev AS jsonb) WHERE term = :term"),
                     {"ev": json.dumps(held[r["term"]], ensure_ascii=False), "term": r["term"]})


def _has_evidence(conn) -> bool:
    """Whether radar_leads has the evidence column yet (migration 027), asked once a run."""
    global _EVIDENCE_COLUMN
    if _EVIDENCE_COLUMN is None:
        from sqlalchemy import text
        _EVIDENCE_COLUMN = conn.execute(text(
            "SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' "
            "AND table_name = 'radar_leads' AND column_name = 'evidence'")).first() is not None
    return _EVIDENCE_COLUMN


def _held(conn, terms: list[str], with_evidence: bool) -> dict:
    """{term: its evidence, or None} for the terms that are leads already (evidence is None for
    all without the column), locked until the transaction ends so that two runs writing one
    lead keep each other's posts."""
    from sqlalchemy import text
    column = "evidence" if with_evidence else "NULL"
    rows = conn.execute(text(f"SELECT term, {column} FROM radar_leads WHERE term = ANY(:terms) FOR UPDATE"),
                        {"terms": list(dict.fromkeys(terms))}).fetchall()
    return {t: json.loads(e) if isinstance(e, str) else e for t, e in rows}


def evidence(row: dict, today: date) -> dict:
    """A lead's evidence (the shape is in the module doc) from its report row: its posts and
    `evidence_posts`, examples and variants, and the parts a signal built (EVIDENCE_PARTS)."""
    out = {"v": EVIDENCE_V, "updated": today.isoformat(),
           "posts": top_posts([*row.get("posts", []), *row.get("evidence_posts", [])]),
           "examples": [str(e) for e in row.get("examples", []) if e][:EVIDENCE_EXAMPLES],
           "variants": list(row.get("variants", [])), **{k: row.get(k) for k in EVIDENCE_PARTS},
           "first_by": {k: today.isoformat() for k in sorted(set(row.get("kinds") or []))}}
    return {k: v for k, v in out.items() if v not in (None, "", [], {})}


def merge_evidence(old: dict | None, new: dict) -> dict:
    """New evidence over what a lead holds: posts are the union by URL (a post read again takes
    its newer copy), the EVIDENCE_POSTS most-liked kept; every other key takes the newest value."""
    old = old if isinstance(old, dict) else {}
    merged = {**old, **{k: v for k, v in new.items() if k != "posts"}}
    merged["posts"] = top_posts([*old.get("posts", []), *new.get("posts", [])])
    merged["first_by"] = earliest(old.get("first_by") or {}, new.get("first_by") or {})
    return {k: v for k, v in merged.items() if v not in ([], {})}


def earliest(a: dict[str, str], b: dict[str, str]) -> dict[str, str]:
    """{signal: the earlier of its two days}."""
    return {k: min(d for d in (a.get(k), b.get(k)) if d) for k in sorted(set(a) | set(b))}


def top_posts(posts: list[dict]) -> list[dict]:
    """Posts in the evidence's shape, one per URL (the later copy wins), most-liked first."""
    unique: dict[str, dict] = {}
    for p in posts:
        q = _post(p)
        unique[q["url"] or f"{q['platform']}|{q['text'][:80]}"] = q
    return sorted(unique.values(), key=lambda p: -p["likes"])[:EVIDENCE_POSTS]


def _post(p: dict) -> dict:
    out = {"url": str(p.get("url") or ""), "account": str(p.get("account") or p.get("author") or ""),
           "text": " ".join(str(p.get("text") or "").split())[:POST_CHARS], "likes": int(p.get("likes") or 0),
           "date": str(p.get("date") or p.get("day") or "")[:10], "platform": str(p.get("platform") or "")}
    return out | {k: p[k] for k in ("views", "link") if p.get(k)}


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


def within_budget(due: list[tuple]) -> list[tuple]:
    """The first due leads, in DUE_SQL's order, whose Trends tasks fit REVIEW_CALLS_MAX, whole leads only; the
    rest stay due."""
    out, calls = [], 0
    for row in due:
        term, _, variants = row
        n = len((list(variants) or [term])[:MAX_VARIANTS])
        if calls + n > REVIEW_CALLS_MAX:
            break
        out.append(row)
        calls += n
    return out


def plan_calls(due: list[tuple], today: date) -> tuple[list[dict], list[tuple]]:
    """One Trends call per search variant of each due lead, over its review window."""
    calls, plan = [], []
    for i, (term, first_seen, variants) in enumerate(due):
        keys = (list(variants) or [term])[:MAX_VARIANTS]
        window = {"date_from": (first_seen - timedelta(days=BEFORE_DAYS)).isoformat(),
                  "date_to": min(first_seen + timedelta(days=REVIEW_AFTER), today).isoformat()}
        ids = [f"r{i}v{j}" for j in range(len(keys))]
        calls += [{"call_id": cid, "tool": TOOL, "arguments": {"body": [{"keywords": [k], **window}]}}
                  for cid, k in zip(ids, keys)]
        plan.append((ids, term, first_seen, keys))
    return calls, plan


def review(today: date | None = None) -> dict:
    from sqlalchemy import text
    today = today or date.today()
    engine = _engine()
    with engine.connect() as conn:
        conn.execute(text("SET LOCAL statement_timeout = '60s'"))
        due = conn.execute(text(DUE_SQL), {"cutoff": today - timedelta(days=REVIEW_AFTER), "n": PER_DAY,
                                           "retired": list(RETIRED_SIGNALS)}).fetchall()
    due = within_budget(due)
    if not due:
        engine.dispose()
        return {"checked": [], "cost_micros": 0}
    calls, plan = plan_calls(due, today)
    data, cost = aisa.call_all(calls)
    checked = []
    with engine.begin() as conn:
        born = _born_held(conn, [p[1] for p in plan])
        for ids, term, first_seen, keys in plan:
            if not all(cid in data for cid in ids):
                continue   # stays due; tomorrow's run takes it again
            per = {k: rose(settled(_series((data[cid].get("tasks") or [{}])[0]), today), first_seen) for cid, k in zip(ids, keys)}
            checked.append(_store(conn, term, first_seen, per, born.get(term, (None, None))))
    engine.dispose()
    return {"checked": checked, "cost_micros": cost}


def _store(conn, term: str, first_seen: date, per: dict, held: tuple) -> dict:
    """Writes one lead's verdict; returns it as today's report lists it. held: (evidence "born", notes)."""
    from sqlalchemy import text
    v, lead = verdict(per, first_seen)
    conn.execute(text("""
        UPDATE radar_leads SET reviewed_at = now(), verdict = :v, lead_days = :lead,
               trends = CAST(:trends AS jsonb) WHERE term = :term
    """), {"v": v, "lead": lead, "trends": json.dumps(per), "term": term})
    vague = v == "hit" and unclear(first_seen, first_rise(per), born_day(*held, first_seen))
    return {"term": term, "first_seen": first_seen.isoformat(), "verdict": v, "lead_days": lead, "unclear": vague}


def _born_held(conn, terms: list[str]) -> dict[str, tuple]:
    """{term: (its evidence's "born" or None, its notes)}, what born_day() reads."""
    from sqlalchemy import text
    born = "evidence->>'born'" if _has_evidence(conn) else "NULL"
    rows = conn.execute(text(f"SELECT term, {born}, notes FROM radar_leads WHERE term = ANY(:terms)"),
                        {"terms": terms}).fetchall()
    return {t: (b, n) for t, b, n in rows}


def recent_sources(today: date | None = None, kinds: tuple[str, ...] = SOURCE_KINDS) -> list[dict]:
    """① leads (X, HF, AI video trends) and new apps the 8-hourly source job kept since yesterday, for the daily report."""
    from sqlalchemy import text
    today = today or date.today()
    engine = _engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT term, signals, notes, named FROM radar_leads
            WHERE signals && CAST(:kinds AS text[]) AND last_seen >= :since ORDER BY last_seen DESC, term LIMIT 20
        """), {"since": today - timedelta(days=1), "kinds": list(kinds)}).fetchall()
    engine.dispose()
    return [{"term": t, "kinds": list(k), "note": (n or [""])[-1], "named": named} for t, k, n, named in rows]


def summary(today: date | None = None) -> dict:
    from sqlalchemy import text
    today = today or date.today()
    engine = _engine()
    with engine.connect() as conn:
        born = "evidence->>'born'" if _has_evidence(conn) else "NULL"
        rows = conn.execute(text(f"""
            SELECT signals, verdict, lead_days, first_seen, trends, {born}, notes FROM radar_leads
            WHERE reviewed_at >= :since AND verdict IS NOT NULL
        """), {"since": today - timedelta(days=WINDOW)}).fetchall()
        pending = conn.execute(text("SELECT count(*) FROM radar_leads WHERE reviewed_at IS NULL")).scalar()
    engine.dispose()
    judged = [(kinds, said, lead, said == "hit" and unclear(seen, first_rise(trends), born_day(b, notes, seen)))
              for kinds, said, lead, seen, trends, b, notes in rows]
    return {"by_signal": tally(judged), "pending": pending, "window_days": WINDOW}


def born_day(born: str | None, notes: list[str] | None, first_seen: date) -> date | None:
    """The day the repository a breakout lead came from was created: the evidence's "born", else its age read
    off breakout's note (BORN_NOTE); None for a lead from no repository."""
    if born:
        return date.fromisoformat(born)
    for note in notes or []:
        m = BORN_NOTE.search(note)
        if m and int(m.group(2)):
            return first_seen - timedelta(days=round(int(m.group(1)) / int(m.group(2))))
    return None


def first_rise(trends: dict | None) -> date | None:
    """The earliest day a variant's rise began, as verdict() dated the lead (radar_leads.trends)."""
    days = [v["first_rise"] for v in (trends or {}).values() if isinstance(v, dict) and v.get("first_rise")]
    return date.fromisoformat(min(days)) if days else None


def unclear(first_seen: date, rise: date | None, born: date | None) -> bool:
    """Whether a hit's lead says nothing about how early the radar was: first seen on RECORDING_START, or a
    rise that began more than PRE_EXISTING_DAYS before the repository it came from existed."""
    if first_seen == RECORDING_START:
        return True
    return bool(rise and born and (born - rise).days > PRE_EXISTING_DAYS)


def outcome(said: str, lead_days: int | None, vague: bool = False) -> str:
    """A stored verdict as the reports count it: a hit is "unclear" when `vague` (unclear()), else "early"
    when Trends rose EARLY_DAYS or more after the radar first saw the term, else "late"; "miss" (no rise)
    and "no_data" stay as they are."""
    if said == "hit":
        if vague:
            return "unclear"
        return "early" if lead_days is not None and lead_days >= EARLY_DAYS else "late"
    return "no_data" if said == "no_data" else "miss"


def tally(rows: list[tuple]) -> dict[str, dict]:
    """{signal: {"checked", "early", "late", "unclear", "miss", "no_data", "median_lead"}} from (signals,
    verdict, lead_days[, vague]) rows; a lead with two signals counts for both. median_lead is the early
    hits' only."""
    by: dict[str, dict] = {}
    for kinds, said, lead_days, *vague in rows:
        got = outcome(said, lead_days, bool(vague and vague[0]))
        for k in kinds or ["?"]:
            s = by.setdefault(k, {"checked": 0, **dict.fromkeys(OUTCOMES, 0), "leads": []})
            s["checked"] += 1
            s[got] += 1
            s["leads"] += [lead_days] if got == "early" else []
    for s in by.values():
        leads = s.pop("leads")
        s["median_lead"] = statistics.median(leads) if leads else None
    return by
