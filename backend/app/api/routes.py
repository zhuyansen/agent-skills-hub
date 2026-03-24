import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.admin import SkillMaster
from app.models.skill import Skill, SkillComposition, SyncLog, WeeklyTrendingSnapshot
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


def _cached_json(data, max_age: int = 300) -> JSONResponse:
    """Return a JSONResponse with Cache-Control header.

    max_age is in seconds. Default 5 minutes.
    """
    return JSONResponse(
        content=data,
        headers={"Cache-Control": f"public, max-age={max_age}, s-maxage={max_age}"},
    )


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


@router.get("/skills/by-slug/{owner}/{repo}", response_model=SkillDetailResponse)
def get_skill_by_slug(owner: str, repo: str, db: Session = Depends(get_db)) -> SkillDetailResponse:
    """Look up a skill by owner/repo slug (repo_full_name)."""
    full_name = f"{owner}/{repo}"
    skill = db.query(Skill).filter(Skill.repo_full_name == full_name).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    compositions = (
        db.query(SkillComposition)
        .filter(SkillComposition.skill_id == skill.id)
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


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Dashboard stats. Cached for 1 hour."""
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

    resp = StatsResponse(
        total_skills=total,
        categories=categories,
        avg_score=round(float(avg), 1),
        last_sync_at=last_sync.started_at if last_sync else None,
        last_sync_status=last_sync.status if last_sync else None,
    )
    return _cached_json(resp.model_dump(mode="json"), max_age=3600)  # 1 hour


@router.get("/sync-status")
def get_sync_status(db: Session = Depends(get_db)):
    """Public sync health endpoint. Returns last sync info and health status.

    Cached for 5 minutes.
    """
    # Last completed sync
    last_completed = (
        db.query(SyncLog)
        .filter(SyncLog.status == "completed")
        .order_by(desc(SyncLog.finished_at))
        .first()
    )
    # Last sync attempt (any status)
    last_attempt = db.query(SyncLog).order_by(desc(SyncLog.started_at)).first()

    # Recent 5 sync logs for history
    recent_logs = (
        db.query(SyncLog)
        .order_by(desc(SyncLog.started_at))
        .limit(5)
        .all()
    )

    now = datetime.now(timezone.utc)
    overdue_threshold_hours = 10  # 8h interval + 2h grace period

    health = "healthy"
    message = ""

    if not last_completed:
        health = "unknown"
        message = "No completed sync found"
    else:
        finished = last_completed.finished_at
        if finished and finished.tzinfo is None:
            from datetime import timezone as tz
            finished = finished.replace(tzinfo=tz.utc)
        hours_since = (now - finished).total_seconds() / 3600 if finished else 999
        if hours_since > overdue_threshold_hours:
            health = "overdue"
            message = f"Last successful sync was {hours_since:.1f}h ago (threshold: {overdue_threshold_hours}h)"
        else:
            message = f"Last sync completed {hours_since:.1f}h ago"

    # Count stuck "running" logs (started > 2h ago, still running)
    two_hours_ago = now - timedelta(hours=2)
    stuck_count = (
        db.query(func.count(SyncLog.id))
        .filter(SyncLog.status == "running")
        .filter(SyncLog.started_at < two_hours_ago)
        .scalar() or 0
    )
    if stuck_count > 0:
        message += f". {stuck_count} stuck sync(s) detected."

    data = {
        "health": health,
        "message": message,
        "last_completed": {
            "id": last_completed.id,
            "started_at": last_completed.started_at.isoformat() if last_completed and last_completed.started_at else None,
            "finished_at": last_completed.finished_at.isoformat() if last_completed and last_completed.finished_at else None,
            "repos_found": last_completed.repos_found if last_completed else 0,
            "repos_updated": last_completed.repos_updated if last_completed else 0,
            "repos_new": last_completed.repos_new if last_completed else 0,
        } if last_completed else None,
        "last_attempt": {
            "id": last_attempt.id,
            "started_at": last_attempt.started_at.isoformat() if last_attempt and last_attempt.started_at else None,
            "status": last_attempt.status if last_attempt else None,
            "error_message": last_attempt.error_message if last_attempt else None,
        } if last_attempt else None,
        "recent_logs": [
            {
                "id": log.id,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "finished_at": log.finished_at.isoformat() if log.finished_at else None,
                "status": log.status,
                "repos_found": log.repos_found,
                "repos_new": log.repos_new,
            }
            for log in recent_logs
        ],
        "stuck_running_count": stuck_count,
    }

    return _cached_json(data, max_age=300)  # 5 minutes


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """Category list. Cached for 1 hour."""
    rows = (
        db.query(Skill.category, func.count(Skill.id))
        .group_by(Skill.category)
        .order_by(func.count(Skill.id).desc())
        .all()
    )
    data = [CategoryCount(name=name, count=count).model_dump(mode="json") for name, count in rows]
    return _cached_json(data, max_age=3600)  # 1 hour


@router.get("/trending")
def get_trending(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Trending skills: high stars relative to repo age (star velocity).

    Formula: stars / max(age_in_days, 1). Only repos with >= 50 stars.
    Cached for 5 minutes.
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
    data = [SkillResponse.model_validate(s).model_dump(mode="json") for s in ranked]
    return _cached_json(data, max_age=300)  # 5 min


@router.get("/rising")
def get_rising(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """New & rising: repos created in the last N days, sorted by stars. Cached 5 min."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    items = (
        db.query(Skill)
        .filter(Skill.created_at >= since)
        .order_by(desc(Skill.stars))
        .limit(limit)
        .all()
    )
    data = [SkillResponse.model_validate(s).model_dump(mode="json") for s in items]
    return _cached_json(data, max_age=300)  # 5 min


@router.get("/trending/weeks")
def get_trending_weeks(db: Session = Depends(get_db)):
    """List available weekly trending snapshots. Cached 10 min."""
    rows = (
        db.query(
            WeeklyTrendingSnapshot.week_start,
            WeeklyTrendingSnapshot.week_end,
            func.count(WeeklyTrendingSnapshot.id),
        )
        .group_by(WeeklyTrendingSnapshot.week_start, WeeklyTrendingSnapshot.week_end)
        .order_by(WeeklyTrendingSnapshot.week_start.desc())
        .all()
    )
    data = [
        {
            "week_start": row[0].strftime("%Y-%m-%d") if row[0] else None,
            "week_end": row[1].strftime("%Y-%m-%d") if row[1] else None,
            "snapshot_count": row[2],
        }
        for row in rows
    ]
    return _cached_json(data, max_age=600)


@router.get("/trending/history")
def get_trending_history(
    week_start: str = Query(..., description="Week start date YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """Get trending history for a specific week. Cached 10 min."""
    try:
        # Parse as date, then convert to datetime for comparison with DateTime column
        ws_date = datetime.strptime(week_start[:10], "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

    rows = (
        db.query(WeeklyTrendingSnapshot)
        .filter(WeeklyTrendingSnapshot.week_start == ws_date)
        .order_by(WeeklyTrendingSnapshot.rank)
        .all()
    )
    data = [
        {
            "rank": r.rank,
            "skill_id": r.skill_id,
            "repo_full_name": r.repo_full_name,
            "repo_name": r.repo_name,
            "author_name": r.author_name,
            "author_avatar_url": r.author_avatar_url,
            "stars": r.stars,
            "star_velocity": r.star_velocity,
            "description": r.description,
            "repo_url": r.repo_url,
            "category": r.category,
            "created_at_snap": r.created_at_snap.isoformat() if r.created_at_snap else None,
            "last_commit_at_snap": r.last_commit_at_snap.isoformat() if r.last_commit_at_snap else None,
        }
        for r in rows
    ]
    return _cached_json(data, max_age=600)


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

    data = results + discovered[:10]
    return _cached_json(data, max_age=600)  # 10 min


@router.get("/top-rated")
def get_top_rated(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """All-time highest scored skills. Cached for 10 minutes."""
    items = (
        db.query(Skill)
        .order_by(desc(Skill.score))
        .limit(limit)
        .all()
    )
    data = [SkillResponse.model_validate(s).model_dump(mode="json") for s in items]
    return _cached_json(data, max_age=600)  # 10 min


@router.get("/most-starred")
def get_most_starred(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Community classics: time-tested repos (>6 months old, 100+ stars). Cached 10 min."""
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
    data = [SkillResponse.model_validate(s).model_dump(mode="json") for s in items]
    return _cached_json(data, max_age=600)  # 10 min


@router.get("/recently-updated")
def get_recently_updated(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Skills most recently pushed to GitHub. Cached 5 min."""
    items = (
        db.query(Skill)
        .filter(Skill.last_commit_at.isnot(None))
        .order_by(desc(Skill.last_commit_at))
        .limit(limit)
        .all()
    )
    data = [SkillResponse.model_validate(s).model_dump(mode="json") for s in items]
    return _cached_json(data, max_age=300)  # 5 min


@router.get("/language-stats")
def get_language_stats(
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """Top programming languages across all skills. Cached 1 hour."""
    rows = (
        db.query(Skill.language, func.count(Skill.id))
        .filter(Skill.language != "")
        .group_by(Skill.language)
        .order_by(func.count(Skill.id).desc())
        .limit(limit)
        .all()
    )
    data = [{"language": lang, "count": count} for lang, count in rows]
    return _cached_json(data, max_age=3600)  # 1 hour


@router.get("/platforms")
def get_platform_stats(
    db: Session = Depends(get_db),
):
    """Platform distribution across all skills. Cached 1 hour."""
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
    data = [{"platform": name, "count": count} for name, count in sorted_platforms]
    return _cached_json(data, max_age=3600)  # 1 hour


@router.post("/submit-skill")
def submit_skill(
    body: dict,
    db: Session = Depends(get_db),
) -> dict:
    """Community skill submission — anyone can submit a GitHub repo URL.
    Adds it to extra_repos for next sync."""
    from app.models.admin import ExtraRepo

    repo_url = body.get("repo_url", "").strip()
    if not repo_url:
        raise HTTPException(status_code=400, detail="repo_url is required")

    # Extract full_name from URL: github.com/owner/repo → owner/repo
    import re
    match = re.match(r"(?:https?://)?github\.com/([^/]+/[^/]+?)(?:\.git)?/?$", repo_url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")

    full_name = match.group(1)

    # Check if already exists in skills
    existing_skill = db.query(Skill).filter(Skill.repo_full_name == full_name).first()
    if existing_skill:
        return {"status": "already_tracked", "message": f"{full_name} is already in our database", "skill_id": existing_skill.id}

    # Check if already submitted
    existing_extra = db.query(ExtraRepo).filter(ExtraRepo.full_name == full_name).first()
    if existing_extra:
        return {"status": "already_submitted", "message": f"{full_name} has already been submitted and is pending review"}

    # Add to extra repos with 'pending' status for admin review
    new_extra = ExtraRepo(full_name=full_name, is_active=False, status="pending")
    db.add(new_extra)
    db.commit()
    db.refresh(new_extra)

    logger.info("Community submitted skill (pending review): %s", full_name)
    return {"status": "submitted", "message": f"{full_name} has been submitted! It will be reviewed by our team and included after approval."}


@router.post("/subscribe")
def subscribe_newsletter(body: dict, db: Session = Depends(get_db)) -> dict:
    """Subscribe to the weekly newsletter. Sends a verification email."""
    import re
    import secrets
    from app.models.skill import Subscriber
    from app.services.email_service import send_verification_email

    email = body.get("email", "").strip().lower()
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    # Check if already subscribed
    existing = db.query(Subscriber).filter(Subscriber.email == email).first()
    if existing:
        if existing.is_active and existing.verified:
            return {"status": "ok", "message": "You're already subscribed and verified!"}
        if existing.is_active and not existing.verified:
            # Re-send verification token
            token = secrets.token_urlsafe(32)
            existing.verification_token = token
            db.commit()
            send_verification_email(email, token)
            return {"status": "ok", "message": "Verification email re-sent. Please check your inbox."}
        # Re-activate
        existing.is_active = True
        token = secrets.token_urlsafe(32)
        existing.verification_token = token
        existing.verified = False
        existing.unsubscribe_token = secrets.token_urlsafe(32)
        db.commit()
        send_verification_email(email, token)
    else:
        token = secrets.token_urlsafe(32)
        new_sub = Subscriber(
            email=email,
            is_active=True,
            verified=False,
            verification_token=token,
            unsubscribe_token=secrets.token_urlsafe(32),
        )
        db.add(new_sub)
        db.commit()
        send_verification_email(email, token)

    logger.info("Newsletter subscription (pending verification): %s", email)
    return {"status": "ok", "message": "Please check your email to confirm your subscription."}


@router.get("/verify-email")
def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    """Verify a subscriber's email address using the token from the verification email.

    After verification, sends a welcome email with this week's trending skills.
    """
    import secrets
    from app.models.skill import Subscriber
    from app.services.email_service import send_welcome_email

    subscriber = db.query(Subscriber).filter(Subscriber.verification_token == token).first()
    if not subscriber:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    if subscriber.verified:
        return Response(
            content=_verified_html("Email already verified!", "You're already subscribed. You can close this page."),
            media_type="text/html",
        )

    subscriber.verified = True
    subscriber.verified_at = datetime.now(timezone.utc)
    subscriber.verification_token = None  # Consume the token
    # Ensure unsubscribe token exists
    if not subscriber.unsubscribe_token:
        subscriber.unsubscribe_token = secrets.token_urlsafe(32)
    db.commit()

    logger.info("Email verified: %s", subscriber.email)

    # ── Send welcome email with trending skills ──
    try:
        from sqlalchemy import desc as _desc

        trending_raw = (
            db.query(Skill)
            .filter(Skill.score > 0)
            .order_by(_desc(Skill.star_momentum))
            .limit(5)
            .all()
        )
        trending_data = [
            {
                "repo_name": s.repo_name,
                "description": s.description or "",
                "stars": s.stars,
                "repo_url": s.repo_url,
                "score": round(s.score, 1) if s.score else 0,
                "category": s.category,
                "star_momentum": s.star_momentum or 0,
            }
            for s in trending_raw
        ]
        total_skills = db.query(func.count(Skill.id)).scalar() or 0
        unsub_url = f"{settings.site_url}/api/unsubscribe?token={subscriber.unsubscribe_token}"

        send_welcome_email(
            email=subscriber.email,
            trending_skills=trending_data,
            total_skills=total_skills,
            unsubscribe_url=unsub_url,
        )
        logger.info("Welcome email sent to %s", subscriber.email)
    except Exception as exc:
        logger.warning("Failed to send welcome email to %s: %s", subscriber.email, exc)

    return Response(
        content=_verified_html(
            "Email verified successfully! &#127881;",
            "Thank you for subscribing! A welcome email with this week's trending skills has been sent to your inbox. "
            "You'll receive weekly updates every Monday.",
        ),
        media_type="text/html",
    )


def _verified_html(title: str, message: str) -> str:
    """Pretty HTML page for verification result."""
    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title></head>
<body style="margin:0;padding:60px 20px;background:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;text-align:center;">
<div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="font-size:48px;margin-bottom:16px;">&#9989;</div>
  <h2 style="color:#1a1a2e;margin:0 0 12px;">{title}</h2>
  <p style="color:#4a5568;line-height:1.6;">{message}</p>
  <a href="{settings.site_url}" style="display:inline-block;margin-top:20px;padding:12px 28px;background:#4f46e5;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">
    Visit Agent Skills Hub
  </a>
</div>
</body>
</html>"""


@router.get("/unsubscribe")
def unsubscribe(token: str = Query(...), db: Session = Depends(get_db)):
    """One-click unsubscribe via token link in emails."""
    from app.models.skill import Subscriber

    subscriber = db.query(Subscriber).filter(Subscriber.unsubscribe_token == token).first()
    if not subscriber:
        raise HTTPException(status_code=400, detail="Invalid unsubscribe link")

    if not subscriber.is_active:
        return Response(
            content=_unsubscribe_html("Already unsubscribed", "You've already been removed from our mailing list."),
            media_type="text/html",
        )

    subscriber.is_active = False
    db.commit()
    logger.info("Unsubscribed: %s", subscriber.email)

    return Response(
        content=_unsubscribe_html(
            "Unsubscribed successfully",
            "You've been removed from the Agent Skills Hub newsletter. "
            "You can re-subscribe anytime on our website.",
        ),
        media_type="text/html",
    )


def _unsubscribe_html(title: str, message: str) -> str:
    """Pretty HTML page for unsubscribe result."""
    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title></head>
<body style="margin:0;padding:60px 20px;background:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;text-align:center;">
<div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="font-size:48px;margin-bottom:16px;">&#128075;</div>
  <h2 style="color:#1a1a2e;margin:0 0 12px;">{title}</h2>
  <p style="color:#4a5568;line-height:1.6;">{message}</p>
  <a href="{settings.site_url}" style="display:inline-block;margin-top:20px;padding:12px 28px;background:#4f46e5;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">
    Visit Agent Skills Hub
  </a>
</div>
</body>
</html>"""


@router.get("/feed.xml")
def rss_feed(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Response:
    """RSS 2.0 feed of latest skills added or updated."""
    items = (
        db.query(Skill)
        .filter(Skill.last_commit_at.isnot(None))
        .order_by(desc(Skill.last_synced))
        .limit(limit)
        .all()
    )

    site_url = settings.site_url or "https://agentskillshub.top"

    def _rfc822(dt: Optional[datetime]) -> str:
        if not dt:
            return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    item_xml_parts = []
    for skill in items:
        desc_text = _escape(skill.description or "No description")
        score_str = f"Score: {skill.score:.1f}" if skill.score else ""
        stars_str = f"Stars: {skill.stars}" if skill.stars else ""
        cat_str = skill.category or "uncategorized"

        item_xml_parts.append(
            f"""    <item>
      <title>{_escape(skill.repo_full_name)}</title>
      <link>{_escape(skill.repo_url)}</link>
      <guid isPermaLink="false">skill-{skill.id}</guid>
      <description>{desc_text} | {score_str} | {stars_str}</description>
      <category>{_escape(cat_str)}</category>
      <pubDate>{_rfc822(skill.last_commit_at)}</pubDate>
    </item>"""
        )

    last_build = _rfc822(datetime.now(timezone.utc))
    items_xml = "\n".join(item_xml_parts)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Agent Skills Hub - Latest Skills</title>
    <link>{site_url}</link>
    <description>Discover and compare open-source Agent Skills, tools and MCP servers. Auto-updated every 8 hours.</description>
    <language>en</language>
    <lastBuildDate>{last_build}</lastBuildDate>
    <atom:link href="{site_url}/api/feed.xml" rel="self" type="application/rss+xml"/>
{items_xml}
  </channel>
</rss>"""

    return Response(
        content=xml,
        media_type="application/rss+xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=1800, s-maxage=1800"},  # 30 min
    )


@router.get("/sitemap.xml")
def sitemap(db: Session = Depends(get_db)) -> Response:
    """Auto-generated sitemap for SEO. Includes all skill detail pages."""
    site_url = settings.site_url or "https://agentskillshub.top"

    skills = (
        db.query(Skill.repo_full_name, Skill.last_synced, Skill.score)
        .order_by(desc(Skill.score))
        .all()
    )

    urls = []
    # Homepage
    urls.append(
        f"""  <url>
    <loc>{site_url}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>"""
    )
    # Explore tab
    urls.append(
        f"""  <url>
    <loc>{site_url}/?tab=explore</loc>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>"""
    )

    for full_name, last_synced, score in skills:
        lastmod = ""
        if last_synced:
            if last_synced.tzinfo is None:
                last_synced = last_synced.replace(tzinfo=timezone.utc)
            lastmod = f"\n    <lastmod>{last_synced.strftime('%Y-%m-%d')}</lastmod>"
        # Higher-scored skills get higher priority
        priority = min(0.9, 0.4 + (score or 0) / 200) if score else 0.4
        urls.append(
            f"""  <url>
    <loc>{site_url}/skill/{full_name}</loc>{lastmod}
    <changefreq>weekly</changefreq>
    <priority>{priority:.1f}</priority>
  </url>"""
        )

    urls_xml = "\n".join(urls)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}
</urlset>"""

    return Response(
        content=xml,
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600, s-maxage=3600"},  # 1 hour
    )


# ═══ Workflow category metadata ═══
_WORKFLOW_META: dict[str, dict] = {
    "claude-skill": {
        "icon": "sparkles",
        "title_zh": "Claude 技能",
        "title_en": "Claude Skills",
        "description_zh": "为 Claude 量身打造的实用技能",
        "description_en": "Purpose-built skills for Claude",
        "sort_order": 1,
    },
    "mcp-server": {
        "icon": "server",
        "title_zh": "MCP 服务器",
        "title_en": "MCP Servers",
        "description_zh": "模型上下文协议工具集合",
        "description_en": "Model Context Protocol tool collection",
        "sort_order": 2,
    },
    "ai-skill": {
        "icon": "cpu",
        "title_zh": "AI 技能",
        "title_en": "AI Skills",
        "description_zh": "跨平台 AI 技能与插件",
        "description_en": "Cross-platform AI skills & plugins",
        "sort_order": 3,
    },
    "agent-tool": {
        "icon": "wrench",
        "title_zh": "Agent 工具",
        "title_en": "Agent Tools",
        "description_zh": "AI Agent 框架与工具",
        "description_en": "AI Agent frameworks & tools",
        "sort_order": 4,
    },
    "entertainment": {
        "icon": "music",
        "title_zh": "生活娱乐",
        "title_en": "Entertainment",
        "description_zh": "音乐、游戏等趣味技能",
        "description_en": "Music, games & fun skills",
        "sort_order": 5,
    },
    "codex-skill": {
        "icon": "code",
        "title_zh": "Codex 技能",
        "title_en": "Codex Skills",
        "description_zh": "OpenAI Codex 专属技能",
        "description_en": "OpenAI Codex skills",
        "sort_order": 6,
    },
    "llm-plugin": {
        "icon": "puzzle",
        "title_zh": "LLM 插件",
        "title_en": "LLM Plugins",
        "description_zh": "大语言模型插件与扩展",
        "description_en": "LLM plugins & extensions",
        "sort_order": 7,
    },
    "youmind-plugin": {
        "icon": "puzzle",
        "title_zh": "YouMind 插件",
        "title_en": "YouMind Plugins",
        "description_zh": "YouMind 平台专属插件",
        "description_en": "YouMind platform plugins",
        "sort_order": 8,
    },
}


@router.get("/workflows")
def get_workflows(db: Session = Depends(get_db)):
    """Dynamic skill workflows grouped by category.

    Returns top skills per category (min 2 skills). Cached for 10 minutes.
    """
    cat_rows = (
        db.query(Skill.category, func.count(Skill.id))
        .group_by(Skill.category)
        .having(func.count(Skill.id) >= 2)
        .all()
    )

    workflows = []
    for cat_name, count in cat_rows:
        meta = _WORKFLOW_META.get(cat_name)
        if not meta:
            continue  # skip uncategorized etc.

        skills = (
            db.query(Skill)
            .filter(Skill.category == cat_name)
            .order_by(desc(Skill.score))
            .limit(4)
            .all()
        )

        workflows.append({
            "id": cat_name,
            "icon": meta["icon"],
            "title_zh": meta["title_zh"],
            "title_en": meta["title_en"],
            "description_zh": meta["description_zh"],
            "description_en": meta["description_en"],
            "sort_order": meta["sort_order"],
            "skill_count": count,
            "skills": [
                {
                    "repo_name": s.repo_name,
                    "repo_full_name": s.repo_full_name,
                    "description": s.description or "",
                    "stars": s.stars,
                    "score": round(s.score, 1) if s.score else 0,
                    "author_name": s.author_name,
                }
                for s in skills
            ],
        })

    # Sort by predefined order
    workflows.sort(key=lambda w: w.get("sort_order", 99))
    for w in workflows:
        w.pop("sort_order", None)

    return _cached_json(workflows, max_age=600)  # 10 min


@router.get("/landing")
def get_landing_data(db: Session = Depends(get_db)):
    """Pre-rendered landing page data: bundles stats + trending + top-rated + hall-of-fame +
    recently-updated + categories + languages into a single cached response.

    Eliminates waterfall requests on first page load. Cached for 10 minutes.
    """
    now = datetime.now(timezone.utc)

    # 1. Stats
    total = db.query(func.count(Skill.id)).scalar() or 0
    avg = db.query(func.avg(Skill.score)).scalar() or 0.0
    cat_rows = (
        db.query(Skill.category, func.count(Skill.id))
        .group_by(Skill.category)
        .order_by(func.count(Skill.id).desc())
        .all()
    )
    last_sync = db.query(SyncLog).order_by(desc(SyncLog.started_at)).first()
    stats = {
        "total_skills": total,
        "avg_score": round(float(avg), 1),
        "categories": [{"name": name, "count": count} for name, count in cat_rows],
        "last_sync_at": last_sync.started_at.isoformat() if last_sync and last_sync.started_at else None,
        "last_sync_status": last_sync.status if last_sync else None,
    }

    # 2. Trending (star velocity, last 7 days)
    since_7 = now - timedelta(days=7)
    trending_raw = (
        db.query(Skill)
        .filter(Skill.stars >= 50, Skill.created_at.isnot(None), Skill.created_at >= since_7)
        .all()
    )

    def _velocity(s: Skill) -> float:
        c = s.created_at
        if c.tzinfo is None:
            c = c.replace(tzinfo=timezone.utc)
        return s.stars / max((now - c).total_seconds() / 86400, 1)

    trending = sorted(trending_raw, key=_velocity, reverse=True)[:10]
    trending_data = [SkillResponse.model_validate(s).model_dump(mode="json") for s in trending]

    # 3. Rising (new this week)
    rising_raw = (
        db.query(Skill)
        .filter(Skill.created_at >= since_7)
        .order_by(desc(Skill.stars))
        .limit(10)
        .all()
    )
    rising_data = [SkillResponse.model_validate(s).model_dump(mode="json") for s in rising_raw]

    # 4. Top rated
    top_rated = (
        db.query(Skill).order_by(desc(Skill.score)).limit(10).all()
    )
    top_rated_data = [SkillResponse.model_validate(s).model_dump(mode="json") for s in top_rated]

    # 5. Hall of fame (community classics, >6 months, 100+ stars)
    cutoff = now - timedelta(days=180)
    hall = (
        db.query(Skill)
        .filter(Skill.stars >= 100, Skill.created_at.isnot(None), Skill.created_at <= cutoff)
        .order_by(desc(Skill.stars))
        .limit(10)
        .all()
    )
    hall_data = [SkillResponse.model_validate(s).model_dump(mode="json") for s in hall]

    # 6. Recently updated
    recent = (
        db.query(Skill)
        .filter(Skill.last_commit_at.isnot(None))
        .order_by(desc(Skill.last_commit_at))
        .limit(10)
        .all()
    )
    recent_data = [SkillResponse.model_validate(s).model_dump(mode="json") for s in recent]

    # 7. Language stats
    lang_rows = (
        db.query(Skill.language, func.count(Skill.id))
        .filter(Skill.language != "")
        .group_by(Skill.language)
        .order_by(func.count(Skill.id).desc())
        .limit(10)
        .all()
    )
    languages = [{"language": lang, "count": cnt} for lang, cnt in lang_rows]

    landing = {
        "stats": stats,
        "trending": trending_data,
        "rising": rising_data,
        "top_rated": top_rated_data,
        "hall_of_fame": hall_data,
        "recently_updated": recent_data,
        "languages": languages,
        "generated_at": now.isoformat(),
    }
    return _cached_json(landing, max_age=600)  # 10 min


# ═══ Security Analyzer (on-demand scanning) ═══

# Simple in-memory rate limiter
_analyzer_requests: dict[str, list[float]] = {}
_ANALYZER_RATE_LIMIT = 10  # per minute per IP
_ANALYZER_WINDOW = 60  # seconds


def _check_rate_limit(client_ip: str) -> bool:
    """Return True if request is allowed, False if rate-limited."""
    import time
    now = time.time()
    reqs = _analyzer_requests.get(client_ip, [])
    # Clean old entries
    reqs = [t for t in reqs if now - t < _ANALYZER_WINDOW]
    if len(reqs) >= _ANALYZER_RATE_LIMIT:
        _analyzer_requests[client_ip] = reqs
        return False
    reqs.append(now)
    _analyzer_requests[client_ip] = reqs
    return True


@router.post("/analyzer/scan")
def analyzer_scan(
    body: dict,
    db: Session = Depends(get_db),
):
    """On-demand security analysis for any GitHub repo URL.

    1. Parses repo URL → owner/repo
    2. Checks if already indexed in DB
    3. If not, fetches from GitHub API
    4. Runs rule-based security scan
    5. If flagged + API key available, runs LLM deep analysis
    6. Returns combined results
    """
    import re as _re
    import time

    repo_url = body.get("repo_url", "").strip()
    if not repo_url:
        raise HTTPException(status_code=400, detail="repo_url is required")

    # Parse GitHub URL
    match = _re.match(
        r"(?:https?://)?github\.com/([^/]+/[^/]+?)(?:\.git)?/?$", repo_url
    )
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")

    full_name = match.group(1)

    # Check if already indexed
    existing = db.query(Skill).filter(Skill.repo_full_name == full_name).first()

    if existing:
        # Return existing data
        from app.services.security_scanner import SecurityScanner

        rule_grade = existing.security_grade or "unknown"
        rule_flags = json.loads(existing.security_flags or "[]")
        llm_analysis = None
        llm_grade = existing.security_llm_grade

        if existing.security_llm_analysis:
            try:
                llm_analysis = json.loads(existing.security_llm_analysis)
            except json.JSONDecodeError:
                pass

        # If no LLM analysis yet and flagged, try now
        if (
            not llm_analysis
            and rule_grade in ("caution", "unsafe")
            and existing.readme_content
            and (settings.llm_api_key or settings.anthropic_api_key)
        ):
            try:
                from app.services.llm_security_analyzer import LLMSecurityAnalyzer

                _key = settings.llm_api_key or settings.anthropic_api_key
                analyzer = LLMSecurityAnalyzer(api_key=_key, model=settings.llm_model, base_url=settings.llm_base_url)
                llm_analysis = analyzer.analyze_single(
                    existing.readme_content,
                    {
                        "full_name": existing.repo_full_name,
                        "stars": existing.stars or 0,
                        "license": existing.license or "none",
                        "category": existing.category or "unknown",
                        "description": existing.description or "",
                        "flags": rule_flags,
                    },
                )
                llm_grade = llm_analysis.get("grade", rule_grade)
                # Persist
                existing.security_llm_grade = llm_grade
                existing.security_llm_analysis = json.dumps(llm_analysis)
                db.commit()
            except Exception as e:
                logger.warning("LLM analysis failed for %s: %s", full_name, e)

        final_grade = llm_grade or rule_grade

        # Trust tier & flag details
        from app.services.security_scanner import SecurityScanner as _SC, _get_trust_tier
        _tier = _get_trust_tier(existing)
        _flag_details = [
            {"name": f, "severity": _SC.get_flag_severity(f), "description": _SC.get_flag_description(f)}
            for f in rule_flags
        ]

        return {
            "repo": {
                "full_name": existing.repo_full_name,
                "stars": existing.stars,
                "description": existing.description,
                "license": existing.license,
                "category": existing.category,
                "repo_url": existing.repo_url,
            },
            "indexed": True,
            "security": {
                "rule_grade": rule_grade,
                "llm_grade": llm_grade,
                "final_grade": final_grade,
                "flags": rule_flags,
                "flag_details": _flag_details,
                "trust_tier": _tier,
                "trust_label": _SC.get_trust_tier_label(_tier),
                "llm_analysis": llm_analysis,
            },
            "quality": {
                "score": existing.quality_score,
                "completeness": existing.quality_completeness,
                "clarity": existing.quality_clarity,
                "specificity": existing.quality_specificity,
                "examples": existing.quality_examples,
                "agent_readiness": existing.quality_agent_readiness,
            },
        }

    # Not indexed — fetch from GitHub
    import httpx

    headers = {}
    if settings.github_token:
        headers["Authorization"] = f"token {settings.github_token}"
    headers["Accept"] = "application/vnd.github.v3+json"

    try:
        with httpx.Client(timeout=15) as client:
            # Fetch repo info
            repo_resp = client.get(
                f"https://api.github.com/repos/{full_name}", headers=headers
            )
            if repo_resp.status_code == 404:
                raise HTTPException(
                    status_code=404, detail=f"Repository {full_name} not found"
                )
            repo_resp.raise_for_status()
            repo_info = repo_resp.json()

            # Fetch README
            readme_resp = client.get(
                f"https://api.github.com/repos/{full_name}/readme",
                headers={**headers, "Accept": "application/vnd.github.v3.raw"},
            )
            readme_content = readme_resp.text if readme_resp.status_code == 200 else ""

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"GitHub API unreachable: {str(e)}")

    # Run rule-based scan
    from app.services.security_scanner import SecurityScanner

    # Create a temporary Skill-like object for scanning
    class _TempSkill:
        def __init__(self, readme, stars, license_name, author):
            self.readme_content = readme
            self.stars = stars
            self.license = license_name
            self.author_name = author

    license_info = repo_info.get("license") or {}
    license_name = license_info.get("spdx_id", "") if isinstance(license_info, dict) else ""
    owner_login = (repo_info.get("owner") or {}).get("login", "unknown")

    temp_skill = _TempSkill(readme_content, repo_info.get("stargazers_count", 0), license_name, owner_login)
    scanner = SecurityScanner()
    rule_grade, rule_flags = scanner.scan_single(temp_skill)

    # LLM deep analysis if flagged
    llm_analysis = None
    llm_grade = None
    _llm_key = settings.llm_api_key or settings.anthropic_api_key
    if rule_grade in ("caution", "unsafe") and readme_content and _llm_key:
        try:
            from app.services.llm_security_analyzer import LLMSecurityAnalyzer

            analyzer = LLMSecurityAnalyzer(api_key=_llm_key, model=settings.llm_model, base_url=settings.llm_base_url)
            llm_analysis = analyzer.analyze_repo_readme(
                readme_content,
                {
                    "full_name": full_name,
                    "stargazers_count": repo_info.get("stargazers_count", 0),
                    "license": license_name,
                    "category": "unknown",
                    "description": repo_info.get("description", ""),
                    "flags": rule_flags,
                },
            )
            llm_grade = llm_analysis.get("grade", rule_grade)
        except Exception as e:
            logger.warning("LLM on-demand analysis failed for %s: %s", full_name, e)

    final_grade = llm_grade or rule_grade

    # Trust tier & flag details
    from app.services.security_scanner import SecurityScanner as _SC2, _get_trust_tier as _gtt2
    _tier2 = _gtt2(temp_skill)
    _flag_details2 = [
        {"name": f, "severity": _SC2.get_flag_severity(f), "description": _SC2.get_flag_description(f)}
        for f in rule_flags
    ]

    return {
        "repo": {
            "full_name": full_name,
            "stars": repo_info.get("stargazers_count", 0),
            "description": repo_info.get("description", ""),
            "license": license_name,
            "category": None,
            "repo_url": repo_info.get("html_url", f"https://github.com/{full_name}"),
        },
        "indexed": False,
        "security": {
            "rule_grade": rule_grade,
            "llm_grade": llm_grade,
            "final_grade": final_grade,
            "flags": rule_flags,
            "flag_details": _flag_details2,
            "trust_tier": _tier2,
            "trust_label": _SC2.get_trust_tier_label(_tier2),
            "llm_analysis": llm_analysis,
        },
        "quality": None,
    }
