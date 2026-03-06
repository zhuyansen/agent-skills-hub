"""
One-time migration script: SQLite → Supabase PostgreSQL.

Usage:
  cd backend
  python migrate_to_supabase.py

Requires:
  - .env with SUPABASE_DB_URL set
  - SQLite database at ./skills_hub.db
  - pip install psycopg2-binary
"""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

SQLITE_URL = "sqlite:///./skills_hub.db"
PG_URL = os.getenv("SUPABASE_DB_URL")

if not PG_URL:
    print("ERROR: SUPABASE_DB_URL not set in .env")
    sys.exit(1)


def migrate():
    # Connect to both databases
    sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    pg_engine = create_engine(PG_URL)

    sqlite_session = sessionmaker(bind=sqlite_engine)()
    pg_session = sessionmaker(bind=pg_engine)()

    tables = [
        "search_queries",
        "extra_repos",
        "skill_masters",
        "sync_logs",
        "skills",
        "skill_compositions",
    ]

    for table_name in tables:
        print(f"\n--- Migrating {table_name} ---")

        # Read all rows from SQLite
        rows = sqlite_session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
        if not rows:
            print(f"  No rows in {table_name}, skipping.")
            continue

        # Get column names
        columns = sqlite_session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        col_names = [col[1] for col in columns]

        print(f"  Found {len(rows)} rows, columns: {col_names}")

        # Clear existing data in PG (optional — for idempotent reruns)
        pg_session.execute(text(f"DELETE FROM {table_name}"))

        # Insert in batches
        batch_size = 100
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            for row in batch:
                values = {}
                for j, col_name in enumerate(col_names):
                    val = row[j]
                    # Convert SQLite datetime strings to proper datetime objects
                    if val is not None and isinstance(val, str) and col_name in (
                        "created_at", "last_commit_at", "pushed_at",
                        "first_seen", "last_synced", "started_at",
                        "finished_at", "x_verified_at", "updated_at",
                    ):
                        try:
                            val = datetime.fromisoformat(val.replace("Z", "+00:00"))
                        except (ValueError, AttributeError):
                            pass
                    values[col_name] = val

                placeholders = ", ".join(f":{col}" for col in col_names)
                col_list = ", ".join(col_names)
                pg_session.execute(
                    text(f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"),
                    values,
                )

            pg_session.commit()
            print(f"  Inserted batch {i // batch_size + 1} ({len(batch)} rows)")

        # Reset sequence to max id
        pg_session.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {table_name}), 1))"
        ))
        pg_session.commit()
        print(f"  Sequence reset for {table_name}")

    print("\n=== Migration complete! ===")

    # Verify counts
    for table_name in tables:
        sqlite_count = sqlite_session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        pg_count = pg_session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        status = "OK" if sqlite_count == pg_count else "MISMATCH"
        print(f"  {table_name}: SQLite={sqlite_count}, PG={pg_count} [{status}]")

    sqlite_session.close()
    pg_session.close()


if __name__ == "__main__":
    migrate()
