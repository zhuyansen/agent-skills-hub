"""V4 migration: Masters X data + project_type + agent_readiness."""
import sqlite3
import sys

DB_PATH = "skills_hub.db"

SKILL_MASTER_COLUMNS = [
    ("x_followers", "INTEGER DEFAULT 0"),
    ("x_posts_count", "INTEGER DEFAULT 0"),
    ("x_verified_at", "DATETIME DEFAULT NULL"),
    ("x_notes", "TEXT DEFAULT NULL"),
]

SKILL_COLUMNS = [
    ("project_type", "VARCHAR(50) DEFAULT 'tool'"),
    ("quality_agent_readiness", "REAL DEFAULT 0.0"),
]


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for col, typedef in SKILL_MASTER_COLUMNS:
        try:
            cur.execute(f"ALTER TABLE skill_masters ADD COLUMN {col} {typedef}")
            print(f"  + skill_masters.{col}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"  ~ skill_masters.{col} (exists)")
            else:
                raise

    for col, typedef in SKILL_COLUMNS:
        try:
            cur.execute(f"ALTER TABLE skills ADD COLUMN {col} {typedef}")
            print(f"  + skills.{col}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"  ~ skills.{col} (exists)")
            else:
                raise

    conn.commit()
    conn.close()
    print("V4 migration complete.")


if __name__ == "__main__":
    migrate()
