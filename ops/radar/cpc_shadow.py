"""Shadow record of what Google Ads already says about each keyword the radar sizes (migration 032):
cost per click, top-of-page bids and competition, which usecases.volumes() reads off the same answer as
the search volume, at no extra cost. Nothing shows it. 2026-10-28: the user chose this over a new signal;
a review 2-4 weeks on checks whether CPC tells which terms turn into sites that earn, and only then may
it replace the "ads on the results page" flag (competition.py), which says the same thing without a size.
"""
from __future__ import annotations

from datetime import date

UPSERT = """
INSERT INTO radar_keyword_cpc (day, phrase, location, kind, names, volume, cpc, bid_low, bid_high,
                               competition, competition_index)
VALUES (:day, :phrase, :location, :kind, :names, :volume, :cpc, :bid_low, :bid_high, :competition,
        :competition_index)
ON CONFLICT (day, phrase, location) DO UPDATE SET
    kind = EXCLUDED.kind, names = EXCLUDED.names, volume = EXCLUDED.volume, cpc = EXCLUDED.cpc,
    bid_low = EXCLUDED.bid_low, bid_high = EXCLUDED.bid_high, competition = EXCLUDED.competition,
    competition_index = EXCLUDED.competition_index
"""


def rows_of(block: dict, today: date) -> list[dict]:
    """The keyword table's rows that Google Ads answered for, as table rows: usecases.run()'s block."""
    location = block.get("location_code")
    return [{"day": today, "phrase": r["phrase"], "location": location, "kind": r.get("kind", "generic"),
             "names": list(r.get("names") or []), "volume": r.get("volume"), **r["gads"]}
            for r in block.get("rows") or [] if r.get("gads") and location is not None]


def record(block: dict, today: date | None = None) -> int:
    """Writes the day's rows; returns how many. Called with the radar's --skip-db honoured (radar.run)."""
    rows = rows_of(block, today or date.today())
    if not rows:
        return 0
    import review
    from sqlalchemy import text
    engine = review._engine()
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL statement_timeout = '60s'"))
        for row in rows:
            conn.execute(text(UPSERT), row)
    engine.dispose()
    return len(rows)
