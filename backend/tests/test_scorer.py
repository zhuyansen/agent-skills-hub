"""Unit tests for the ScoringEngine static helpers."""

import math
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.scorer import ScoringEngine


def _make_skill(**overrides):
    """Create a minimal skill-like object for testing."""
    defaults = {
        "stars": 100,
        "forks": 20,
        "open_issues": 5,
        "total_issues": 20,
        "total_commits": 50,
        "author_followers": 10,
        "prev_stars": 80,
        "quality_score": 50,
        "repo_size_kb": 200,
        "last_commit_at": datetime.now(timezone.utc) - timedelta(days=10),
        "star_momentum": 0.0,
        "score": 0.0,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestLogNormalize:
    def test_returns_zero_when_all_equal(self):
        vals = [math.log1p(10)] * 5
        assert ScoringEngine._log_normalize(vals[0], vals) == 0.0

    def test_min_is_zero(self):
        vals = [math.log1p(0), math.log1p(100), math.log1p(500)]
        assert ScoringEngine._log_normalize(vals[0], vals) == 0.0

    def test_max_is_one(self):
        vals = [math.log1p(0), math.log1p(100), math.log1p(500)]
        assert ScoringEngine._log_normalize(vals[-1], vals) == 1.0

    def test_mid_between_zero_and_one(self):
        vals = [math.log1p(0), math.log1p(100), math.log1p(500)]
        mid = ScoringEngine._log_normalize(vals[1], vals)
        assert 0.0 < mid < 1.0


class TestIssueResolutionRate:
    def test_no_issues_returns_neutral(self):
        skill = _make_skill(total_issues=0, open_issues=0)
        assert ScoringEngine._issue_resolution_rate(skill) == 0.5

    def test_all_closed(self):
        skill = _make_skill(total_issues=20, open_issues=0)
        assert ScoringEngine._issue_resolution_rate(skill) == 1.0

    def test_all_open(self):
        skill = _make_skill(total_issues=10, open_issues=10)
        assert ScoringEngine._issue_resolution_rate(skill) == 0.0

    def test_half_resolved(self):
        skill = _make_skill(total_issues=10, open_issues=5)
        assert ScoringEngine._issue_resolution_rate(skill) == 0.5


class TestRecencyDecay:
    def test_no_commit_returns_minimum(self):
        skill = _make_skill(last_commit_at=None)
        assert ScoringEngine._recency_decay(skill) == 0.05

    def test_recent_commit_near_one(self):
        skill = _make_skill(last_commit_at=datetime.now(timezone.utc) - timedelta(hours=1))
        assert ScoringEngine._recency_decay(skill) > 0.99

    def test_old_commit_near_zero(self):
        skill = _make_skill(last_commit_at=datetime.now(timezone.utc) - timedelta(days=365))
        assert ScoringEngine._recency_decay(skill) < 0.05

    def test_30_day_decay(self):
        skill = _make_skill(last_commit_at=datetime.now(timezone.utc) - timedelta(days=30))
        val = ScoringEngine._recency_decay(skill)
        assert 0.70 < val < 0.78  # e^(-0.3) ≈ 0.74

    def test_naive_datetime_handled(self):
        """Ensure naive datetimes (no tzinfo) don't crash."""
        skill = _make_skill(last_commit_at=datetime(2024, 1, 1))
        val = ScoringEngine._recency_decay(skill)
        assert 0.0 <= val <= 1.0


class TestMomentumZscore:
    def test_average_growth_maps_to_half(self):
        skill = _make_skill(stars=110, prev_stars=100)
        # mean=10, delta=10 => z=0 => 0.5
        assert ScoringEngine._momentum_zscore(skill, mean=10, std=5) == 0.5

    def test_high_growth_above_half(self):
        skill = _make_skill(stars=200, prev_stars=100)
        val = ScoringEngine._momentum_zscore(skill, mean=10, std=20)
        assert val > 0.5

    def test_no_growth_below_half(self):
        skill = _make_skill(stars=100, prev_stars=100)
        val = ScoringEngine._momentum_zscore(skill, mean=10, std=5)
        assert val < 0.5

    def test_clamped_to_zero_one(self):
        skill = _make_skill(stars=100, prev_stars=100)
        val = ScoringEngine._momentum_zscore(skill, mean=1000, std=1)
        assert val >= 0.0
        skill2 = _make_skill(stars=100000, prev_stars=0)
        val2 = ScoringEngine._momentum_zscore(skill2, mean=0, std=1)
        assert val2 <= 1.0


class TestSizeBonus:
    def test_unknown_size(self):
        assert ScoringEngine._size_bonus(_make_skill(repo_size_kb=0)) == 0.3

    def test_micro(self):
        assert ScoringEngine._size_bonus(_make_skill(repo_size_kb=50)) == 1.0

    def test_small(self):
        assert ScoringEngine._size_bonus(_make_skill(repo_size_kb=200)) == 0.8

    def test_medium(self):
        assert ScoringEngine._size_bonus(_make_skill(repo_size_kb=3000)) == 0.5

    def test_large(self):
        assert ScoringEngine._size_bonus(_make_skill(repo_size_kb=10000)) == 0.2
