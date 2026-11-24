"""Unit tests for ops/health/fetch_health.py."""
from unittest.mock import MagicMock

import fetch_health


def _resp(status_code=200, text="", json_data=None):
    r = MagicMock()
    r.status_code = status_code
    r.text = text
    r.json.return_value = json_data if json_data is not None else {}
    return r


def test_jev_real_inference_ok(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-jev")
    for k in ("FLATROUTER_API_KEY", "OPENROUTER_API_KEY", "AISA_API_KEY"):
        monkeypatch.delenv(k, raising=False)

    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs["json"]))
        return _resp(200, '{"answers":{"c1":{"choice":"done"}}}', {"answers": {"c1": {"choice": "done"}}})

    monkeypatch.setattr(fetch_health.requests, "post", fake_post)
    checks = fetch_health.check_channels()
    assert len(checks) == 1
    assert checks[0]["ok"] is True
    assert "systemone" in calls[0][0]
    assert "推理正常" in checks[0]["status_text"]


def test_jev_real_inference_missing_answers_fails(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-jev")
    for k in ("FLATROUTER_API_KEY", "OPENROUTER_API_KEY", "AISA_API_KEY"):
        monkeypatch.delenv(k, raising=False)

    monkeypatch.setattr(fetch_health.requests, "post", lambda *a, **kw: _resp(200, "{}", {}))
    checks = fetch_health.check_channels()
    assert len(checks) == 1
    assert checks[0]["ok"] is False
    assert "answers" in checks[0]["status_text"]


def test_check_sites_validates_status_and_marker(monkeypatch):
    def fake_get(url, **kwargs):
        if url.endswith("sitemap.xml"):
            return _resp(503, "Service Unavailable")
        if url.endswith("llms.txt"):
            return _resp(200, "wrong body")
        return _resp(200, "<html><title>AgentSkillsHub</title></html>")

    monkeypatch.setattr(fetch_health.requests, "get", fake_get)
    sites = fetch_health.check_sites()
    by_id = {s["id"]: s for s in sites}
    assert by_id["home"]["ok"] is True
    assert by_id["sitemap"]["ok"] is False
    assert by_id["sitemap"]["status_code"] == 503
    assert by_id["llms"]["ok"] is False
    assert "缺失" in by_id["llms"]["status_text"]


def _run(conclusion, start, end, status="completed"):
    return {"status": status, "conclusion": conclusion, "created_at": start, "run_started_at": start,
            "updated_at": end, "html_url": f"https://github.com/x/actions/runs/{start}"}


def _runs_api(monkeypatch, runs):
    monkeypatch.setattr(fetch_health, "WORKFLOWS", {"index-watch.yml": "Google 收录巡检"})
    monkeypatch.setattr(fetch_health.requests, "get", lambda *a, **kw: _resp(200, "", {"workflow_runs": runs}))
    return fetch_health.check_workflows()[0]


def test_timeouts_since_last_success_fail_the_workflow(monkeypatch):
    w = _runs_api(monkeypatch, [
        _run("cancelled", "2026-11-23T09:46:24Z", "2026-11-23T12:46:44Z"),
        _run("cancelled", "2026-11-22T08:50:10Z", "2026-11-22T11:50:29Z"),
        _run("success", "2026-11-21T08:45:27Z", "2026-11-21T10:14:41Z"),
    ])
    assert w["ok"] is False and w["conclusion"] == "timed_out"
    assert "最近 2 次运行超时被取消" in w["error"] and "3.0 小时" in w["error"]


def test_a_quick_cancel_is_a_superseded_run_not_a_failure(monkeypatch):
    w = _runs_api(monkeypatch, [
        _run("cancelled", "2026-11-23T09:46:24Z", "2026-11-23T09:47:00Z"),
        _run("success", "2026-11-23T09:40:00Z", "2026-11-23T09:45:00Z"),
    ])
    assert w["ok"] is True and w["conclusion"] == "success"


def test_an_old_timeout_before_a_success_is_forgotten(monkeypatch):
    w = _runs_api(monkeypatch, [
        _run("success", "2026-11-24T09:00:00Z", "2026-11-24T10:00:00Z"),
        _run("cancelled", "2026-11-23T09:46:24Z", "2026-11-23T12:46:44Z"),
    ])
    assert w["ok"] is True


def test_a_run_in_progress_does_not_hide_a_timeout(monkeypatch):
    w = _runs_api(monkeypatch, [
        _run(None, "2026-11-24T09:00:00Z", "2026-11-24T09:30:00Z", status="in_progress"),
        _run("cancelled", "2026-11-23T09:46:24Z", "2026-11-23T12:46:44Z"),
        _run("success", "2026-11-21T08:45:27Z", "2026-11-21T10:14:41Z"),
    ])
    assert w["ok"] is False and w["running"] is True
