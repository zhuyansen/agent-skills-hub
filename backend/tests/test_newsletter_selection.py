"""Unit tests for the newsletter "New This Week" dedup.

This logic shipped a duplicate-riddled issue once (subscriber 秋秋 caught it,
2026-06) — these tests pin the fixed behavior. Pure-function tests, no DB.
"""
from types import SimpleNamespace

from newsletter_runner import select_new_skills


def _skill(full_name, desc="", author=None, name=None):
    owner, _, repo = full_name.partition("/")
    return SimpleNamespace(
        repo_full_name=full_name,
        author_name=author if author is not None else owner,
        repo_name=name if name is not None else repo,
        description=desc,
    )


def test_same_author_same_desc_merges():
    # A rename by one author: keep the first (highest-star, pool is star-desc).
    pool = [
        _skill("alice/videocut", "cut videos with AI"),
        _skill("alice/videocut-pro", "cut videos with AI"),
    ]
    picked = select_new_skills(pool)
    assert [s.repo_full_name for s in picked] == ["alice/videocut"]


def test_cross_author_fork_same_name_same_desc_merges():
    pool = [
        _skill("alice/gini-agent", "an agent for gini"),
        _skill("bob/gini-agent", "an agent for gini"),
    ]
    picked = select_new_skills(pool)
    assert [s.repo_full_name for s in picked] == ["alice/gini-agent"]


def test_different_tools_sharing_generic_desc_are_kept():
    # desc matches but neither author nor repo name does → genuinely different.
    pool = [
        _skill("alice/scraper", "MCP server"),
        _skill("bob/mailer", "MCP server"),
    ]
    picked = select_new_skills(pool)
    assert len(picked) == 2


def test_empty_desc_never_over_merges():
    pool = [
        _skill("alice/tool-a", ""),
        _skill("bob/tool-b", ""),
        _skill("alice/tool-a", ""),  # true duplicate row
    ]
    picked = select_new_skills(pool)
    assert [s.repo_full_name for s in picked] == ["alice/tool-a", "bob/tool-b"]


def test_desc_compare_is_case_insensitive_and_trimmed():
    pool = [
        _skill("alice/x", "  Cut Videos With AI "),
        _skill("alice/y", "cut videos with ai"),
    ]
    picked = select_new_skills(pool)
    assert len(picked) == 1


def test_limit_respected_and_order_preserved():
    pool = [_skill(f"a{i}/tool{i}", f"desc {i}") for i in range(30)]
    picked = select_new_skills(pool, limit=20)
    assert len(picked) == 20
    assert picked[0].repo_full_name == "a0/tool0"  # star-desc order kept
