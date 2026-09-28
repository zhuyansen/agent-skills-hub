"""Estimate token consumption for skills."""
import logging

from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.services.skill_batches import skill_batches

logger = logging.getLogger(__name__)

# Claude 200K context window
CLAUDE_CONTEXT_WINDOW = 200_000


class TokenEstimator:
    """Estimates token count based on repo size, README size, and language."""

    CODE_TOKENS_PER_KB = 150
    README_TOKENS_PER_CHAR = 0.25
    CODE_RATIO = 0.6

    # estimated_tokens models the *context cost of adopting the skill* — what an
    # agent actually loads: the SKILL.md / README plus, at most, a few relevant
    # code files. It is NOT the token count of the entire repository. Without
    # these caps a 100K-star monorepo (e.g. openclaw, ~690MB) reported ~103M
    # "context tokens", which is meaningless: you load the skill, not the repo.
    CODE_KB_CAP = 200            # count at most ~200KB of code toward context
    CONTEXT_WINDOW = 200_000     # nothing can cost more than Claude's window

    # Language-specific token density coefficients
    LANG_COEFF = {
        "Python": 0.8, "TypeScript": 1.0, "JavaScript": 1.0,
        "Go": 0.87, "Rust": 1.33, "Ruby": 0.8, "Java": 1.1,
        "Kotlin": 1.0, "C#": 1.1, "C": 0.9, "C++": 1.05,
        "Shell": 0.6, "Bash": 0.6, "PHP": 1.0, "Swift": 0.95,
    }

    # Estimated non-code file ratio by ecosystem
    BINARY_OVERHEAD = {
        "Python": 0.10, "TypeScript": 0.25, "JavaScript": 0.30,
        "Go": 0.05, "Rust": 0.10, "Ruby": 0.10, "Java": 0.20,
        "Shell": 0.05,
    }

    def estimate_all(self, db: Session, batch_size: int = 500,
                     repo_names: list[str] | None = None) -> int:
        """Estimate tokens for skills. If repo_names given, only those."""
        count = 0
        for batch in skill_batches(db, repo_names, batch_size):
            for skill in batch:
                skill.estimated_tokens = self._estimate(skill)
            db.commit()
            count += len(batch)
        logger.info("Token estimation: %d skills", count)
        return count

    def _estimate(self, skill: Skill) -> int:
        # Cap repo size first: only a skill's own files plausibly enter context,
        # not an entire monorepo. This is what kills the runaway estimates.
        repo_kb = min(skill.repo_size_kb or 0, self.CODE_KB_CAP)
        readme_chars = skill.readme_size or 0
        language = skill.language or ""

        lang_coeff = self.LANG_COEFF.get(language, 1.0)
        overhead = self.BINARY_OVERHEAD.get(language, 0.15)
        effective_ratio = self.CODE_RATIO * (1 - overhead)

        code_tokens = int(repo_kb * self.CODE_TOKENS_PER_KB * lang_coeff * effective_ratio)
        readme_tokens = int(readme_chars * self.README_TOKENS_PER_CHAR)

        # README/SKILL.md is the real driver; final value can't exceed the window.
        return min(code_tokens + readme_tokens, self.CONTEXT_WINDOW)
