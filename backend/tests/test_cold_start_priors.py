"""The post-sync cold-start step: stop on account errors, fail loudly when nothing scored."""
from datetime import datetime

import httpx
import pytest

import cold_start_priors as csp
from app.services.cold_start_prior import endpoint_from_env

ENDPOINT = endpoint_from_env({"TYPESAFE_API_KEY": "t"})
ANSWER = {"model": "jev-x", "answers": {"n": {"type": "noul", "noul": 0.5}}}


def _rows(n):
    return [{"repo_full_name": f"a/r{i}", "author_name": "a", "category": "c", "description": "d",
             "stars": 1, "created_at": datetime(2026, 10, 1), "first_seen": datetime(2026, 10, 2),
             "readme": "# R\n" + "x" * 400} for i in range(n)]


@pytest.fixture
def jev(monkeypatch):
    """Route the script's Jev calls to `handler` and record what would have been saved."""
    state = {"calls": 0, "saved": [], "status": [200]}
    real_client = httpx.Client

    def handler(request):
        status = state["status"][min(state["calls"], len(state["status"]) - 1)]
        state["calls"] += 1
        return httpx.Response(status, json=ANSWER if status == 200 else {"error": "no"})

    monkeypatch.setattr(csp.httpx, "Client", lambda: real_client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(csp, "_save_prior", lambda engine, row, prior, model: state["saved"].append(row["repo_full_name"]))
    return state


def test_out_of_credit_stops_after_the_first_call(monkeypatch, jev):
    monkeypatch.setattr(csp, "_new_repos", lambda engine: _rows(150))
    jev["status"] = [402]
    stats = csp.score_new(None, ENDPOINT)
    assert jev["calls"] == 1 and stats == {"candidates": 150, "scored": 0, "failed": 0, "stopped": "HTTP 402"}


def test_a_bad_repo_is_skipped_not_the_run(monkeypatch, jev):
    monkeypatch.setattr(csp, "_new_repos", lambda engine: _rows(3))
    jev["status"] = [400, 200]
    stats = csp.score_new(None, ENDPOINT)
    assert stats == {"candidates": 3, "scored": 2, "failed": 1} and jev["saved"] == ["a/r1", "a/r2"]


def _run_main(monkeypatch, stats):
    monkeypatch.setenv("TYPESAFE_API_KEY", "t")
    monkeypatch.setattr(csp, "_connect", lambda: None)
    monkeypatch.setattr(csp, "fill_outcomes", lambda engine: 0)
    monkeypatch.setattr(csp, "score_new", lambda engine, endpoint: stats)
    return csp.main()


def test_main_fails_when_candidates_got_no_prior(monkeypatch):
    assert _run_main(monkeypatch, {"candidates": 5, "scored": 0, "failed": 5}) == 1


def test_main_passes_on_a_quiet_day_or_partial_success(monkeypatch):
    assert _run_main(monkeypatch, {"candidates": 0, "scored": 0, "failed": 0}) == 0
    assert _run_main(monkeypatch, {"candidates": 5, "scored": 1, "failed": 4}) == 0


def test_main_skips_without_any_key(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert csp.main() == 0


def test_query_reads_readmes_only_for_picked_rows():
    sql = str(csp.NEW_REPOS)
    assert sql.index("left(s.readme_content, 4000)") > sql.index("picked as materialized")
    assert sql.index("length(readme_content)") < sql.index("picked as materialized")
    assert "nullif(readme_size, 0)" in sql
    assert "order by r.first_seen desc, r.id desc" in sql   # the same 150 every time
