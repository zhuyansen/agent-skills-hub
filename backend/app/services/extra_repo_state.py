"""The life of an `extra_repos` row, as one state instead of two columns.

`status` (pending / approved / rejected) and `is_active` are written together in
several places, and the sync only reads `is_active`. Written apart they drift:
until 2026-11-10 the admin "add" endpoint saved a row with the column defaults,
pending but active, so the sync fetched a repo the review page still listed as
waiting. The four states a row can be in:

    pending   submitted, waiting for review          (pending,  inactive)
    active    approved, fetched on every sync        (approved, active)
    paused    approved, held back by the backfill    (approved, inactive)
    rejected  turned down                            (rejected, inactive)

An admin may reverse a decision (approve a rejected row, reject an approved
one); only a pending row may be decided by a maintainer command
(catalog_admission.py, in SQL). Pausing and resuming belong to the paced
backfill (backfill_extra_repos.py, in SQL): only an approved row moves.
"""
from datetime import datetime, timezone
from enum import Enum


class State(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    REJECTED = "rejected"


class Event(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    PAUSE = "pause"
    RESUME = "resume"


class InvalidTransition(ValueError):
    """The event does not apply to a row in this state."""


# state -> (status, is_active)
COLUMNS = {
    State.PENDING: ("pending", False),
    State.ACTIVE: ("approved", True),
    State.PAUSED: ("approved", False),
    State.REJECTED: ("rejected", False),
}

TRANSITIONS = {
    (State.PENDING, Event.APPROVE): State.ACTIVE,
    (State.PENDING, Event.REJECT): State.REJECTED,
    (State.ACTIVE, Event.REJECT): State.REJECTED,
    (State.ACTIVE, Event.PAUSE): State.PAUSED,
    (State.PAUSED, Event.RESUME): State.ACTIVE,
    (State.PAUSED, Event.APPROVE): State.ACTIVE,
    (State.PAUSED, Event.REJECT): State.REJECTED,
    (State.REJECTED, Event.APPROVE): State.ACTIVE,
}

REVIEW_EVENTS = frozenset({Event.APPROVE, Event.REJECT})


def state_of(status: str | None, is_active: bool | None) -> State:
    """The state two stored columns stand for. A pending row is pending whatever
    `is_active` says: the rows the old "add" endpoint left are waiting for review."""
    if status == "rejected":
        return State.REJECTED
    if status == "approved":
        return State.ACTIVE if is_active else State.PAUSED
    return State.PENDING


def next_state(state: State, event: Event) -> State:
    """Where the event takes a row. Deciding the same way twice changes nothing."""
    target = TRANSITIONS.get((state, event))
    if target is not None:
        return target
    if event in REVIEW_EVENTS and state == TRANSITIONS.get((State.PENDING, event)):
        return state
    raise InvalidTransition(f"cannot {event.value} a row that is {state.value}")


def columns(state: State) -> dict:
    """The stored columns of a state, for a new row or an update."""
    status, is_active = COLUMNS[state]
    return {"status": status, "is_active": is_active}


def apply(row, event: Event, now: datetime | None = None) -> State:
    """Move an ExtraRepo row and write both columns; a review also stamps `reviewed_at`."""
    target = next_state(state_of(row.status, row.is_active), event)
    row.status, row.is_active = COLUMNS[target]
    if event in REVIEW_EVENTS:
        row.reviewed_at = now or datetime.now(timezone.utc)
    return target
