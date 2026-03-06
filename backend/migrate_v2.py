#!/usr/bin/env python3
"""
Migration script: Add v2 columns to skills table and create new tables.
Safe to run multiple times (idempotent).

Run: cd backend && source venv/bin/activate && python migrate_v2.py
"""
import json
import logging
import sqlite3

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from app.config import settings

# Parse SQLite path from URL
db_path = settings.database_url.replace("sqlite:///./", "").replace("sqlite:///", "")

# New columns to add to the skills table
NEW_SKILL_COLUMNS = [
    ("quality_completeness", "REAL DEFAULT 0.0"),
    ("quality_clarity", "REAL DEFAULT 0.0"),
    ("quality_specificity", "REAL DEFAULT 0.0"),
    ("quality_examples", "REAL DEFAULT 0.0"),
    ("quality_score", "REAL DEFAULT 0.0"),
    ("size_category", "VARCHAR(20) DEFAULT 'unknown'"),
    ("repo_size_kb", "INTEGER DEFAULT 0"),
    ("readme_size", "INTEGER DEFAULT 0"),
    ("file_count", "INTEGER DEFAULT 0"),
    ("platforms", "TEXT DEFAULT '[]'"),
    ("estimated_tokens", "INTEGER DEFAULT 0"),
]

# Hardcoded seed data for admin tables
SEED_MASTERS = [
    {
        "github": "op7418",
        "github_aliases": json.dumps([]),
        "name": "歸藏",
        "x_handle": "op7418",
        "bio": "产品设计师 / AI 工具专家 / Claude Skills 先驱",
        "tags": json.dumps(["claude-skill", "ppt", "video", "im-bridge"]),
    },
    {
        "github": "zarazhangrui",
        "github_aliases": json.dumps([]),
        "name": "Zara Zhang",
        "x_handle": "zarazhangrui",
        "bio": "AI Tinkerer / Frontend 达人 / YouTube-to-Ebook 作者",
        "tags": json.dumps(["frontend", "youtube", "ebook"]),
    },
    {
        "github": "joeseesun",
        "github_aliases": json.dumps([]),
        "name": "向阳乔木",
        "x_handle": "vista8",
        "bio": "AI 工具达人 / MCP & Agent Skills 资深开发者",
        "tags": json.dumps(["mcp", "agent-tools", "automation", "youtube", "notebooklm"]),
    },
    {
        "github": "dotey",
        "github_aliases": json.dumps(["JimLiu"]),
        "name": "宝玉",
        "x_handle": "dotey",
        "bio": "AI 翻译 & 工具达人 / 开源贡献者",
        "tags": json.dumps(["translation", "ai-tools", "open-source", "skills"]),
    },
    {
        "github": "Panniantong",
        "github_aliases": json.dumps([]),
        "name": "Neo",
        "x_handle": "Neo_Reidlab",
        "bio": "Agent Skills 开发者 / Agent Reach 作者",
        "tags": json.dumps(["agent-reach", "agent-tools"]),
    },
]

SEED_EXTRA_REPOS = [
    "runningZ1/union-search-skill",
    "Panniantong/Agent-Reach",
    "JimLiu/baoyu-skills",
    "joeseesun/yt-search-download",
    "joeseesun/anything-to-notebooklm",
    "joeseesun/skill-publisher",
]

SEED_SEARCH_QUERIES = [
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
    "agent-skill in:name,description,topics",
    "claude-code skill in:name,description",
    "codex skill in:name,description stars:>5",
    "ai skill tool in:name,description stars:>10",
    "cursor-skill in:name,topics",
    "windsurf-skill in:name,topics",
    "antigravity skill in:name,description",
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Add new columns to skills table
    cursor.execute("PRAGMA table_info(skills)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    for col_name, col_def in NEW_SKILL_COLUMNS:
        if col_name not in existing_cols:
            sql = f"ALTER TABLE skills ADD COLUMN {col_name} {col_def}"
            cursor.execute(sql)
            logger.info("Added column: skills.%s", col_name)
        else:
            logger.info("Column already exists: skills.%s", col_name)

    # 2. Create skill_compositions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_compositions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            compatible_skill_id INTEGER NOT NULL,
            compatibility_score REAL DEFAULT 0.0,
            reason VARCHAR(255) DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_sc_skill_id ON skill_compositions(skill_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_sc_compatible_id ON skill_compositions(compatible_skill_id)")
    logger.info("Created table: skill_compositions")

    # 3. Create admin tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_masters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            github VARCHAR(255) UNIQUE NOT NULL,
            github_aliases TEXT DEFAULT '[]',
            name VARCHAR(255) NOT NULL,
            x_handle VARCHAR(255),
            bio TEXT,
            tags TEXT DEFAULT '[]',
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("Created table: skill_masters")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extra_repos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name VARCHAR(255) UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("Created table: extra_repos")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query VARCHAR(500) UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("Created table: search_queries")

    # 4. Seed admin tables (skip if already populated)
    cursor.execute("SELECT COUNT(*) FROM skill_masters")
    if cursor.fetchone()[0] == 0:
        for m in SEED_MASTERS:
            cursor.execute(
                "INSERT INTO skill_masters (github, github_aliases, name, x_handle, bio, tags) VALUES (?, ?, ?, ?, ?, ?)",
                (m["github"], m["github_aliases"], m["name"], m["x_handle"], m["bio"], m["tags"]),
            )
        logger.info("Seeded %d masters", len(SEED_MASTERS))
    else:
        logger.info("skill_masters already populated, skipping seed")

    cursor.execute("SELECT COUNT(*) FROM extra_repos")
    if cursor.fetchone()[0] == 0:
        for repo in SEED_EXTRA_REPOS:
            cursor.execute("INSERT INTO extra_repos (full_name) VALUES (?)", (repo,))
        logger.info("Seeded %d extra repos", len(SEED_EXTRA_REPOS))
    else:
        logger.info("extra_repos already populated, skipping seed")

    cursor.execute("SELECT COUNT(*) FROM search_queries")
    if cursor.fetchone()[0] == 0:
        for q in SEED_SEARCH_QUERIES:
            cursor.execute("INSERT INTO search_queries (query) VALUES (?)", (q,))
        logger.info("Seeded %d search queries", len(SEED_SEARCH_QUERIES))
    else:
        logger.info("search_queries already populated, skipping seed")

    conn.commit()
    conn.close()
    logger.info("Migration complete!")


if __name__ == "__main__":
    main()
