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

# ── Core queries: run EVERY sync (10 queries) ──
CORE_QUERIES = [
    "mcp-server in:name,topics",
    "claude-mcp in:name,description,topics",
    "model-context-protocol in:name,description,topics",
    "mcp in:topics language:python",
    "mcp in:topics language:typescript",
    "mcp-tool in:name,topics",
    "claude-skill in:name,description,topics",
    "claude-code in:topics",
    "agent-skill in:name,topics",
    "ai-agent-tool in:name,description,topics",
]

# ── OpenClaw / NanoClaw ecosystem queries ──
OPENCLAW_QUERIES = [
    "openclaw in:topics stars:>50",
    "openclaw-skills in:topics",
    "nanoclaw in:topics,name stars:>50",
    "clawdbot in:topics stars:>50",
    "clawhub in:topics",
    "openclaw-plugin in:topics stars:>50",
]

# ── Extended queries: run WEEKLY (Sunday) or on full sync ──
EXTENDED_QUERIES = [
    "mcp-plugin in:name,description,topics",
    "claude-code-skill in:name,description,topics",
    "anthropic in:topics language:python",
    "anthropic in:topics language:typescript",
    "agent-tools in:name,description,topics",
    "llm-tool in:name,description,topics",
    "llm-agent in:name,topics stars:>10",
    "ai-tools in:topics stars:>20",
    "codex-skills in:name,description,topics",
    "codex-cli in:name,topics",
    "codex in:topics stars:>100",
    "agent-skills in:topics stars:>50",
    "openai-agent in:name,topics",
    "openai-tool in:name,topics",
    "gemini-agent in:name,topics",
    "gemini-tool in:name,description,topics",
    "youmind in:name,description,topics",
    "youmind-plugin in:name,topics",
    "function-calling in:topics language:python stars:>50",
    "tool-use in:topics language:typescript stars:>50",
    "ai-automation in:topics stars:>20",
]

# Combined for backwards compatibility
SEARCH_QUERIES = CORE_QUERIES + OPENCLAW_QUERIES + EXTENDED_QUERIES

# Masters / influencers whose repos should always be collected
MASTERS_USERS = [
    "op7418", "zarazhangrui",
    "joeseesun",  # vista8 / 向阳乔木
    "JimLiu",  # 宝玉 (dotey account deleted/private)
    "Panniantong",
    "abczsl520",  # Node.js 架构 / 中文记忆修复 / 调试方法论
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
    # abczsl520 skills
    "abczsl520/nodejs-project-arch",
    "abczsl520/openclaw-memory-cn",
    "abczsl520/debug-methodology",
    "abczsl520/bug-audit-skill",
    "abczsl520/codex-review",
    "abczsl520/browser-use-skill",
    "abczsl520/game-quality-gates",
    # MediaCrawler - multi-platform social media crawler (45k+ stars)
    "NanmiCoder/MediaCrawler",
    # x-tweet-fetcher - fetch tweets without login/API keys (OpenClaw skill)
    "ythx-101/x-tweet-fetcher",
    # Cloudflare official Agent Skills (601 stars)
    "cloudflare/skills",
]

# ── Rate Limit Management ──
# GitHub API: 5000 requests/hour (core), 30 requests/min (search)
# Strategy: WAIT for reset instead of failing — GitHub Actions has 6hr timeout.

_rate_limit_remaining = 5000
_rate_limit_reset_at = 0

# Maximum time to wait for a rate limit reset (seconds)
MAX_RATE_LIMIT_WAIT = 3700  # ~61 minutes — covers a full reset window


async def _check_rate_limit(client: httpx.AsyncClient) -> dict:
    """Pre-flight: query GitHub's /rate_limit endpoint to know exact budget."""
    global _rate_limit_remaining, _rate_limit_reset_at

    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    try:
        resp = await client.get("https://api.github.com/rate_limit", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            core = data.get("resources", {}).get("core", {})
            search = data.get("resources", {}).get("search", {})

            _rate_limit_remaining = core.get("remaining", 5000)
            _rate_limit_reset_at = core.get("reset", 0)

            logger.info(
                "Rate limit check: core=%d/%d (reset %s), search=%d/%d",
                _rate_limit_remaining, core.get("limit", 5000),
                datetime.fromtimestamp(_rate_limit_reset_at).strftime('%H:%M:%S') if _rate_limit_reset_at else "?",
                search.get("remaining", 30), search.get("limit", 30),
            )
            return {"core_remaining": _rate_limit_remaining, "search_remaining": search.get("remaining", 30)}
    except Exception as exc:
        logger.warning("Could not check rate limit: %s", exc)

    return {"core_remaining": _rate_limit_remaining, "search_remaining": 30}


async def _wait_for_rate_limit(reset_at: int, label: str = "core") -> None:
    """Wait until the rate limit resets. GitHub resets are at most ~60 min away."""
    if not reset_at:
        logger.warning("No reset timestamp for %s, sleeping 60s as fallback", label)
        await asyncio.sleep(60)
        return

    wait_seconds = max(reset_at - time.time(), 0) + 5  # 5s buffer
    if wait_seconds <= 0:
        return

    if wait_seconds > MAX_RATE_LIMIT_WAIT:
        logger.warning(
            "Rate limit %s reset too far away (%.0fs), capping at %ds",
            label, wait_seconds, MAX_RATE_LIMIT_WAIT,
        )
        wait_seconds = MAX_RATE_LIMIT_WAIT

    reset_time_str = datetime.fromtimestamp(reset_at).strftime('%H:%M:%S')
    minutes = int(wait_seconds // 60)
    logger.info(
        "⏳ Waiting %d min %.0f sec for %s rate limit reset at %s ...",
        minutes, wait_seconds % 60, label, reset_time_str,
    )
    await asyncio.sleep(wait_seconds)
    logger.info("✅ Rate limit wait complete for %s, resuming", label)


async def _ensure_rate_limit(client: httpx.AsyncClient, min_remaining: int = 50) -> None:
    """Check current rate limit and wait for reset if too low.

    Call this BETWEEN phases to avoid starting a phase with no budget.
    """
    budget = await _check_rate_limit(client)
    if budget["core_remaining"] < min_remaining:
        logger.warning(
            "Core rate limit too low (%d < %d), waiting for reset...",
            budget["core_remaining"], min_remaining,
        )
        await _wait_for_rate_limit(_rate_limit_reset_at, "inter-phase")
        # Re-check after wait
        await _check_rate_limit(client)


async def _github_request(
    client: httpx.AsyncClient,
    url: str,
    params: Optional[dict] = None,
    max_retries: int = 3,
    _retry: int = 0,
) -> dict[str, Any]:
    """Make a GitHub API request with smart rate limit handling.

    Key behavior: when rate limited, WAIT for the actual reset time
    (up to ~60 min) instead of giving up after a fixed retry.
    This guarantees the sync eventually completes.
    """
    global _rate_limit_remaining, _rate_limit_reset_at

    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    try:
        resp = await client.get(url, headers=headers, params=params)
    except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as exc:
        if _retry < max_retries:
            logger.warning("Network error for %s: %s. Retry %d/%d", url[:80], exc, _retry + 1, max_retries)
            await asyncio.sleep(5 * (_retry + 1))
            return await _github_request(client, url, params, max_retries, _retry + 1)
        raise

    # Update rate limit tracking from response headers
    remaining_hdr = resp.headers.get("X-RateLimit-Remaining")
    reset_hdr = resp.headers.get("X-RateLimit-Reset")
    if remaining_hdr is not None:
        _rate_limit_remaining = int(remaining_hdr)
    if reset_hdr:
        _rate_limit_reset_at = int(reset_hdr)

    # Log when rate limit is getting low
    if _rate_limit_remaining <= 100 and _rate_limit_remaining >= 0:
        logger.info(
            "Rate limit: %d remaining (reset %s)",
            _rate_limit_remaining,
            datetime.fromtimestamp(_rate_limit_reset_at).strftime('%H:%M:%S') if _rate_limit_reset_at else "?",
        )

    if resp.status_code in (403, 429):
        if _retry >= max_retries:
            logger.error("Max retries (%d) reached for %s, returning empty", max_retries, url[:80])
            return {"items": [], "total_count": 0}

        # Determine if this is a rate limit or a permission error
        is_rate_limit = (
            _rate_limit_remaining == 0
            or "rate limit" in resp.text.lower()
            or resp.status_code == 429
        )

        if is_rate_limit:
            # ── RATE LIMITED: WAIT for the actual reset time ──
            logger.warning(
                "Rate limited (HTTP %d, %d remaining). Waiting for reset at %s (attempt %d/%d)",
                resp.status_code, _rate_limit_remaining,
                datetime.fromtimestamp(_rate_limit_reset_at).strftime('%H:%M:%S') if _rate_limit_reset_at else "?",
                _retry + 1, max_retries,
            )
            await _wait_for_rate_limit(_rate_limit_reset_at, "request")
            return await _github_request(client, url, params, max_retries, _retry + 1)
        else:
            # Permission/abuse error — short wait then retry
            logger.warning("HTTP %d (not rate limit) for %s: %s", resp.status_code, url[:80], resp.text[:200])
            await asyncio.sleep(30)
            return await _github_request(client, url, params, max_retries, _retry + 1)

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

    Rate limit strategy:
      - Pre-flight check: verify we have enough API budget before starting
      - Wait on limit: if rate limited, sleep until reset (~max 60 min)
      - Inter-phase check: verify budget between phases, wait if needed
      - Budget cap: enrichment limited to 500 API calls max
      - GitHub Actions timeout is 6 hours; rate limit resets in ≤1 hour.
    """
    from app.database import SessionLocal
    from app.models.skill import Skill, SyncLog
    from app.services.data_cleaner import DataCleaner
    from app.services.scorer import ScoringEngine

    db = SessionLocal()
    sync_log_id_ref = sync_log_id

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

    sync_log_id_ref = sync_log.id

    try:
        all_repos: dict[str, dict] = {}
        owner_cache: dict[str, int] = {}

        # ── Incremental sync: determine pushed:> filter ──
        pushed_filter = ""
        if incremental:
            last_sync_at = _get_last_successful_sync(db)
            if last_sync_at:
                since = last_sync_at - timedelta(hours=1)
                pushed_filter = f" pushed:>{since.strftime('%Y-%m-%dT%H:%M:%SZ')}"
                logger.info("Incremental sync: fetching repos pushed after %s", since.isoformat())
            else:
                logger.info("No previous sync found, performing full sync")

        # ── Load search queries with priority tiers ──
        is_full_sync = not pushed_filter
        is_weekly = datetime.now(timezone.utc).weekday() == 6  # Sunday
        if is_full_sync or is_weekly:
            all_queries = list(SEARCH_QUERIES)
            logger.info("Running FULL query set (%d queries): %s",
                        len(all_queries), "full sync" if is_full_sync else "weekly")
        else:
            all_queries = list(CORE_QUERIES) + list(OPENCLAW_QUERIES)
            logger.info("Running CORE + OPENCLAW query set (%d queries, incremental)", len(all_queries))

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

        async with httpx.AsyncClient(timeout=30.0) as client:
            # ═══════════════════════════════════════════════════════
            # PRE-FLIGHT: Check rate limit before starting
            # ═══════════════════════════════════════════════════════
            budget = await _check_rate_limit(client)
            if budget["core_remaining"] < 100:
                logger.warning("Low rate limit at start (%d). Waiting for reset...", budget["core_remaining"])
                await _wait_for_rate_limit(_rate_limit_reset_at, "pre-flight")
                await _check_rate_limit(client)

            # ═══════════════════════════════════════════════════════
            # Phase 1: Search GitHub for repos
            # ═══════════════════════════════════════════════════════
            search_start = time.time()
            for i, query in enumerate(all_queries):
                effective_query = query + pushed_filter if pushed_filter else query
                try:
                    for page in range(1, 4):  # up to 3 pages per query
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
                        # Respect search rate limit: 30 req/min → ~2s per request
                        await asyncio.sleep(2.5)
                except Exception as exc:
                    logger.error("Search failed [%s]: %s", query, exc)
                await asyncio.sleep(2)

            logger.info("Phase 1 complete: %d unique repos from search (%.0fs)", len(all_repos), time.time() - search_start)

            # ── Inter-phase rate check ──
            await _ensure_rate_limit(client, min_remaining=50)

            # ═══════════════════════════════════════════════════════
            # Phase 2: Fetch repos for masters (by username)
            # ═══════════════════════════════════════════════════════
            for username in masters_list:
                try:
                    for page in range(1, 4):
                        data = await _github_request(
                            client,
                            f"https://api.github.com/users/{username}/repos",
                            params={"per_page": 100, "page": page, "sort": "stars"},
                        )
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

            logger.info("Phase 2 complete: %d unique repos after masters", len(all_repos))

            # ── Inter-phase rate check ──
            await _ensure_rate_limit(client, min_remaining=30)

            # ═══════════════════════════════════════════════════════
            # Phase 3: Fetch curated extra repos
            # ═══════════════════════════════════════════════════════
            for full_name in extra_repos_list:
                if full_name in all_repos:
                    continue
                try:
                    repo_data = await _github_request(
                        client, f"https://api.github.com/repos/{full_name}"
                    )
                    if repo_data.get("full_name"):
                        all_repos[full_name] = repo_data
                    await asyncio.sleep(0.5)
                except Exception as exc:
                    logger.error("Extra repo fetch failed [%s]: %s", full_name, exc)

            logger.info("Phase 3 complete: %d unique repos total", len(all_repos))

            # ═══════════════════════════════════════════════════════
            # Phase 4: Enrich with owner followers
            # ═══════════════════════════════════════════════════════
            try:
                existing_skills = db.query(Skill.author_name, Skill.author_followers).all()
                for name, followers in existing_skills:
                    if name and name not in owner_cache:
                        owner_cache[name] = followers or 0
                if owner_cache:
                    logger.info("Pre-loaded %d owner followers from DB cache", len(owner_cache))
            except Exception:
                pass

            # Check budget before enrichment
            await _ensure_rate_limit(client, min_remaining=100)

            enriched_count = 0
            skipped_enrichment = 0
            ENRICHMENT_BUDGET = 500  # Max API calls for enrichment per sync
            for fn, repo in all_repos.items():
                owner_login = repo.get("owner", {}).get("login", "")
                if owner_login and owner_login not in owner_cache:
                    if enriched_count >= ENRICHMENT_BUDGET:
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
                        except Exception:
                            owner_cache[owner_login] = 0
                            skipped_enrichment += 1
                repo["_owner_followers"] = owner_cache.get(owner_login, 0)
                repo["_total_issues"] = repo.get("open_issues_count", 0) + repo.get("_closed_issues", 0)
                repo["_total_commits"] = repo.get("_total_commits", 0)

            logger.info("Phase 4 complete: enriched %d owners, skipped %d (budget %d)", enriched_count, skipped_enrichment, ENRICHMENT_BUDGET)

        # ═══════════════════════════════════════════════════════
        # Phase 5: Fetch README content
        # ═══════════════════════════════════════════════════════
        readme_cache: dict[str, str] = {}
        try:
            # Clear any invalid transaction state from previous phases
            # (PgBouncer may have killed the connection during long API fetches)
            try:
                db.rollback()
            except Exception:
                pass
            null_readme_skills = (
                db.query(Skill.repo_full_name)
                .filter(Skill.readme_content.is_(None))
                .order_by(Skill.score.desc().nullslast())
                .limit(300)
                .all()
            )
            readme_targets = {r.repo_full_name for r in null_readme_skills} & set(all_repos.keys())
            if readme_targets:
                logger.info("Fetching README for %d skills", len(readme_targets))
                async with httpx.AsyncClient(timeout=30.0) as readme_client:
                    await _ensure_rate_limit(readme_client, min_remaining=50)

                    readme_headers = {"Accept": "application/vnd.github.raw"}
                    if settings.github_token:
                        readme_headers["Authorization"] = f"Bearer {settings.github_token}"

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
                                reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
                                if reset_ts:
                                    await _wait_for_rate_limit(reset_ts, "readme")
                                else:
                                    await asyncio.sleep(60)
                                continue
                            fetched += 1
                            if fetched % 50 == 0:
                                logger.info("README fetch: %d/%d", fetched, len(readme_targets))
                            await asyncio.sleep(0.5)
                        except Exception:
                            pass
                logger.info("README fetch complete: %d/%d successful", len(readme_cache), len(readme_targets))
        except Exception as exc:
            logger.warning("README fetch phase failed: %s", exc)

        # ═══════════════════════════════════════════════════════
        # Phase 6: Clean, upsert, and score
        # ═══════════════════════════════════════════════════════
        if not all_repos:
            raise Exception("No repos found — sync produced empty result")

        logger.info("Processing %d repos for database upsert...", len(all_repos))

        cleaner = DataCleaner()
        cleaned = cleaner.process(list(all_repos.values()))

        # Refresh DB session — old connection may have been killed by
        # PgBouncer during the long API-fetch phase (could be 30-90 min).
        # NOTE: sync_log_id_ref was already saved at the start of the function
        # (line ~307). Do NOT access sync_log.id here — the connection may be
        # dead and SQLAlchemy's lazy-load will fail.
        db.close()
        db = SessionLocal()
        sync_log = db.query(SyncLog).filter(SyncLog.id == sync_log_id_ref).first()

        BATCH_SIZE = 200
        new_count, updated_count = 0, 0
        new_repo_names = []  # Track truly new skill repo names for composability
        for i, repo_data in enumerate(cleaned):
            try:
                existing = (
                    db.query(Skill)
                    .filter(Skill.repo_full_name == repo_data["repo_full_name"])
                    .first()
                )
                if existing:
                    existing.prev_stars = existing.stars
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
                    new_repo_names.append(repo_data.get("repo_full_name", ""))
                    new_count += 1
            except Exception as row_exc:
                logger.warning("Upsert failed for %s: %s", repo_data.get("repo_full_name", "?"), row_exc)
                db.rollback()

            if (i + 1) % BATCH_SIZE == 0:
                try:
                    db.commit()
                    logger.info("Batch commit: %d/%d (%d new, %d updated)", i + 1, len(cleaned), new_count, updated_count)
                except Exception as batch_exc:
                    logger.error("Batch commit failed at %d: %s", i + 1, batch_exc)
                    db.rollback()

        try:
            db.commit()
        except Exception as final_exc:
            logger.error("Final commit failed: %s", final_exc)
            db.rollback()

        logger.info("Database upsert complete: %d new, %d updated", new_count, updated_count)

        scoring_engine = ScoringEngine()
        scoring_engine.score_all(db)

        from app.services.composability import ComposabilityEngine
        if new_count > 0 and new_repo_names:
            # Only recompute composability for truly NEW skills, not all updated ones.
            # Using last_synced >= started_at would include all updated skills (thousands),
            # making composability take hours. Instead, only pass new skill IDs.
            new_skill_ids = {
                s.id for s in db.query(Skill.id)
                .filter(Skill.repo_full_name.in_(new_repo_names))
                .all()
            }
            logger.info("Composability: %d truly new skills (not %d updated)", len(new_skill_ids), updated_count)
            ComposabilityEngine().compute_all(db, changed_ids=new_skill_ids)
        else:
            logger.info("Composability: full recompute (no new skills or first run)")
            ComposabilityEngine().compute_all(db)

        # Take weekly trending snapshot (non-fatal if fails)
        maybe_take_weekly_snapshot(db)

        sync_log.status = "completed"
        sync_log.repos_found = len(cleaned)
        sync_log.repos_new = new_count
        sync_log.repos_updated = updated_count
        sync_log.finished_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "✅ Sync completed: %d found, %d new, %d updated",
            len(cleaned), new_count, updated_count,
        )

    except Exception as exc:
        logger.exception("Sync job failed")
        try:
            db.rollback()
            sync_log = db.query(SyncLog).filter(SyncLog.id == sync_log_id_ref).first()
            if sync_log:
                sync_log.status = "failed"
                sync_log.error_message = str(exc)[:1000]
                sync_log.finished_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            logger.error("Could not update sync log after failure: %s", exc)
    finally:
        db.close()


def maybe_take_weekly_snapshot(db: "Session") -> None:
    """Update the weekly trending snapshot on every sync.

    Called at the end of each sync. Captures top 20 trending skills
    (by star velocity) for the current Monday→Sunday week.
    Deletes and re-inserts the current week's data each time so the
    snapshot always reflects the latest state.
    """
    from app.models.skill import Skill, WeeklyTrendingSnapshot

    try:
        # Determine current week boundaries (Monday start)
        today = datetime.now(timezone.utc).date()
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        # Delete existing snapshot for the current week (will be re-created)
        deleted = (
            db.query(WeeklyTrendingSnapshot)
            .filter(WeeklyTrendingSnapshot.week_start == week_start)
            .delete()
        )
        if deleted:
            logger.info("Deleted %d existing snapshot rows for week %s", deleted, week_start)

        # Compute star velocity for ALL skills with enough stars
        # Uses stars/age formula — covers both new and established projects
        now = datetime.now(timezone.utc)
        candidates = (
            db.query(Skill)
            .filter(Skill.stars >= 20)
            .filter(Skill.created_at.isnot(None))
            .all()
        )

        def star_velocity(skill: Skill) -> float:
            created = skill.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_days = max((now - created).total_seconds() / 86400, 1)
            return skill.stars / age_days

        ranked = sorted(candidates, key=star_velocity, reverse=True)[:20]

        if not ranked:
            logger.info("No trending skills to snapshot for week %s", week_start)
            return

        for i, skill in enumerate(ranked):
            snapshot = WeeklyTrendingSnapshot(
                week_start=week_start,
                week_end=week_end,
                rank=i + 1,
                skill_id=skill.id,
                repo_full_name=skill.repo_full_name,
                repo_name=skill.repo_name,
                author_name=skill.author_name,
                author_avatar_url=skill.author_avatar_url or "",
                stars=skill.stars,
                star_velocity=round(star_velocity(skill), 2),
                description=skill.description or "",
                repo_url=skill.repo_url or "",
                category=skill.category or "",
                created_at_snap=skill.created_at,
                last_commit_at_snap=skill.last_commit_at,
            )
            db.add(snapshot)

        db.commit()
        logger.info("📸 Weekly trending snapshot updated for %s: %d skills", week_start, len(ranked))

    except Exception as exc:
        logger.warning("Weekly snapshot failed (non-fatal): %s", exc)
        try:
            db.rollback()
        except Exception:
            pass


def run_sync(sync_log_id: int) -> None:
    """Synchronous wrapper for background task triggered by POST /api/sync."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(sync_all_skills(sync_log_id=sync_log_id))
    finally:
        loop.close()
