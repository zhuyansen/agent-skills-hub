from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (
        # Composite indexes for common query patterns
        Index("ix_skills_category_score", "category", "score"),
        Index("ix_skills_last_commit_at", "last_commit_at"),
        Index("ix_skills_stars", "stars"),
        Index("ix_skills_last_synced", "last_synced"),
        Index("ix_skills_author_name", "author_name"),
        Index("ix_skills_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # GitHub identity
    repo_full_name = Column(String(255), unique=True, nullable=False, index=True)
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(String(512), nullable=False)
    description = Column(Text, default="")
    homepage_url = Column(String(512), default="")

    # Author / Org
    author_name = Column(String(255), nullable=False)
    author_avatar_url = Column(String(512), default="")
    author_followers = Column(Integer, default=0)

    # GitHub metrics
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    watchers = Column(Integer, default=0)
    total_commits = Column(Integer, default=0)
    contributors_count = Column(Integer, default=0)

    # Timestamps from GitHub
    created_at = Column(DateTime, nullable=True)
    last_commit_at = Column(DateTime, nullable=True)
    pushed_at = Column(DateTime, nullable=True)

    # Classification
    category = Column(String(100), default="uncategorized", index=True)
    language = Column(String(50), default="")
    topics = Column(Text, default="[]")
    license = Column(String(100), default="")

    # Computed score (overall)
    score = Column(Float, default=0.0, index=True)

    # Momentum (star growth tracking)
    prev_stars = Column(Integer, default=0)
    star_momentum = Column(Float, default=0.0)

    # Quality scoring (4 dimensions)
    quality_completeness = Column(Float, default=0.0)
    quality_clarity = Column(Float, default=0.0)
    quality_specificity = Column(Float, default=0.0)
    quality_examples = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)

    # Project type
    project_type = Column(String(50), default="tool")

    # Agent readiness
    quality_agent_readiness = Column(Float, default=0.0)

    # Size / Focus
    size_category = Column(String(20), default="unknown")
    repo_size_kb = Column(Integer, default=0)
    readme_size = Column(Integer, default=0)
    readme_content = Column(Text, nullable=True)
    readme_structure_score = Column(Float, default=0.0)
    file_count = Column(Integer, default=0)

    # Platform compatibility (JSON list)
    platforms = Column(Text, default="[]")

    # Token budget
    estimated_tokens = Column(Integer, default=0)

    # Security
    security_grade = Column(String, default="unknown")
    security_flags = Column(Text, default="[]")
    security_llm_grade = Column(String, nullable=True)
    security_llm_analysis = Column(Text, nullable=True)

    # Official flag
    is_official = Column(Boolean, default=False, server_default="false")

    # Internal timestamps
    first_seen = Column(DateTime, server_default=func.now())
    last_synced = Column(DateTime, server_default=func.now(), onupdate=func.now())


class WeeklyTrendingSnapshot(Base):
    __tablename__ = "weekly_trending_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    rank = Column(Integer, nullable=False)
    skill_id = Column(Integer, nullable=False)
    repo_full_name = Column(String(255), nullable=False)
    repo_name = Column(String(255), nullable=False)
    author_name = Column(String(255), nullable=False)
    author_avatar_url = Column(String(512), default="")
    stars = Column(Integer, nullable=False)
    star_velocity = Column(Float, nullable=False)
    description = Column(Text, default="")
    repo_url = Column(String(512), default="")
    category = Column(String(100), default="")
    created_at_snap = Column(DateTime, nullable=True)
    last_commit_at_snap = Column(DateTime, nullable=True)
    snapshot_taken_at = Column(DateTime, server_default=func.now())


class SkillComposition(Base):
    __tablename__ = "skill_compositions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Integer, index=True, nullable=False)
    compatible_skill_id = Column(Integer, index=True, nullable=False)
    compatibility_score = Column(Float, default=0.0)
    reason = Column(String(255), default="")
    created_at = Column(DateTime, server_default=func.now())


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")
    repos_found = Column(Integer, default=0)
    repos_updated = Column(Integer, default=0)
    repos_new = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    subscribed_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    # Email verification
    verified = Column(Boolean, default=False)
    verification_token = Column(String(64), nullable=True, index=True)
    verified_at = Column(DateTime, nullable=True)
    # Unsubscribe
    unsubscribe_token = Column(String(64), nullable=True, unique=True, index=True)
