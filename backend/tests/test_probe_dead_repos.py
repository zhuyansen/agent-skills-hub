"""ops/probe_dead_repos.py: what each GitHub answer means, what a run writes and in which
order the queue goes. No network, no database."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops"))

import probe_dead_repos as pd  # noqa: E402
from app.services.extra_repo_backfill import QUEUE_TAGS  # noqa: E402

CREATED = datetime(2023, 5, 25, 10, 11, 12)          # skills.created_at is naive UTC
NEWER = "2026-09-29T12:00:00Z"                        # a repository that took the name later
ROW = pd.Candidate(1699, "SamurAIGPT/Generative-Media-Skills", 4337, datetime(2026, 9, 29, 4, 42), CREATED)


def answer(name=ROW.name, created="2023-05-25T10:11:12Z", stars=4400, description="Media skills"):
    return {"id": 645381450, "full_name": name, "created_at": created, "stargazers_count": stars,
            "forks_count": 7, "open_issues_count": 2, "pushed_at": "2026-11-01T08:00:00Z",
            "description": description}


def row(i, name=None):
    return ROW._replace(id=i, name=name or f"o/r{i}")


class Cursor:
    def __init__(self, conn):
        self.conn, self.rowcount = conn, 1

    def execute(self, sql, params=None):
        self.conn.log.append((sql, params))

    def fetchall(self):
        return self.conn.rows


class Conn:
    def __init__(self, rows=()):
        self.log, self.rows, self.commits, self.closed = [], list(rows), 0, False

    def cursor(self):
        return Cursor(self)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def flat(sql):
    return " ".join(sql.split())


# ── Verdicts ──────────────────────────────────────────────────────────────────────────

def test_each_answer_has_one_verdict():
    assert pd.verdict(ROW, 404, None) == "gone"
    assert pd.verdict(ROW, None, None) == "unknown"
    assert pd.verdict(ROW, 451, None) == "unknown"
    assert pd.verdict(ROW, 200, answer()) == "live"
    assert pd.verdict(ROW, 200, answer(name="samuraigpt/generative-media-skills")) == "live"
    assert pd.verdict(ROW, 200, answer(name="Anil-matcha/open-duet")) == "moved"
    assert pd.verdict(ROW, 200, answer(created=NEWER, stars=34)) == "reused"


def test_a_reused_name_is_a_created_at_other_than_the_stored_one():
    assert not pd.is_reused_name(CREATED, answer())
    assert not pd.is_reused_name(CREATED.replace(tzinfo=timezone.utc), answer())
    assert not pd.is_reused_name(CREATED.replace(microsecond=250000), answer())
    assert pd.is_reused_name(CREATED, answer(created="2023-05-25T10:11:13Z"))
    assert pd.is_reused_name(CREATED, answer(created=NEWER))


def test_a_row_or_answer_without_created_at_counts_as_the_same_repository():
    assert not pd.is_reused_name(None, answer(created=NEWER))
    assert not pd.is_reused_name(CREATED, answer(created=None))
    assert not pd.is_reused_name(CREATED, answer(created="not a time"))
    assert pd.verdict(ROW._replace(created_at=None), 200, answer(created=NEWER)) == "live"


# ── The queue ─────────────────────────────────────────────────────────────────────────

def test_the_queue_goes_by_last_probe_and_skips_rows_probed_or_synced_lately():
    sql = flat(pd.CANDIDATE_SQL)
    assert "ORDER BY repo_status_checked_at ASC NULLS FIRST, last_synced ASC, id ASC" in sql
    assert ("(repo_status_checked_at IS NULL OR repo_status_checked_at < now() - "
            "make_interval(days => %(days)s))") in sql
    assert "last_synced < now() - make_interval(days => %(days)s)" in sql
    assert "repo_status <> 'gone'" in sql and "stars >= %(min_stars)s" in sql


def test_fetch_candidates_passes_the_window_and_returns_candidates():
    conn = Conn(rows=[(1699, ROW.name, 4337, ROW.last_synced, CREATED)])
    assert pd.fetch_candidates(conn, 20, 1200, 14) == [ROW]
    assert conn.log[0][1] == {"min_stars": 20, "days": 14, "limit": 1200}


def test_every_row_github_answered_is_stamped_and_an_unreached_one_is_not():
    for kind in ("live", "gone", "moved"):
        assert "repo_status_checked_at = now()" in pd.STATUS_SQL[kind]
    assert "repo_status_checked_at" not in pd.STATUS_SQL["unknown"]
    assert "repo_status = 'unknown'" in pd.STATUS_SQL["unknown"]
    assert "repo_status =" not in pd.STATUS_SQL["moved"]       # renamed_repos.py decides that row
    assert "repo_status_checked_at = now()" in pd.RESET_SQL


def test_write_status_writes_each_bucket_that_has_rows_once():
    conn = Conn()
    pd.write_status(conn, {"live": ["a/b"], "gone": [], "unknown": ["c/d"], "moved": ["e/f"], "stats": []})
    assert [params for _, params in conn.log] == [(["a/b"],), (["c/d"],), (["e/f"],)]
    assert conn.commits == 1


def test_a_run_reaches_every_row_it_probed_except_the_unreached():
    rows = [row(i) for i in range(6)]
    results = [(rows[0], "live", answer(name="o/r0")), (rows[1], "gone", None),
               (rows[2], "moved", answer(name="o/new")), (rows[3], "unknown", None),
               (rows[4], "reused", answer(name="o/r4", created=NEWER)), (rows[5], "live", answer(name="o/r5"))]
    buckets = pd.buckets_of(results)
    stamped = {n for kind in ("live", "gone", "moved") for n in buckets[kind]}
    assert stamped | {r.name for r, _ in pd.reused_of(results)} == {r.name for r in rows} - {"o/r3"}


# ── Stars ─────────────────────────────────────────────────────────────────────────────

def test_stars_go_to_the_stored_name_and_a_reused_row_gets_none():
    live, old, reused = row(1, "MiroMindAI/miroflow"), row(2, "affaan-m/everything-claude-code"), row(3)
    results = [(live, "live", answer(name="MiroMindAI/MiroFlow", stars=900)),
               (old, "moved", answer(name="affaan-m/ECC", stars=293682)),
               (reused, "reused", answer(name="o/r3", created=NEWER, stars=34)),
               (row(4, "gone/repo"), "gone", None)]
    buckets = pd.buckets_of(results)
    assert buckets["live"] == ["MiroMindAI/miroflow"] and buckets["moved"] == [old.name]
    assert buckets["gone"] == ["gone/repo"] and buckets["unknown"] == []
    assert [(s[0], s[1]) for s in buckets["stats"]] == [("MiroMindAI/miroflow", 900), ("affaan-m/ECC", 293682)]


def test_write_stats_only_touches_rows_whose_stars_changed():
    conn = Conn()
    pd.write_stats(conn, [("a/b", 10, 1, 0, None)])
    sql, params = conn.log[0]
    assert "stars IS DISTINCT FROM %s" in sql and "last_synced = now()" in sql
    assert params == (10, 10, 1, 0, None, "a/b", 10)


# ── Same name, another repository ─────────────────────────────────────────────────────

def test_a_reused_name_is_rewritten_from_github_and_queued_for_the_sync():
    conn = Conn()
    pd.reset_reused(conn, [(ROW, answer(created=NEWER, stars=34, description="  " + "x" * 600))])
    (reset_sql, params), (queue_sql, queue_params) = conn.log
    assert params["id"] == 1699 and params["stars"] == 34 and params["forks"] == 7
    assert params["created_at"] == datetime(2026, 9, 29, 12, 0)     # naive UTC, like the column
    assert params["pushed"] == datetime(2026, 11, 1, 8, 0)
    assert params["description"] == "x" * pd.DESCRIPTION_MAX
    for clause in ("prev_stars = %(stars)s", "created_at = %(created_at)s", "readme_content = NULL",
                   "readme_fetched_at = NULL", "security_grade = 'unknown'", "last_synced = now()",
                   "WHERE id = %(id)s"):
        assert clause in reset_sql
    assert "INSERT INTO extra_repos" in queue_sql and "ON CONFLICT (full_name) DO NOTHING" in queue_sql
    assert queue_params == {"name": ROW.name, "tag": pd.REUSE_TAG}
    assert conn.commits == 1


def test_the_reuse_tag_is_a_queue_tag_so_its_row_is_retired_after_the_sync():
    assert pd.REUSE_TAG in QUEUE_TAGS


def reused_results(n):
    return [(row(i), "reused", answer(name=f"o/r{i}", created=NEWER)) for i in range(n)]


def test_up_to_the_cap_reused_names_are_reset(monkeypatch):
    conn = Conn()
    monkeypatch.setattr(pd, "connect", lambda: conn)
    results = reused_results(pd.MAX_REUSED_PER_RUN)
    assert pd.persist(results, pd.buckets_of(results)) == 0
    assert sum("readme_content = NULL" in sql for sql, _ in conn.log) == pd.MAX_REUSED_PER_RUN
    assert conn.closed


def test_too_many_reused_names_in_one_run_reset_none_and_fail(monkeypatch):
    conn = Conn()
    monkeypatch.setattr(pd, "connect", lambda: conn)
    results = reused_results(pd.MAX_REUSED_PER_RUN + 1)
    assert pd.persist(results, pd.buckets_of(results)) == 1
    assert not any("readme_content = NULL" in sql or "extra_repos" in sql for sql, _ in conn.log)
    assert conn.closed


# ── Files and replay ──────────────────────────────────────────────────────────────────

def test_outputs_list_the_dead_and_the_reused_and_replay_writes_statuses_and_stars(tmp_path, monkeypatch):
    monkeypatch.setattr(pd, "OUT_DIR", str(tmp_path))
    results = [(row(1, "a/b"), "live", answer(name="a/b", stars=12)), (row(2, "c/d"), "gone", None),
               (row(3, "e/f"), "reused", answer(name="e/f", created=NEWER, stars=34))]
    dead, reused = pd.save_outputs(results, pd.buckets_of(results))
    assert [d["repo_full_name"] for d in dead] == ["c/d"]
    assert reused[0]["github_stars"] == 34 and reused[0]["stored_created_at"] == str(CREATED)
    assert json.loads((tmp_path / "name-reused.json").read_text()) == reused
    conn = Conn()
    monkeypatch.setattr(pd, "connect", lambda: conn)
    assert pd.replay() == 0
    assert [params for _, params in conn.log] == [(["a/b"],), (["c/d"],), (12, 12, 7, 2, "2026-11-01T08:00:00Z", "a/b", 12)]


# ── Token ─────────────────────────────────────────────────────────────────────────────

class Resp:
    def __init__(self, status):
        self.status_code, self.ok = status, status == 200

    def json(self):
        return {"resources": {"core": {"remaining": 4999}}}


def test_github_token_takes_the_first_token_github_accepts(monkeypatch):
    answers = {"dead": (Resp(401), None), "flaky": (None, "ConnectionError"), "good": (Resp(200), None)}
    monkeypatch.setattr(pd, "_token_candidates",
                        lambda: [("gh", "dead"), ("env", "flaky"), ("none", ""), ("other", "good")])
    monkeypatch.setattr(pd, "_rate_limit", lambda tok: answers[tok])
    assert pd.github_token() == "good"


def test_github_token_stops_the_run_when_no_token_works(monkeypatch):
    monkeypatch.setattr(pd, "_token_candidates", lambda: [("gh", ""), ("env", "dead")])
    monkeypatch.setattr(pd, "_rate_limit", lambda tok: (Resp(401), None))
    with pytest.raises(SystemExit):
        pd.github_token()


def test_the_token_check_retries_a_dropped_connection(monkeypatch):
    calls = []

    def get(*args, **kwargs):
        calls.append(kwargs["headers"])
        if len(calls) < pd.RETRIES:
            raise pd.requests.ConnectionError()
        return Resp(200)

    monkeypatch.setattr(pd.requests, "get", get)
    monkeypatch.setattr(pd.time, "sleep", lambda seconds: None)
    response, error = pd._rate_limit("tok")
    assert response.ok and error is None and len(calls) == pd.RETRIES
