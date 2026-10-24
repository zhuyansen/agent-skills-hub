"""A re-grade after a rules change resumes where the last sync stopped (on a real, in-memory catalog).

From 2026-10-22 (7333f54 changed the scanner, so the fingerprint) every sync re-graded every
README'd row from id 0. That takes longer than a sync has left after its other phases, so the
job limit or a statement timeout cut it each time and the next sync started over: six runs
without progress, and the newest repos (the highest ids) were never graded.
"""
import itertools
import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from app.models.skill import Skill
from app.services import grade_refresh
from app.services.security_scanner import SecurityScanner

sqlite3.register_adapter(list, json.dumps)  # Skill.tags is a Postgres ARRAY

OLD_RULES = "0" * grade_refresh.FINGERPRINT_CHARS
LAST_WEEK = datetime.now(timezone.utc) - timedelta(days=7)
BATCH = 500
REAL_SCAN = SecurityScanner.scan_single


@compiles(ARRAY, "sqlite")
def _array_as_text(_type, _compiler, **_kw):
    return "TEXT"


def _greatest(conn, _record):
    # Postgres greatest() skips NULLs, which the incremental filter relies on.
    conn.create_function("greatest", -1, lambda *a: max((x for x in a if x is not None), default=None))


@pytest.fixture
def catalog(monkeypatch):
    monkeypatch.delenv("SCAN_FULL", raising=False)
    engine = create_engine("sqlite://")
    event.listen(engine, "connect", _greatest)
    Skill.__table__.create(engine)
    db = sessionmaker(bind=engine)()
    yield db
    db.close()
    engine.dispose()


def _add(db, ids, graded=True):
    """README'd rows. Graded ones were graded last week, under OLD_RULES."""
    grade = {"security_grade": "safe", "security_flags": "[]", "scanner_version": OLD_RULES,
             "security_scanned_at": LAST_WEEK} if graded else {}
    for i in ids:
        db.add(Skill(id=i, repo_full_name=f"o/r{i}", repo_name=f"r{i}", repo_url=f"https://github.com/o/r{i}",
                     author_name="o", readme_content="# r\nA plain readme.",
                     readme_fetched_at=LAST_WEEK - timedelta(days=1), last_synced=LAST_WEEK - timedelta(days=1),
                     **grade))
    db.commit()


def _interrupted(db, monkeypatch, rows):
    """A sync the job limit or a 57014 ends after `rows` rows were scanned."""
    calls = itertools.count(1)

    def scan(self, skill):
        if next(calls) > rows:
            raise RuntimeError("canceling statement due to statement timeout")
        return REAL_SCAN(self, skill)

    monkeypatch.setattr(SecurityScanner, "scan_single", scan)
    with pytest.raises(RuntimeError):
        grade_refresh.refresh_grades(db, batch_size=BATCH)
    db.rollback()
    monkeypatch.setattr(SecurityScanner, "scan_single", REAL_SCAN)


def _on_current_rules(db):
    return db.query(Skill).filter(Skill.scanner_version == grade_refresh.RULES_FINGERPRINT)


def test_an_interrupted_regrade_resumes_where_it_stopped(catalog, monkeypatch):
    _add(catalog, range(1, 2001))
    _interrupted(catalog, monkeypatch, rows=1500)  # three batches committed, the fourth cut
    assert _on_current_rules(catalog).count() == 1500
    assert grade_refresh.refresh_grades(catalog, batch_size=BATCH)["scanned"] == 500  # was 2,000: from id 0
    assert grade_refresh.full_scan_reason(catalog) is None


def test_new_repos_get_graded_ahead_of_the_backlog(catalog, monkeypatch):
    _add(catalog, range(1, 2001))
    _add(catalog, range(5001, 5101), graded=False)  # this sync's new repos: the highest ids
    _interrupted(catalog, monkeypatch, rows=500)
    assert _on_current_rules(catalog).filter(Skill.id > 5000).count() == 100  # was 0


def test_the_backlog_stops_at_the_deadline_and_the_next_sync_goes_on(catalog, monkeypatch):
    _add(catalog, range(1, 2001))
    checks = itertools.count()
    # Check 0 finds no new rows; checks 1-3 grade a batch each; check 4 is past the deadline.
    monkeypatch.setattr(grade_refresh, "_past", lambda deadline: next(checks) >= 4)
    assert grade_refresh.refresh_grades(catalog, batch_size=BATCH, deadline=1.0)["scanned"] == 1500
    assert grade_refresh.full_scan_reason(catalog) == "rules fingerprint changed"
    monkeypatch.setattr(grade_refresh, "_past", lambda deadline: False)
    assert grade_refresh.refresh_grades(catalog, batch_size=BATCH, deadline=1.0)["scanned"] == 500
    assert grade_refresh.full_scan_reason(catalog) is None


def test_sparse_ids_get_walked_one_window_at_a_time(catalog, monkeypatch):
    # Production resumes with ~135K ids already done; no query may have to read past all of them.
    monkeypatch.setattr(grade_refresh, "ID_WINDOW", 7)
    _add(catalog, [1, 2, 3, 30, 31, 95])  # gaps wider than a window
    assert grade_refresh.refresh_grades(catalog, batch_size=2)["scanned"] == 6
    assert grade_refresh.full_scan_reason(catalog) is None


def test_changed_rows_cut_by_the_deadline_get_logged_then_graded(catalog, monkeypatch, caplog):
    _add(catalog, range(1, 101), graded=False)
    monkeypatch.setattr(grade_refresh, "_past", lambda deadline: deadline is not None)
    with caplog.at_level("WARNING", logger=grade_refresh.logger.name):
        assert grade_refresh.refresh_grades(catalog, batch_size=BATCH, deadline=1.0)["scanned"] == 0
    assert "Changed rows: stopped at the deadline" in caplog.text
    assert grade_refresh.refresh_grades(catalog, batch_size=BATCH)["scanned"] == 100


def test_with_the_rules_unchanged_only_rows_whose_inputs_moved_are_graded(catalog):
    _add(catalog, range(1, 1001))
    grade_refresh.refresh_grades(catalog, batch_size=BATCH)  # clears the backlog
    assert grade_refresh.refresh_grades(catalog, batch_size=BATCH)["scanned"] == 0
    catalog.get(Skill, 7).readme_fetched_at = datetime.now(timezone.utc) + timedelta(hours=1)
    catalog.commit()
    assert grade_refresh.refresh_grades(catalog, batch_size=BATCH)["scanned"] == 1


def test_scan_full_regrades_every_row_and_runs_to_the_end(catalog, monkeypatch):
    _add(catalog, range(1, 1001))
    grade_refresh.refresh_grades(catalog, batch_size=BATCH)  # every row on the current rules
    monkeypatch.setenv("SCAN_FULL", "1")
    monkeypatch.setattr(grade_refresh, "_past", lambda deadline: deadline is not None)
    assert grade_refresh.refresh_grades(catalog, batch_size=BATCH, deadline=1.0)["scanned"] == 1000


def test_past_is_the_monotonic_clock_and_none_never_passes():
    now = time.monotonic()
    assert not grade_refresh._past(None)
    assert grade_refresh._past(now - 1) and not grade_refresh._past(now + 60)
