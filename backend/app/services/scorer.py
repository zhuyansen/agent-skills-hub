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

    v2 improvements:
    - Log normalization for stars/forks/followers/commits (reduces outlier dominance)
    - Exponential time decay for recency (smooth curve instead of step function)
    - Momentum uses z-score instead of min-max (better distribution)
    """

    WEIGHTS = {
        "stars": 0.18,
        "forks": 0.10,
        "author_followers": 0.08,
        "issue_resolution": 0.10,
        "commits": 0.10,
        "recency": 0.11,
        "quality": 0.20,
        "size_bonus": 0.05,
        "momentum": 0.08,
    }

    def score_all(self, db: Session) -> int:
        """Re-score every skill: quality analysis, platform inference, token estimation, then scoring."""
        # Run quality analysis first (populates quality_* fields)
        analyzer = QualityAnalyzer()
        analyzer.analyze_all(db)

        # Infer platforms
        inferrer = PlatformInferrer()
        inferrer.infer_all(db)

        # Estimate tokens
        estimator = TokenEstimator()
        estimator.estimate_all(db)

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
            )
            skill.score = round(raw * 100, 1)
            updated += 1

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
        """Reward focused repos, penalize bloated ones."""
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
