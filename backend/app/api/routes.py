import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin import SkillMaster
from app.models.skill import Skill, SkillComposition, SyncLog
from app.schemas.skill import (
    CategoryCount,
    PaginatedSkillsResponse,
    SkillCompositionItem,
    SkillDetailResponse,
    SkillResponse,
    SortField,
    SortOrder,
    StatsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/skills", response_model=PaginatedSkillsResponse)
def list_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: SortField = Query(SortField.score),
    sort_order: SortOrder = Query(SortOrder.desc),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    size_category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> PaginatedSkillsResponse:
    query = db.query(Skill)

    if category:
        query = query.filter(Skill.category == category)

    if platform:
        query = query.filter(Skill.platforms.ilike(f'%"{platform}"%'))

    if size_category:
        query = query.filter(Skill.size_category == size_category)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Skill.repo_name.ilike(pattern)
            | Skill.description.ilike(pattern)
            | Skill.author_name.ilike(pattern)
            | Skill.topics.ilike(pattern)
        )

    sort_column = getattr(Skill, sort_by.value)
    if sort_order == SortOrder.desc:
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedSkillsResponse(
        items=[SkillResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/skills/category/{category_name}", response_model=PaginatedSkillsResponse)
def list_skills_by_category(
    category_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: SortField = Query(SortField.score),
    sort_order: SortOrder = Query(SortOrder.desc),
    db: Session = Depends(get_db),
) -> PaginatedSkillsResponse:
    return list_skills(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        search=None,
        category=category_name,
        platform=None,
        size_category=None,
        db=db,
    )


@router.get("/skills/{skill_id}", response_model=SkillDetailResponse)
def get_skill(skill_id: int, db: Session = Depends(get_db)) -> SkillDetailResponse:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    compositions = (
        db.query(SkillComposition)
        .filter(SkillComposition.skill_id == skill_id)
        .order_by(desc(SkillComposition.compatibility_score))
        .limit(5)
        .all()
    )
    compatible_skills = []
    for comp in compositions:
        other = db.query(Skill).filter(Skill.id == comp.compatible_skill_id).first()
        if other:
            compatible_skills.append(SkillCompositionItem(
                skill_id=other.id,
                skill_name=other.repo_name,
                skill_score=other.score or 0.0,
                compatibility_score=comp.compatibility_score,
                reason=comp.reason,
            ))

    detail = SkillDetailResponse.model_validate(skill)
    detail.compatible_skills = compatible_skills
    return detail


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    total = db.query(func.count(Skill.id)).scalar() or 0
    avg = db.query(func.avg(Skill.score)).scalar() or 0.0

    cat_rows = (
        db.query(Skill.category, func.count(Skill.id))
        .group_by(Skill.category)
        .order_by(func.count(Skill.id).desc())
        .all()
    )
    categories = [CategoryCount(name=name, count=count) for name, count in cat_rows]

    last_sync = db.query(SyncLog).order_by(desc(SyncLog.started_at)).first()

    return StatsResponse(
        total_skills=total,
        categories=categories,
        avg_score=round(float(avg), 1),
        last_sync_at=last_sync.started_at if last_sync else None,
        last_sync_status=last_sync.status if last_sync else None,
    )


@router.get("/categories", response_model=list[CategoryCount])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryCount]:
    rows = (
        db.query(Skill.category, func.count(Skill.id))
        .group_by(Skill.category)
        .order_by(func.count(Skill.id).desc())
        .all()
    )
    return [CategoryCount(name=name, count=count) for name, count in rows]


@router.get("/trending", response_model=list[SkillResponse])
def get_trending(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[SkillResponse]:
    """Trending skills: high stars relative to repo age (star velocity).

    Formula: stars / max(age_in_days, 1). Only repos with >= 50 stars.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    items = (
        db.query(Skill)
        .filter(Skill.stars >= 50)
        .filter(Skill.created_at.isnot(None))
        .filter(Skill.created_at >= since)
        .all()
    )
    now = datetime.now(timezone.utc)

    def star_velocity(skill: Skill) -> float:
        created = skill.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_days = max((now - created).total_seconds() / 86400, 1)
        return skill.stars / age_days

    ranked = sorted(items, key=star_velocity, reverse=True)[:limit]
    return [SkillResponse.model_validate(s) for s in ranked]


@router.get("/rising", response_model=list[SkillResponse])
def get_rising(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[SkillResponse]:
    """New & rising: repos created in the last N days, sorted by stars."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    items = (
        db.query(Skill)
        .filter(Skill.created_at >= since)
        .order_by(desc(Skill.stars))
        .limit(limit)
        .all()
    )
    return [SkillResponse.model_validate(s) for s in items]


@router.get("/masters")
def get_masters(db: Session = Depends(get_db)) -> list[dict]:
    """Skills masters / influencers with their repos and stats."""
    db_masters = db.query(SkillMaster).filter(SkillMaster.is_active == True).all()  # noqa: E712

    results = []
    known_githubs: set[str] = set()
    for m in db_masters:
        aliases = json.loads(m.github_aliases) if m.github_aliases else []
        tags = json.loads(m.tags) if m.tags else []
        all_usernames = [m.github] + aliases
        known_githubs.update(all_usernames)

        repos = (
            db.query(Skill)
            .filter(Skill.author_name.in_(all_usernames))
            .order_by(desc(Skill.stars))
            .all()
        )
        total_stars = sum(r.stars for r in repos)
        results.append({
            "github": m.github,
            "github_aliases": aliases,
            "name": m.name,
            "x_handle": m.x_handle,
            "bio": m.bio,
            "tags": tags,
            "x_followers": m.x_followers or 0,
            "x_posts_count": m.x_posts_count or 0,
            "x_verified_at": m.x_verified_at.isoformat() if m.x_verified_at else None,
            "x_notes": m.x_notes,
            "avatar_url": repos[0].author_avatar_url if repos else f"https://github.com/{m.github}.png",
            "repo_count": len(repos),
            "total_stars": total_stars,
            "top_repos": [
                {
                    "id": r.id,
                    "repo_name": r.repo_name,
                    "repo_full_name": r.repo_full_name,
                    "repo_url": r.repo_url,
                    "description": r.description,
                    "stars": r.stars,
                    "score": r.score,
                    "category": r.category,
                }
                for r in repos[:5]
            ],
        })

    # Auto-discover emerging builders: 3+ repos, 500+ stars, active in last 3 months
    three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
    emerging = (
        db.query(
            Skill.author_name,
            func.count(Skill.id).label("cnt"),
            func.sum(Skill.stars).label("total"),
        )
        .filter(Skill.last_commit_at >= three_months_ago)
        .group_by(Skill.author_name)
        .having(func.count(Skill.id) >= 3)
        .having(func.sum(Skill.stars) >= 500)
        .order_by(func.sum(Skill.stars).desc())
        .limit(20)
        .all()
    )
    discovered = []
    for author, cnt, total in emerging:
        if author in known_githubs:
            continue
        repos = (
            db.query(Skill)
            .filter(Skill.author_name == author)
            .order_by(desc(Skill.stars))
            .limit(5)
            .all()
        )
        discovered.append({
            "github": author,
            "name": author,
            "x_handle": None,
            "bio": None,
            "tags": [],
            "avatar_url": repos[0].author_avatar_url if repos else f"https://github.com/{author}.png",
            "repo_count": cnt,
            "total_stars": int(total),
            "top_repos": [
                {
                    "id": r.id,
                    "repo_name": r.repo_name,
                    "repo_full_name": r.repo_full_name,
                    "repo_url": r.repo_url,
                    "description": r.description,
                    "stars": r.stars,
                    "score": r.score,
                    "category": r.category,
                }
                for r in repos
            ],
            "discovered": True,
        })

    return results + discovered[:10]


@router.get("/top-rated", response_model=list[SkillResponse])
def get_top_rated(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[SkillResponse]:
    """All-time highest scored skills."""
    items = (
        db.query(Skill)
        .order_by(desc(Skill.score))
        .limit(limit)
        .all()
    )
    return [SkillResponse.model_validate(s) for s in items]


@router.get("/most-starred", response_model=list[SkillResponse])
def get_most_starred(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[SkillResponse]:
    """Community classics: time-tested repos (>6 months old, 100+ stars)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=180)
    items = (
        db.query(Skill)
        .filter(Skill.stars >= 100)
        .filter(Skill.created_at.isnot(None))
        .filter(Skill.created_at <= cutoff)
        .order_by(desc(Skill.stars))
        .limit(limit)
        .all()
    )
    return [SkillResponse.model_validate(s) for s in items]


@router.get("/recently-updated", response_model=list[SkillResponse])
def get_recently_updated(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[SkillResponse]:
    """Skills most recently pushed to GitHub."""
    items = (
        db.query(Skill)
        .filter(Skill.last_commit_at.isnot(None))
        .order_by(desc(Skill.last_commit_at))
        .limit(limit)
        .all()
    )
    return [SkillResponse.model_validate(s) for s in items]


@router.get("/language-stats")
def get_language_stats(
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Top programming languages across all skills."""
    rows = (
        db.query(Skill.language, func.count(Skill.id))
        .filter(Skill.language != "")
        .group_by(Skill.language)
        .order_by(func.count(Skill.id).desc())
        .limit(limit)
        .all()
    )
    return [{"language": lang, "count": count} for lang, count in rows]


@router.get("/platforms")
def get_platform_stats(
    db: Session = Depends(get_db),
) -> list[dict]:
    """Platform distribution across all skills."""
    all_skills = db.query(Skill.platforms).filter(Skill.platforms != "[]").all()
    platform_counts: dict[str, int] = {}
    for (platforms_json,) in all_skills:
        try:
            platforms = json.loads(platforms_json)
            for p in platforms:
                platform_counts[p] = platform_counts.get(p, 0) + 1
        except (json.JSONDecodeError, TypeError):
            continue
    sorted_platforms = sorted(platform_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"platform": name, "count": count} for name, count in sorted_platforms]
