"""Infer platform compatibility from skill metadata with negation + file detection."""
import json
import logging
import re
from typing import List

from sqlalchemy.orm import Session

from app.models.skill import Skill

logger = logging.getLogger(__name__)


class PlatformInferrer:
    """Infers which platforms/runtimes a skill is compatible with."""

    LANGUAGE_MAP = {
        "Python": "python",
        "TypeScript": "node",
        "JavaScript": "node",
        "Go": "go",
        "Rust": "rust",
        "Ruby": "ruby",
        "Java": "java",
        "C#": "dotnet",
        "Shell": "cli",
        "Bash": "cli",
    }

    TOPIC_KEYWORDS = {
        "docker": "docker",
        "kubernetes": "k8s",
        "aws": "aws",
        "cli": "cli",
        "vscode": "vscode",
        "browser": "browser",
        "web": "browser",
        "chrome": "browser",
        "claude": "claude-code",
        "claude-code": "claude-code",
        "claude-skill": "claude-code",
        "codex": "codex",
        "openai-codex": "codex",
        "codex-skill": "codex",
        "gemini": "gemini",
        "mcp": "mcp",
        "model-context-protocol": "mcp",
        "mcp-server": "mcp",
    }

    NEGATION_PATTERNS = [
        r"not\s+compatible\s+with\s+(\w+)",
        r"without\s+(\w+)\s+support",
        r"no\s+(\w+)\s+support",
        r"doesn'?t\s+support\s+(\w+)",
    ]

    FILE_HINTS = {
        "dockerfile": "docker",
        "docker-compose": "docker",
        "mcp.json": "mcp",
        "package.json": "node",
        "pyproject.toml": "python",
        "cargo.toml": "rust",
        "go.mod": "go",
        "makefile": "cli",
    }

    def infer_all(self, db: Session, batch_size: int = 500,
                  repo_names: list[str] | None = None) -> int:
        """Infer platforms for skills. If repo_names given, only those."""
        if repo_names:
            skills = (db.query(Skill)
                      .filter(Skill.repo_full_name.in_(repo_names))
                      .all())
        else:
            skills = db.query(Skill).all()
        for i, skill in enumerate(skills):
            platforms = self._infer(skill)
            skill.platforms = json.dumps(platforms)
            if (i + 1) % batch_size == 0:
                db.commit()
        db.commit()
        logger.info("Platform inference: %d skills", len(skills))
        return len(skills)

    def _infer(self, skill: Skill) -> List[str]:
        platforms = set()

        # From language
        if skill.language and skill.language in self.LANGUAGE_MAP:
            platforms.add(self.LANGUAGE_MAP[skill.language])

        # From topics
        topics = json.loads(skill.topics) if skill.topics else []
        for topic in topics:
            topic_lower = topic.lower()
            for keyword, platform in self.TOPIC_KEYWORDS.items():
                if keyword in topic_lower:
                    platforms.add(platform)

        # From description
        desc_lower = (skill.description or "").lower()
        for keyword, platform in self.TOPIC_KEYWORDS.items():
            if keyword in desc_lower:
                platforms.add(platform)

        # From repo name
        name_lower = skill.repo_name.lower()
        for keyword, platform in self.TOPIC_KEYWORDS.items():
            if keyword in name_lower:
                platforms.add(platform)

        # File hints from description + README preview
        readme_preview = (skill.readme_content or "")[:2000].lower() if hasattr(skill, "readme_content") and skill.readme_content else ""
        combined_text = f"{desc_lower} {readme_preview}"
        for file_hint, platform in self.FILE_HINTS.items():
            if file_hint in combined_text:
                platforms.add(platform)

        # Apply negation: remove platforms explicitly excluded in description
        for pattern in self.NEGATION_PATTERNS:
            for match in re.findall(pattern, desc_lower):
                match_lower = match.lower()
                for keyword, platform in self.TOPIC_KEYWORDS.items():
                    if match_lower in keyword or keyword in match_lower:
                        platforms.discard(platform)
                for lang, platform in self.LANGUAGE_MAP.items():
                    if match_lower == lang.lower():
                        platforms.discard(platform)

        return sorted(platforms)
