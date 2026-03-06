from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class MasterCreate(BaseModel):
    github: str
    name: str
    github_aliases: List[str] = []
    x_handle: Optional[str] = None
    bio: Optional[str] = None
    tags: List[str] = []
    x_followers: int = 0
    x_posts_count: int = 0
    x_notes: Optional[str] = None


class MasterUpdate(BaseModel):
    name: Optional[str] = None
    github_aliases: Optional[List[str]] = None
    x_handle: Optional[str] = None
    bio: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    x_followers: Optional[int] = None
    x_posts_count: Optional[int] = None
    x_verified_at: Optional[datetime] = None
    x_notes: Optional[str] = None


class MasterResponse(BaseModel):
    id: int
    github: str
    github_aliases: str  # JSON string
    name: str
    x_handle: Optional[str] = None
    bio: Optional[str] = None
    tags: str  # JSON string
    x_followers: int = 0
    x_posts_count: int = 0
    x_verified_at: Optional[datetime] = None
    x_notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ExtraRepoCreate(BaseModel):
    full_name: str


class ExtraRepoResponse(BaseModel):
    id: int
    full_name: str
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SearchQueryCreate(BaseModel):
    query: str


class SearchQueryResponse(BaseModel):
    id: int
    query: str
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SkillUpdateAdmin(BaseModel):
    """Admin manual override for skill fields."""
    category: Optional[str] = None
    quality_completeness: Optional[float] = None
    quality_clarity: Optional[float] = None
    quality_specificity: Optional[float] = None
    quality_examples: Optional[float] = None
    platforms: Optional[str] = None  # JSON string
    estimated_tokens: Optional[int] = None
