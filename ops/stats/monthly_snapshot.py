"""Monthly snapshot of the catalog for the /stats/ page (State of Agent Skills).

Read-only aggregate queries against Supabase; writes frontend/public/stats/data/<period>.json
and .csv, which the build turns into /stats/ and /stats/<period>/. A snapshot is never
rewritten once published: people cite its numbers, so a second run for the same period
stops unless --force is given.

The period is the month the issue covers: run on 2026-11-01, it is 2026-10. Counts are
repositories (not SKILL.md files), as indexed at snapshot time.

    python ops/stats/monthly_snapshot.py                 # previous month
    python ops/stats/monthly_snapshot.py --period 2026-10 --out /tmp/stats --force
"""
import argparse
import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "frontend" / "public" / "stats" / "data"
SCENARIOS = ROOT / "frontend" / "scripts" / "scenario-keywords.json"
SCHEMA_VERSION = 1
GROWTH_START = "2025-10"          # first month on the growth chart
GROWTH_TYPES = ("mcp-server", "claude-skill", "codex-skill")
TOP_PATTERNS = 12
TOP_LICENSES = 8
TOP_PLATFORMS = 10
TOP_MOVERS = 10
STATEMENT_TIMEOUT = "120s"
SPAM_NAME = re.compile(r"/r\d{2}-")  # star-farmed "rNN-…awesome…" copies (2026-10-17)
CJK = r"[一-鿿぀-ヿ가-힯]"
JSON_LIST = "case when {col} ~ '^\\[' then {col}::jsonb else '[]'::jsonb end"


def previous_month(now):
    year, month = (now.year, now.month - 1) if now.month > 1 else (now.year - 1, 12)
    return f"{year:04d}-{month:02d}"


def month_bounds(period):
    year, month = map(int, period.split("-"))
    nxt = f"{year + 1:04d}-01" if month == 12 else f"{year:04d}-{month + 1:02d}"
    return f"{period}-01", f"{nxt}-01"


def excluded_repos():
    """Repos the scenario pages exclude (spam, copies); kept off the movers list too."""
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    return {r.lower() for s in scenarios for r in s.get("match", {}).get("exclude_repos", [])}


def rows(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchall()


def totals(cur):
    (repos, five, official, scanned), = rows(cur, """
        select count(*), count(*) filter (where stars >= 5), count(*) filter (where is_official),
               count(*) filter (where security_scanned_at is not null) from skills""")
    return {"repos": repos, "repos_5_stars": five, "official": official, "scanned": scanned}


def counted(cur, sql, params=()):
    return [{"key": k, "count": n} for k, n in rows(cur, sql, params)]


def growth(cur, period):
    _, end = month_bounds(period)
    cols = ", ".join(f"count(*) filter (where project_type = '{t}')" for t in GROWTH_TYPES)
    found = rows(cur, f"""
        select to_char(date_trunc('month', created_at), 'YYYY-MM'), count(*), {cols} from skills
        where created_at >= %s and created_at < %s group by 1 order by 1""", (f"{GROWTH_START}-01", end))
    out = []
    for month, total, *typed in found:
        entry = {"month": month, "total": total, **dict(zip(GROWTH_TYPES, typed))}
        entry["other"] = total - sum(typed)
        out.append(entry)
    return out


def security(cur):
    grades = dict(rows(cur, """select security_grade, count(*) from skills
        where security_scanned_at is not null group by 1"""))
    patterns = counted(cur, f"""select f, count(*) from skills, jsonb_array_elements_text({JSON_LIST.format(col='security_flags')}) f
        where security_scanned_at is not null group by 1 order by 2 desc, 1 limit %s""", (TOP_PATTERNS,))
    return {"grades": grades, "patterns": patterns}


def licenses(cur, total):
    top = counted(cur, """select coalesce(nullif(license, ''), '(none)'), count(*) from skills
        group by 1 order by 2 desc limit %s""", (TOP_LICENSES,))
    rest = total - sum(r["count"] for r in top)
    return top + ([{"key": "(other)", "count": rest}] if rest > 0 else [])


def platforms(cur):
    return counted(cur, f"""select p, count(*) from skills, jsonb_array_elements_text({JSON_LIST.format(col='platforms')}) p
        group by 1 order by 2 desc, 1 limit %s""", (TOP_PLATFORMS,))


def cjk_share(cur):
    (share,), = rows(cur, f"""select round(100.0 * count(*) filter (where description ~ %s) / greatest(count(*), 1), 1)
        from skills""", (CJK,))
    return float(share)


def movers(cur, period, exclude):
    start, end = month_bounds(period)
    found = rows(cur, """select distinct on (repo_full_name) repo_full_name, week_start::date, stars, star_velocity
        from weekly_trending_snapshots where week_start >= %s and week_start < %s
        order by repo_full_name, star_velocity desc""", (start, end))
    keep = [r for r in found if r[0].lower() not in exclude and not SPAM_NAME.search(r[0])]
    keep.sort(key=lambda r: r[3], reverse=True)
    return [{"repo": r, "week": str(w), "stars": s, "stars_per_day": round(v, 1)} for r, w, s, v in keep[:TOP_MOVERS]]


def snapshot(cur, period):
    tot = totals(cur)
    return {
        "schema": SCHEMA_VERSION,
        "period": period,
        "snapshot_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "license": "CC-BY-4.0",
        "totals": tot,
        "types": counted(cur, "select project_type, count(*) from skills group by 1 order by 2 desc"),
        "growth": growth(cur, period),
        "security": security(cur),
        "licenses": licenses(cur, tot["repos"]),
        "platforms": platforms(cur),
        "cjk_description_share_pct": cjk_share(cur),
        "movers": movers(cur, period, excluded_repos()),
    }


def take(period):
    with psycopg2.connect(os.environ["SUPABASE_DB_URL"], connect_timeout=30) as conn, conn.cursor() as cur:
        # SET LOCAL only: the pooler hands this connection to the next client afterwards.
        cur.execute(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'")
        cur.execute("SET LOCAL transaction_read_only = on")
        data = snapshot(cur, period)
        conn.rollback()
    return data


def csv_rows(data):
    out = [("totals", k, "", v) for k, v in data["totals"].items()]
    out += [("types", r["key"], "", r["count"]) for r in data["types"]]
    out += [("growth", k, g["month"], v) for g in data["growth"] for k, v in g.items() if k != "month"]
    out += [("security_grade", k, "", v) for k, v in data["security"]["grades"].items()]
    out += [("risk_pattern", r["key"], "", r["count"]) for r in data["security"]["patterns"]]
    out += [("license", r["key"], "", r["count"]) for r in data["licenses"]]
    out += [("platform", r["key"], "", r["count"]) for r in data["platforms"]]
    out += [("languages", "cjk_description_share_pct", "", data["cjk_description_share_pct"])]
    out += [("mover", m["repo"], m["week"], m["stars_per_day"]) for m in data["movers"]]
    return out


def write(data, out_dir, force):
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{data['period']}.json"
    if target.exists() and not force:
        raise SystemExit(f"{target} exists; a published snapshot is not rewritten (use --force)")
    target.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with open(out_dir / f"{data['period']}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(("section", "key", "month", "value"))
        writer.writerows(csv_rows(data))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--period", default=previous_month(datetime.now(timezone.utc)))
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}", args.period):
        raise SystemExit("--period must look like 2026-10")
    target = write(take(args.period), args.out, args.force)
    print(f"wrote {target} and its .csv")


if __name__ == "__main__":
    main()
