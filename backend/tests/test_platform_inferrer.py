"""Unit tests for PlatformInferrer."""

import json
from types import SimpleNamespace

from app.services.platform_inferrer import PlatformInferrer


def _skill(**overrides):
    """A minimal Skill-like object with the fields the inferrer reads."""
    base = {
        "language": None,
        "topics": "[]",
        "description": "",
        "repo_name": "repo",
        "readme_content": None,
    }
    base.update(overrides)
    if isinstance(base["topics"], list):
        base["topics"] = json.dumps(base["topics"])
    return SimpleNamespace(**base)


def _infer(**overrides):
    return PlatformInferrer()._infer(_skill(**overrides))


class TestWholeWordKeywords:
    def test_websites_is_not_a_browser(self):
        assert "browser" not in _infer(description="Audit websites and check links.")

    def test_web_on_its_own_still_counts(self):
        assert "browser" in _infer(topics=["web", "seo"])

    def test_mcp_client_is_not_a_cli(self):
        assert "cli" not in _infer(topics=["mcp-client"])

    def test_cli_on_its_own_still_counts(self):
        assert "cli" in _infer(topics=["gemini-cli"])

    def test_laws_is_not_aws(self):
        assert "aws" not in _infer(description="Track privacy laws across regions.")

    def test_longer_keywords_still_match_inside_words(self):
        assert "docker" in _infer(topics=["docker-compose"])
        assert "mcp" in _infer(topics=["fastmcp"])


class TestOptimizationTargetTopics:
    def test_engine_seo_topics_are_not_runtimes(self):
        platforms = _infer(topics=["gemini-seo", "chatgpt-seo", "perplexity-geo", "claude-code-plugin"])
        assert platforms == ["claude-code"]

    def test_engine_topics_without_suffix_still_count(self):
        assert "gemini" in _infer(topics=["gemini"])


class TestAkiiPlugin:
    def test_claude_code_only(self):
        platforms = _infer(
            repo_name="akii-seo-ai-search-optimizer",
            description="Free MIT-licensed Claude Code plugin for SEO, AEO and GEO. Audit websites, "
                        "plan content, generate schema and check links. Includes 12 skills, 5 agents and 3 commands.",
            topics=["aeo", "ai-seo", "ai-visibility", "chatgpt-seo", "claude-code-plugin", "claude-plugin",
                    "claude-seo", "gemini-seo", "geo", "llms-txt", "perplexity-seo", "princeton-geo",
                    "schema", "seo"],
        )
        assert platforms == ["claude-code"]
