import json
import logging
import math
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.services.platform_inferrer import PlatformInferrer
from app.services.quality_analyzer import QualityAnalyzer
from app.services.token_estimator import TokenEstimator

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Computes a 0-100 quality score for each skill.

    v3 improvements (inspired by SkillsBench paper, arXiv:2602.12670):
    - Domain-aware scoring: specialized domains (healthcare, manufacturing, etc.)
      benefit most from Skills (+51.9pp healthcare vs +4.5pp software engineering)
    - Quality weight increased: paper shows skill quality is the #1 predictor
    - Platform diversity bonus: paper shows cross-harness portability matters
    - Log normalization for stars/forks/followers/commits (reduces outlier dominance)
    - Exponential time decay for recency (smooth curve instead of step function)
    - Momentum uses z-score instead of min-max (better distribution)
    """

    WEIGHTS = {
        "stars": 0.15,           # reduced from 0.18: paper shows stars != quality
        "forks": 0.08,           # reduced from 0.10
        "author_followers": 0.06,  # reduced from 0.08
        "issue_resolution": 0.10,
        "commits": 0.08,        # reduced from 0.10
        "recency": 0.11,
        "quality": 0.25,        # INCREASED from 0.20: paper's key finding
        "size_bonus": 0.05,
        "momentum": 0.07,       # reduced from 0.08
        "domain_bonus": 0.05,   # NEW: domain-specific effectiveness
    }

    # Domain specialization bonus — from SkillsBench Table 4
    # Paper shows Skills benefit varies hugely by domain:
    #   Healthcare: +51.9pp, Manufacturing: +41.9pp (high benefit)
    #   Software Engineering: +4.5pp, Mathematics: +6.0pp (low benefit, well-covered)
    # We give bonus to skills in under-served domains where Skills matter most
    DOMAIN_BONUS = {
        # Categories matching specialized domains (high Skills benefit)
        "mcp-server": 0.6,       # Infrastructure: cross-domain utility
        "claude-skill": 0.8,     # Agent-native: highest relevance
        "codex-skill": 0.7,      # Agent-native
        "agent-tool": 0.7,       # General agent tooling
        "ai-skill": 0.6,         # General AI skills
        "llm-plugin": 0.5,       # LLM integration
        "youmind-plugin": 0.5,   # Specialized plugin
        "uncategorized": 0.3,    # Unknown: neutral
    }

    # Topic-based domain bonus (supplement category-level scoring)
    # Skills in specialized/under-served domains get extra credit
    TOPIC_DOMAIN_BONUS = {
        "healthcare": 0.3, "medical": 0.3, "clinical": 0.3,
        "manufacturing": 0.25, "industrial": 0.25,
        "cybersecurity": 0.2, "security": 0.15,
        "finance": 0.2, "fintech": 0.2, "trading": 0.15,
        "robotics": 0.15, "iot": 0.15,
        "energy": 0.15, "climate": 0.15,
        "science": 0.1, "research": 0.1,
        "education": 0.1,
        # Well-covered domains get less bonus (models already know these)
        "web": 0.0, "frontend": 0.0, "backend": 0.0,
        "javascript": 0.0, "python": 0.0,
    }

    def score_all(self, db: Session, batch_size: int = 500) -> int:
        """Re-score every skill with batch commits to avoid PgBouncer timeouts.

        Phases: quality analysis → platform inference → token estimation → scoring.
        Each phase commits in batches of `batch_size` rows to keep transactions short.
        """
        # Run quality analysis first (populates quality_* fields)
        analyzer = QualityAnalyzer()
        analyzer.analyze_all(db, batch_size=batch_size)

        # Infer platforms
        inferrer = PlatformInferrer()
        inferrer.infer_all(db, batch_size=batch_size)

        # Estimate tokens
        estimator = TokenEstimator()
        estimator.estimate_all(db, batch_size=batch_size)

        # Now compute overall scores
        skills: List[Skill] = db.query(Skill).all()
        if not skills:
            return 0

        # Pre-compute log values for normalization (reduces outlier dominance)
        stars_log = [math.log1p(s.stars) for s in skills]
        forks_log = [math.log1p(s.forks) for s in skills]
        followers_log = [math.log1p(s.author_followers) for s in skills]
        commits_log = [math.log1p(s.total_commits) for s in skills]

        # Momentum: compute z-score stats
        deltas = [s.stars - (s.prev_stars or 0) for s in skills]
        delta_mean = sum(deltas) / len(deltas) if deltas else 0
        delta_std = (
            math.sqrt(sum((d - delta_mean) ** 2 for d in deltas) / len(deltas))
            if deltas
            else 1
        )
        if delta_std < 1:
            delta_std = 1  # avoid division by near-zero

        updated = 0
        for i, skill in enumerate(skills):
            norm_stars = self._log_normalize(stars_log[i], stars_log)
            norm_forks = self._log_normalize(forks_log[i], forks_log)
            norm_followers = self._log_normalize(followers_log[i], followers_log)
            norm_commits = self._log_normalize(commits_log[i], commits_log)
            ir = self._issue_resolution_rate(skill)
            recency = self._recency_decay(skill)
            quality = (skill.quality_score or 0) / 100.0  # normalize to 0-1
            size_bonus = self._size_bonus(skill)
            momentum = self._momentum_zscore(skill, delta_mean, delta_std)
            domain_bonus = self._domain_bonus(skill)
            skill.star_momentum = round(momentum, 3)

            raw = (
                self.WEIGHTS["stars"] * norm_stars
                + self.WEIGHTS["forks"] * norm_forks
                + self.WEIGHTS["author_followers"] * norm_followers
                + self.WEIGHTS["issue_resolution"] * ir
                + self.WEIGHTS["commits"] * norm_commits
                + self.WEIGHTS["recency"] * recency
                + self.WEIGHTS["quality"] * quality
                + self.WEIGHTS["size_bonus"] * size_bonus
                + self.WEIGHTS["momentum"] * momentum
                + self.WEIGHTS["domain_bonus"] * domain_bonus
            )
            skill.score = round(raw * 100, 1)
            updated += 1

            # Batch commit to avoid PgBouncer transaction timeout
            if (i + 1) % batch_size == 0:
                db.commit()
                logger.info("Score batch commit: %d/%d", i + 1, len(skills))

        db.commit()
        logger.info("Scored %d skills", updated)
        return updated

    @staticmethod
    def _log_normalize(log_value: float, all_log_values: List[float]) -> float:
        """Normalize using log1p values to reduce outlier dominance.

        log1p(stars) compresses the range: a repo with 100k stars won't
        dominate 100x more than one with 1k stars (only ~2.3x in log space).
        """
        lo = min(all_log_values)
        hi = max(all_log_values)
        if hi <= lo:
            return 0.0
        return (log_value - lo) / (hi - lo)

    @staticmethod
    def _issue_resolution_rate(skill: Skill) -> float:
        total = skill.total_issues
        if total == 0:
            return 0.5  # neutral when no issues exist
        closed = total - skill.open_issues
        return max(0.0, min(1.0, closed / total))

    @staticmethod
    def _recency_decay(skill: Skill) -> float:
        """Exponential time decay: e^(-0.01 * age_days).

        - 1 day old  -> 0.99
        - 30 days    -> 0.74
        - 90 days    -> 0.41
        - 180 days   -> 0.17
        - 365 days   -> 0.026

        Much smoother than the old step function.
        """
        if not skill.last_commit_at:
            return 0.05
        now = datetime.now(timezone.utc)
        last = skill.last_commit_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        days = max((now - last).total_seconds() / 86400, 0)
        return math.exp(-0.01 * days)

    @staticmethod
    def _momentum_zscore(skill: Skill, mean: float, std: float) -> float:
        """Z-score momentum: how many standard deviations above the mean.

        Clamp to [0, 1] for scoring. 0.5 = average growth.
        """
        delta = skill.stars - (skill.prev_stars or 0)
        z = (delta - mean) / std
        # Map z-score to 0-1: z=0 -> 0.5, z=2 -> ~0.95, z=-2 -> ~0.05
        return max(0.0, min(1.0, 0.5 + 0.25 * z))

    @staticmethod
    def _size_bonus(skill: Skill) -> float:
        """Reward focused repos, penalize bloated ones.

        Paper Finding 5: 2-3 focused Skills outperform 4+ Skills.
        Smaller, focused repos tend to be more effective as Skills.
        """
        size_kb = skill.repo_size_kb or 0
        if size_kb <= 0:
            return 0.3  # unknown size, neutral
        if size_kb <= 100:
            return 1.0  # micro: highly focused
        if size_kb <= 500:
            return 0.8  # small: good
        if size_kb <= 5000:
            return 0.5  # medium: ok
        return 0.2  # large: penalized

    def _domain_bonus(self, skill: Skill) -> float:
        """Domain-aware scoring bonus.

        SkillsBench Table 4 shows Skills benefit varies hugely by domain:
        - Healthcare: +51.9pp, Manufacturing: +41.9pp (specialized domains)
        - Software Engineering: +4.5pp (well-covered by models already)

        Skills in specialized/under-served domains deserve higher scores because
        they provide more value to agents that lack domain knowledge.
        """
        score = 0.0

        # Category-level bonus
        category = skill.category or "uncategorized"
        score += self.DOMAIN_BONUS.get(category, 0.3)

        # Topic-level bonus (check for specialized domain topics)
        try:
            topics = json.loads(skill.topics) if skill.topics else []
        except (json.JSONDecodeError, TypeError):
            topics = []

        max_topic_bonus = 0.0
        for topic in topics:
            topic_lower = topic.lower()
            for keyword, bonus in self.TOPIC_DOMAIN_BONUS.items():
                if keyword in topic_lower:
                    max_topic_bonus = max(max_topic_bonus, bonus)
        score += max_topic_bonus

        return min(score, 1.0)
