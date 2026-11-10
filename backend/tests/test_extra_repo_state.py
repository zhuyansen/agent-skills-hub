"""Tests for the extra_repos row states (app/services/extra_repo_state.py)."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services.extra_repo_state import (
    COLUMNS, Event, InvalidTransition, State, apply, columns, next_state, state_of,
)


def row(status, is_active):
    return SimpleNamespace(status=status, is_active=is_active, reviewed_at=None)


def test_every_state_round_trips_through_its_columns():
    for state, (status, is_active) in COLUMNS.items():
        assert state_of(status, is_active) == state


def test_a_pending_row_left_active_by_the_old_add_endpoint_is_pending():
    assert state_of("pending", True) == State.PENDING
    assert state_of(None, None) == State.PENDING


def test_only_the_active_state_is_fetched_by_the_sync():
    assert [s for s in State if columns(s)["is_active"]] == [State.ACTIVE]


def test_approve_writes_both_columns_and_the_review_time():
    r = row("pending", False)
    now = datetime(2026, 11, 10, tzinfo=timezone.utc)
    assert apply(r, Event.APPROVE, now) == State.ACTIVE
    assert (r.status, r.is_active, r.reviewed_at) == ("approved", True, now)


def test_reject_turns_an_active_row_off():
    r = row("approved", True)
    apply(r, Event.REJECT)
    assert (r.status, r.is_active) == ("rejected", False)
    assert r.reviewed_at is not None


def test_an_admin_can_reverse_a_rejection():
    assert next_state(State.REJECTED, Event.APPROVE) == State.ACTIVE


def test_deciding_the_same_way_twice_changes_nothing():
    assert next_state(State.ACTIVE, Event.APPROVE) == State.ACTIVE
    assert next_state(State.REJECTED, Event.REJECT) == State.REJECTED


def test_pause_and_resume_only_move_an_approved_row():
    r = row("approved", True)
    apply(r, Event.PAUSE)
    assert (r.status, r.is_active, r.reviewed_at) == ("approved", False, None)
    assert apply(r, Event.RESUME) == State.ACTIVE
    for state in (State.PENDING, State.REJECTED):
        with pytest.raises(InvalidTransition):
            next_state(state, Event.PAUSE)
        with pytest.raises(InvalidTransition):
            next_state(state, Event.RESUME)


def test_a_paused_row_cannot_be_paused_again():
    with pytest.raises(InvalidTransition):
        next_state(State.PAUSED, Event.PAUSE)
