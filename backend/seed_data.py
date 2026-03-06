#!/usr/bin/env python3
"""
Seed script: fetch Agent Skills from GitHub, clean, score, and store in DB.
Also searches for trending repos from the last 3 days.
Run: cd backend && source venv/bin/activate && python seed_data.py
"""
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────
from app.config import settings
from app.database import Base, SessionLocal
from app.database import engine as db_engine
from app.models.skill import Skill, SyncLog
from app.services.data_cleaner import DataCleaner
from app.services.scorer import ScoringEngine

TOKEN = settings.github_token
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

# Search queries for popular Agent Skills
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
    "langchain-tool in:name,topics",
    # Broader skill-type searches
    "agent-skill in:name,description,topics",
    "claude-code skill in:name,description",
    "codex skill in:name,description stars:>5",
    "ai skill tool in:name,description stars:>10",
    "cursor-skill in:name,topics",
    "windsurf-skill in:name,topics",
    "antigravity skill in:name,description",
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

# Additional: trending repos from last 3 days
THREE_DAYS_AGO = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")
TRENDING_QUERIES = [
    f"mcp created:>{THREE_DAYS_AGO} in:name,topics",
    f"mcp-server created:>{THREE_DAYS_AGO}",
    f"agent tool created:>{THREE_DAYS_AGO} stars:>5",
    f"agent skill created:>{THREE_DAYS_AGO} stars:>2",
    f"claude tool created:>{THREE_DAYS_AGO}",
    f"claude skill created:>{THREE_DAYS_AGO}",
    f"model-context-protocol created:>{THREE_DAYS_AGO}",
    f"codex skill created:>{THREE_DAYS_AGO}",
]


async def github_request(
    client: httpx.AsyncClient, url: str, params: dict | None = None
) -> dict[str, Any]:
    """Make a GitHub API request with rate limit handling."""
    for attempt in range(3):
        resp = await client.get(url, headers=HEADERS, params=params)
        if resp.status_code in (403, 429):
            reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
            remaining = resp.headers.get("X-RateLimit-Remaining", "?")
            if reset_ts:
                wait = max(reset_ts - time.time(), 0) + 5
            else:
                wait = 30 * (attempt + 1)
            wait = min(wait, 120)
            logger.warning(
                "Rate limited (remaining=%s). Sleeping %.0fs (attempt %d)",
                remaining, wait, attempt + 1,
            )
            await asyncio.sleep(wait)
            continue
        if resp.status_code == 422:
            return {"items": [], "total_count": 0}
        resp.raise_for_status()
        return resp.json()
    return {"items": [], "total_count": 0}


async def search_repos(client: httpx.AsyncClient, query: str, max_pages: int = 3) -> list[dict]:
    """Search GitHub repos with pagination."""
    results = []
    for page in range(1, max_pages + 1):
        data = await github_request(
            client,
            "https://api.github.com/search/repositories",
            params={"q": query, "per_page": 100, "page": page, "sort": "stars"},
        )
        items = data.get("items", [])
        results.extend(items)
        total = data.get("total_count", 0)
        logger.info(
            "  Query [%s] page %d: %d items (total %d)",
            query[:40], page, len(items), total,
        )
        if len(items) < 100 or len(results) >= 500:
            break
        await asyncio.sleep(2.5)
    return results


async def enrich_repo(
    client: httpx.AsyncClient, repo: dict, owner_cache: dict[str, int]
) -> dict:
    """Add owner followers to repo data."""
    owner_login = repo.get("owner", {}).get("login", "")
    if owner_login and owner_login not in owner_cache:
        try:
            user_data = await github_request(client, f"https://api.github.com/users/{owner_login}")
            owner_cache[owner_login] = user_data.get("followers", 0)
            await asyncio.sleep(0.3)
        except Exception:
            owner_cache[owner_login] = 0
    repo["_owner_followers"] = owner_cache.get(owner_login, 0)
    repo["_total_issues"] = repo.get("open_issues_count", 0)
    repo["_total_commits"] = 0
    return repo


async def main():
    Base.metadata.create_all(bind=db_engine)
    db = SessionLocal()

    sync_log = SyncLog(status="running")
    db.add(sync_log)
    db.commit()
    db.refresh(sync_log)

    all_repos: dict[str, dict] = {}
    owner_cache: dict[str, int] = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ── Phase 1: Main searches ──
        logger.info("═══ Phase 1: Searching popular Agent Skills ═══")
        for query in SEARCH_QUERIES:
            try:
                repos = await search_repos(client, query, max_pages=3)
                for repo in repos:
                    fn = repo.get("full_name", "")
                    if fn and fn not in all_repos:
                        all_repos[fn] = repo
            except Exception as exc:
                logger.error("Search failed [%s]: %s", query, exc)
            await asyncio.sleep(3)

        logger.info("After main searches: %d unique repos", len(all_repos))

        # ── Phase 2: Trending (last 3 days) ──
        logger.info("═══ Phase 2: Searching trending repos (last 3 days) ═══")
        trending_repos = []
        for query in TRENDING_QUERIES:
            try:
                repos = await search_repos(client, query, max_pages=2)
                for repo in repos:
                    fn = repo.get("full_name", "")
                    if fn:
                        if fn not in all_repos:
                            all_repos[fn] = repo
                        trending_repos.append(repo)
            except Exception as exc:
                logger.error("Trending search failed [%s]: %s", query, exc)
            await asyncio.sleep(3)

        logger.info("Trending repos found: %d", len(trending_repos))

        # ── Phase 2.5: Fetch repos for masters (by username) ──
        logger.info("═══ Phase 2.5: Fetching masters' repos ═══")
        for username in MASTERS_USERS:
            try:
                for page in range(1, 4):
                    data = await github_request(
                        client,
                        f"https://api.github.com/users/{username}/repos",
                        params={"per_page": 100, "page": page, "sort": "stars"},
                    )
                    items = data if isinstance(data, list) else data.get("items", [])
                    added = 0
                    for repo in items:
                        fn = repo.get("full_name", "")
                        if fn and fn not in all_repos:
                            all_repos[fn] = repo
                            added += 1
                    logger.info("  User [%s] page %d: %d new repos", username, page, added)
                    if len(items) < 100:
                        break
                    await asyncio.sleep(1)
            except Exception as exc:
                logger.error("Masters fetch failed [%s]: %s", username, exc)
            await asyncio.sleep(1)

        logger.info("After masters fetch: %d unique repos", len(all_repos))

        # ── Phase 3: Fetch curated extra repos ──
        logger.info("═══ Phase 3: Fetching curated extra repos ═══")
        for full_name in EXTRA_REPOS:
            if full_name in all_repos:
                logger.info("  Already have %s, skipping", full_name)
                continue
            try:
                repo_data = await github_request(
                    client, f"https://api.github.com/repos/{full_name}"
                )
                if repo_data.get("full_name"):
                    all_repos[full_name] = repo_data
                    logger.info("  Added %s (stars=%s)", full_name, repo_data.get("stargazers_count", 0))
                await asyncio.sleep(1)
            except Exception as exc:
                logger.error("  Failed to fetch %s: %s", full_name, exc)

        # ── Phase 4: Enrich top repos with owner data ──
        logger.info("═══ Phase 4: Enriching repos with owner data ═══")
        count = 0
        for fn, repo in all_repos.items():
            await enrich_repo(client, repo, owner_cache)
            count += 1
            if count % 50 == 0:
                logger.info("  Enriched %d/%d repos", count, len(all_repos))

    # ── Phase 5: Clean and store ──
    logger.info("═══ Phase 5: Cleaning and storing data ═══")
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
            for key, val in repo_data.items():
                setattr(existing, key, val)
            updated_count += 1
        else:
            db.add(Skill(**repo_data))
            new_count += 1

    db.commit()
    logger.info("Stored: %d new, %d updated", new_count, updated_count)

    # ── Phase 6: Score all ──
    logger.info("═══ Phase 6: Scoring all skills ═══")
    engine = ScoringEngine()
    scored = engine.score_all(db)
    logger.info("Scored %d skills", scored)

    # Update sync log
    sync_log.status = "completed"
    sync_log.repos_found = len(cleaned)
    sync_log.repos_new = new_count
    sync_log.repos_updated = updated_count
    sync_log.finished_at = datetime.now(timezone.utc)
    db.commit()

    # ── Report ──
    total = db.query(Skill).count()
    top_skills = db.query(Skill).order_by(Skill.score.desc()).limit(20).all()

    print("\n" + "=" * 70)
    print(f"  SYNC COMPLETE: {total} total skills in database")
    print("=" * 70)
    print(f"\n{'Rank':<5} {'Score':<7} {'Stars':<8} {'Name':<40} {'Category'}")
    print("-" * 90)
    for i, s in enumerate(top_skills, 1):
        print(f"{i:<5} {s.score:<7.1f} {s.stars:<8} {s.repo_full_name:<40} {s.category}")

    # Show trending
    print("\n" + "=" * 70)
    print("  TRENDING (Created in last 3 days)")
    print("=" * 70)
    trending_in_db = (
        db.query(Skill)
        .filter(Skill.created_at >= datetime.now(timezone.utc) - timedelta(days=3))
        .order_by(Skill.stars.desc())
        .limit(20)
        .all()
    )
    if trending_in_db:
        print(f"\n{'Stars':<8} {'Score':<7} {'Name':<45} {'Category'}")
        print("-" * 80)
        for s in trending_in_db:
            print(f"{s.stars:<8} {s.score:<7.1f} {s.repo_full_name:<45} {s.category}")
    else:
        print("  No repos created in the last 3 days found.")

    db.close()
    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(main())
