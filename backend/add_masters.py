#!/usr/bin/env python3
"""Quick script to add masters' repos to the database without full re-sync."""
import asyncio
import logging
import time
from typing import Any

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from app.config import settings
from app.database import Base, SessionLocal
from app.database import engine as db_engine
from app.models.skill import Skill
from app.services.data_cleaner import DataCleaner
from app.services.scorer import ScoringEngine

TOKEN = settings.github_token
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

MASTERS_USERS = [
    "joeseesun",  # vista8 / 向阳乔木
    "dotey",      # dotey / 宝玉
    "JimLiu",     # dotey / 宝玉's coding account
    "Panniantong",
    "op7418",
    "zarazhangrui",
]

EXTRA_REPOS = [
    "Panniantong/Agent-Reach",
    "JimLiu/baoyu-skills",
    "joeseesun/yt-search-download",
    "joeseesun/anything-to-notebooklm",
    "joeseesun/skill-publisher",
]


async def github_request(client: httpx.AsyncClient, url: str, params: dict | None = None) -> Any:
    for attempt in range(3):
        resp = await client.get(url, headers=HEADERS, params=params)
        if resp.status_code in (403, 429):
            reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
            if reset_ts:
                wait = max(reset_ts - time.time(), 0) + 5
            else:
                wait = 30 * (attempt + 1)
            wait = min(wait, 120)
            logger.warning("Rate limited. Sleeping %.0fs (attempt %d)", wait, attempt + 1)
            await asyncio.sleep(wait)
            continue
        if resp.status_code == 422:
            return []
        resp.raise_for_status()
        return resp.json()
    return []


async def main():
    Base.metadata.create_all(bind=db_engine)
    db = SessionLocal()

    all_repos: dict[str, dict] = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch repos for each master user
        for username in MASTERS_USERS:
            logger.info("Fetching repos for %s...", username)
            try:
                for page in range(1, 4):
                    data = await github_request(
                        client,
                        f"https://api.github.com/users/{username}/repos",
                        params={"per_page": 100, "page": page, "sort": "stars"},
                    )
                    items = data if isinstance(data, list) else []
                    for repo in items:
                        fn = repo.get("full_name", "")
                        if fn:
                            all_repos[fn] = repo
                    logger.info("  Page %d: %d repos", page, len(items))
                    if len(items) < 100:
                        break
                    await asyncio.sleep(1)
            except Exception as exc:
                logger.error("Failed for %s: %s", username, exc)
            await asyncio.sleep(1)

        logger.info("Total repos from masters: %d", len(all_repos))

        # Fetch specific extra repos
        for full_name in EXTRA_REPOS:
            if full_name in all_repos:
                continue
            try:
                data = await github_request(client, f"https://api.github.com/repos/{full_name}")
                if isinstance(data, dict) and data.get("full_name"):
                    all_repos[full_name] = data
                    logger.info("Added extra: %s (stars=%s)", full_name, data.get("stargazers_count", 0))
                await asyncio.sleep(1)
            except Exception as exc:
                logger.error("Failed to fetch %s: %s", full_name, exc)

        # Enrich with owner followers
        owner_cache: dict[str, int] = {}
        for fn, repo in all_repos.items():
            owner_login = repo.get("owner", {}).get("login", "")
            if owner_login and owner_login not in owner_cache:
                try:
                    user_data = await github_request(client, f"https://api.github.com/users/{owner_login}")
                    if isinstance(user_data, dict):
                        owner_cache[owner_login] = user_data.get("followers", 0)
                    await asyncio.sleep(0.3)
                except Exception:
                    owner_cache[owner_login] = 0
            repo["_owner_followers"] = owner_cache.get(owner_login, 0)
            repo["_total_issues"] = repo.get("open_issues_count", 0)
            repo["_total_commits"] = 0

    # Clean and store
    cleaner = DataCleaner()
    cleaned = cleaner.process(list(all_repos.values()))

    new_count, updated_count = 0, 0
    for repo_data in cleaned:
        existing = db.query(Skill).filter(Skill.repo_full_name == repo_data["repo_full_name"]).first()
        if existing:
            for key, val in repo_data.items():
                setattr(existing, key, val)
            updated_count += 1
        else:
            db.add(Skill(**repo_data))
            new_count += 1

    db.commit()
    logger.info("Stored: %d new, %d updated", new_count, updated_count)

    # Re-score all
    engine = ScoringEngine()
    scored = engine.score_all(db)
    logger.info("Scored %d skills", scored)

    # Verify masters repos
    for username in MASTERS_USERS:
        count = db.query(Skill).filter(Skill.author_name == username).count()
        logger.info("  %s: %d repos in DB", username, count)

    db.close()
    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(main())
