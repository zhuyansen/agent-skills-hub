"""Writing security grades to the catalog: which rows, and when.

The rules live in security_scanner.py; this module decides which rows to grade
and stores the result. The split is what makes RULES_FINGERPRINT honest: it
hashes security_scanner.py, so any change to how a README is graded — a pattern,
a helper, the trust tiers — changes it and forces a full re-grade, while edits
here do not.

Every sync grades the rows whose inputs moved since they were graded: never
graded, a README fetched after the last grade, or stars/license/homepage changed
(the sync and the stale-row probe bump last_synced only when a value actually
changes). Before this, every sync re-read ~31K READMEs (~1.5 GB) and re-graded
all of them.

When a README'd row carries a different, non-null scanner_version (the rules
changed), the sync then works through the re-grade backlog: rows graded under
other rules, in id order, until the deadline the sync hands in. A row written
carries RULES_FINGERPRINT and leaves the backlog, so the next sync goes on where
this one stopped. The full pass this replaced started over at id 0: from
2026-10-22 it needed longer than a sync had left, was cut six times in a row,
and never graded the newest repos (the highest ids). SCAN_FULL=1 re-grades every
README'd row, to the end. Never-stamped rows are incremental work, not a reason
for a re-grade.

Chunked with a commit per batch and keyset pagination by id: one 106K-row
transaction once hit statement_timeout (57014) and wrote nothing.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path

from sqlalchemy import ColumnElement, bindparam, func, or_, true, update
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.services import security_scanner

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
FINGERPRINT_CHARS = 16
FORCED = "SCAN_FULL=1"
# Ids one query may look through. A filter few rows match still reads every row in its
# range: when a re-grade resumes, the rows an earlier pass already did (ids 0 to ~135K on
# 2026-10-24) would otherwise all sit in its first query. The incremental pass's queries
# already span about this many ids (~7,500 matches over ~250K ids, 500 a query).
ID_WINDOW = 20_000


def fingerprint(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:FINGERPRINT_CHARS]


RULES_FINGERPRINT = fingerprint(Path(security_scanner.__file__))

_TABLE = Skill.__table__
# Grading is not a sync. Writing last_synced explicitly stops the ORM's
# onupdate=now() from firing: a bumped last_synced hides the row from the
# stale-row probe (refresh-stale.yml orders by it) and freezes its stars.
_WRITE_GRADE = (
    update(_TABLE)
    .where(_TABLE.c.id == bindparam("_id"))
    .values(
        security_grade=bindparam("_grade"),
        security_flags=bindparam("_flags"),
        security_scanned_at=func.now(),
        scanner_version=RULES_FINGERPRINT,
        last_synced=_TABLE.c.last_synced,
    )
)


def _has_readme():
    return (Skill.readme_content.isnot(None), Skill.readme_content != "")


def full_scan_reason(db: Session | None) -> str | None:
    if os.environ.get("SCAN_FULL") == "1":
        return FORCED
    # Only a row graded under DIFFERENT rules starts a re-grade. Rows never
    # stamped (every sync inserts some, with READMEs) take the incremental path,
    # which already selects security_scanned_at IS NULL — treating them as a
    # reason for a full pass made every sync full (2026-09-24, three runs).
    stale = (
        db.query(Skill.id)
        .filter(*_has_readme())
        .filter(Skill.scanner_version.isnot(None), Skill.scanner_version != RULES_FINGERPRINT)
        .limit(1)
        .first()
    )
    return "rules fingerprint changed" if stale else None


def _inputs_changed_since_graded():
    # greatest() skips NULLs, so a row never fetched through the marker still
    # re-grades when last_synced moves.
    return or_(
        Skill.security_scanned_at.is_(None),
        Skill.security_scanned_at < func.greatest(Skill.readme_fetched_at, Skill.last_synced),
    )


def _graded_under_other_rules():
    # NULL too: a row graded before stamps existed was graded under rules we no longer have.
    return or_(Skill.scanner_version.is_(None), Skill.scanner_version != RULES_FINGERPRINT)


def _past(deadline: float | None) -> bool:
    return deadline is not None and time.monotonic() >= deadline


def _graded(scanner: security_scanner.SecurityScanner, skill: Skill, stats: dict) -> dict:
    grade, flags = scanner.scan_single(skill)
    stats["scanned"] += 1
    stats[grade] = stats.get(grade, 0) + 1
    return {"_id": skill.id, "_grade": grade, "_flags": json.dumps(flags)}


def _grade_readme_rows(
    db: Session, where: ColumnElement[bool], stats: dict, batch_size: int, deadline: float | None,
) -> int | None:
    """Grade the README'd rows matching `where`, in id order, ID_WINDOW ids per query at most.

    Returns None once every id was looked at, or the last id done when the deadline stopped
    it. A row written leaves both the changed-inputs and the other-rules filter, so a pass
    the deadline stopped loses nothing: the next sync selects what is left.
    """
    scanner = security_scanner.SecurityScanner()
    last_id, top = 0, db.query(func.max(Skill.id)).scalar() or 0
    while last_id < top:
        if _past(deadline):
            return last_id
        window_end = last_id + ID_WINDOW
        batch = (
            db.query(Skill).filter(*_has_readme()).filter(where)
            .filter(Skill.id > last_id, Skill.id <= window_end)
            .order_by(Skill.id.asc()).limit(batch_size).all()
        )
        rows = [_graded(scanner, skill, stats) for skill in batch]
        last_id = rows[-1]["_id"] if len(rows) == batch_size else window_end  # a short batch ends the window
        if rows:
            db.execute(_WRITE_GRADE, rows)
            db.commit()
    return None


def _grade_changed(db: Session, stats: dict, batch_size: int, deadline: float | None) -> None:
    stopped_after = _grade_readme_rows(db, _inputs_changed_since_graded(), stats, batch_size, deadline)
    if stopped_after is not None:
        # New and changed repos wait a sync: the phases before the scan used up its time.
        logger.warning(
            "Changed rows: stopped at the deadline after id %d; the next sync grades the rest", stopped_after,
        )


def _regrade_backlog(db: Session, stats: dict, batch_size: int, deadline: float | None) -> None:
    before = stats["scanned"]
    stopped_after = _grade_readme_rows(db, _graded_under_other_rules(), stats, batch_size, deadline)
    graded = stats["scanned"] - before
    if stopped_after is None:
        logger.info("Re-grade backlog: %d rows this run, none left", graded)
    else:
        logger.info(
            "Re-grade backlog: %d rows this run, stopped at the deadline after id %d; the next sync goes on from there",
            graded, stopped_after,
        )


def _mark_readmeless_unknown(db: Session, stats: dict, batch_size: int) -> None:
    # Only rows not already 'unknown', so this stays a near no-op at steady state.
    last_id = 0
    while True:
        ids = [
            r.id for r in (
                db.query(Skill.id)
                .filter((Skill.readme_content.is_(None)) | (Skill.readme_content == ""))
                .filter(Skill.security_grade.isnot(None))
                .filter(Skill.security_grade != "unknown")
                .filter(Skill.id > last_id)
                .order_by(Skill.id.asc())
                .limit(batch_size)
                .all()
            )
        ]
        if not ids:
            return
        db.query(Skill).filter(Skill.id.in_(ids)).update(
            {"security_grade": "unknown", "security_flags": "[]", "last_synced": Skill.last_synced},
            synchronize_session=False,
        )
        stats["no_readme"] += len(ids)
        last_id = ids[-1]
        db.commit()


def refresh_grades(db: Session, batch_size: int = BATCH_SIZE, deadline: float | None = None) -> dict:
    """Grade what changed, then the re-grade backlog until `deadline` (a time.monotonic() value)."""
    stats = {"scanned": 0, "safe": 0, "caution": 0, "unsafe": 0, "reject": 0, "unknown": 0, "no_readme": 0}
    reason = full_scan_reason(db)
    logger.info(
        "scan mode=%s%s fingerprint=%s",
        "full" if reason else "incremental", f" reason={reason}" if reason else "", RULES_FINGERPRINT,
    )
    if reason == FORCED:
        _grade_readme_rows(db, true(), stats, batch_size, deadline=None)  # asked for all of it
    else:
        _grade_changed(db, stats, batch_size, deadline)
        if reason:
            _regrade_backlog(db, stats, batch_size, deadline)
    _mark_readmeless_unknown(db, stats, batch_size)
    logger.info(
        "Security scan complete: %d scanned, %d safe, %d caution, %d unsafe, %d reject, %d newly-unknown",
        stats["scanned"], stats["safe"], stats["caution"], stats["unsafe"], stats["reject"], stats["no_readme"],
    )
    return stats
