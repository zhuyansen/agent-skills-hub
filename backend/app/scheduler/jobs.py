import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

SEARCH_QUERIES = [
    "mcp-server in:name,topics",
    "claude-mcp in:name,description,topics",
    "model-context-protocol in:name,description,topics",
    "mcp in:topics language:python",
    "mcp in:topics language:typescript",
    "agent-tools in:name,description,topics",
    "codex-skills in:name,description,topics",
    "youmind in:name,description,topics",
    "claude-skill in:name,description,topics",
    "ai-agent-tool in:name,description,topics",
    "llm-tool in:name,description,topics",
]

# Masters / influencers whose repos should always be collected
MASTERS_USERS = [
    "op7418", "zarazhangrui",
    "joeseesun",  # vista8 / 向阳乔木
    "dotey", "JimLiu",  # dotey / 宝玉
    "Panniantong",
]

# Specific repos to always include (manually curated)
EXTRA_REPOS = [
    "runningZ1/union-search-skill",
    "Panniantong/Agent-Reach",
    "JimLiu/baoyu-skills",
    "joeseesun/yt-search-download",
    "joeseesun/anything-to-notebooklm",
    "joeseesun/skill-publisher",
    "joeseesun/defuddle-skill",
    "joeseesun/qiaomu-x-article-publisher",
    "joeseesun/knowledge-site-creator",
    "joeseesun/qiaomu-music-player-spotify",
    "joeseesun/qiaomu-design-advisor",
]


async def _github_request(
    client: httpx.AsyncClient,
    url: str,
    params: Optional[dict] = None,
    retry: int = 0,
) -> dict[str, Any]:
    if retry > 2:
        return {"items": [], "total_count": 0}

    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    resp = await client.get(url, headers=headers, params=params)

    if resp.status_code in (403, 429):
        reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
        wait = max(reset_ts - time.time(), 0) + 5 if reset_ts else 60
        wait = min(wait, 120)
        logger.warning("Rate limited (%d). Sleeping %.0fs", resp.status_code, wait)
        await asyncio.sleep(wait)
        return await _github_request(client, url, params, retry + 1)

    if resp.status_code == 422:
        return {"items": [], "total_count": 0}

    resp.raise_for_status()
    return resp.json()


async def sync_all_skills(sync_log_id: Optional[int] = None) -> None:
    """Main scheduled sync: fetch GitHub data, clean, upsert, and re-score.

    Args:
        sync_log_id: If provided, reuse an existing SyncLog instead of creating a new one.
    """
    from app.database import SessionLocal
    from app.models.skill import Skill, SyncLog
    from app.services.data_cleaner import DataCleaner
    from app.services.scorer import ScoringEngine

    db = SessionLocal()
    if sync_log_id:
        sync_log = db.query(SyncLog).filter(SyncLog.id == sync_log_id).first()
        if not sync_log:
            sync_log = SyncLog(status="running")
            db.add(sync_log)
            db.commit()
            db.refresh(sync_log)
    else:
        sync_log = SyncLog(status="running")
        db.add(sync_log)
        db.commit()
        db.refresh(sync_log)

    try:
        all_repos: dict[str, dict] = {}
        owner_cache: dict[str, int] = {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in SEARCH_QUERIES:
                try:
                    for page in range(1, 4):  # up to 3 pages
                        data = await _github_request(
                            client,
                            "https://api.github.com/search/repositories",
                            params={"q": query, "per_page": 100, "page": page, "sort": "stars"},
                        )
                        items = data.get("items", [])
                        for repo in items:
                            fn = repo.get("full_name", "")
                            if fn and fn not in all_repos:
                                all_repos[fn] = repo
                        if len(items) < 100:
                            break
                        await asyncio.sleep(2.5)
                except Exception as exc:
                    logger.error("Search failed [%s]: %s", query, exc)
                await asyncio.sleep(3)

            # ── Phase 2: Fetch repos for masters (by username) ──
            for username in MASTERS_USERS:
                try:
                    for page in range(1, 4):
                        data = await _github_request(
                            client,
                            f"https://api.github.com/users/{username}/repos",
                            params={"per_page": 100, "page": page, "sort": "stars"},
                        )
                        # user repos endpoint returns a list, not search-style dict
                        items = data if isinstance(data, list) else data.get("items", [])
                        for repo in items:
                            fn = repo.get("full_name", "")
                            if fn and fn not in all_repos:
                                all_repos[fn] = repo
                        if len(items) < 100:
                            break
                        await asyncio.sleep(1)
                except Exception as exc:
                    logger.error("Masters fetch failed [%s]: %s", username, exc)
                await asyncio.sleep(1)

            logger.info("After masters fetch: %d unique repos", len(all_repos))

            # ── Phase 3: Fetch curated extra repos ──
            for full_name in EXTRA_REPOS:
                if full_name in all_repos:
                    continue
                try:
                    repo_data = await _github_request(
                        client, f"https://api.github.com/repos/{full_name}"
                    )
                    if repo_data.get("full_name"):
                        all_repos[full_name] = repo_data
                        logger.info("Added extra repo %s", full_name)
                    await asyncio.sleep(1)
                except Exception as exc:
                    logger.error("Extra repo fetch failed [%s]: %s", full_name, exc)

            # Enrich with owner followers
            count = 0
            for fn, repo in all_repos.items():
                owner_login = repo.get("owner", {}).get("login", "")
                if owner_login and owner_login not in owner_cache:
                    try:
                        user_data = await _github_request(
                            client, f"https://api.github.com/users/{owner_login}"
                        )
                        owner_cache[owner_login] = user_data.get("followers", 0)
                        await asyncio.sleep(0.3)
                    except Exception:
                        owner_cache[owner_login] = 0
                repo["_owner_followers"] = owner_cache.get(owner_login, 0)
                # open_issues_count from GitHub API actually includes PRs;
                # use it as total_issues for scoring (closed = total - open)
                repo["_total_issues"] = repo.get("open_issues_count", 0) + repo.get("_closed_issues", 0)
                repo["_total_commits"] = repo.get("_total_commits", 0)
                count += 1
                if count % 100 == 0:
                    logger.info("Enriched %d/%d repos", count, len(all_repos))

        # ── Phase 4: Fetch README content (incremental, max 300 per sync) ──
        readme_cache: dict[str, str] = {}
        try:
            null_readme_skills = (
                db.query(Skill.repo_full_name)
                .filter(Skill.readme_content.is_(None))
                .limit(300)
                .all()
            )
            readme_targets = {r.repo_full_name for r in null_readme_skills} & set(all_repos.keys())
            if readme_targets:
                logger.info("Fetching README for %d skills", len(readme_targets))
                readme_headers = {"Accept": "application/vnd.github.raw"}
                if settings.github_token:
                    readme_headers["Authorization"] = f"Bearer {settings.github_token}"
                async with httpx.AsyncClient(timeout=30.0) as readme_client:
                    fetched = 0
                    for full_name in readme_targets:
                        try:
                            resp = await readme_client.get(
                                f"https://api.github.com/repos/{full_name}/readme",
                                headers=readme_headers,
                            )
                            if resp.status_code == 200:
                                readme_cache[full_name] = resp.text[:50000]
                            fetched += 1
                            if fetched % 50 == 0:
                                logger.info("README fetch: %d/%d", fetched, len(readme_targets))
                            await asyncio.sleep(0.5)
                        except Exception:
                            pass
                logger.info("README fetch complete: %d/%d successful", len(readme_cache), len(readme_targets))
        except Exception as exc:
            logger.warning("README fetch phase failed: %s", exc)

        cleaner = DataCleaner()
        cleaned = cleaner.process(list(all_repos.values()))

        new_count, updated_count = 0, 0
        for repo_data in cleaned:
            existing = (
                db.query(Skill)
                .filter(Skill.repo_full_name == repo_data["repo_full_name"])
                .first()
            )
            if existing:
                existing.prev_stars = existing.stars  # capture before overwrite
                for key, val in repo_data.items():
                    setattr(existing, key, val)
                readme = readme_cache.get(existing.repo_full_name)
                if readme:
                    existing.readme_content = readme
                    existing.readme_size = len(readme)
                updated_count += 1
            else:
                new_skill = Skill(**repo_data)
                readme = readme_cache.get(repo_data.get("repo_full_name", ""))
                if readme:
                    new_skill.readme_content = readme
                    new_skill.readme_size = len(readme)
                db.add(new_skill)
                new_count += 1

        db.commit()

        scoring_engine = ScoringEngine()
        scoring_engine.score_all(db)

        from app.services.composability import ComposabilityEngine
        ComposabilityEngine().compute_all(db)

        sync_log.status = "completed"
        sync_log.repos_found = len(cleaned)
        sync_log.repos_new = new_count
        sync_log.repos_updated = updated_count
        sync_log.finished_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "Sync completed: %d found, %d new, %d updated",
            len(cleaned), new_count, updated_count,
        )

    except Exception as exc:
        sync_log.status = "failed"
        sync_log.error_message = str(exc)[:1000]
        sync_log.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.exception("Sync job failed")
    finally:
        db.close()


def run_sync(sync_log_id: int) -> None:
    """Synchronous wrapper for background task triggered by POST /api/sync."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(sync_all_skills(sync_log_id=sync_log_id))
    finally:
        loop.close()
