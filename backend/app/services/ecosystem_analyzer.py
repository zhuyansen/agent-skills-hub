"""Ecosystem and dependency analysis for composability signals."""
import json
import logging
import re
from collections import Counter
from typing import Dict, List, Set, Tuple

from app.models.skill import Skill

logger = logging.getLogger(__name__)


class EcosystemAnalyzer:
    """Analyzes topic co-occurrence and framework dependencies across skills."""

    FRAMEWORK_PATTERNS = {
        "langchain": "langchain",
        "crewai": "crewai",
        "crew-ai": "crewai",
        "autogen": "autogen",
        "fastapi": "fastapi",
        "express": "express",
        "next.js": "nextjs",
        "nextjs": "nextjs",
        "react": "react",
        "vue": "vue",
        "django": "django",
        "flask": "flask",
        "spring": "spring",
        "openai": "openai",
        "anthropic": "anthropic",
        "ollama": "ollama",
        "huggingface": "huggingface",
        "transformers": "huggingface",
        "pytorch": "pytorch",
        "tensorflow": "tensorflow",
        "supabase": "supabase",
        "prisma": "prisma",
        "vercel": "vercel",
        "cloudflare": "cloudflare",
        "boto3": "aws",
        "selenium": "selenium",
        "playwright": "playwright",
        "puppeteer": "puppeteer",
        "streamlit": "streamlit",
        "gradio": "gradio",
    }

    def __init__(self) -> None:
        self._topic_counts: Counter = Counter()
        self._skill_frameworks: Dict[int, Set[str]] = {}
        self._skill_rare_topics: Dict[int, Set[str]] = {}

    def build_index(self, skills: List[Skill], rare_threshold: int = 50) -> None:
        """Build topic co-occurrence and framework index from all skills."""
        all_topic_lists: List[Tuple[int, List[str]]] = []
        for skill in skills:
            topics = json.loads(skill.topics) if skill.topics else []
            topics_lower = [t.lower() for t in topics]
            all_topic_lists.append((skill.id, topics_lower))
            for t in topics_lower:
                self._topic_counts[t] += 1

        # Identify rare topics per skill
        for skill_id, topics in all_topic_lists:
            rare = {t for t in topics if self._topic_counts[t] < rare_threshold}
            if rare:
                self._skill_rare_topics[skill_id] = rare

        # Detect frameworks from description + readme
        for skill in skills:
            desc = (skill.description or "").lower()
            readme_preview = (skill.readme_content or "")[:3000].lower() if skill.readme_content else ""
            combined = f"{desc} {readme_preview}"

            frameworks: Set[str] = set()
            for pattern, canonical in self.FRAMEWORK_PATTERNS.items():
                if re.search(r"\b" + re.escape(pattern) + r"\b", combined):
                    frameworks.add(canonical)

            if frameworks:
                self._skill_frameworks[skill.id] = frameworks

        logger.info(
            "Ecosystem index: %d unique topics, %d with frameworks, %d with rare topics",
            len(self._topic_counts),
            len(self._skill_frameworks),
            len(self._skill_rare_topics),
        )

    def shared_rare_topics_score(self, skill_id_a: int, skill_id_b: int) -> float:
        """Score based on shared rare topics. Range 0-1."""
        rare_a = self._skill_rare_topics.get(skill_id_a, set())
        rare_b = self._skill_rare_topics.get(skill_id_b, set())
        if not rare_a or not rare_b:
            return 0.0
        shared = rare_a & rare_b
        if not shared:
            return 0.0
        return min(len(shared) * 0.3, 1.0)

    def shared_framework_score(self, skill_id_a: int, skill_id_b: int) -> float:
        """Score based on shared framework dependencies. Range 0-1."""
        fw_a = self._skill_frameworks.get(skill_id_a, set())
        fw_b = self._skill_frameworks.get(skill_id_b, set())
        if not fw_a or not fw_b:
            return 0.0
        shared = fw_a & fw_b
        if not shared:
            return 0.0
        return min(len(shared) * 0.4, 1.0)

    def get_frameworks(self, skill_id: int) -> Set[str]:
        """Return detected frameworks for a skill."""
        return self._skill_frameworks.get(skill_id, set())
