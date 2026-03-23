import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DataCleaner:
    """Normalizes raw GitHub API responses into Skill-ready dicts."""

    # ── Primary keyword matching (checked first via substring in searchable) ──
    CATEGORY_KEYWORDS: Dict[str, List[str]] = {
        "mcp-server": [
            "mcp", "model-context-protocol", "claude-mcp", "mcp-server",
            "mcp-tool", "mcp-client", "mcp-plugin",
        ],
        "claude-skill": [
            "claude-skill", "claude-tool", "claude skill",
            "claude-code skill", "claude code skill",
            "claude code tool", "claude code template",
            "claude code hook", "claude code config",
            "for claude code", "claude code usage",
            "claude code best practice", "claude code monitor",
            "claude code agent", "claude code cli",
            "claude code workflow", "claude code custom",
            "claude desktop",
        ],
        "codex-skill": [
            "codex", "openai-codex", "codex-skill", "codex skill",
            "openclaw skill", "openclaw plugin", "openclaw-skill",
        ],
        "agent-tool": [
            "agent-tool", "ai-agent", "langchain-tool", "crewai-tool",
            "agent-framework", "agent-skill", "agent skill",
            "agent platform", "agent sdk", "agent runtime",
            "agent harness", "multi-agent", "multi agent",
            "agentic framework", "agent orchestrat",
            "autonomous agent", "coding agent",
            "agent infrastructure", "agentic coding",
            "agent workflow", "agent builder", "ai agent",
            "agent-native", "agentic ai",
        ],
        "youmind-plugin": ["youmind"],
        "llm-plugin": [
            "llm-tool", "llm-plugin", "llm-extension",
            "llm framework", "llm library",
        ],
        "ai-skill": [
            "ai-skill", "ai skill", "cursor-skill", "windsurf-skill",
            "antigravity skill", "antigravity-skill",
            "cursor rules", "cursor rule", "vibe-coding", "vibe coding",
        ],
    }

    # ── Topic-based classification (checked after primary keywords) ──
    TOPIC_CATEGORY_MAP: Dict[str, str] = {
        # Exact topic → category
        "mcp": "mcp-server",
        "model-context-protocol": "mcp-server",
        "mcp-server": "mcp-server",
        "mcp-servers": "mcp-server",
        "claude-code-skill": "claude-skill",
        "claude-skill": "claude-skill",
        "claudecode": "claude-skill",
        "claude-code": "claude-skill",  # broad: claude-code topic → claude-skill
        "anthropic-claude": "claude-skill",
        "claude-ai": "claude-skill",
        "codex-skill": "codex-skill",
        "openclaw-skill": "codex-skill",
        "openclaw": "codex-skill",
        "clawdbot": "codex-skill",
        "agent-framework": "agent-tool",
        "agentic-ai": "agent-tool",
        "llm-agent": "agent-tool",
        "llm-agents": "agent-tool",
        "multi-agent": "agent-tool",
        "autonomous-agent": "agent-tool",
        "agent-tool": "agent-tool",
        "agent-sdk": "agent-tool",
        "agentic": "agent-tool",
        "agent-workflow": "agent-tool",
        "ai-agents": "agent-tool",
        "multiagent": "agent-tool",
        "agent-platform": "agent-tool",
        "ai-tools": "agent-tool",
        "cursor-skill": "ai-skill",
        "windsurf-skill": "ai-skill",
        "vibe-coding": "ai-skill",
        "cursor-rules": "ai-skill",
        "ai-coding": "ai-skill",
        "llm-tool": "llm-plugin",
        "llm-plugin": "llm-plugin",
        "llm-framework": "llm-plugin",
    }

    # ── Broad description-based AI detection (last resort) ──
    AI_KEYWORDS = [
        "ai", "llm", "gpt", "openai", "anthropic", "claude",
        "machine learning", "deep learning", "language model",
        "chatgpt", "gemini", "deepseek", "ollama", "inference",
        "embedding", "vector", "rag", "retrieval", "fine-tun",
    ]
    TOOL_KEYWORDS = [
        "tool", "framework", "library", "sdk", "platform",
        "toolkit", "system", "engine", "service", "application",
        "pipeline", "workflow", "suite", "client",
    ]

    def process(self, raw_repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean, deduplicate, and categorize a batch of raw repo data."""
        seen: set[str] = set()
        results: List[Dict[str, Any]] = []

        for repo in raw_repos:
            full_name = repo.get("full_name", "")
            if not full_name or full_name in seen:
                continue
            seen.add(full_name)

            cleaned = self._clean_single(repo)
            if cleaned:
                results.append(cleaned)

        logger.info("Cleaned %d repos from %d raw entries", len(results), len(raw_repos))
        return results

    def _clean_single(self, repo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform a single raw repo dict into a Skill-ready dict."""
        owner = repo.get("owner") or {}
        return {
            "repo_full_name": repo.get("full_name", ""),
            "repo_name": repo.get("name", ""),
            "repo_url": repo.get("html_url", ""),
            "description": (repo.get("description") or "").strip()[:500],
            "homepage_url": repo.get("homepage") or "",
            "author_name": owner.get("login", "unknown"),
            "author_avatar_url": owner.get("avatar_url", ""),
            "author_followers": repo.get("_owner_followers", 0),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "open_issues": repo.get("open_issues_count", 0),
            "total_issues": repo.get("_total_issues", 0),
            "watchers": repo.get("watchers_count", 0),
            "total_commits": repo.get("_total_commits", 0),
            "contributors_count": repo.get("_contributors_count", 0),
            "created_at": self._parse_dt(repo.get("created_at")),
            "last_commit_at": self._parse_dt(repo.get("pushed_at")),
            "pushed_at": self._parse_dt(repo.get("pushed_at")),
            "category": self._classify(repo),
            "language": repo.get("language") or "",
            "topics": json.dumps(repo.get("topics") or []),
            "license": (repo.get("license") or {}).get("spdx_id", ""),
            "repo_size_kb": repo.get("size", 0),
            "size_category": self._categorize_size(repo.get("size", 0)),
            "project_type": self._infer_project_type(repo),
            "is_official": self._is_official(repo),
        }

    @staticmethod
    def _categorize_size(size_kb: int) -> str:
        """Categorize repo by size in KB."""
        if size_kb <= 0:
            return "unknown"
        if size_kb <= 50:
            return "micro"
        if size_kb <= 500:
            return "small"
        if size_kb <= 5000:
            return "medium"
        return "large"

    def _classify(self, repo: Dict[str, Any]) -> str:
        """Assign category based on multi-pass keyword matching.

        Pass 1: Primary keyword matching in combined searchable text.
        Pass 2: Exact topic matching via TOPIC_CATEGORY_MAP.
        Pass 3: Broad AI + tool detection from description.
        """
        description = (repo.get("description") or "").lower()
        full_name = repo.get("full_name", "").lower()
        topics = [t.lower() for t in (repo.get("topics") or [])]
        searchable = f"{full_name} {description} {' '.join(topics)}"

        # Pass 1: Primary keyword matching (fastest, most specific)
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in searchable for kw in keywords):
                return category

        # Pass 2: Exact topic matching
        for topic in topics:
            if topic in self.TOPIC_CATEGORY_MAP:
                return self.TOPIC_CATEGORY_MAP[topic]

        # Pass 3: Broad AI + tool detection → agent-tool
        has_ai = any(kw in description for kw in self.AI_KEYWORDS)
        has_tool = any(kw in description for kw in self.TOOL_KEYWORDS)
        if has_ai and has_tool:
            return "agent-tool"

        return "uncategorized"

    OFFICIAL_ORGS = {"anthropics", "modelcontextprotocol", "openai", "microsoft", "google"}

    @staticmethod
    def _is_official(repo: Dict[str, Any]) -> bool:
        """Check if repo belongs to an official org."""
        owner = (repo.get("owner") or {}).get("login", "").lower()
        return owner in DataCleaner.OFFICIAL_ORGS

    def _infer_project_type(self, repo: Dict[str, Any]) -> str:
        """Infer project type from category, name, topics, and description."""
        category = self._classify(repo)

        # Direct category mapping
        category_map = {
            "mcp-server": "mcp-server",
            "claude-skill": "claude-skill",
            "codex-skill": "codex-skill",
            "agent-tool": "agent-tool",
            "llm-plugin": "llm-plugin",
            "youmind-plugin": "llm-plugin",
            "ai-skill": "skill",
        }
        if category in category_map:
            return category_map[category]

        # Check for agent frameworks (large, well-known projects)
        searchable = " ".join([
            repo.get("full_name", ""),
            repo.get("description") or "",
            " ".join(repo.get("topics") or []),
        ]).lower()
        stars = repo.get("stargazers_count", 0)

        if stars > 5000 and any(kw in searchable for kw in [
            "framework", "platform", "workflow", "orchestrat", "automation"
        ]):
            return "agent-framework"

        # Check name/topics for skill keyword
        name = repo.get("name", "").lower()
        if "skill" in name or "skill" in searchable:
            return "skill"

        return "tool"

    @staticmethod
    def _parse_dt(value: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 datetime string from GitHub."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
