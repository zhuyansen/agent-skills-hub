"""Read skills in batches, one query per batch.

The analyzers used to load every row in one query and commit every 500. A commit
expires the objects the session holds, so from row 501 on each row was read again
on first touch, one SELECT per row with its README, in each of three analyzers:
about 27,000 single-row reads for a 9,000-repo sync. Scoring took 10 minutes while
most rows had no README and an hour once they did, and the sync hit its two-hour
limit (2026-09-27 19:26 and 2026-09-28 03:03).

Here a batch is loaded, handled, committed, and not touched again.

A batch whose commit fails is rolled back and skipped (commit_batch), the way the
upsert treats its batches. One failed commit used to end the whole sync: on
2026-10-18 12:39 a statement timeout left on a pooled connection by another client
cancelled the first quality batch, and the run, its deploy and the cold-start
priors all stopped there.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.skill import Skill

logger = logging.getLogger(__name__)


def skill_batches(db: Session, repo_names: list[str] | None, batch_size: int) -> Iterator[list[Skill]]:
    """The named skills, or all of them when repo_names is empty. Commit after each batch."""
    if repo_names:
        yield from _named(db, list(repo_names), batch_size)
    else:
        yield from _all(db, batch_size)


def _named(db: Session, names: list[str], batch_size: int) -> Iterator[list[Skill]]:
    for start in range(0, len(names), batch_size):
        batch = db.query(Skill).filter(Skill.repo_full_name.in_(names[start:start + batch_size])).all()
        if batch:
            yield batch


def _all(db: Session, batch_size: int) -> Iterator[list[Skill]]:
    last_id = 0
    while True:
        batch = db.query(Skill).filter(Skill.id > last_id).order_by(Skill.id.asc()).limit(batch_size).all()
        if not batch:
            return
        last_id = batch[-1].id  # read before the caller's commit expires the row
        yield batch


def commit_batch(db: Session, what: str, done: int) -> bool:
    """Commit one batch. On a database error, log it, roll back and return False so the next batch still runs."""
    try:
        db.commit()
        return True
    except SQLAlchemyError as exc:
        logger.error("%s: batch commit failed at %d: %s", what, done, exc)
        db.rollback()
        return False
