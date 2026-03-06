"""Heuristic-based quality analyzer for skills (4→6 dimensions)."""
import json
import logging
import re

from sqlalchemy.orm import Session

from app.models.skill import Skill

logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """Scores skills on 4 quality dimensions using locally available data."""

    def analyze_all(self, db: Session) -> int:
        skills = db.query(Skill).all()
        for skill in skills:
            self._analyze(skill)
        db.commit()
        return len(skills)

    # Section headings that indicate good README structure
    VALUABLE_SECTIONS = [
        r"(?i)^#{1,3}\s*(installation|install|setup|getting started)",
        r"(?i)^#{1,3}\s*(usage|how to use|quick start)",
        r"(?i)^#{1,3}\s*(api|api reference|reference)",
        r"(?i)^#{1,3}\s*(configuration|config|options|settings)",
        r"(?i)^#{1,3}\s*(examples?|demos?)",
        r"(?i)^#{1,3}\s*(contributing|contribute|development)",
        r"(?i)^#{1,3}\s*(license|licensing)",
        r"(?i)^#{1,3}\s*(changelog|changes|releases)",
        r"(?i)^#{1,3}\s*(requirements|prerequisites|dependencies)",
        r"(?i)^#{1,3}\s*(features|capabilities|highlights)",
        r"(?i)^#{1,3}\s*(troubleshooting|faq|known issues)",
    ]

    # Sections that indicate agent-readiness
    AGENT_SECTIONS = {
        "install": r"(?i)^#{1,3}\s*(installation|install|setup|getting started)",
        "tools": r"(?i)^#{1,3}\s*(api|tools?|functions?|endpoints?|commands?|capabilities)",
        "usage": r"(?i)^#{1,3}\s*(usage|how to use|quick start|examples?)",
        "config": r"(?i)^#{1,3}\s*(configuration|config|options|settings|environment)",
    }

    def _analyze(self, skill: Skill) -> None:
        skill.quality_completeness = self._completeness(skill)
        skill.quality_clarity = self._clarity(skill)
        skill.quality_specificity = self._specificity(skill)
        skill.quality_examples = self._examples(skill)

        readme_struct = self._readme_structure(skill)
        skill.readme_structure_score = round(readme_struct, 3)

        agent_ready = self._agent_readiness(skill)
        skill.quality_agent_readiness = round(agent_ready, 3)

        if skill.readme_content:
            # 6-dimension weighted scoring when README content is available
            skill.quality_score = (
                skill.quality_completeness * 0.15
                + skill.quality_clarity * 0.15
                + skill.quality_specificity * 0.15
                + skill.quality_examples * 0.12
                + readme_struct * 0.23
                + agent_ready * 0.20
            ) * 100
        else:
            # 5-dimension scoring without README
            skill.quality_score = (
                skill.quality_completeness * 0.20
                + skill.quality_clarity * 0.20
                + skill.quality_specificity * 0.20
                + skill.quality_examples * 0.20
                + agent_ready * 0.20
            ) * 100

    def _completeness(self, skill: Skill) -> float:
        """How complete is the project? README, description, license, etc."""
        score = 0.0
        desc = skill.description or ""
        readme_sz = skill.readme_size or 0

        # README size
        if readme_sz > 5000:
            score += 0.35
        elif readme_sz > 2000:
            score += 0.25
        elif readme_sz > 500:
            score += 0.15
        elif readme_sz > 0:
            score += 0.05

        # Has description
        if len(desc) > 50:
            score += 0.2
        elif len(desc) > 10:
            score += 0.1

        # Has license
        if skill.license and skill.license not in ("", "NOASSERTION"):
            score += 0.15

        # Has homepage
        if skill.homepage_url:
            score += 0.1

        # Has meaningful stars (indicates community validation)
        if skill.stars >= 100:
            score += 0.2
        elif skill.stars >= 10:
            score += 0.1

        return min(score, 1.0)

    def _clarity(self, skill: Skill) -> float:
        """How clear and well-documented is the project?"""
        score = 0.0
        desc = skill.description or ""

        # Description quality
        if 30 <= len(desc) <= 300:
            score += 0.25  # concise and descriptive
        elif len(desc) > 300:
            score += 0.15  # verbose
        elif len(desc) > 0:
            score += 0.05

        # README exists and is substantial
        readme_sz = skill.readme_size or 0
        if readme_sz > 3000:
            score += 0.3
        elif readme_sz > 1000:
            score += 0.2
        elif readme_sz > 0:
            score += 0.1

        # Has topics (helps discoverability)
        topics = json.loads(skill.topics) if skill.topics else []
        if len(topics) >= 3:
            score += 0.2
        elif len(topics) >= 1:
            score += 0.1

        # Repo name is descriptive (contains hyphen/underscore = multi-word)
        if "-" in skill.repo_name or "_" in skill.repo_name:
            score += 0.15

        # Not a fork (higher originality)
        if skill.forks > 0:
            score += 0.1

        return min(score, 1.0)

    def _specificity(self, skill: Skill) -> float:
        """How focused is the project? Single-purpose is better."""
        score = 0.0

        # Has a primary language (focused codebase)
        if skill.language and skill.language != "":
            score += 0.25

        # Topics count: 2-8 is ideal (focused but descriptive)
        topics = json.loads(skill.topics) if skill.topics else []
        topic_count = len(topics)
        if 2 <= topic_count <= 8:
            score += 0.25
        elif topic_count == 1:
            score += 0.1
        elif topic_count > 8:
            score += 0.05  # too many = unfocused

        # Has a specific category (not uncategorized)
        if skill.category and skill.category != "uncategorized":
            score += 0.2

        # Size: smaller is more focused
        size_kb = skill.repo_size_kb or 0
        if 10 <= size_kb <= 500:
            score += 0.2  # sweet spot
        elif size_kb <= 5000:
            score += 0.1
        # large repos get no bonus

        # Has a clear name pattern (skill, tool, mcp, etc.)
        name_lower = skill.repo_name.lower()
        if any(kw in name_lower for kw in ["skill", "tool", "mcp", "agent", "plugin", "server"]):
            score += 0.1

        return min(score, 1.0)

    def _examples(self, skill: Skill) -> float:
        """Does the project have good examples and usage documentation?"""
        score = 0.0
        desc = (skill.description or "").lower()
        topics = json.loads(skill.topics) if skill.topics else []
        topics_lower = " ".join(topics).lower()

        # Description mentions examples or usage
        if any(kw in desc for kw in ["example", "usage", "demo", "tutorial", "getting started"]):
            score += 0.25

        # Topics mention examples
        if any(kw in topics_lower for kw in ["example", "tutorial", "demo", "starter"]):
            score += 0.15

        # README size suggests examples (larger README = more examples/docs)
        readme_sz = skill.readme_size or 0
        if readme_sz > 5000:
            score += 0.3
        elif readme_sz > 2000:
            score += 0.2
        elif readme_sz > 500:
            score += 0.1

        # Has meaningful commit count (active development suggests documentation)
        if skill.total_commits > 50:
            score += 0.15
        elif skill.total_commits > 10:
            score += 0.1

        # Has contributors (multi-person = better docs usually)
        if skill.contributors_count > 3:
            score += 0.15
        elif skill.contributors_count > 1:
            score += 0.1

        return min(score, 1.0)

    def _agent_readiness(self, skill: Skill) -> float:
        """How ready is this skill for agent/LLM consumption? Returns 0-1.

        Inspired by Anthropic skill-creator evaluation:
        - Functional quality (tool definitions, API docs)
        - Trigger quality (clear description for agent activation)
        - Structural quality (install, config, examples)
        """
        score = 0.0
        content = (skill.readme_content or "")[:10000]
        desc = skill.description or ""
        desc_lower = desc.lower()
        topics = json.loads(skill.topics) if skill.topics else []
        topics_lower = " ".join(topics).lower()
        name_lower = skill.repo_name.lower()

        # 1. Installation ready (max 0.15)
        if content and re.search(self.AGENT_SECTIONS["install"], content, re.MULTILINE):
            score += 0.15
        elif any(kw in desc_lower for kw in ["npm install", "pip install", "cargo install", "brew install"]):
            score += 0.10

        # 2. Tool/API definition documented (max 0.20)
        if content and re.search(self.AGENT_SECTIONS["tools"], content, re.MULTILINE):
            score += 0.20
        elif any(kw in desc_lower for kw in ["tool", "function", "api", "endpoint", "server"]):
            score += 0.10

        # 3. Usage examples (max 0.20)
        has_usage_section = bool(content and re.search(self.AGENT_SECTIONS["usage"], content, re.MULTILINE))
        code_blocks = len(re.findall(r"```", content)) // 2 if content else 0
        if has_usage_section:
            score += 0.10
        if code_blocks >= 2:
            score += 0.10
        elif code_blocks >= 1:
            score += 0.05

        # 4. Configuration documented (max 0.15)
        if content and re.search(self.AGENT_SECTIONS["config"], content, re.MULTILINE):
            score += 0.15
        elif any(kw in desc_lower for kw in [".env", "config", "settings"]):
            score += 0.08

        # 5. Skill/MCP compliance (max 0.15)
        compliance_text = f"{content} {topics_lower} {name_lower}"
        if any(kw in compliance_text for kw in ["skill.md", "mcp.json", "tool-config"]):
            score += 0.10
        if any(kw in name_lower for kw in ["skill", "mcp", "tool", "agent", "server"]):
            score += 0.05

        # 6. Description quality for agent activation (max 0.15)
        if desc:
            # Action-oriented description (starts with verb or uses "for"/"that"/"to")
            action_words = ["a ", "an ", "the ", "create", "build", "generate", "manage",
                           "search", "fetch", "monitor", "analyze", "convert", "provide"]
            if any(desc_lower.startswith(w) for w in action_words) or \
               any(f" {w} " in f" {desc_lower} " for w in ["for", "that", "to"]):
                score += 0.10
            # Concise and clear (30-200 chars is ideal)
            if 30 <= len(desc) <= 200:
                score += 0.05
            elif len(desc) > 200:
                score += 0.02

        return min(score, 1.0)

    def _readme_structure(self, skill: Skill) -> float:
        """Analyze README content for structural quality. Returns 0-1."""
        content = skill.readme_content
        if not content:
            return 0.0

        score = 0.0

        # Section detection (max 0.4): each valuable section +0.04, up to 10
        sections_found = sum(
            1 for pattern in self.VALUABLE_SECTIONS
            if re.search(pattern, content, re.MULTILINE)
        )
        score += min(sections_found * 0.04, 0.4)

        # Code blocks (max 0.25)
        code_blocks = len(re.findall(r"```", content)) // 2
        if code_blocks >= 3:
            score += 0.25
        elif code_blocks >= 1:
            score += 0.15
        elif "`" in content:
            score += 0.05

        # Badges (max 0.1)
        if any(re.search(p, content) for p in [r"\[!\[", r"shields\.io", r"img\.shields"]):
            score += 0.1

        # Table of contents indicator (max 0.1)
        toc_count = sum(1 for p in [r"(?i)table of contents", r"(?i)## contents", r"\[.*\]\(#"]
                        if re.search(p, content))
        if toc_count >= 2:
            score += 0.1
        elif toc_count >= 1:
            score += 0.05

        # Length adequacy (max 0.15)
        length = len(content)
        if length >= 3000:
            score += 0.15
        elif length >= 1000:
            score += 0.1
        elif length >= 300:
            score += 0.05

        return min(score, 1.0)
