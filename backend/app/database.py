from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

# SQLite needs check_same_thread=False; PostgreSQL does not
connect_args = {}
engine_kwargs = {}

if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif "pooler.supabase.com" in settings.database_url or settings.database_url.startswith("postgresql"):
    # When using Supabase Connection Pooler (PgBouncer), disable SQLAlchemy's
    # own connection pool to avoid double-pooling.  Transaction pooler mode
    # doesn't support PREPARE statements but psycopg2 doesn't use them.
    engine_kwargs["poolclass"] = NullPool
    # pool_pre_ping validates connections before use (detects stale PgBouncer connections)
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(settings.database_url, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
