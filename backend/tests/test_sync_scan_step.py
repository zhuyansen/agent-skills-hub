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


def test_a_failed_scan_leaves_an_alert_for_the_workflow(monkeypatch, tmp_path):
    # 2026-11-19 to 11-21: every scan died on one README and only a WARNING said so.
    alert = tmp_path / "scan-alert.txt"
    monkeypatch.setenv("SCAN_ALERT_FILE", str(alert))

    def broken(db, **_kw):
        raise ValueError("Invalid IPv6 URL")

    monkeypatch.setattr(grade_refresh, "refresh_grades", broken)
    jobs._grade_security(_Db(), deadline=1.0)
    assert "stopped with an error" in alert.read_text()
    assert "Invalid IPv6 URL" in alert.read_text()


def test_skipped_readmes_leave_an_alert_naming_them(monkeypatch, tmp_path):
    alert = tmp_path / "scan-alert.txt"
    monkeypatch.setenv("SCAN_ALERT_FILE", str(alert))
    stats = {"failed": 1, "failed_rows": ["70894 crbnos/carbon: ValueError: Invalid IPv6 URL"]}
    monkeypatch.setattr(grade_refresh, "refresh_grades", lambda db, **kw: stats)
    jobs._grade_security(_Db(), deadline=1.0)
    assert "70894 crbnos/carbon" in alert.read_text()


def test_a_clean_scan_leaves_no_alert(monkeypatch, tmp_path):
    alert = tmp_path / "scan-alert.txt"
    monkeypatch.setenv("SCAN_ALERT_FILE", str(alert))
    monkeypatch.setattr(grade_refresh, "refresh_grades", lambda db, **kw: {"failed": 0, "failed_rows": []})
    jobs._grade_security(_Db(), deadline=1.0)
    assert not alert.exists()


def test_the_workflow_hands_the_alert_file_and_the_sync_outcome_to_the_mailer():
    sync_yml = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "sync.yml").read_text()
    assert sync_yml.count("SCAN_ALERT_FILE: ${{ runner.temp }}/scan-alert.txt") == 2  # the sync step and the mail step
    assert "SYNC_OUTCOME: ${{ steps.sync.outcome }}" in sync_yml
    assert "issues: write" in sync_yml


def test_an_alert_that_cannot_be_written_does_not_cost_the_sync(monkeypatch, tmp_path):
    monkeypatch.setenv("SCAN_ALERT_FILE", str(tmp_path / "no-such-dir" / "scan-alert.txt"))

    def broken(db, **_kw):
        raise ValueError("Invalid IPv6 URL")

    monkeypatch.setattr(grade_refresh, "refresh_grades", broken)
    db = _Db()
    jobs._grade_security(db, deadline=1.0)  # no OSError escapes
    assert db.rollbacks == 1
