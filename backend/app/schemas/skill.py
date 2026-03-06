from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class SortField(str, Enum):
    score = "score"
    stars = "stars"
    updated = "last_commit_at"
    created = "created_at"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class SkillResponse(BaseModel):
    id: int
    repo_full_name: str
    repo_name: str
    repo_url: str
    description: str
    homepage_url: str = ""
    author_name: str
    author_avatar_url: str
    author_followers: int
    stars: int
    forks: int
    open_issues: int
    total_issues: int
    total_commits: int
    language: str
    category: str
    topics: str
    license: str
    score: float
    star_momentum: float = 0.0
    last_commit_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_synced: Optional[datetime] = None

    # Project type
    project_type: str = "tool"

    # Quality scoring (4+ dimensions)
    quality_completeness: float = 0.0
    quality_clarity: float = 0.0
    quality_specificity: float = 0.0
    quality_examples: float = 0.0
    quality_agent_readiness: float = 0.0
    quality_score: float = 0.0

    # Size / Focus
    size_category: str = "unknown"
    repo_size_kb: int = 0
    readme_size: int = 0
    readme_structure_score: float = 0.0

    # Platforms
    platforms: str = "[]"

    # Token budget
    estimated_tokens: int = 0

    model_config = {"from_attributes": True}


class SkillCompositionItem(BaseModel):
    skill_id: int
    skill_name: str
    skill_score: float
    compatibility_score: float
    reason: str


class SkillDetailResponse(SkillResponse):
    """Extended response with composability recommendations."""
    compatible_skills: List[SkillCompositionItem] = []


class PaginatedSkillsResponse(BaseModel):
    items: List[SkillResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CategoryCount(BaseModel):
    name: str
    count: int


class StatsResponse(BaseModel):
    total_skills: int
    categories: List[CategoryCount]
    avg_score: float
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None


class SyncTriggerResponse(BaseModel):
    message: str
    sync_id: int
