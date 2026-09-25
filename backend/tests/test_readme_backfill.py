"""Pure decisions of the scheduled README backfill."""
import readme_backfill as rb
from app.services.readme_coverage import MISSING_README_SQL


def test_keeps_the_first_tier_while_work_remains():
    assert rb.choose_floor(rb.DROP_BELOW, allow_drop=True) == rb.DEFAULT_FLOOR


def test_drops_to_one_star_once_the_first_tier_is_nearly_done():
    assert rb.choose_floor(rb.DROP_BELOW - 1, allow_drop=True) == rb.LOW_FLOOR


def test_never_drops_without_the_flag():
    assert rb.choose_floor(0, allow_drop=False) == rb.DEFAULT_FLOOR


def test_zero_star_repos_are_never_targets():
    assert rb.clamp_floor(0) == rb.LOW_FLOOR == 1


def test_stops_under_the_quota_floor():
    assert rb.quota_exhausted(rb.QUOTA_FLOOR - 1)
    assert not rb.quota_exhausted(rb.QUOTA_FLOOR)


def test_candidates_follow_the_shared_rule():
    sql = rb.CANDIDATE_SQL
    assert MISSING_README_SQL in sql
    assert "security_grade = 'unknown'" in sql and "repo_status" in sql
    assert "stars >= %(floor)s" in sql and "ORDER BY stars DESC" in sql


def test_writes_never_replace_a_real_readme():
    assert "readme_content IS NULL OR readme_content = ''" in rb.WRITE_SQL


def test_import_needs_no_credentials():
    # CI imports this module in tests without GH_TOKEN or a database.
    assert rb.main


def test_one_transient_write_failure_does_not_fail_the_run():
    assert rb.exit_code({"ok": 1216, "absent": 80, "error": 3, "write_failed": 1}) == 0


def test_a_broken_database_fails_the_run():
    assert rb.exit_code({"ok": 100, "absent": 0, "error": 0, "write_failed": 40}) == 1
