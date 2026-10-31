"""renamed_repos.py: reading GraphQL answers, what to do per repository, the writes in order,
when a run stops, and the stale-row probe's old-name check. No network, no database."""
import io
import json
import sys
import urllib.error
from collections import Counter
from pathlib import Path

import pytest

import renamed_repos as rr
from renamed_repos import Found, Move, Row

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops"))

import probe_dead_repos  # noqa: E402

ECC = Found("affaan-m/ECC", "https://github.com/affaan-m/ECC", "Agent harness", 293682, 40000,
            "2026-10-30T12:00:00Z", "https://avatars.example/u/1")
CUA = Found("microsoft/CUAWright", "https://github.com/microsoft/CUAWright", "", 6079, 300, None, "")


def node(found):
    return {"nameWithOwner": found.full_name, "url": found.url, "description": found.description,
            "stargazerCount": found.stars, "forkCount": found.forks, "pushedAt": found.pushed_at,
            "owner": {"avatarUrl": found.avatar}}


def test_graphql_query_aliases_each_name_and_asks_for_the_budget():
    q = rr.graphql_query(["affaan-m/everything-claude-code", "a/b.c"])
    assert 'r0: repository(owner: "affaan-m", name: "everything-claude-code")' in q
    assert 'r1: repository(owner: "a", name: "b.c")' in q
    assert q.count("nameWithOwner") == 2 and q.endswith("rateLimit { remaining } }")


def test_verdict_ignores_a_change_of_case_only():
    assert rr.verdict("affaan-m/ECC", "affaan-m/ECC") == "same"
    assert rr.verdict("MiroMindAI/miroflow", "MiroMindAI/MiroFlow") == "case"
    assert rr.verdict("affaan-m/everything-claude-code", "affaan-m/ECC") == "renamed"


def test_read_batch_sorts_answers_into_verdicts():
    rows = [Row(1, "affaan-m/everything-claude-code", 186550), Row(2, "affaan-m/ECC", 293652),
            Row(3, "gone/repo", 900), Row(4, "blocked/repo", 800)]
    body = {"data": {"r0": node(ECC), "r1": node(ECC), "r2": None, "r3": None},
            "errors": [{"type": "NOT_FOUND", "path": ["r2"]}, {"type": "FORBIDDEN", "path": ["r3"]}]}
    out = rr.read_batch(body, rows)
    assert [(r.id, kind) for r, kind, _ in out] == [(1, "renamed"), (2, "same"), (3, "absent"), (4, "error")]
    assert out[0][2] == ECC
    assert [kind for _, kind, _ in rr.read_batch(None, rows[:2])] == ["error", "error"]


def test_plan_groups_old_names_by_repository_and_finds_its_row_in_any_case():
    renamed = [(Row(11, "mindsdb/minds-platform", 39229), Found("mindsdb/mindshub", "", "", 1, 0, None, "")),
               (Row(12, "mindsdb/mindsdb", 39138), Found("mindsdb/mindshub", "", "", 1, 0, None, "")),
               (Row(13, "affaan-m/everything-claude-code", 186550), ECC),
               (Row(14, "microsoft/Webwright", 6028), CUA)]
    current = {"mindsdb/mindshub": Row(20, "MindsDB/mindshub", 39835), "affaan-m/ecc": Row(21, "affaan-m/ECC", 293652)}
    moves = rr.plan(renamed, current)
    assert [m.old[0].full_name for m in moves] == ["affaan-m/everything-claude-code", "mindsdb/minds-platform",
                                                   "microsoft/Webwright"]
    assert [r.id for r in moves[1].old] == [11, 12] and moves[1].target == "MindsDB/mindshub"
    assert moves[2].keep is None and moves[2].target == "microsoft/CUAWright"


def test_a_merge_moves_first_seen_and_votes_then_deletes_the_old_row_and_records_the_redirect():
    move = Move(ECC, [Row(13, "affaan-m/everything-claude-code", 186550)], keep=Row(21, "affaan-m/ECC", 293652))
    steps = rr.statements(move)
    sqls = [sql for sql, _ in steps]
    assert sqls[:len(rr.MERGE_SQL)] == list(rr.MERGE_SQL)
    assert all(params == {"keep": 21, "old": 13} for _, params in steps[:len(rr.MERGE_SQL)])
    assert "o.first_seen < n.first_seen" in sqls[0]
    assert sqls[-3:] == [rr.LIVE_NAME_SQL, *rr.REDIRECT_SQL]
    assert steps[-1][1] == {"old": "affaan-m/everything-claude-code", "new": "affaan-m/ECC"}
    moved_first = [i for i, s in enumerate(sqls) if "arena_votes" in s or "user_favorites" in s]
    assert len(moved_first) == 4 and sqls.index("DELETE FROM skills WHERE id = %(old)s") > max(moved_first)


def test_a_lone_old_name_is_renamed_in_place_and_a_second_old_name_merges_into_it():
    move = Move(CUA, [Row(14, "microsoft/Webwright", 6028), Row(15, "microsoft/webwright-old", 900)])
    steps = rr.statements(move)
    assert steps[0][0] == rr.RENAME_SQL
    assert steps[0][1] == {"id": 14, "name": "microsoft/CUAWright", "repo": "CUAWright",
                           "url": "https://github.com/microsoft/CUAWright", "owner": "microsoft", "avatar": "",
                           "description": "", "stars": 6079, "forks": 300, "pushed": None}
    assert {"keep": 14, "old": 15} in [p for _, p in steps[1:1 + len(rr.MERGE_SQL)]]
    redirects = [p for sql, p in steps if sql == rr.REDIRECT_SQL[0]]
    assert redirects == [{"old": "microsoft/Webwright", "new": "microsoft/CUAWright"},
                         {"old": "microsoft/webwright-old", "new": "microsoft/CUAWright"}]


def test_a_renamed_row_takes_fresh_numbers_and_gives_up_its_readme_and_grade():
    for fragment in ("prev_stars = %(stars)s", "readme_content = NULL", "readme_fetched_at = NULL",
                     "security_grade = 'unknown'", "repo_status = 'live'", "WHERE id = %(id)s"):
        assert fragment in rr.RENAME_SQL
    assert "first_seen" not in rr.RENAME_SQL


def test_describe_says_which_row_is_renamed_and_which_deleted():
    lines = rr.describe(Move(CUA, [Row(14, "microsoft/Webwright", 6028), Row(15, "x/y", 900)]))
    assert lines[0].split()[0] == "rename" and lines[1].split()[0] == "delete"
    assert "not in the catalog" in lines[0]


def batch_answer(rows, found=ECC, left=4000):
    data = {f"r{i}": node(found) for i in range(len(rows))}
    data["rateLimit"] = {"remaining": left}
    return {"data": data}


def test_sweep_collects_old_names_and_stops_at_the_budget_floor(monkeypatch):
    rows = [Row(i, f"o/r{i}", 100) for i in range(rr.BATCH + 5)]
    calls = []

    def answer(q, t, p):
        calls.append(q)
        return batch_answer(rows, left=rr.GRAPHQL_FLOOR - 1)
    monkeypatch.setattr(rr, "post_graphql", answer)
    sw = rr.sweep(rows, "token", minutes=5)
    assert len(calls) == 1 and sw.stopped == "GraphQL budget under the floor"
    assert sw.counts["renamed"] == rr.BATCH and not sw.refused


def test_sweep_stops_and_flags_a_refused_token(monkeypatch):
    def refuse(q, t, p):
        raise rr.Halt("GitHub answered HTTP 401")
    monkeypatch.setattr(rr, "post_graphql", refuse)
    sw = rr.sweep([Row(1, "o/r", 100)], "token", minutes=5)
    assert sw.refused and sw.stopped == "GitHub answered HTTP 401" and not sw.counts


class _Answer(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_fetch_once_retries_a_server_error_and_halts_on_a_refusal(monkeypatch):
    def answer(code):
        def urlopen(req, timeout):
            raise urllib.error.HTTPError(req.full_url, code, "x", {}, None)
        return urlopen
    req = rr.urllib.request.Request(rr.GRAPHQL_URL)
    monkeypatch.setattr(rr.urllib.request, "urlopen", answer(502))
    assert rr.fetch_once(req) is None
    monkeypatch.setattr(rr.urllib.request, "urlopen", answer(401))
    with pytest.raises(rr.Halt):
        rr.fetch_once(req)
    limited = json.dumps({"data": None, "errors": [{"type": "RATE_LIMITED"}]}).encode()
    monkeypatch.setattr(rr.urllib.request, "urlopen", lambda req, timeout: _Answer(limited))
    with pytest.raises(rr.Halt):
        rr.fetch_once(req)


class _Cursor:
    def __init__(self, log, fail_on):
        self.log, self.fail_on = log, fail_on

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if self.fail_on and params and params.get("old") == self.fail_on:
            raise RuntimeError("unique violation")
        self.log.append(sql)


class _Conn:
    def __init__(self, fail_on=None):
        self.log, self.fail_on, self.commits, self.rollbacks = [], fail_on, 0, 0

    def cursor(self):
        return _Cursor(self.log, self.fail_on)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_apply_writes_one_transaction_per_repository_and_goes_on_after_a_failure(monkeypatch):
    monkeypatch.setattr(rr, "sync_active", lambda: False)
    moves = [Move(ECC, [Row(13, "affaan-m/everything-claude-code", 186550)], keep=Row(21, "affaan-m/ECC", 1)),
             Move(CUA, [Row(14, "microsoft/Webwright", 6028), Row(15, "x/y", 900)])]
    conn = _Conn(fail_on=13)
    done, halted = rr.apply(conn, moves)
    assert done == Counter(failed=1, renamed=1, deleted=1) and halted == ""
    assert conn.commits == 1 and conn.rollbacks == 1
    assert conn.log[0] == rr.TIMEOUT_SQL


def test_apply_writes_nothing_while_a_sync_runs(monkeypatch):
    monkeypatch.setattr(rr, "sync_active", lambda: True)
    conn = _Conn()
    done, halted = rr.apply(conn, [Move(CUA, [Row(14, "microsoft/Webwright", 6028)])])
    assert halted == "a sync is queued or running" and not done and not conn.log


def test_exit_code_fails_on_a_refusal_a_failed_write_or_many_failed_lookups():
    rows = [Row(i, f"o/r{i}", 100) for i in range(1000)]
    assert rr.exit_code(rows, rr.Sweep(counts=Counter(error=100)), Counter()) == 0
    assert rr.exit_code(rows, rr.Sweep(counts=Counter(error=101)), Counter()) == 1
    assert rr.exit_code(rows, rr.Sweep(refused=True), Counter()) == 1
    assert rr.exit_code(rows, rr.Sweep(), Counter(failed=1)) == 1


def test_probe_treats_an_answer_for_another_name_as_an_old_name():
    assert probe_dead_repos.is_old_name("affaan-m/everything-claude-code", {"full_name": "affaan-m/ECC"})
    assert not probe_dead_repos.is_old_name("MiroMindAI/miroflow", {"full_name": "MiroMindAI/MiroFlow"})
    assert not probe_dead_repos.is_old_name("gone/repo", None)
