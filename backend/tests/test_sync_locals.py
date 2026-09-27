"""sync_all_skills must not shadow module-level names with a late local import."""
from app.scheduler import jobs


def test_text_is_not_a_local_of_the_sync():
    # A `from sqlalchemy import text` anywhere inside the function makes `text` local
    # to all of it; the README phase then fails before the import line is reached.
    code = jobs.sync_all_skills.__code__
    assert "text" not in code.co_varnames + code.co_cellvars
    assert jobs.text.__module__.startswith("sqlalchemy")
