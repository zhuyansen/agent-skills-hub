"""Writing security grades to the catalog: which rows, and when.

The rules live in security_scanner.py; this module decides which rows to grade
and stores the result. The split is what makes RULES_FINGERPRINT honest: it
hashes security_scanner.py, so any change to how a README is graded — a pattern,
a helper, the trust tiers — changes it and forces a full re-grade, while edits
here do not.

A full pass runs when a README'd row carries a different scanner_version (the
rules changed, or the row was graded before stamps existed) or SCAN_FULL=1.
Otherwise only rows whose inputs moved since they were graded: a README fetched
after the last grade, or stars/license/homepage changed (the sync and the
stale-row probe bump last_synced only when a value actually changes). Before
this, every sync re-read ~31K READMEs (~1.5 GB) and re-graded all of them.

Chunked with a commit per batch and keyset pagination by id: one 106K-row
transaction once hit statement_timeout (57014) and wrote nothing.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

from sqlalchemy import bindparam, func, or_, update
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.services import security_scanner

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
FINGERPRINT_CHARS = 16


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
        return "SCAN_FULL=1"
    stale = (
        db.query(Skill.id)
        .filter(*_has_readme())
        .filter(or_(Skill.scanner_version.is_(None), Skill.scanner_version != RULES_FINGERPRINT))
        .limit(1)
        .first()
    )
    return "rules fingerprint changed or rows never stamped" if stale else None


def _inputs_changed_since_graded():
    # greatest() skips NULLs, so a row never fetched through the marker still
    # re-grades when last_synced moves.
    return or_(
        Skill.security_scanned_at.is_(None),
        Skill.security_scanned_at < func.greatest(Skill.readme_fetched_at, Skill.last_synced),
    )


def _grade_readme_rows(db: Session, full: bool, stats: dict, batch_size: int) -> None:
    scanner = security_scanner.SecurityScanner()
    last_id = 0
    while True:
        q = db.query(Skill).filter(*_has_readme()).filter(Skill.id > last_id)
        if not full:
            q = q.filter(_inputs_changed_since_graded())
        batch = q.order_by(Skill.id.asc()).limit(batch_size).all()
        if not batch:
            return
        rows = []
        for skill in batch:
            grade, flags = scanner.scan_single(skill)
            rows.append({"_id": skill.id, "_grade": grade, "_flags": json.dumps(flags)})
            stats["scanned"] += 1
            stats[grade] = stats.get(grade, 0) + 1
        last_id = batch[-1].id
        db.execute(_WRITE_GRADE, rows)
        db.commit()


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


def refresh_grades(db: Session, batch_size: int = BATCH_SIZE) -> dict:
    stats = {"scanned": 0, "safe": 0, "caution": 0, "unsafe": 0, "reject": 0, "unknown": 0, "no_readme": 0}
    reason = full_scan_reason(db)
    logger.info(
        "scan mode=%s%s fingerprint=%s",
        "full" if reason else "incremental", f" reason={reason}" if reason else "", RULES_FINGERPRINT,
    )
    _grade_readme_rows(db, full=bool(reason), stats=stats, batch_size=batch_size)
    _mark_readmeless_unknown(db, stats, batch_size)
    logger.info(
        "Security scan complete: %d scanned, %d safe, %d caution, %d unsafe, %d reject, %d newly-unknown",
        stats["scanned"], stats["safe"], stats["caution"], stats["unsafe"], stats["reject"], stats["no_readme"],
    )
    return stats
