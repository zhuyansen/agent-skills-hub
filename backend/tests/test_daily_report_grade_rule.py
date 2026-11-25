"""The daily report only recommends repos graded safe, the same rule its prompt gives the model.

Until 2026-11-25 the code let ungraded rows (None or "unknown") through while the prompt said
to skip anything not safe. On 11-21 the grader had been down two days and the picks it
published were all ungraded.
"""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "ops" / "daily_skills_report.py"
spec = importlib.util.spec_from_file_location("daily_skills_report", SCRIPT)
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)


def candidate(grade, gh=None):
    return {"repo_full_name": "someone/tool", "d": "A CLI for agents", "stars": 40, "security_grade": grade, "gh": gh}


@pytest.mark.parametrize("grade", [None, "unknown", "caution", "unsafe", "reject"])
def test_anything_not_graded_safe_is_dropped_before_github_is_asked(grade):
    assert daily.hard_reject(candidate(grade), clusters={}).startswith("security_grade")


def test_a_safe_repo_goes_on_to_the_github_check():
    assert daily.hard_reject(candidate("safe"), clusters={}) is None
