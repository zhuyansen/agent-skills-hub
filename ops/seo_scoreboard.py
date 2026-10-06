"""Fill the weekly table of ops/seo-scoreboard.md from Search Console.

One row per finished week (Monday to Sunday): clicks, impressions, the position
of the exact brand query, and the position of `ppt skills` in the notes. The
other columns (Bing, GEO, conversions, Clarity) stay for a person to fill.
Weeks already in the table are left alone, so the history is never rewritten;
an empty placeholder row for a week is filled in.

  python ops/seo_scoreboard.py              # every missing week since 2026-07-13
  python ops/seo_scoreboard.py --dry-run    # print the rows, write nothing

Search Console data is final about three days after a day ends, so the
workflow runs on Thursdays (.github/workflows/seo-scoreboard.yml).
"""
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "gsc"))
import fetch_gsc as gsc  # noqa: E402

BOARD = Path(__file__).parent / "seo-scoreboard.md"
FIRST_WEEK = dt.date(2026, 7, 13)   # the first weekly check the table planned for
BRAND = "agent skills hub"
WATCHED = "ppt skills"
FINAL_AFTER_DAYS = 3
ROW_DATE = re.compile(r"^\| (\d{4}-\d{2}-\d{2})(?: |\(|\|)")


def finished_weeks(today: dt.date) -> list[dt.date]:
    """Mondays of every week whose Sunday has final data."""
    last_final = today - dt.timedelta(days=FINAL_AFTER_DAYS)
    weeks, monday = [], FIRST_WEEK
    while monday + dt.timedelta(days=6) <= last_final:
        weeks.append(monday)
        monday += dt.timedelta(days=7)
    return weeks


def position(svc, site, start, end, term: str) -> str:
    flt = [{"dimension": "query", "operator": "equals", "expression": term}]
    rows = gsc.query(svc, site, start, end, ["query"], filters=flt, limit=1)
    return f"{rows[0]['position']:.1f}" if rows else "—"


def week_row(svc, site, monday: dt.date) -> str:
    sunday = monday + dt.timedelta(days=6)
    days = gsc.query(svc, site, monday, sunday, ["date"], limit=10)
    clicks = sum(r["clicks"] for r in days)
    impressions = sum(r["impressions"] for r in days)
    brand = position(svc, site, monday, sunday, BRAND)
    watched = position(svc, site, monday, sunday, WATCHED)
    note = f"自动:`{WATCHED}` pos {watched}"
    return f"| {monday} | {clicks:,} | {impressions:,} | {brand} | | | | | {note} |"


def weekly_rows(lines: list[str]) -> tuple[int, int]:
    """First and last line index of the weekly table's body."""
    head = next(i for i, l in enumerate(lines) if l.startswith("## 周表"))
    first = next(i for i in range(head, len(lines)) if lines[i].startswith("|---")) + 1
    last = first
    while last + 1 < len(lines) and lines[last + 1].startswith("|"):
        last += 1
    return first, last


def merge(lines: list[str], new_rows: dict[str, str]) -> list[str]:
    """Add rows for weeks the table lacks; fill rows that are only a date."""
    first, last = weekly_rows(lines)
    body = lines[first:last + 1]
    present = {}
    for i, row in enumerate(body):
        m = ROW_DATE.match(row)
        if m:
            present[m[1]] = i
    for date, row in sorted(new_rows.items()):
        i = present.get(date)
        if i is None:
            body.append(row)
        elif not body[i].split("|")[2].strip():
            body[i] = row
    return lines[:first] + body + lines[last + 1:]


def main() -> None:
    svc = gsc.get_service()
    site = gsc.pick_site(svc)
    text = BOARD.read_text()
    have = {m[1] for line in text.splitlines()
            if (m := ROW_DATE.match(line)) and line.split("|")[2].strip()}
    todo = [m for m in finished_weeks(dt.date.today()) if str(m) not in have]
    rows = {str(m): week_row(svc, site, m) for m in todo}
    for row in rows.values():
        print(row)
    if rows and "--dry-run" not in sys.argv:
        BOARD.write_text("\n".join(merge(text.splitlines(), rows)) + "\n")
    print(f"{len(rows)} week(s) added", file=sys.stderr)


if __name__ == "__main__":
    main()
