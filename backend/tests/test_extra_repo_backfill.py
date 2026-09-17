"""Planner for the paced extra_repos backfill (app/services/extra_repo_backfill.py)."""
import json

from app.services.extra_repo_backfill import (
    CANDIDATES_FILE,
    ExistingRow,
    load_candidates,
    plan_backfill,
)

CANDIDATES = [f"owner/repo-{i}" for i in range(10)]  # already highest-stars first


def row(name, active=True, tagged=True, syncs=0):
    return {name.lower(): ExistingRow(name, active, tagged, syncs)}


def test_first_run_activates_up_to_limit_in_priority_order():
    plan = plan_backfill(CANDIDATES, in_catalog=set(), existing={}, limit=3)
    assert plan.activate == ["owner/repo-0", "owner/repo-1", "owner/repo-2"]
    assert plan.queued == 7
    assert not plan.retire_ingested and not plan.retire_stuck


def test_candidates_already_indexed_are_never_activated():
    plan = plan_backfill(CANDIDATES, in_catalog={"owner/repo-0"}, existing={}, limit=2)
    assert plan.activate == ["owner/repo-1", "owner/repo-2"]
    assert plan.ingested_total == 1


def test_in_flight_rows_use_up_slots():
    existing = {**row("owner/repo-0"), **row("owner/repo-1")}
    plan = plan_backfill(CANDIDATES, in_catalog=set(), existing=existing, limit=3)
    assert plan.in_flight == 2
    assert plan.activate == ["owner/repo-2"]


def test_ingested_rows_retire_and_free_their_slots():
    existing = {**row("owner/repo-0"), **row("owner/repo-1")}
    plan = plan_backfill(CANDIDATES, in_catalog={"owner/repo-0", "owner/repo-1"}, existing=existing, limit=2)
    assert sorted(plan.retire_ingested) == ["owner/repo-0", "owner/repo-1"]
    assert plan.activate == ["owner/repo-2", "owner/repo-3"]


def test_rows_that_never_ingest_are_given_up_after_enough_syncs():
    existing = {**row("owner/repo-0", syncs=1), **row("owner/repo-1", syncs=2)}
    plan = plan_backfill(CANDIDATES, in_catalog=set(), existing=existing, limit=2, give_up_after=2)
    assert plan.retire_stuck == ["owner/repo-1"]
    assert plan.in_flight == 1
    assert plan.activate == ["owner/repo-2"]


def test_untagged_rows_belong_to_someone_else_and_are_left_alone():
    existing = {**row("owner/repo-0", tagged=False), **row("owner/repo-1", active=False, tagged=False)}
    plan = plan_backfill(CANDIDATES, in_catalog={"owner/repo-0"}, existing=existing, limit=5)
    assert not plan.retire_ingested and not plan.retire_stuck
    assert "owner/repo-0" not in plan.activate and "owner/repo-1" not in plan.activate


def test_retired_rows_are_not_reactivated():
    existing = row("owner/repo-0", active=False)
    plan = plan_backfill(CANDIDATES, in_catalog=set(), existing=existing, limit=1)
    assert plan.activate == ["owner/repo-1"]


def test_matching_is_case_insensitive():
    plan = plan_backfill(["Owner/Repo-A"], in_catalog={"owner/repo-a"}, existing={}, limit=5)
    assert plan.activate == []


def test_rerun_without_a_sync_changes_nothing():
    first = plan_backfill(CANDIDATES, in_catalog=set(), existing={}, limit=3)
    existing = {}
    for name in first.activate:
        existing.update(row(name))
    second = plan_backfill(CANDIDATES, in_catalog=set(), existing=existing, limit=3)
    assert second.activate == [] and second.in_flight == 3


def test_committed_candidate_file_is_well_formed():
    rows = json.loads(CANDIDATES_FILE.read_text(encoding="utf-8"))
    names = [r["full_name"] for r in rows]
    assert len(names) == len({n.lower() for n in names}), "duplicate candidates"
    assert all(n.count("/") == 1 and all(n.split("/")) for n in names)
    assert all(isinstance(r["stars"], int) and r["stars"] > 50 for r in rows)
    ordered = load_candidates()
    stars = {r["full_name"]: r["stars"] for r in rows}
    assert [stars[n] for n in ordered] == sorted(stars.values(), reverse=True)
