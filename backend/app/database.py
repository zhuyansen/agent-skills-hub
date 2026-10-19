from typing import Generator

from sqlalchemy import create_engine, event
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

# Supabase's transaction pooler (port 6543) gives each transaction a pooled backend
# connection, and a session-level SET another client left on it applies to us too:
# on 2026-10-18 a review script's `SET statement_timeout = '30s'` cancelled the sync's
# writes after ~50 s and the run failed. Re-assert the database default at the start of
# every transaction, scoped to that transaction, so a leaked value never reaches us.
STATEMENT_TIMEOUT = "120s"


def _own_statement_timeout(conn) -> None:
    conn.exec_driver_sql(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'")


if engine.dialect.name == "postgresql":
    event.listen(engine, "begin", _own_statement_timeout)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
