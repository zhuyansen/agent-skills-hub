"""Export the graded-skills dataset for HuggingFace/Kaggle.

Pulls the public-safe columns from Supabase (keyset-paginated, gentle) and
writes parquet + csv to ops/research/out/. No PII — only public GitHub repo
metadata + our derived grades.

Run: python ops/research/export_dataset.py [--min-stars 0]
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "backend"))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "backend", ".env"))

from sqlalchemy import create_engine, text  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
COLS = [
    "repo_full_name", "category", "stars", "forks", "security_grade",
    "security_flags", "quality_score", "score", "language", "license",
    "last_commit_at", "created_at",
]


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


def main():
    try:
        import pandas as pd
    except ImportError:
        sys.exit("pip install pandas pyarrow first")

    min_stars = arg("--min-stars", 0)
    eng = create_engine(
        os.environ["SUPABASE_DB_URL"], pool_pre_ping=True,
        connect_args={"keepalives": 1, "keepalives_idle": 30,
                      "options": "-c statement_timeout=120000"},
    )
    rows, last_id, CHUNK = [], 0, 2000
    col_sql = ", ".join(COLS)
    while True:
        with eng.begin() as c:
            batch = c.execute(text(
                f"SELECT id, {col_sql} FROM skills WHERE id > :lid AND stars >= :ms "
                f"ORDER BY id LIMIT :n"
            ), {"lid": last_id, "ms": min_stars, "n": CHUNK}).mappings().all()
        if not batch:
            break
        rows.extend(dict(r) for r in batch)
        last_id = batch[-1]["id"]
        print(f"  pulled {len(rows)}", flush=True)
        time.sleep(0.2)
        if len(batch) < CHUNK:
            break

    df = pd.DataFrame(rows).drop(columns=["id"])
    os.makedirs(OUT, exist_ok=True)
    df.to_parquet(os.path.join(OUT, "agent-skills-security-grades.parquet"), index=False)
    df.to_csv(os.path.join(OUT, "agent-skills-security-grades.csv"), index=False)
    print(f"✓ {len(df):,} rows → ops/research/out/  (grades: "
          f"{df['security_grade'].value_counts().to_dict()})")


if __name__ == "__main__":
    main()
