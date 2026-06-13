-- 016_author_name_trgm_index.sql
--
-- Speeds up /author/{username}/ runtime queries, which filter the 106K-row
-- skills table with `author_name ILIKE $1` (case-insensitive exact match).
-- Without a matching index this did a seq scan + sort + count and tripped the
-- statement_timeout (57014 / 504), so author pages rendered empty for users.
--
-- A trigram GIN index supports ILIKE. Build it CONCURRENTLY to avoid locking
-- the table, and disable the statement timeout for the build (a GIN build over
-- 106K rows exceeds the default).
--
-- NOTE: CREATE INDEX CONCURRENTLY cannot run inside a transaction block. If
-- applying via a migration tool that wraps statements in a transaction, run
-- this file outside that wrapper (or apply manually with autocommit).
-- Already applied manually to production on 2026-06-13.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

SET statement_timeout = 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_skills_author_name_trgm
  ON skills USING gin (author_name gin_trgm_ops);
