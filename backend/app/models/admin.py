from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class SkillMaster(Base):
    __tablename__ = "skill_masters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    github = Column(String(255), unique=True, nullable=False)
    github_aliases = Column(Text, default="[]")  # JSON list
    name = Column(String(255), nullable=False)
    x_handle = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    tags = Column(Text, default="[]")  # JSON list
    x_followers = Column(Integer, default=0)
    x_posts_count = Column(Integer, default=0)
    x_verified_at = Column(DateTime, nullable=True)
    x_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ExtraRepo(Base):
    __tablename__ = "extra_repos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    # Review workflow: pending → approved / rejected
    status = Column(String(20), default="pending")  # pending, approved, rejected
    submitted_by = Column(String(255), nullable=True)  # optional: email or IP
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(500), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
