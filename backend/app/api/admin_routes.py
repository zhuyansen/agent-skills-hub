"""Admin API routes with simple token-based authentication."""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.admin import ExtraRepo, SearchQuery, SkillMaster
from app.models.skill import Skill, Subscriber, SyncLog
from app.schemas.admin import (
    ExtraRepoCreate,
    ExtraRepoResponse,
    MasterCreate,
    MasterResponse,
    MasterUpdate,
    SearchQueryCreate,
    SearchQueryResponse,
    SkillUpdateAdmin,
)
from app.schemas.skill import SkillResponse

logger = logging.getLogger(__name__)
admin_router = APIRouter(prefix="/api/admin")


def verify_admin(authorization: str = Header(default="")) -> None:
    """Simple bearer token authentication."""
    if not settings.admin_token:
        raise HTTPException(403, "Admin token not configured")
    expected = f"Bearer {settings.admin_token}"
    if authorization != expected:
        raise HTTPException(401, "Invalid admin token")


# ═══ Masters CRUD ═══

@admin_router.get("/masters", response_model=list[MasterResponse])
def list_masters(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> list[MasterResponse]:
    masters = db.query(SkillMaster).order_by(desc(SkillMaster.id)).all()
    return [MasterResponse.model_validate(m) for m in masters]


@admin_router.post("/masters", response_model=MasterResponse)
def create_master(
    data: MasterCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> MasterResponse:
    existing = db.query(SkillMaster).filter(SkillMaster.github == data.github).first()
    if existing:
        raise HTTPException(400, f"Master '{data.github}' already exists")
    master = SkillMaster(
        github=data.github,
        name=data.name,
        github_aliases=json.dumps(data.github_aliases),
        x_handle=data.x_handle,
        bio=data.bio,
        tags=json.dumps(data.tags),
        x_followers=data.x_followers,
        x_posts_count=data.x_posts_count,
        x_notes=data.x_notes,
    )
    db.add(master)
    db.commit()
    db.refresh(master)
    return MasterResponse.model_validate(master)


@admin_router.put("/masters/{master_id}", response_model=MasterResponse)
def update_master(
    master_id: int,
    data: MasterUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> MasterResponse:
    master = db.query(SkillMaster).filter(SkillMaster.id == master_id).first()
    if not master:
        raise HTTPException(404, "Master not found")
    if data.name is not None:
        master.name = data.name
    if data.github_aliases is not None:
        master.github_aliases = json.dumps(data.github_aliases)
    if data.x_handle is not None:
        master.x_handle = data.x_handle
    if data.bio is not None:
        master.bio = data.bio
    if data.tags is not None:
        master.tags = json.dumps(data.tags)
    if data.is_active is not None:
        master.is_active = data.is_active
    if data.x_followers is not None:
        master.x_followers = data.x_followers
    if data.x_posts_count is not None:
        master.x_posts_count = data.x_posts_count
    if data.x_verified_at is not None:
        master.x_verified_at = data.x_verified_at
    if data.x_notes is not None:
        master.x_notes = data.x_notes
    db.commit()
    db.refresh(master)
    return MasterResponse.model_validate(master)


@admin_router.delete("/masters/{master_id}")
def delete_master(
    master_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> dict:
    master = db.query(SkillMaster).filter(SkillMaster.id == master_id).first()
    if not master:
        raise HTTPException(404, "Master not found")
    master.is_active = False
    db.commit()
    return {"message": "Master deactivated"}


# ═══ Extra Repos CRUD ═══

@admin_router.get("/extra-repos", response_model=list[ExtraRepoResponse])
def list_extra_repos(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> list[ExtraRepoResponse]:
    repos = db.query(ExtraRepo).order_by(desc(ExtraRepo.id)).all()
    return [ExtraRepoResponse.model_validate(r) for r in repos]


@admin_router.post("/extra-repos", response_model=ExtraRepoResponse)
def create_extra_repo(
    data: ExtraRepoCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> ExtraRepoResponse:
    existing = db.query(ExtraRepo).filter(ExtraRepo.full_name == data.full_name).first()
    if existing:
        raise HTTPException(400, f"Repo '{data.full_name}' already exists")
    repo = ExtraRepo(full_name=data.full_name)
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return ExtraRepoResponse.model_validate(repo)


@admin_router.delete("/extra-repos/{repo_id}")
def delete_extra_repo(
    repo_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> dict:
    repo = db.query(ExtraRepo).filter(ExtraRepo.id == repo_id).first()
    if not repo:
        raise HTTPException(404, "Repo not found")
    db.delete(repo)
    db.commit()
    return {"message": "Repo removed"}


@admin_router.put("/extra-repos/{repo_id}/approve")
def approve_extra_repo(
    repo_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> dict:
    """Approve a pending community submission. Makes it active for next sync."""
    repo = db.query(ExtraRepo).filter(ExtraRepo.id == repo_id).first()
    if not repo:
        raise HTTPException(404, "Repo not found")
    repo.status = "approved"
    repo.is_active = True
    repo.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Repo '{repo.full_name}' approved and will be included in next sync"}


@admin_router.put("/extra-repos/{repo_id}/reject")
def reject_extra_repo(
    repo_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> dict:
    """Reject a pending community submission."""
    repo = db.query(ExtraRepo).filter(ExtraRepo.id == repo_id).first()
    if not repo:
        raise HTTPException(404, "Repo not found")
    repo.status = "rejected"
    repo.is_active = False
    repo.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Repo '{repo.full_name}' rejected"}


# ═══ Search Queries CRUD ═══

@admin_router.get("/search-queries", response_model=list[SearchQueryResponse])
def list_search_queries(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> list[SearchQueryResponse]:
    queries = db.query(SearchQuery).order_by(desc(SearchQuery.id)).all()
    return [SearchQueryResponse.model_validate(q) for q in queries]


@admin_router.post("/search-queries", response_model=SearchQueryResponse)
def create_search_query(
    data: SearchQueryCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> SearchQueryResponse:
    existing = db.query(SearchQuery).filter(SearchQuery.query == data.query).first()
    if existing:
        raise HTTPException(400, "Query already exists")
    query = SearchQuery(query=data.query)
    db.add(query)
    db.commit()
    db.refresh(query)
    return SearchQueryResponse.model_validate(query)


@admin_router.delete("/search-queries/{query_id}")
def delete_search_query(
    query_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> dict:
    query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
    if not query:
        raise HTTPException(404, "Query not found")
    db.delete(query)
    db.commit()
    return {"message": "Query removed"}


# ═══ Skills Admin ═══

@admin_router.get("/skills", response_model=list[SkillResponse])
def list_admin_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> list[SkillResponse]:
    query = db.query(Skill).order_by(desc(Skill.score))
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Skill.repo_name.ilike(pattern)
            | Skill.author_name.ilike(pattern)
            | Skill.description.ilike(pattern)
        )
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return [SkillResponse.model_validate(s) for s in items]


@admin_router.put("/skills/{skill_id}", response_model=SkillResponse)
def update_skill_admin(
    skill_id: int,
    data: SkillUpdateAdmin,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> SkillResponse:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(404, "Skill not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)
    db.commit()
    db.refresh(skill)
    return SkillResponse.model_validate(skill)


@admin_router.delete("/skills/{skill_id}")
def delete_skill_admin(
    skill_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> dict:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(404, "Skill not found")
    db.delete(skill)
    db.commit()
    return {"message": "Skill deleted"}


# ═══ Subscribers Management ═══

@admin_router.get("/subscribers")
def list_subscribers(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> list[dict]:
    """List all newsletter subscribers."""
    subs = db.query(Subscriber).order_by(desc(Subscriber.id)).all()
    return [
        {
            "id": s.id,
            "email": s.email,
            "subscribed_at": s.subscribed_at.isoformat() if s.subscribed_at else None,
            "is_active": s.is_active,
            "verified": s.verified,
            "verified_at": s.verified_at.isoformat() if s.verified_at else None,
        }
        for s in subs
    ]


@admin_router.delete("/subscribers/{sub_id}")
def delete_subscriber(
    sub_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> dict:
    sub = db.query(Subscriber).filter(Subscriber.id == sub_id).first()
    if not sub:
        raise HTTPException(404, "Subscriber not found")
    db.delete(sub)
    db.commit()
    return {"message": f"Subscriber '{sub.email}' removed"}


@admin_router.post("/newsletter/send")
def send_newsletter_email(
    body: dict = None,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> dict:
    """Send weekly newsletter to all verified subscribers (or a specific email for testing).

    Request body (optional):
      - test_email: Send only to this email (for testing)
    """
    from app.services.email_service import send_newsletter

    body = body or {}
    test_email = body.get("test_email", "").strip()

    # Get trending skills
    trending = (
        db.query(Skill)
        .filter(Skill.score > 0)
        .order_by(desc(Skill.star_momentum))
        .limit(10)
        .all()
    )
    trending_data = [
        {
            "repo_name": s.repo_name,
            "description": s.description or "",
            "stars": s.stars,
            "repo_url": s.repo_url,
            "score": s.score,
            "category": s.category,
            "star_momentum": s.star_momentum or 0,
        }
        for s in trending
    ]

    # Stats
    from datetime import timedelta
    total_skills = db.query(Skill).count()
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_skills = db.query(Skill).filter(Skill.first_seen >= week_ago).count()

    if test_email:
        # Test mode: send to a specific email (no unsubscribe token needed)
        recipients = [{"email": test_email, "unsubscribe_token": ""}]
        logger.info("Sending test newsletter to: %s", test_email)
    else:
        # Production: send to all verified, active subscribers
        import secrets
        verified_subs = (
            db.query(Subscriber)
            .filter(Subscriber.is_active == True, Subscriber.verified == True)  # noqa: E712
            .all()
        )
        if not verified_subs:
            return {"status": "error", "message": "No verified subscribers found"}

        # Ensure all subscribers have unsubscribe tokens
        for sub in verified_subs:
            if not sub.unsubscribe_token:
                sub.unsubscribe_token = secrets.token_urlsafe(32)
        db.commit()

        recipients = [
            {"email": s.email, "unsubscribe_token": s.unsubscribe_token or ""}
            for s in verified_subs
        ]
        logger.info("Sending newsletter to %d verified subscribers", len(recipients))

    result = send_newsletter(
        recipients=recipients,
        trending_skills=trending_data,
        new_skills_count=new_skills,
        total_skills=total_skills,
    )
    return {"status": "ok", **result}


@admin_router.post("/newsletter/test-verification")
def test_verification_email(
    body: dict,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> dict:
    """Send a test verification email to a specific address."""
    import secrets
    from app.services.email_service import send_verification_email

    email = body.get("email", "").strip()
    if not email:
        raise HTTPException(400, "Email is required")

    token = secrets.token_urlsafe(32)
    ok = send_verification_email(email, token)
    return {
        "status": "ok" if ok else "error",
        "message": f"Verification email {'sent' if ok else 'failed'} to {email}",
        "token": token,
    }


# ═══ Sync Management ═══

@admin_router.get("/sync-logs")
def list_sync_logs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> list[dict]:
    logs = db.query(SyncLog).order_by(desc(SyncLog.started_at)).limit(limit).all()
    return [
        {
            "id": log.id,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "finished_at": log.finished_at.isoformat() if log.finished_at else None,
            "status": log.status,
            "repos_found": log.repos_found,
            "repos_new": log.repos_new,
            "repos_updated": log.repos_updated,
            "error_message": log.error_message,
        }
        for log in logs
    ]


@admin_router.post("/sync")
def trigger_admin_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
) -> dict:
    from app.scheduler.jobs import run_sync

    sync_log = SyncLog(status="running")
    db.add(sync_log)
    db.commit()
    db.refresh(sync_log)

    background_tasks.add_task(run_sync, sync_log.id)
    return {"message": "Sync started", "sync_id": sync_log.id}
