"""sync_all_skills must not shadow module-level names with a late local import."""
from app.scheduler import jobs


def test_text_is_not_a_local_of_the_sync():
    # A `from sqlalchemy import text` anywhere inside the function makes `text` local
    # to all of it; the README phase then fails before the import line is reached.
    code = jobs.sync_all_skills.__code__
    assert "text" not in code.co_varnames + code.co_cellvars
    assert jobs.text.__module__.startswith("sqlalchemy")


def test_settled_repos_query_builds():
    # not_(text(...)) raised a bare AssertionError while the query was being built, so
    # the helper failed on every call. Building and compiling it for Postgres is enough
    # to catch that; the rule itself needs Postgres to run (an interval).
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.orm import Session

    from app.services.readme_coverage import HAS_README_SQL

    query = jobs._settled_query(Session(), ["a/one", "a/two"], HAS_README_SQL)
    sql = str(query.statement.compile(dialect=postgresql.dialect()))
    assert "NOT (readme_content IS NULL" in sql and "repo_full_name IN" in sql


def test_has_readme_is_the_negation_of_missing():
    from app.services.readme_coverage import HAS_README_SQL, MISSING_README_SQL
    assert HAS_README_SQL == f"NOT {MISSING_README_SQL}"
