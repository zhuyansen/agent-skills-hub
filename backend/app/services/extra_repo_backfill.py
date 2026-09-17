"""Paced backfill of repos that sync's search queries never matched.

Sync only fetches repos pushed since its last run, so a dormant repo no query
matched can never enter the catalog on its own. extra_repos rows are fetched by
name every sync regardless of push date, which makes that table the channel.

Backfill rows carry BACKFILL_TAG in submitted_by, and the pipeline uses it to
tell them apart from curated extras:
  - backfill_extra_repos.py keeps at most IN_FLIGHT_LIMIT of them active and
    retires each once it is ingested (curated rows stay active and refresh on
    every sync);
  - the upsert sets prev_stars = stars on their first insert, so years of
    stars don't count as a single day's gain in scoring or the daily report;
  - the newsletter and the daily report don't list them as new. That follows
    the call newsletter_runner already made for the 2026-03-23 bulk import.

Candidates (data/backfill_agent_skills_2026-09.json): the 1,000 results GitHub
returned for '"agent skills" in:description stars:>50' on 2026-09-17, minus
forks and repos already indexed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

BACKFILL_TAG = "backfill-agent-skills-2026-09"
CANDIDATES_FILE = Path(__file__).resolve().parents[2] / "data" / "backfill_agent_skills_2026-09.json"
# About one sync's worth. Every active row costs one GET /repos/{name} per sync.
IN_FLIGHT_LIMIT = 100
# A row still missing from skills after this many completed syncs was dropped by
# the pipeline (renamed, deleted or filtered out), so stop fetching it.
GIVE_UP_AFTER_SYNCS = 2


@dataclass(frozen=True)
class ExistingRow:
    """An extra_repos row whose name matches a candidate."""

    full_name: str
    is_active: bool
    tagged: bool
    completed_syncs_since_activation: int = 0


@dataclass
class BackfillPlan:
    retire_ingested: list[str] = field(default_factory=list)
    retire_stuck: list[str] = field(default_factory=list)
    activate: list[str] = field(default_factory=list)
    in_flight: int = 0
    ingested_total: int = 0
    queued: int = 0


def load_candidates(path: Path = CANDIDATES_FILE) -> list[str]:
    """Candidate full names, highest stars first."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [r["full_name"] for r in sorted(rows, key=lambda r: -r["stars"])]


def plan_backfill(
    candidates: list[str],
    in_catalog: set[str],
    existing: dict[str, ExistingRow],
    limit: int = IN_FLIGHT_LIMIT,
    give_up_after: int = GIVE_UP_AFTER_SYNCS,
) -> BackfillPlan:
    """Decide which backfill rows to retire and which candidates to activate.

    in_catalog holds lowercased names already in skills. existing maps a
    lowercased name to its extra_repos row, tagged or not. Untagged rows belong
    to curated or community submissions and are never touched.
    """
    plan = BackfillPlan(ingested_total=sum(1 for c in candidates if c.lower() in in_catalog))
    _retire(plan, existing, in_catalog, give_up_after)
    _activate(plan, candidates, in_catalog, existing, limit)
    return plan


def _retire(plan: BackfillPlan, existing: dict[str, ExistingRow], in_catalog: set[str], give_up_after: int) -> None:
    for key, row in existing.items():
        if not (row.tagged and row.is_active):
            continue
        if key in in_catalog:
            plan.retire_ingested.append(row.full_name)
        elif row.completed_syncs_since_activation >= give_up_after:
            plan.retire_stuck.append(row.full_name)
        else:
            plan.in_flight += 1


def _activate(
    plan: BackfillPlan, candidates: list[str], in_catalog: set[str], existing: dict[str, ExistingRow], limit: int
) -> None:
    slots = max(0, limit - plan.in_flight)
    for name in candidates:
        key = name.lower()
        if key in in_catalog or key in existing:
            continue
        if len(plan.activate) < slots:
            plan.activate.append(name)
        else:
            plan.queued += 1
