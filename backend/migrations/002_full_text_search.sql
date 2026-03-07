-- ═══════════════════════════════════════════════════════════
-- Full-text search: GIN index + tsvector for fast search
-- Run in Supabase SQL Editor after 001_init_supabase.sql
-- ═══════════════════════════════════════════════════════════

-- Add generated tsvector column for full-text search
ALTER TABLE skills ADD COLUMN IF NOT EXISTS search_vector tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(repo_name, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(author_name, '')), 'C') ||
    setweight(to_tsvector('english', coalesce(topics, '')), 'C')
  ) STORED;

-- GIN index on the tsvector column for fast full-text search
CREATE INDEX IF NOT EXISTS ix_skills_search_vector ON skills USING GIN (search_vector);

-- Trigram index for fuzzy/partial matching (LIKE %keyword%)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS ix_skills_repo_name_trgm ON skills USING GIN (repo_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_skills_description_trgm ON skills USING GIN (description gin_trgm_ops);
