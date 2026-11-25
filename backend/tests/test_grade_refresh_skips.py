"""A README the scanner raises on is skipped; the rest of the pass is still graded.

From 2026-11-19 urlparse raised ValueError on one README (crbnos/carbon, id 70894). The pass
went in id order and stopped there, so every repo added after it stayed ungraded for two days,
and only a WARNING in the sync log said so.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

import pytest

from app.models.skill import Skill
from app.services import grade_refresh
from app.services.security_scanner import SecurityScanner

from tests.test_regrade_backlog import _array_as_text, _greatest  # noqa: F401 - registers the SQLite shims

REAL_SCAN = SecurityScanner.scan_single
BROKEN = 7


@pytest.fixture
def catalog(monkeypatch):
    monkeypatch.delenv("SCAN_FULL", raising=False)
    engine = create_engine("sqlite://")
    event.listen(engine, "connect", _greatest)
    Skill.__table__.create(engine)
    db = sessionmaker(bind=engine)()
    for i in range(1, 13):  # never graded, so all of them are this sync's work
        db.add(Skill(id=i, repo_full_name=f"o/r{i}", repo_name=f"r{i}", repo_url=f"https://github.com/o/r{i}",
                     author_name="o", readme_content="# r\nA plain readme."))
    db.commit()
    yield db
    db.close()
    engine.dispose()


def _raises_on(row_id, exc):
    def scan(self, skill):
        if skill.id == row_id:
            raise exc
        return REAL_SCAN(self, skill)
    return scan


def _graded_ids(db):
    return {s.id for s in db.query(Skill).filter(Skill.scanner_version == grade_refresh.RULES_FINGERPRINT)}


def test_the_rows_after_a_readme_the_scanner_raises_on_are_graded(catalog, monkeypatch):
    monkeypatch.setattr(SecurityScanner, "scan_single", _raises_on(BROKEN, ValueError("Invalid IPv6 URL")))
    stats = grade_refresh.refresh_grades(catalog, batch_size=5)  # the broken row sits in a full batch
    assert _graded_ids(catalog) == set(range(1, 13)) - {BROKEN}
    assert stats["scanned"] == 11
    assert stats["failed"] == 1
    assert stats["failed_rows"] == [f"{BROKEN} o/r{BROKEN}: ValueError: Invalid IPv6 URL"]


def test_the_skipped_row_is_tried_again_by_the_next_sync(catalog, monkeypatch):
    monkeypatch.setattr(SecurityScanner, "scan_single", _raises_on(BROKEN, ValueError("Invalid IPv6 URL")))
    grade_refresh.refresh_grades(catalog, batch_size=5)
    monkeypatch.setattr(SecurityScanner, "scan_single", REAL_SCAN)  # the scanner got fixed
    assert grade_refresh.refresh_grades(catalog, batch_size=5)["scanned"] == 1
    assert _graded_ids(catalog) == set(range(1, 13))


def test_a_database_error_still_ends_the_pass(catalog, monkeypatch):
    timeout = OperationalError("SELECT …", {}, Exception("canceling statement due to statement timeout"))
    monkeypatch.setattr(SecurityScanner, "scan_single", _raises_on(BROKEN, timeout))
    with pytest.raises(OperationalError):
        grade_refresh.refresh_grades(catalog, batch_size=5)


def test_only_the_first_rows_are_named(catalog, monkeypatch):
    monkeypatch.setattr(grade_refresh, "FAILED_NAMED", 2)
    monkeypatch.setattr(SecurityScanner, "scan_single", lambda self, skill: (_ for _ in ()).throw(KeyError("x")))
    stats = grade_refresh.refresh_grades(catalog, batch_size=5)
    assert (stats["failed"], len(stats["failed_rows"]), stats["scanned"]) == (12, 2, 0)


def test_a_row_both_passes_meet_is_counted_once(catalog, monkeypatch):
    # After a rules change the backlog pass meets the row the changed-rows pass skipped.
    old = "0" * grade_refresh.FINGERPRINT_CHARS
    catalog.query(Skill).update({"scanner_version": old})
    catalog.commit()
    monkeypatch.setattr(SecurityScanner, "scan_single", _raises_on(BROKEN, ValueError("Invalid IPv6 URL")))
    stats = grade_refresh.refresh_grades(catalog, batch_size=5)
    assert (stats["failed"], len(stats["failed_rows"])) == (1, 1)
    assert "failed_ids" not in stats  # the log line and the alert get counts and names, not a set
