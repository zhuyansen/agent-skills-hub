-- ═══════════════════════════════════════════════════════════
-- Agent Skills Hub — Supabase Initial Migration
-- Run this in Supabase SQL Editor to create all tables,
-- views, indexes, and functions.
-- Safe to re-run (idempotent).
-- ═══════════════════════════════════════════════════════════

-- ═══ 1. TABLES ═══

CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    repo_full_name VARCHAR(255) UNIQUE NOT NULL,
    repo_name VARCHAR(255) NOT NULL,
    repo_url VARCHAR(512) NOT NULL,
    description TEXT DEFAULT '',
    homepage_url VARCHAR(512) DEFAULT '',
    author_name VARCHAR(255) NOT NULL,
    author_avatar_url VARCHAR(512) DEFAULT '',
    author_followers INTEGER DEFAULT 0,
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    open_issues INTEGER DEFAULT 0,
    total_issues INTEGER DEFAULT 0,
    watchers INTEGER DEFAULT 0,
    total_commits INTEGER DEFAULT 0,
    contributors_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    last_commit_at TIMESTAMP,
    pushed_at TIMESTAMP,
    category VARCHAR(100) DEFAULT 'uncategorized',
    language VARCHAR(50) DEFAULT '',
    topics TEXT DEFAULT '[]',
    license VARCHAR(100) DEFAULT '',
    score FLOAT DEFAULT 0.0,
    prev_stars INTEGER DEFAULT 0,
    star_momentum FLOAT DEFAULT 0.0,
    quality_completeness FLOAT DEFAULT 0.0,
    quality_clarity FLOAT DEFAULT 0.0,
    quality_specificity FLOAT DEFAULT 0.0,
    quality_examples FLOAT DEFAULT 0.0,
    quality_score FLOAT DEFAULT 0.0,
    project_type VARCHAR(50) DEFAULT 'tool',
    quality_agent_readiness FLOAT DEFAULT 0.0,
    size_category VARCHAR(20) DEFAULT 'unknown',
    repo_size_kb INTEGER DEFAULT 0,
    readme_size INTEGER DEFAULT 0,
    readme_content TEXT,
    readme_structure_score FLOAT DEFAULT 0.0,
    file_count INTEGER DEFAULT 0,
    platforms TEXT DEFAULT '[]',
    estimated_tokens INTEGER DEFAULT 0,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_synced TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skill_compositions (
    id SERIAL PRIMARY KEY,
    skill_id INTEGER NOT NULL,
    compatible_skill_id INTEGER NOT NULL,
    compatibility_score FLOAT DEFAULT 0.0,
    reason VARCHAR(255) DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running',
    repos_found INTEGER DEFAULT 0,
    repos_updated INTEGER DEFAULT 0,
    repos_new INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS skill_masters (
    id SERIAL PRIMARY KEY,
    github VARCHAR(255) UNIQUE NOT NULL,
    github_aliases TEXT DEFAULT '[]',
    name VARCHAR(255) NOT NULL,
    x_handle VARCHAR(255),
    bio TEXT,
    tags TEXT DEFAULT '[]',
    x_followers INTEGER DEFAULT 0,
    x_posts_count INTEGER DEFAULT 0,
    x_verified_at TIMESTAMP,
    x_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS extra_repos (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'pending',
    submitted_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS search_queries (
    id SERIAL PRIMARY KEY,
    query VARCHAR(500) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscribers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    subscribed_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(64),
    verified_at TIMESTAMP
);

-- ═══ 2. INDEXES ═══

CREATE INDEX IF NOT EXISTS ix_skills_repo_full_name ON skills(repo_full_name);
CREATE INDEX IF NOT EXISTS ix_skills_category ON skills(category);
CREATE INDEX IF NOT EXISTS ix_skills_score ON skills(score);
CREATE INDEX IF NOT EXISTS ix_skills_category_score ON skills(category, score);
CREATE INDEX IF NOT EXISTS ix_skills_last_commit_at ON skills(last_commit_at);
CREATE INDEX IF NOT EXISTS ix_skills_stars ON skills(stars);
CREATE INDEX IF NOT EXISTS ix_skills_last_synced ON skills(last_synced);
CREATE INDEX IF NOT EXISTS ix_skills_author_name ON skills(author_name);
CREATE INDEX IF NOT EXISTS ix_skills_created_at ON skills(created_at);
CREATE INDEX IF NOT EXISTS ix_compositions_skill_id ON skill_compositions(skill_id);
CREATE INDEX IF NOT EXISTS ix_compositions_compatible ON skill_compositions(compatible_skill_id);
CREATE INDEX IF NOT EXISTS ix_subscribers_email ON subscribers(email);
CREATE INDEX IF NOT EXISTS ix_subscribers_token ON subscribers(verification_token);

-- ═══ 3. VIEWS ═══

CREATE OR REPLACE VIEW v_stats AS
SELECT
    COUNT(*) AS total_skills,
    ROUND(COALESCE(AVG(score), 0)::numeric, 1) AS avg_score,
    (SELECT started_at FROM sync_logs ORDER BY started_at DESC LIMIT 1) AS last_sync_at,
    (SELECT status FROM sync_logs ORDER BY started_at DESC LIMIT 1) AS last_sync_status
FROM skills;

CREATE OR REPLACE VIEW v_categories AS
SELECT category AS name, COUNT(*) AS count
FROM skills
GROUP BY category
ORDER BY count DESC;

CREATE OR REPLACE VIEW v_language_stats AS
SELECT language, COUNT(*) AS count
FROM skills
WHERE language IS NOT NULL AND language != ''
GROUP BY language
ORDER BY count DESC
LIMIT 15;

CREATE OR REPLACE VIEW v_trending AS
SELECT *
FROM skills
WHERE stars >= 50
  AND created_at IS NOT NULL
  AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY (stars::float / GREATEST(EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400, 1)) DESC
LIMIT 20;

CREATE OR REPLACE VIEW v_rising AS
SELECT *
FROM skills
WHERE star_momentum > 0
ORDER BY star_momentum DESC
LIMIT 20;

CREATE OR REPLACE VIEW v_top_rated AS
SELECT *
FROM skills
WHERE score > 0
ORDER BY score DESC
LIMIT 20;

CREATE OR REPLACE VIEW v_community_classics AS
SELECT *
FROM skills
WHERE stars >= 100
  AND created_at IS NOT NULL
  AND created_at < NOW() - INTERVAL '180 days'
ORDER BY stars DESC
LIMIT 20;

CREATE OR REPLACE VIEW v_recently_updated AS
SELECT *
FROM skills
WHERE last_commit_at IS NOT NULL
ORDER BY last_commit_at DESC
LIMIT 20;

-- ═══ 4. FUNCTIONS ═══

CREATE OR REPLACE FUNCTION get_masters()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'masters', COALESCE((
            SELECT json_agg(row_to_json(m))
            FROM (
                SELECT
                    sm.github,
                    sm.name,
                    sm.x_handle,
                    sm.bio,
                    sm.tags::json AS tags,
                    sm.github_aliases::json AS github_aliases,
                    sm.x_followers,
                    sm.x_posts_count,
                    sm.x_notes,
                    COALESCE(agg.total_stars, 0) AS total_stars,
                    COALESCE(agg.skill_count, 0) AS skill_count,
                    COALESCE(agg.avg_score, 0) AS avg_score,
                    TRUE AS is_verified
                FROM skill_masters sm
                LEFT JOIN LATERAL (
                    SELECT
                        SUM(s.stars) AS total_stars,
                        COUNT(*) AS skill_count,
                        ROUND(AVG(s.score)::numeric, 1) AS avg_score
                    FROM skills s
                    WHERE s.author_name = sm.github
                       OR s.author_name = ANY(
                            SELECT jsonb_array_elements_text(sm.github_aliases::jsonb)
                       )
                ) agg ON TRUE
                WHERE sm.is_active = TRUE
                  AND sm.x_followers >= 1000
                ORDER BY sm.x_followers DESC
            ) m
        ), '[]'::json),
        'emerging', COALESCE((
            SELECT json_agg(row_to_json(e))
            FROM (
                SELECT
                    sm.github,
                    sm.name,
                    sm.x_handle,
                    sm.bio,
                    sm.tags::json AS tags,
                    sm.github_aliases::json AS github_aliases,
                    sm.x_followers,
                    sm.x_posts_count,
                    sm.x_notes,
                    COALESCE(agg.total_stars, 0) AS total_stars,
                    COALESCE(agg.skill_count, 0) AS skill_count,
                    COALESCE(agg.avg_score, 0) AS avg_score,
                    FALSE AS is_verified
                FROM skill_masters sm
                LEFT JOIN LATERAL (
                    SELECT
                        SUM(s.stars) AS total_stars,
                        COUNT(*) AS skill_count,
                        ROUND(AVG(s.score)::numeric, 1) AS avg_score
                    FROM skills s
                    WHERE s.author_name = sm.github
                       OR s.author_name = ANY(
                            SELECT jsonb_array_elements_text(sm.github_aliases::jsonb)
                       )
                ) agg ON TRUE
                WHERE sm.is_active = TRUE
                  AND (sm.x_followers < 1000 OR sm.x_followers IS NULL)
                ORDER BY COALESCE(agg.total_stars, 0) DESC
            ) e
        ), '[]'::json)
    ) INTO result;

    RETURN result;
END;
$$;

CREATE OR REPLACE FUNCTION get_last_sync_at()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    result TEXT;
BEGIN
    SELECT started_at::text INTO result
    FROM sync_logs
    WHERE status = 'completed'
    ORDER BY finished_at DESC
    LIMIT 1;
    RETURN result;
END;
$$;

-- ═══ 5. ROW LEVEL SECURITY (RLS) ═══

ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_compositions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_masters ENABLE ROW LEVEL SECURITY;
ALTER TABLE extra_repos ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;

-- Drop existing policies first (idempotent)
DROP POLICY IF EXISTS "Public read skills" ON skills;
DROP POLICY IF EXISTS "Public read compositions" ON skill_compositions;
DROP POLICY IF EXISTS "Public read sync_logs" ON sync_logs;
DROP POLICY IF EXISTS "Public read skill_masters" ON skill_masters;
DROP POLICY IF EXISTS "Service write skills" ON skills;
DROP POLICY IF EXISTS "Service write compositions" ON skill_compositions;
DROP POLICY IF EXISTS "Service write sync_logs" ON sync_logs;
DROP POLICY IF EXISTS "Service write skill_masters" ON skill_masters;
DROP POLICY IF EXISTS "Service write extra_repos" ON extra_repos;
DROP POLICY IF EXISTS "Service write search_queries" ON search_queries;
DROP POLICY IF EXISTS "Service write subscribers" ON subscribers;

-- Public read (anon key)
CREATE POLICY "Public read skills" ON skills FOR SELECT USING (true);
CREATE POLICY "Public read compositions" ON skill_compositions FOR SELECT USING (true);
CREATE POLICY "Public read sync_logs" ON sync_logs FOR SELECT USING (true);
CREATE POLICY "Public read skill_masters" ON skill_masters FOR SELECT USING (true);

-- Full access for postgres role (used by sync_runner via connection string)
CREATE POLICY "Service write skills" ON skills FOR ALL TO postgres USING (true) WITH CHECK (true);
CREATE POLICY "Service write compositions" ON skill_compositions FOR ALL TO postgres USING (true) WITH CHECK (true);
CREATE POLICY "Service write sync_logs" ON sync_logs FOR ALL TO postgres USING (true) WITH CHECK (true);
CREATE POLICY "Service write skill_masters" ON skill_masters FOR ALL TO postgres USING (true) WITH CHECK (true);
CREATE POLICY "Service write extra_repos" ON extra_repos FOR ALL TO postgres USING (true) WITH CHECK (true);
CREATE POLICY "Service write search_queries" ON search_queries FOR ALL TO postgres USING (true) WITH CHECK (true);
CREATE POLICY "Service write subscribers" ON subscribers FOR ALL TO postgres USING (true) WITH CHECK (true);

-- ═══ DONE ═══
