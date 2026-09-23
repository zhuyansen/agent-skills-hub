"""The rule the sync and the backfill share for 'this repo still needs its README'."""
from datetime import datetime, timedelta, timezone

from app.services.readme_coverage import (
    MISSING_README_SQL,
    NO_README_RETRY_DAYS,
    readme_missing,
    readme_update,
)

NOW = datetime(2026, 9, 23, 12, tzinfo=timezone.utc)


def test_never_fetched_is_missing():
    assert readme_missing(None, None, NOW)


def test_a_fetched_readme_is_never_missing():
    assert not readme_missing("# Title", NOW - timedelta(days=400), NOW)
    assert not readme_missing("# Title", None, NOW)  # fetched before the marker existed


def test_confirmed_absent_waits_for_the_retry_window():
    assert not readme_missing("", NOW - timedelta(days=NO_README_RETRY_DAYS - 1), NOW)
    assert readme_missing("", NOW - timedelta(days=NO_README_RETRY_DAYS + 1), NOW)


def test_empty_without_a_marker_is_rechecked():
    # '' written before readme_fetched_at existed: some are ingestion artifacts
    # for repos that do have a README (gozen3ji/consulting-pptx-skill).
    assert readme_missing("", None, NOW)


def test_sql_matches_the_retry_window():
    assert f"interval '{NO_README_RETRY_DAYS} days'" in MISSING_README_SQL
    assert "readme_content IS NULL" in MISSING_README_SQL


def test_a_fetched_readme_is_written_with_the_marker():
    assert readme_update(None, "# Hi", absent=False, now=NOW) == {
        "readme_content": "# Hi", "readme_size": 4, "readme_fetched_at": NOW}


def test_absent_marks_a_row_without_text():
    assert readme_update(None, None, absent=True, now=NOW) == {
        "readme_content": "", "readme_size": 0, "readme_fetched_at": NOW}
    assert readme_update("", None, absent=True, now=NOW)["readme_fetched_at"] == NOW


def test_absent_never_erases_a_real_readme():
    # A 404 for a repo we hold text for is likelier a rename or a blip than a deleted README.
    assert readme_update("# Real", None, absent=True, now=NOW) == {}


def test_an_error_records_nothing():
    assert readme_update(None, None, absent=False, now=NOW) == {}
