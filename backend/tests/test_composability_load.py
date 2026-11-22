"""Composability loads only the columns it reads, not whole Skill rows.

On 2026-11-21 `db.query(Skill).filter(Skill.stars >= 5).all()` pulled every README and
LLM analysis, ran past the 120 s statement timeout and failed the sync."""
import json
from collections import namedtuple
from unittest.mock import MagicMock

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.services import composability
from app.services.composability import ComposabilityEngine, candidates_query


def test_query_selects_only_light_columns():
    sql = str(candidates_query(Session()).statement.compile(dialect=postgresql.dialect()))
    select = sql.split("FROM")[0]
    assert "substr(skills.readme_content" in select
    for heavy in ("security_llm_analysis", "security_flags", "skills.readme_content AS"):
        assert heavy not in select
    assert "skills.stars >=" in sql


Row = namedtuple("Row", "id author_name description topics category platforms language stars quality_score readme_content")


def test_compute_all_works_on_light_rows(monkeypatch):
    descs = ["claude video editing skill with remotion", "remotion video rendering for claude agents",
             "ffmpeg video editing agent skill", "slide deck ppt generator", "ppt presentation skill for codex",
             "postgres database migration helper"]
    rows = [Row(i, f"author{i}", d, json.dumps(d.split()[:2]), "video" if "video" in d else "docs",
                json.dumps(["claude"]), "Python", 50, 60, d) for i, d in enumerate(descs, start=1)]
    monkeypatch.setattr(composability, "load_candidates", lambda db: rows)
    db = MagicMock()
    count = ComposabilityEngine().compute_all(db, changed_ids={1})
    added = [c for call in db.add_all.call_args_list for c in call.args[0]]
    assert count == len(added) > 0
    assert {c.skill_id for c in added} == {1}
    assert {c.compatible_skill_id for c in added} <= {2, 3, 4, 5, 6}
