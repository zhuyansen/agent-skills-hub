"""ops/awesome/repo_rows.py and the places that use it: one GitHub lookup per listed repo for a whole
run of the daily pass. It used to look every listed repo up three times per page (exclude_gone and two
builds of the list): 14,000 REST calls a run against a quota of 5,000 an hour."""
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/awesome"))

import build_video_list as bvl  # noqa: E402
import daily_video_pass as dvp  # noqa: E402
import repo_rows as rr  # noqa: E402

# One repo as GitHub's REST API and its GraphQL API answer for it (recorded 11-08, trimmed to the fields used).
REST = {"full_name": "remotion-dev/remotion", "stargazers_count": 71596, "description": "Make videos with React",
        "created_at": "2020-06-23T19:49:10Z", "language": "TypeScript", "license": {"key": "other", "spdx_id": "NOASSERTION"}}
NODE = {"nameWithOwner": "remotion-dev/remotion", "stargazerCount": 71596, "description": "Make videos with React",
        "createdAt": "2020-06-23T19:49:10Z", "primaryLanguage": {"name": "TypeScript"}, "licenseInfo": {"spdxId": "NOASSERTION"}}
BARE_REST = {"full_name": "a/bare", "stargazers_count": 5, "description": None, "created_at": "2026-01-01T00:00:00Z",
             "language": None, "license": None}
BARE_NODE = {"nameWithOwner": "a/bare", "stargazerCount": 5, "description": None, "createdAt": "2026-01-01T00:00:00Z",
             "primaryLanguage": None, "licenseInfo": None}


def done(returncode=0, out="", err=""):
    return subprocess.CompletedProcess([], returncode, out, err)


def row(name):
    return {"repo_full_name": name, "stars": 1}


@pytest.fixture
def cache(tmp_path, monkeypatch):
    path = tmp_path / "rows.jsonl"
    monkeypatch.setenv(rr.CACHE_ENV, str(path))
    return path


@pytest.fixture
def page(tmp_path, monkeypatch):
    """A one-page world for exclude_gone: the page's kinds and keywords files, in tmp_path."""
    def make(repos):
        (tmp_path / "kinds.json").write_text(json.dumps({"p": {"kinds": [], "repos": {n: "general" for n in repos}}}))
        (tmp_path / "kw.json").write_text(json.dumps([{"slug": "p", "match": {}}]))
        monkeypatch.setattr(dvp, "KINDS", tmp_path / "kinds.json")
        monkeypatch.setattr(dvp, "KEYWORDS", tmp_path / "kw.json")
        monkeypatch.setattr(dvp, "SLUG", "p")
        return tmp_path
    return make


# --- the GraphQL answer is the row the REST answer makes -----------------------------------

@pytest.mark.parametrize("rest, node", [(REST, NODE), (BARE_REST, BARE_NODE)])
def test_a_graphql_node_is_the_row_github_row_builds_from_rest(monkeypatch, rest, node):
    monkeypatch.setattr(bvl.subprocess, "run", lambda *a, **k: done(0, json.dumps(rest)))
    assert rr.row_from_graphql(node) == bvl._github_row_rest(rest["full_name"])


def test_a_batch_answer_is_read_name_by_name():
    body = {"data": {"r0": NODE, "r1": None, "r2": None},
            "errors": [{"type": "NOT_FOUND", "path": ["r1"], "message": "Could not resolve to a Repository"},
                       {"type": "SERVICE_UNAVAILABLE", "path": ["r2"], "message": "try later"}]}
    got = rr.parse(["a/found", "b/gone", "c/unsure", "d/unanswered"], json.dumps(body))
    assert got["a/found"] == rr.row_from_graphql(NODE)
    assert got["b/gone"] is None                                   # NOT_FOUND: deleted, or private to us
    assert "c/unsure" not in got and "d/unanswered" not in got     # left for the one-by-one lookup


@pytest.mark.parametrize("text", ["", "<html>502 Bad Gateway</html>", '{"errors": [{"message": "boom"}]}', '{"data": null}'])
def test_an_answer_with_nothing_usable_teaches_nothing(text):
    assert rr.parse(["a/b"], text) == {}


def test_the_query_names_each_repo_by_alias_and_escapes_the_names():
    query = rr.query(["o/r", 'x"y/z'])
    assert 'r0: repository(owner: "o", name: "r")' in query
    assert 'r1: repository(owner: "x\\"y", name: "z")' in query


def test_run_batch_reads_the_answer_even_when_gh_exits_1(monkeypatch):
    body = {"data": {"r0": NODE, "r1": None}, "errors": [{"type": "NOT_FOUND", "path": ["r1"]}]}
    seen = []
    monkeypatch.setattr(rr.subprocess, "run", lambda cmd, **kw: seen.append(cmd) or done(1, json.dumps(body), "gh: Could not resolve"))
    got = rr.run_batch(["remotion-dev/remotion", "x/gone"])
    assert got["remotion-dev/remotion"]["stars"] == 71596 and got["x/gone"] is None
    assert seen[0][:3] == ["gh", "api", "graphql"]


def test_run_batch_raises_when_github_answered_nothing_usable(monkeypatch):
    monkeypatch.setattr(rr.subprocess, "run", lambda *a, **k: done(1, "", "HTTP 502"))
    with pytest.raises(RuntimeError):
        rr.run_batch(["a/b"])


# --- the cache file the run shares ---------------------------------------------------------

def test_the_cache_remembers_rows_and_missing_repos_without_regard_to_case(cache):
    assert rr.get("Owner/Repo") == (False, None)
    rr.put("Owner/Repo", row("owner/repo"))
    rr.put("gone/repo", None)
    assert rr.get("owner/REPO") == (True, row("owner/repo"))
    assert rr.get("gone/repo") == (True, None)


def test_rows_written_by_another_process_are_seen(cache):
    assert rr.get("a/b") == (False, None)
    cache.write_text(json.dumps({"k": "a/b", "row": None}) + "\n")          # the list builder runs as a child process
    assert rr.get("a/b") == (True, None)


def test_a_torn_last_line_is_ignored(cache):
    cache.write_text(json.dumps({"k": "a/b", "row": None}) + '\n{"k": "c/d", "ro')
    assert rr.get("a/b") == (True, None) and rr.get("c/d") == (False, None)


def test_without_a_cache_file_nothing_is_remembered(monkeypatch):
    monkeypatch.delenv(rr.CACHE_ENV, raising=False)
    rr.put("a/b", row("a/b"))
    assert rr.get("a/b") == (False, None)


# --- the batch at the start of a run -------------------------------------------------------

def test_prefetch_asks_in_batches_for_the_names_the_cache_lacks(cache, monkeypatch):
    asked = []
    monkeypatch.setattr(rr, "BATCH", 2)
    monkeypatch.setattr(rr, "run_batch", lambda names: asked.append(list(names)) or {n: row(n) for n in names})
    rr.put("a/cached", None)
    stats = rr.prefetch(["a/cached", "b/one", "c/two", "d/three", "e/f/g", "H/Four", "h/four"])
    assert asked == [["b/one", "c/two"], ["d/three", "H/Four"]]       # not the cached one, the folder key, or the repeat
    assert rr.get("h/four") == (True, row("H/Four")) and rr.get("e/f/g") == (False, None)
    assert stats == {"asked": 4, "found": 4, "gone": 0, "left": 0, "requests": 2}


def test_a_failed_batch_leaves_its_names_and_the_next_one_goes_on(cache, monkeypatch):
    def fake(names):
        if names == ["b/two"]:
            raise RuntimeError("HTTP 502")
        return {n: None for n in names}
    monkeypatch.setattr(rr, "BATCH", 1)
    monkeypatch.setattr(rr.time, "sleep", lambda s: None)
    monkeypatch.setattr(rr, "run_batch", fake)
    stats = rr.prefetch(["a/one", "b/two", "c/three"])
    assert rr.get("a/one") == (True, None) and rr.get("c/three") == (True, None) and rr.get("b/two") == (False, None)
    assert stats == {"asked": 3, "found": 0, "gone": 2, "left": 1, "requests": 4}      # b/two was tried twice


def test_a_flood_of_not_found_is_not_believed(cache, monkeypatch):
    names = [f"o/r{i}" for i in range(200)]
    monkeypatch.setattr(rr, "run_batch", lambda chunk: {n: (None if int(n[3:]) < 30 else row(n)) for n in chunk})
    stats = rr.prefetch(names)                     # 30 of 200 "not found" is far above 2%
    assert stats["doubted"] == 30 and stats["gone"] == 0 and stats["found"] == 170 and stats["left"] == 30
    assert rr.get("o/r0") == (False, None) and rr.get("o/r30") == (True, row("o/r30"))


def test_a_few_not_found_are_believed(cache, monkeypatch):
    names = [f"o/r{i}" for i in range(200)]
    monkeypatch.setattr(rr, "run_batch", lambda chunk: {n: (None if int(n[3:]) < 3 else row(n)) for n in chunk})
    stats = rr.prefetch(names)                     # the 3 of 4,453 seen on 11-08
    assert "doubted" not in stats and stats["gone"] == 3 and rr.get("o/r0") == (True, None)


def test_a_name_the_batch_did_not_answer_is_left(cache, monkeypatch):
    monkeypatch.setattr(rr, "run_batch", lambda names: {names[0]: row(names[0])})
    stats = rr.prefetch(["a/one", "b/two"])
    assert stats["found"] == 1 and stats["left"] == 1 and rr.get("b/two") == (False, None)


# --- the two places that ask GitHub about a listed repo ------------------------------------

def test_github_row_reads_the_cache_before_asking_github(cache, monkeypatch):
    rr.put("a/b", row("a/b"))
    monkeypatch.setattr(bvl.subprocess, "run", lambda *a, **k: pytest.fail("asked GitHub"))
    assert bvl.github_row("A/B") == row("a/b")


def test_github_row_remembers_the_answer_of_the_first_lookup(cache, monkeypatch):
    calls = []
    monkeypatch.setattr(bvl.subprocess, "run", lambda cmd, **kw: calls.append(cmd) or done(0, json.dumps(REST)))
    first = bvl.github_row("remotion-dev/remotion")
    assert bvl.github_row("remotion-dev/remotion") == first and len(calls) == 1


def test_github_row_remembers_a_missing_repo_but_not_a_failure(cache, monkeypatch):
    answers = iter([done(1, "", "gh: Not Found (HTTP 404)"), done(1, "", "gh: Server Error (HTTP 500)")])
    monkeypatch.setattr(bvl.subprocess, "run", lambda *a, **k: next(answers))
    assert bvl.github_row("gone/x") is None and rr.get("gone/x") == (True, None)
    with pytest.raises(RuntimeError):
        bvl.github_row("flaky/y")
    assert rr.get("flaky/y") == (False, None)


def test_github_row_without_a_cache_file_asks_github_every_time(monkeypatch):
    monkeypatch.delenv(rr.CACHE_ENV, raising=False)
    calls = []
    monkeypatch.setattr(bvl.subprocess, "run", lambda cmd, **kw: calls.append(cmd) or done(0, json.dumps(REST)))
    bvl.github_row("remotion-dev/remotion")
    bvl.github_row("remotion-dev/remotion")
    assert len(calls) == 2


def test_exclude_gone_drops_gone_and_renamed_repos_using_the_cache(cache, page, monkeypatch):
    folder = page(["o/kept", "o/gone", "o/old", "o/new", "o/folder/sub"])
    rr.put("o/kept", row("o/kept"))
    rr.put("o/gone", None)
    rr.put("o/old", row("o/new"))                        # renamed, and the new name is listed too
    rr.put("o/new", row("o/new"))
    monkeypatch.setattr(dvp.subprocess, "run", lambda *a, **k: pytest.fail("asked GitHub"))
    assert sorted(dvp.exclude_gone()) == ["o/gone", "o/old"]
    assert sorted(json.loads((folder / "kinds.json").read_text())["p"]["repos"]) == ["o/folder/sub", "o/kept", "o/new"]
    assert sorted(json.loads((folder / "kw.json").read_text())[0]["match"]["exclude_repos"]) == ["o/gone", "o/old"]


def test_exclude_gone_keeps_a_renamed_repo_whose_new_name_is_not_listed(cache, page, monkeypatch):
    page(["o/old"])
    rr.put("o/old", row("o/new"))
    monkeypatch.setattr(dvp.subprocess, "run", lambda *a, **k: pytest.fail("asked GitHub"))
    assert dvp.exclude_gone() == []


def test_exclude_gone_asks_github_about_a_name_the_cache_lacks(cache, page, monkeypatch):
    page(["o/uncached", "o/fine"])
    answers = {"repos/o/uncached": done(1, "", "gh: Not Found (HTTP 404)"), "repos/o/fine": done(0, "o/fine\n")}
    monkeypatch.setattr(dvp.subprocess, "run", lambda cmd, **kw: answers[cmd[2]])
    assert dvp.exclude_gone() == ["o/uncached"]


# --- the start of a run --------------------------------------------------------------------

def test_start_lookups_prefetches_the_listed_names_of_the_runs_pages_once(tmp_path, monkeypatch):
    kinds = {"p1": {"repos": {"o/a": "x", "O/A": "x", "o/folder/sub": "x"}}, "p2": {"repos": {"o/b": "x"}},
             "not-run": {"repos": {"o/c": "x"}}}
    (tmp_path / "kinds.json").write_text(json.dumps(kinds))
    monkeypatch.setattr(dvp, "KINDS", tmp_path / "kinds.json")
    monkeypatch.setenv(rr.CACHE_ENV, "")                 # not set for this run: start_lookups gives it a file
    asked = []
    monkeypatch.setattr(rr, "prefetch", lambda names: asked.append(list(names)) or {"asked": len(names)})
    dvp.start_lookups(["p1", "p2"])
    assert asked == [["O/A", "o/a", "o/b", "o/folder/sub"]]
    assert os.environ[rr.CACHE_ENV].endswith("rows.jsonl")


def test_a_failed_lookup_batch_does_not_stop_the_run(tmp_path, monkeypatch, capsys):
    (tmp_path / "kinds.json").write_text(json.dumps({"p1": {"repos": {"o/a": "x"}}}))
    monkeypatch.setattr(dvp, "KINDS", tmp_path / "kinds.json")
    monkeypatch.setenv(rr.CACHE_ENV, "")
    monkeypatch.setattr(rr, "prefetch", lambda names: (_ for _ in ()).throw(RuntimeError("gh is missing")))
    dvp.start_lookups(["p1"])
    assert "gh is missing" in capsys.readouterr().out


# --- where the time goes, in the log -------------------------------------------------------

def test_stage_seconds_add_up_per_stage():
    spent, clock = {}, iter([0.0, 2.0, 5.0, 9.0])
    assert dvp.timed(spent, "search", lambda x: x + 1, 1, clock=lambda: next(clock)) == 2
    dvp.timed(spent, "search", lambda: None, clock=lambda: next(clock))
    assert spent == {"search": 6.0}


def test_a_stage_that_raises_is_still_timed():
    spent, clock = {}, iter([0.0, 3.0])

    def boom():
        raise ValueError("x")
    with pytest.raises(ValueError):
        dvp.timed(spent, "list", boom, clock=lambda: next(clock))
    assert spent == {"list": 3.0}


def test_the_stage_line_names_the_page_and_each_stage():
    assert dvp.stage_line("p", {"search": 190.4, "list": 3.6}) == "[p] 194s: search 190, list 4"


def test_run_page_times_every_stage_in_order(tmp_path, monkeypatch):
    fake_jev = ModuleType("jev_client")
    fake_jev.OpenRouter = lambda: object()
    monkeypatch.setitem(sys.modules, "jev_client", fake_jev)
    admitted = {"repo": "o/a", "stars": 60, "verdict": "admit"}
    stubs = {"consistency": lambda: "consistent", "fresh_candidates": lambda: [admitted],
             "admitted": lambda fresh: ([admitted], [admitted]), "describe_zh": lambda r, jev: ("zh", 0.9),
             "add_to_page": lambda names, zh: None, "keep_page_rows": lambda ok: None, "queue_and_grade": lambda names: {},
             "exclude_gone": lambda: [], "rebuild_list": lambda d: "1 repos", "report": lambda *a: None}
    for name, stub in stubs.items():
        monkeypatch.setattr(dvp, name, stub)
    monkeypatch.setattr(dvp, "SLUG", dvp.SLUG)           # run_page sets it; put it back afterwards
    monkeypatch.setattr(dvp.gate, "judge", lambda slug: None)
    monkeypatch.setattr(dvp.gate, "types", lambda slug: None)
    spent = {}
    dvp.run_page("p", tmp_path, tmp_path / "report.md", spent)
    assert list(spent) == ["check", "search", "judge", "describe", "types", "queue", "gone-check", "list"]


def test_main_logs_each_pages_stage_line_even_when_the_page_fails(tmp_path, monkeypatch, capsys):
    started = []

    def fake_run_page(slug, list_dir, part, spent):
        spent["search"] = 5.0
        if slug == "p2":
            raise RuntimeError("boom")
        part.write_text("## p1\n")
    monkeypatch.setattr(sys, "argv", ["daily_video_pass.py", str(tmp_path / "report.md"), "p1=dir1", "p2=dir2"])
    monkeypatch.setattr(dvp, "wait_for_sync", lambda: True)
    monkeypatch.setattr(dvp, "start_lookups", started.append)
    monkeypatch.setattr(dvp, "run_page", fake_run_page)
    assert dvp.main() == 0
    out = capsys.readouterr().out
    assert started == [["p1", "p2"]]
    assert "[p1] 5s: search 5" in out and "[p2] failed: boom" in out and "[p2] 5s: search 5" in out


def test_a_quota_wait_in_the_list_build_reaches_the_log(page, tmp_path, monkeypatch, capsys):
    page(["o/a"])
    monkeypatch.setattr(dvp.gate, "out_dir", lambda slug: tmp_path)
    monkeypatch.setattr(dvp.subprocess, "run", lambda *a, **k: done(0, "1 repos\n", "noise\nGitHub core quota used up; waiting 600s\n"))
    dvp.rebuild_list(tmp_path)
    out = capsys.readouterr().out
    assert "waiting 600s" in out and "noise" not in out


def test_wait_for_quota_says_it_is_waiting(monkeypatch, capsys):
    slept = []
    monkeypatch.setattr(bvl.subprocess, "run", lambda *a, **k: done(0, "1000\n"))
    monkeypatch.setattr(bvl.time, "time", lambda: 900.0)
    monkeypatch.setattr(bvl.time, "sleep", slept.append)
    bvl.wait_for_quota()
    assert slept == [130.0] and "waiting 130s" in capsys.readouterr().err
