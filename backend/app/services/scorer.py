import logging
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.services.platform_inferrer import PlatformInferrer
from app.services.quality_analyzer import QualityAnalyzer
from app.services.token_estimator import TokenEstimator

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Computes a 0-100 quality score for each skill using weighted normalization."""

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

        stars_vals = [s.stars for s in skills]
        forks_vals = [s.forks for s in skills]
        followers_vals = [s.author_followers for s in skills]
        commits_vals = [s.total_commits for s in skills]
        deltas = [s.stars - (s.prev_stars or 0) for s in skills]

        updated = 0
        for skill in skills:
            norm_stars = self._minmax(skill.stars, stars_vals)
            norm_forks = self._minmax(skill.forks, forks_vals)
            norm_followers = self._minmax(skill.author_followers, followers_vals)
            norm_commits = self._minmax(skill.total_commits, commits_vals)
            ir = self._issue_resolution_rate(skill)
            recency = self._recency_score(skill)
            quality = (skill.quality_score or 0) / 100.0  # normalize to 0-1
            size_bonus = self._size_bonus(skill)
            momentum = self._momentum_score(skill, deltas)
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
    def _minmax(value: int, all_values: List[int]) -> float:
        lo, hi = min(all_values), max(all_values)
        if hi == lo:
            return 0.0
        return (value - lo) / (hi - lo)

    @staticmethod
    def _issue_resolution_rate(skill: Skill) -> float:
        total = skill.total_issues
        if total == 0:
            return 0.5  # neutral when no issues exist
        closed = total - skill.open_issues
        return max(0.0, min(1.0, closed / total))

    @staticmethod
    def _recency_score(skill: Skill) -> float:
        if not skill.last_commit_at:
            return 0.15
        now = datetime.now(timezone.utc)
        last = skill.last_commit_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        days = (now - last).days
        if days <= 30:
            return 1.0
        if days <= 90:
            return 0.9
        if days <= 180:
            return 0.7
        if days <= 365:
            return 0.4
        return 0.15

    @staticmethod
    def _momentum_score(skill: Skill, all_deltas: List[int]) -> float:
        """Score based on star growth since last sync. Returns 0-1 (0.5 = neutral)."""
        delta = skill.stars - (skill.prev_stars or 0)
        if not all_deltas:
            return 0.5
        lo, hi = min(all_deltas), max(all_deltas)
        if hi == lo:
            return 0.5
        return max(0.0, min(1.0, (delta - lo) / (hi - lo)))

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
