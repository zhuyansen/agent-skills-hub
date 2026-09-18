"""Pure fetch decisions extracted from scheduler/jobs.py."""
from app.services.sync_selection import select_new_repo_readme_targets, with_push_filter

PUSHED = " pushed:>2026-09-18T01:00:00Z"


def test_ordinary_queries_get_the_incremental_filter():
    assert with_push_filter("mcp-server in:name,topics", PUSHED) == "mcp-server in:name,topics" + PUSHED


def test_no_filter_on_a_full_sync():
    assert with_push_filter("mcp-server in:name,topics", "") == "mcp-server in:name,topics"


def test_creation_bounded_queries_skip_the_filter():
    # The Jev wave was created 09-16/17; most of it was pushed before the query existed.
    q = "jev in:name,description,topics created:>=2026-09-15"
    assert with_push_filter(q, PUSHED) == q


def repo(stars):
    return {"stargazers_count": stars}


def test_only_repos_not_yet_in_skills_are_targets():
    all_repos = {"a/known": repo(900), "b/new": repo(10)}
    assert select_new_repo_readme_targets(all_repos, known_names={"a/known"}) == {"b/new"}


def test_cap_keeps_the_most_starred_new_repos():
    all_repos = {"a/one": repo(5), "b/two": repo(2635), "c/three": repo(914), "d/four": repo(None)}
    assert select_new_repo_readme_targets(all_repos, known_names=set(), limit=2) == {"b/two", "c/three"}


def test_missing_star_counts_sort_last_and_do_not_crash():
    all_repos = {"a/nostars": {}, "b/some": repo(3)}
    assert select_new_repo_readme_targets(all_repos, known_names=set(), limit=1) == {"b/some"}
