"""The sync's security step: it hands the scan a deadline, and a failed scan does not poison what follows."""
import re
from pathlib import Path

from app.scheduler import jobs
from app.services import grade_refresh


class _Db:
    def __init__(self):
        self.rollbacks = 0

    def rollback(self):
        self.rollbacks += 1


def test_a_failed_scan_is_rolled_back_before_the_weekly_snapshot(monkeypatch):
    # 2026-10-22 23:03 and 10-24 07:04: the scan's statement timeout left the transaction
    # aborted, and the weekly snapshot after it failed with InFailedSqlTransaction.
    def timed_out(db, **_kw):
        raise RuntimeError("canceling statement due to statement timeout")

    monkeypatch.setattr(grade_refresh, "refresh_grades", timed_out)
    db = _Db()
    jobs._grade_security(db, deadline=1.0)
    assert db.rollbacks == 1


def test_the_scan_gets_the_sync_deadline(monkeypatch):
    seen = {}
    monkeypatch.setattr(grade_refresh, "refresh_grades", lambda db, **kw: seen.update(kw) or {})
    jobs._grade_security(_Db(), deadline=42.0)
    assert seen == {"deadline": 42.0}


def test_the_scan_stops_well_inside_the_job_limit():
    sync_yml = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "sync.yml"
    limit_minutes = int(re.search(r"timeout-minutes:\s*(\d+)", sync_yml.read_text()).group(1))
    # After the scan: the weekly snapshot, three cache refreshes (2 min each when the database
    # is slow), the sync log, and the cold-start step in the same job.
    assert jobs.SCAN_STOP_AFTER_SECONDS <= (limit_minutes - 20) * 60
