import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

SEARCH_QUERIES = [
    # ── Core MCP ecosystem (highest priority) ──
    "mcp-server in:name,topics",
    "claude-mcp in:name,description,topics",
    "model-context-protocol in:name,description,topics",
    "mcp in:topics language:python",
    "mcp in:topics language:typescript",
    "mcp-tool in:name,topics",
    "mcp-plugin in:name,description,topics",
    # ── Claude / Anthropic skills ──
    "claude-skill in:name,description,topics",
    "claude-code-skill in:name,description,topics",
    "claude-code in:topics",
    "anthropic in:topics language:python",
    "anthropic in:topics language:typescript",
    # ── Agent tools & frameworks ──
    "agent-tools in:name,description,topics",
    "ai-agent-tool in:name,description,topics",
    "agent-skill in:name,topics",
    "llm-tool in:name,description,topics",
    "llm-agent in:name,topics stars:>10",
    "ai-tools in:topics stars:>20",
    # ── Codex / OpenAI agent skills ──
    "codex-skills in:name,description,topics",
    "codex-cli in:name,topics",
    "openai-agent in:name,topics",
    "openai-tool in:name,topics",
    # ── Gemini / Google agent skills ──
    "gemini-agent in:name,topics",
    "gemini-tool in:name,description,topics",
    # ── YouMind / other platforms ──
    "youmind in:name,description,topics",
    "youmind-plugin in:name,topics",
    # ── Trending topics (broader discovery) ──
    "function-calling in:topics language:python stars:>50",
    "tool-use in:topics language:typescript stars:>50",
    "ai-automation in:topics stars:>20",
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


class RateLimitExhausted(Exception):
    """Raised when GitHub API rate limit is fully exhausted and we should stop."""
    pass


# Global flag to track rate limit state within a sync session
_rate_limit_exhausted = False
_rate_limit_reset_at = 0


async def _github_request(
    client: httpx.AsyncClient,
    url: str,
    params: Optional[dict] = None,
    retry: int = 0,
) -> dict[str, Any]:
    global _rate_limit_exhausted, _rate_limit_reset_at

    # If rate limit already known to be exhausted, fail fast
    if _rate_limit_exhausted:
        if time.time() < _rate_limit_reset_at:
            raise RateLimitExhausted(f"Rate limit exhausted until {_rate_limit_reset_at}")
        else:
            # Reset window has passed, try again
            _rate_limit_exhausted = False

    if retry > 1:
        # Max 2 retries (3 total attempts). If still failing, mark rate exhausted.
        _rate_limit_exhausted = True
        logger.warning("Max retries reached for %s, marking rate limit exhausted", url[:80])
        return {"items": [], "total_count": 0}

    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    resp = await client.get(url, headers=headers, params=params)

    # Check remaining rate limit from headers
    remaining = int(resp.headers.get("X-RateLimit-Remaining", "999"))
    if remaining <= 5 and remaining >= 0:
        reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
        if reset_ts:
            _rate_limit_reset_at = reset_ts
        logger.warning("Rate limit nearly exhausted: %d remaining, reset at %d", remaining, reset_ts)

    if resp.status_code in (403, 429):
        reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
        wait_time = max(reset_ts - time.time(), 0) + 5 if reset_ts else 60
        wait_time = min(wait_time, 60)  # Max 60s wait per retry (down from 120)

        if reset_ts:
            _rate_limit_reset_at = reset_ts

        logger.warning(
            "Rate limited (%d). Retry %d/1, sleeping %.0fs (reset at %s)",
            resp.status_code, retry, wait_time,
            datetime.fromtimestamp(reset_ts).strftime('%H:%M:%S') if reset_ts else "unknown"
        )
        await asyncio.sleep(wait_time)
        return await _github_request(client, url, params, retry + 1)

    if resp.status_code == 422:
        return {"items": [], "total_count": 0}

    resp.raise_for_status()
    return resp.json()


def _get_last_successful_sync(db: "Session") -> Optional[datetime]:
    """Get the timestamp of the last successful sync for incremental mode."""
    from app.models.skill import SyncLog
    last = (
        db.query(SyncLog)
        .filter(SyncLog.status == "completed")
        .order_by(SyncLog.finished_at.desc())
        .first()
    )
    return last.finished_at if last else None


async def sync_all_skills(sync_log_id: Optional[int] = None, incremental: bool = True) -> None:
    """Main scheduled sync: fetch GitHub data, clean, upsert, and re-score.

    Args:
        sync_log_id: If provided, reuse an existing SyncLog instead of creating a new one.
        incremental: If True, only fetch repos pushed since last successful sync.
                     Falls back to full sync if no previous sync found.
    """
    global _rate_limit_exhausted, _rate_limit_reset_at

    from app.database import SessionLocal
    from app.models.skill import Skill, SyncLog
    from app.services.data_cleaner import DataCleaner
    from app.services.scorer import ScoringEngine

    # Reset global rate limit state for this sync session
    _rate_limit_exhausted = False
    _rate_limit_reset_at = 0

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

        # ── Incremental sync: determine pushed:> filter ──
        pushed_filter = ""
        if incremental:
            last_sync_at = _get_last_successful_sync(db)
            if last_sync_at:
                # Add 1-hour buffer to avoid missing edge cases
                since = last_sync_at - timedelta(hours=1)
                pushed_filter = f" pushed:>{since.strftime('%Y-%m-%dT%H:%M:%SZ')}"
                logger.info("Incremental sync: fetching repos pushed after %s", since.isoformat())
            else:
                logger.info("No previous sync found, performing full sync")

        # ── Load DB-managed search queries (admin panel) & merge with hardcoded ──
        all_queries = list(SEARCH_QUERIES)
        try:
            from app.models.admin import SearchQuery as SQModel
            db_queries = db.query(SQModel).filter(SQModel.is_active == True).all()  # noqa: E712
            for sq in db_queries:
                if sq.query not in all_queries:
                    all_queries.append(sq.query)
            if db_queries:
                logger.info("Loaded %d additional search queries from DB", len(db_queries))
        except Exception as exc:
            logger.warning("Could not load DB search queries: %s", exc)

        # ── Load DB-managed extra repos ──
        extra_repos_list = list(EXTRA_REPOS)
        try:
            from app.models.admin import ExtraRepo as ERModel
            db_extras = db.query(ERModel).filter(ERModel.is_active == True).all()  # noqa: E712
            for er in db_extras:
                if er.full_name not in extra_repos_list:
                    extra_repos_list.append(er.full_name)
            if db_extras:
                logger.info("Loaded %d additional extra repos from DB", len(db_extras))
        except Exception as exc:
            logger.warning("Could not load DB extra repos: %s", exc)

        # ── Load DB-managed masters ──
        masters_list = list(MASTERS_USERS)
        try:
            from app.models.admin import SkillMaster as SMModel
            db_masters = db.query(SMModel).filter(SMModel.is_active == True).all()  # noqa: E712
            for m in db_masters:
                if m.github not in masters_list:
                    masters_list.append(m.github)
        except Exception:
            pass

        # ═══════════════════════════════════════════════════════
        # Phase 1: Search GitHub for repos
        # ═══════════════════════════════════════════════════════
        skipped_queries = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, query in enumerate(all_queries):
                # Skip remaining queries if rate limited
                if _rate_limit_exhausted:
                    skipped_queries += 1
                    continue

                effective_query = query + pushed_filter if pushed_filter else query
                try:
                    for page in range(1, 4):  # up to 3 pages
                        data = await _github_request(
                            client,
                            "https://api.github.com/search/repositories",
                            params={"q": effective_query, "per_page": 100, "page": page, "sort": "stars"},
                        )
                        items = data.get("items", [])
                        for repo in items:
                            fn = repo.get("full_name", "")
                            if fn and fn not in all_repos:
                                all_repos[fn] = repo
                        if len(items) < 100:
                            break
                        await asyncio.sleep(2.5)
                except RateLimitExhausted:
                    logger.warning("Rate limit exhausted during search phase at query %d/%d", i + 1, len(all_queries))
                    skipped_queries += 1
                except Exception as exc:
                    logger.error("Search failed [%s]: %s", query, exc)
                await asyncio.sleep(2)

            if skipped_queries:
                logger.warning("Skipped %d search queries due to rate limit", skipped_queries)
            logger.info("Phase 1 complete: %d unique repos from search", len(all_repos))

            # ═══════════════════════════════════════════════════════
            # Phase 2: Fetch repos for masters (by username)
            # ═══════════════════════════════════════════════════════
            skipped_masters = 0
            if not _rate_limit_exhausted:
                for username in masters_list:
                    if _rate_limit_exhausted:
                        skipped_masters += 1
                        continue
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
                    except RateLimitExhausted:
                        logger.warning("Rate limit hit during masters fetch, skipping remaining masters")
                        skipped_masters += 1
                    except Exception as exc:
                        logger.error("Masters fetch failed [%s]: %s", username, exc)
                    await asyncio.sleep(1)
            else:
                skipped_masters = len(masters_list)
                logger.warning("Skipping all masters due to rate limit exhaustion")

            if skipped_masters:
                logger.warning("Skipped %d/%d masters due to rate limit", skipped_masters, len(masters_list))
            logger.info("Phase 2 complete: %d unique repos after masters", len(all_repos))

            # ═══════════════════════════════════════════════════════
            # Phase 3: Fetch curated extra repos
            # ═══════════════════════════════════════════════════════
            skipped_extras = 0
            for full_name in extra_repos_list:
                if full_name in all_repos:
                    continue
                if _rate_limit_exhausted:
                    skipped_extras += 1
                    continue
                try:
                    repo_data = await _github_request(
                        client, f"https://api.github.com/repos/{full_name}"
                    )
                    if repo_data.get("full_name"):
                        all_repos[full_name] = repo_data
                        logger.info("Added extra repo %s", full_name)
                    await asyncio.sleep(1)
                except RateLimitExhausted:
                    skipped_extras += 1
                except Exception as exc:
                    logger.error("Extra repo fetch failed [%s]: %s", full_name, exc)

            if skipped_extras:
                logger.warning("Skipped %d extra repos due to rate limit", skipped_extras)
            logger.info("Phase 3 complete: %d unique repos total", len(all_repos))

            # ═══════════════════════════════════════════════════════
            # Phase 4: Enrich with owner followers (skip if rate limited)
            # ═══════════════════════════════════════════════════════
            # Pre-load existing owner followers from DB (works for both modes)
            try:
                existing_skills = db.query(Skill.author_name, Skill.author_followers).all()
                for name, followers in existing_skills:
                    if name and name not in owner_cache:
                        owner_cache[name] = followers or 0
                if owner_cache:
                    logger.info("Pre-loaded %d owner followers from DB cache", len(owner_cache))
            except Exception:
                pass

            enriched_count = 0
            skipped_enrichment = 0
            for fn, repo in all_repos.items():
                owner_login = repo.get("owner", {}).get("login", "")
                if owner_login and owner_login not in owner_cache:
                    if _rate_limit_exhausted:
                        # Use 0 as default when rate limited
                        owner_cache[owner_login] = 0
                        skipped_enrichment += 1
                    else:
                        try:
                            user_data = await _github_request(
                                client, f"https://api.github.com/users/{owner_login}"
                            )
                            owner_cache[owner_login] = user_data.get("followers", 0)
                            enriched_count += 1
                            await asyncio.sleep(0.3)
                        except RateLimitExhausted:
                            owner_cache[owner_login] = 0
                            skipped_enrichment += 1
                        except Exception:
                            owner_cache[owner_login] = 0
                repo["_owner_followers"] = owner_cache.get(owner_login, 0)
                repo["_total_issues"] = repo.get("open_issues_count", 0) + repo.get("_closed_issues", 0)
                repo["_total_commits"] = repo.get("_total_commits", 0)

            if skipped_enrichment:
                logger.warning("Skipped enrichment for %d owners due to rate limit", skipped_enrichment)
            logger.info("Phase 4 complete: enriched %d owners, skipped %d", enriched_count, skipped_enrichment)

        # ═══════════════════════════════════════════════════════
        # Phase 5: Fetch README content (only if we have API quota)
        # ═══════════════════════════════════════════════════════
        readme_cache: dict[str, str] = {}
        if not _rate_limit_exhausted:
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
                                elif resp.status_code in (403, 429):
                                    logger.warning("Rate limited during README fetch, stopping")
                                    break
                                fetched += 1
                                if fetched % 50 == 0:
                                    logger.info("README fetch: %d/%d", fetched, len(readme_targets))
                                await asyncio.sleep(0.5)
                            except Exception:
                                pass
                    logger.info("README fetch complete: %d/%d successful", len(readme_cache), len(readme_targets))
            except Exception as exc:
                logger.warning("README fetch phase failed: %s", exc)
        else:
            logger.info("Skipping README fetch phase due to rate limit")

        # ═══════════════════════════════════════════════════════
        # Phase 6: Clean, upsert, and score
        # ═══════════════════════════════════════════════════════
        if not all_repos:
            raise Exception("No repos found — sync produced empty result (rate limit may have blocked all queries)")

        logger.info("Processing %d repos for database upsert...", len(all_repos))

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
        logger.info("Database upsert complete: %d new, %d updated", new_count, updated_count)

        scoring_engine = ScoringEngine()
        scoring_engine.score_all(db)

        from app.services.composability import ComposabilityEngine
        ComposabilityEngine().compute_all(db)

        sync_log.status = "completed"
        sync_log.repos_found = len(cleaned)
        sync_log.repos_new = new_count
        sync_log.repos_updated = updated_count
        sync_log.finished_at = datetime.now(timezone.utc)

        # Add note about rate limiting if it occurred
        if _rate_limit_exhausted:
            sync_log.error_message = (
                f"Partial sync: rate limit hit. Skipped {skipped_queries} queries, "
                f"{skipped_masters} masters, {skipped_enrichment} enrichments. "
                f"Still wrote {len(cleaned)} repos."
            )

        db.commit()

        logger.info(
            "Sync completed: %d found, %d new, %d updated%s",
            len(cleaned), new_count, updated_count,
            " (partial due to rate limit)" if _rate_limit_exhausted else "",
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
