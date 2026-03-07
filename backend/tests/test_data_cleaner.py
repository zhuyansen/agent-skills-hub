"""Unit tests for DataCleaner."""

import json
from datetime import datetime, timezone

from app.services.data_cleaner import DataCleaner


def _make_repo(**overrides):
    """Create a minimal GitHub API repo-like dict."""
    base = {
        "full_name": "owner/repo",
        "name": "repo",
        "html_url": "https://github.com/owner/repo",
        "description": "A test repo",
        "homepage": "",
        "owner": {"login": "owner", "avatar_url": "https://example.com/avatar.png"},
        "stargazers_count": 10,
        "forks_count": 2,
        "open_issues_count": 1,
        "watchers_count": 8,
        "language": "Python",
        "topics": ["mcp", "ai"],
        "license": {"spdx_id": "MIT"},
        "size": 150,
        "created_at": "2024-01-01T00:00:00Z",
        "pushed_at": "2024-06-01T00:00:00Z",
        "_owner_followers": 50,
        "_total_issues": 10,
        "_total_commits": 30,
        "_contributors_count": 3,
    }
    base.update(overrides)
    return base


class TestProcess:
    def test_basic_processing(self):
        cleaner = DataCleaner()
        result = cleaner.process([_make_repo()])
        assert len(result) == 1
        assert result[0]["repo_full_name"] == "owner/repo"

    def test_deduplication(self):
        cleaner = DataCleaner()
        repo = _make_repo()
        result = cleaner.process([repo, repo, repo])
        assert len(result) == 1

    def test_skips_empty_full_name(self):
        cleaner = DataCleaner()
        result = cleaner.process([_make_repo(full_name="")])
        assert len(result) == 0

    def test_multiple_unique_repos(self):
        cleaner = DataCleaner()
        repos = [
            _make_repo(full_name="a/one", name="one"),
            _make_repo(full_name="b/two", name="two"),
        ]
        result = cleaner.process(repos)
        assert len(result) == 2


class TestCleanSingle:
    def test_field_mapping(self):
        cleaner = DataCleaner()
        result = cleaner.process([_make_repo()])[0]
        assert result["stars"] == 10
        assert result["forks"] == 2
        assert result["author_name"] == "owner"
        assert result["language"] == "Python"
        assert result["license"] == "MIT"
        assert result["repo_size_kb"] == 150

    def test_description_truncated_to_500(self):
        cleaner = DataCleaner()
        long_desc = "x" * 600
        result = cleaner.process([_make_repo(description=long_desc)])[0]
        assert len(result["description"]) == 500

    def test_null_description(self):
        cleaner = DataCleaner()
        result = cleaner.process([_make_repo(description=None)])[0]
        assert result["description"] == ""

    def test_topics_json_serialized(self):
        cleaner = DataCleaner()
        result = cleaner.process([_make_repo(topics=["a", "b"])])[0]
        assert json.loads(result["topics"]) == ["a", "b"]

    def test_missing_owner(self):
        cleaner = DataCleaner()
        result = cleaner.process([_make_repo(owner=None)])[0]
        assert result["author_name"] == "unknown"

    def test_missing_license(self):
        cleaner = DataCleaner()
        result = cleaner.process([_make_repo(license=None)])[0]
        assert result["license"] == ""


class TestClassify:
    def test_mcp_server(self):
        cleaner = DataCleaner()
        repo = _make_repo(full_name="user/mcp-server-git", topics=["mcp"])
        result = cleaner.process([repo])[0]
        assert result["category"] == "mcp-server"

    def test_claude_skill(self):
        cleaner = DataCleaner()
        repo = _make_repo(full_name="user/my-claude-skill", topics=["claude-skill"])
        result = cleaner.process([repo])[0]
        assert result["category"] == "claude-skill"

    def test_agent_tool(self):
        cleaner = DataCleaner()
        repo = _make_repo(
            full_name="user/agent-tool-x",
            description="An AI agent tool",
            topics=["agent-tool"],
        )
        result = cleaner.process([repo])[0]
        assert result["category"] == "agent-tool"

    def test_uncategorized_fallback(self):
        cleaner = DataCleaner()
        repo = _make_repo(
            full_name="user/random-project",
            description="Nothing special",
            topics=["web"],
        )
        result = cleaner.process([repo])[0]
        assert result["category"] == "uncategorized"


class TestCategorizeSize:
    def test_unknown(self):
        assert DataCleaner._categorize_size(0) == "unknown"

    def test_micro(self):
        assert DataCleaner._categorize_size(30) == "micro"

    def test_small(self):
        assert DataCleaner._categorize_size(200) == "small"

    def test_medium(self):
        assert DataCleaner._categorize_size(3000) == "medium"

    def test_large(self):
        assert DataCleaner._categorize_size(10000) == "large"


class TestInferProjectType:
    def test_mcp_server_type(self):
        cleaner = DataCleaner()
        repo = _make_repo(full_name="user/mcp-server", topics=["mcp"])
        result = cleaner.process([repo])[0]
        assert result["project_type"] == "mcp-server"

    def test_agent_framework(self):
        cleaner = DataCleaner()
        repo = _make_repo(
            full_name="user/big-framework",
            description="An agent framework for orchestration",
            topics=["uncategorized-topic"],
            stargazers_count=10000,
        )
        result = cleaner.process([repo])[0]
        assert result["project_type"] == "agent-framework"

    def test_skill_in_name(self):
        cleaner = DataCleaner()
        repo = _make_repo(
            full_name="user/my-skill-lib",
            description="A library",
            topics=["lib"],
        )
        result = cleaner.process([repo])[0]
        assert result["project_type"] == "skill"


class TestParseDatetime:
    def test_valid_iso(self):
        dt = DataCleaner._parse_dt("2024-01-15T10:30:00Z")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.tzinfo is not None

    def test_none_input(self):
        assert DataCleaner._parse_dt(None) is None

    def test_empty_string(self):
        assert DataCleaner._parse_dt("") is None

    def test_invalid_format(self):
        assert DataCleaner._parse_dt("not-a-date") is None
