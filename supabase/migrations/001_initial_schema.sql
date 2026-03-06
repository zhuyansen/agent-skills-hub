-- ============================================================
-- Agent Skills Hub — Supabase PostgreSQL Schema
-- Migrated from SQLAlchemy/SQLite
-- ============================================================

-- 1. TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS skills (
  id              BIGSERIAL PRIMARY KEY,

  -- GitHub identity
  repo_full_name  VARCHAR(255) NOT NULL UNIQUE,
  repo_name       VARCHAR(255) NOT NULL,
  repo_url        VARCHAR(512) NOT NULL,
  description     TEXT DEFAULT '',
  homepage_url    VARCHAR(512) DEFAULT '',

  -- Author / Org
  author_name       VARCHAR(255) NOT NULL,
  author_avatar_url VARCHAR(512) DEFAULT '',
  author_followers  INTEGER DEFAULT 0,

  -- GitHub metrics
  stars             INTEGER DEFAULT 0,
  forks             INTEGER DEFAULT 0,
  open_issues       INTEGER DEFAULT 0,
  total_issues      INTEGER DEFAULT 0,
  watchers          INTEGER DEFAULT 0,
  total_commits     INTEGER DEFAULT 0,
  contributors_count INTEGER DEFAULT 0,

  -- Timestamps from GitHub
  created_at      TIMESTAMPTZ,
  last_commit_at  TIMESTAMPTZ,
  pushed_at       TIMESTAMPTZ,

  -- Classification
  category        VARCHAR(100) DEFAULT 'uncategorized',
  language        VARCHAR(50) DEFAULT '',
  topics          TEXT DEFAULT '[]',
  license         VARCHAR(100) DEFAULT '',

  -- Computed score (overall)
  score           DOUBLE PRECISION DEFAULT 0.0,

  -- Momentum
  prev_stars      INTEGER DEFAULT 0,
  star_momentum   DOUBLE PRECISION DEFAULT 0.0,

  -- Quality scoring (4 dimensions)
  quality_completeness DOUBLE PRECISION DEFAULT 0.0,
  quality_clarity      DOUBLE PRECISION DEFAULT 0.0,
  quality_specificity  DOUBLE PRECISION DEFAULT 0.0,
  quality_examples     DOUBLE PRECISION DEFAULT 0.0,
  quality_score        DOUBLE PRECISION DEFAULT 0.0,

  -- Project type
  project_type    VARCHAR(50) DEFAULT 'tool',

  -- Agent readiness
  quality_agent_readiness DOUBLE PRECISION DEFAULT 0.0,

  -- Size / Focus
  size_category   VARCHAR(20) DEFAULT 'unknown',
  repo_size_kb    INTEGER DEFAULT 0,
  readme_size     INTEGER DEFAULT 0,
  readme_content  TEXT,
  readme_structure_score DOUBLE PRECISION DEFAULT 0.0,
  file_count      INTEGER DEFAULT 0,

  -- Platform compatibility (JSON list)
  platforms       TEXT DEFAULT '[]',

  -- Token budget
  estimated_tokens INTEGER DEFAULT 0,

  -- Internal timestamps
  first_seen      TIMESTAMPTZ DEFAULT NOW(),
  last_synced     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skill_compositions (
  id                    BIGSERIAL PRIMARY KEY,
  skill_id              BIGINT NOT NULL,
  compatible_skill_id   BIGINT NOT NULL,
  compatibility_score   DOUBLE PRECISION DEFAULT 0.0,
  reason                VARCHAR(255) DEFAULT '',
  created_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sync_logs (
  id            BIGSERIAL PRIMARY KEY,
  started_at    TIMESTAMPTZ DEFAULT NOW(),
  finished_at   TIMESTAMPTZ,
  status        VARCHAR(20) DEFAULT 'running',
  repos_found   INTEGER DEFAULT 0,
  repos_updated INTEGER DEFAULT 0,
  repos_new     INTEGER DEFAULT 0,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS skill_masters (
  id              BIGSERIAL PRIMARY KEY,
  github          VARCHAR(255) NOT NULL UNIQUE,
  github_aliases  TEXT DEFAULT '[]',
  name            VARCHAR(255) NOT NULL,
  x_handle        VARCHAR(255),
  bio             TEXT,
  tags            TEXT DEFAULT '[]',
  x_followers     INTEGER DEFAULT 0,
  x_posts_count   INTEGER DEFAULT 0,
  x_verified_at   TIMESTAMPTZ,
  x_notes         TEXT,
  is_active       BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS extra_repos (
  id          BIGSERIAL PRIMARY KEY,
  full_name   VARCHAR(255) NOT NULL UNIQUE,
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS search_queries (
  id          BIGSERIAL PRIMARY KEY,
  query       VARCHAR(500) NOT NULL UNIQUE,
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);


-- 2. INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_skills_repo_full_name ON skills(repo_full_name);
CREATE INDEX IF NOT EXISTS idx_skills_category       ON skills(category);
CREATE INDEX IF NOT EXISTS idx_skills_score          ON skills(score DESC);
CREATE INDEX IF NOT EXISTS idx_skills_stars          ON skills(stars DESC);
CREATE INDEX IF NOT EXISTS idx_skills_created_at     ON skills(created_at);
CREATE INDEX IF NOT EXISTS idx_skills_last_commit_at ON skills(last_commit_at DESC);
CREATE INDEX IF NOT EXISTS idx_skills_author_name    ON skills(author_name);

CREATE INDEX IF NOT EXISTS idx_compositions_skill_id      ON skill_compositions(skill_id);
CREATE INDEX IF NOT EXISTS idx_compositions_compatible_id  ON skill_compositions(compatible_skill_id);

CREATE INDEX IF NOT EXISTS idx_sync_logs_started_at ON sync_logs(started_at DESC);


-- 3. ROW-LEVEL SECURITY
-- ============================================================

ALTER TABLE skills             ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_compositions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_logs          ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_masters      ENABLE ROW LEVEL SECURITY;
ALTER TABLE extra_repos        ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_queries     ENABLE ROW LEVEL SECURITY;

-- Public read for anon / authenticated users
CREATE POLICY "skills_public_read"       ON skills             FOR SELECT USING (true);
CREATE POLICY "compositions_public_read" ON skill_compositions FOR SELECT USING (true);
CREATE POLICY "sync_logs_public_read"    ON sync_logs          FOR SELECT USING (true);
CREATE POLICY "masters_public_read"      ON skill_masters      FOR SELECT USING (true);

-- Service role can do everything (used by GitHub Actions sync)
CREATE POLICY "skills_service_all"       ON skills             FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "compositions_service_all" ON skill_compositions FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "sync_logs_service_all"    ON sync_logs          FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "masters_service_all"      ON skill_masters      FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "extra_repos_service_all"  ON extra_repos        FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "queries_service_all"      ON search_queries     FOR ALL USING (auth.role() = 'service_role');


-- 4. VIEWS (replace FastAPI aggregation endpoints)
-- ============================================================

-- Trending: star velocity for repos created in last 7 days with >= 50 stars
CREATE OR REPLACE VIEW v_trending AS
SELECT *,
  stars::DOUBLE PRECISION / GREATEST(EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0, 1) AS star_velocity
FROM skills
WHERE stars >= 50
  AND created_at IS NOT NULL
  AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY star_velocity DESC
LIMIT 20;

-- Rising: new repos in last 7 days, sorted by stars
CREATE OR REPLACE VIEW v_rising AS
SELECT *
FROM skills
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY stars DESC
LIMIT 20;

-- Top Rated: highest scores
CREATE OR REPLACE VIEW v_top_rated AS
SELECT *
FROM skills
ORDER BY score DESC
LIMIT 20;

-- Community Classics: 6+ months old, 100+ stars
CREATE OR REPLACE VIEW v_community_classics AS
SELECT *
FROM skills
WHERE stars >= 100
  AND created_at IS NOT NULL
  AND created_at <= NOW() - INTERVAL '180 days'
ORDER BY stars DESC
LIMIT 20;

-- Recently Updated: most recent last_commit_at
CREATE OR REPLACE VIEW v_recently_updated AS
SELECT *
FROM skills
WHERE last_commit_at IS NOT NULL
ORDER BY last_commit_at DESC
LIMIT 20;

-- Stats aggregate
CREATE OR REPLACE VIEW v_stats AS
SELECT
  COUNT(*)::INTEGER AS total_skills,
  ROUND(AVG(score)::NUMERIC, 1)::DOUBLE PRECISION AS avg_score,
  COUNT(DISTINCT category)::INTEGER AS category_count,
  (SELECT started_at FROM sync_logs ORDER BY started_at DESC LIMIT 1) AS last_sync_at,
  (SELECT status FROM sync_logs ORDER BY started_at DESC LIMIT 1) AS last_sync_status
FROM skills;

-- Category distribution
CREATE OR REPLACE VIEW v_categories AS
SELECT
  category AS name,
  COUNT(*)::INTEGER AS count
FROM skills
GROUP BY category
ORDER BY count DESC;

-- Language stats
CREATE OR REPLACE VIEW v_language_stats AS
SELECT
  language,
  COUNT(*)::INTEGER AS count
FROM skills
WHERE language <> ''
GROUP BY language
ORDER BY count DESC
LIMIT 10;


-- 5. FUNCTIONS
-- ============================================================

-- get_masters: returns masters + emerging builders as JSON array
CREATE OR REPLACE FUNCTION get_masters()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
BEGIN
  WITH master_data AS (
    SELECT
      m.github,
      m.github_aliases,
      m.name,
      m.x_handle,
      m.bio,
      m.tags,
      m.x_followers,
      m.x_posts_count,
      m.x_verified_at,
      m.x_notes
    FROM skill_masters m
    WHERE m.is_active = TRUE
  ),
  master_repos AS (
    SELECT
      md.github,
      md.github_aliases,
      md.name,
      md.x_handle,
      md.bio,
      md.tags,
      md.x_followers,
      md.x_posts_count,
      md.x_verified_at,
      md.x_notes,
      COALESCE(
        (SELECT json_agg(row_to_json(r) ORDER BY r.stars DESC)
         FROM (
           SELECT s.id, s.repo_name, s.repo_full_name, s.repo_url,
                  s.description, s.stars, s.score, s.category, s.author_avatar_url
           FROM skills s
           WHERE s.author_name = md.github
              OR s.author_name = ANY(
                SELECT jsonb_array_elements_text(md.github_aliases::jsonb)
              )
           ORDER BY s.stars DESC
           LIMIT 5
         ) r),
        '[]'::json
      ) AS top_repos
    FROM master_data md
  ),
  master_results AS (
    SELECT json_agg(
      json_build_object(
        'github', mr.github,
        'github_aliases', mr.github_aliases::json,
        'name', mr.name,
        'x_handle', mr.x_handle,
        'bio', mr.bio,
        'tags', mr.tags::json,
        'x_followers', COALESCE(mr.x_followers, 0),
        'x_posts_count', COALESCE(mr.x_posts_count, 0),
        'x_verified_at', mr.x_verified_at,
        'x_notes', mr.x_notes,
        'avatar_url', COALESCE(
          (SELECT s.author_avatar_url FROM skills s
           WHERE s.author_name = mr.github LIMIT 1),
          'https://github.com/' || mr.github || '.png'
        ),
        'repo_count', (
          SELECT COUNT(*) FROM skills s
          WHERE s.author_name = mr.github
             OR s.author_name = ANY(
               SELECT jsonb_array_elements_text(mr.github_aliases::jsonb)
             )
        ),
        'total_stars', (
          SELECT COALESCE(SUM(s.stars), 0) FROM skills s
          WHERE s.author_name = mr.github
             OR s.author_name = ANY(
               SELECT jsonb_array_elements_text(mr.github_aliases::jsonb)
             )
        ),
        'top_repos', mr.top_repos
      )
    ) FROM master_repos mr
  ),
  -- Emerging builders: 3+ repos, 500+ total stars, active last 3 months
  known AS (
    SELECT jsonb_array_elements_text(
      jsonb_build_array(md.github) || COALESCE(md.github_aliases::jsonb, '[]'::jsonb)
    ) AS uname
    FROM master_data md
  ),
  emerging AS (
    SELECT
      s.author_name,
      COUNT(*)::INTEGER AS cnt,
      SUM(s.stars)::INTEGER AS total
    FROM skills s
    WHERE s.last_commit_at >= NOW() - INTERVAL '90 days'
      AND s.author_name NOT IN (SELECT uname FROM known)
    GROUP BY s.author_name
    HAVING COUNT(*) >= 3 AND SUM(s.stars) >= 500
    ORDER BY SUM(s.stars) DESC
    LIMIT 20
  ),
  emerging_results AS (
    SELECT json_agg(
      json_build_object(
        'github', e.author_name,
        'name', e.author_name,
        'x_handle', NULL,
        'bio', NULL,
        'tags', '[]'::json,
        'avatar_url', COALESCE(
          (SELECT s2.author_avatar_url FROM skills s2
           WHERE s2.author_name = e.author_name LIMIT 1),
          'https://github.com/' || e.author_name || '.png'
        ),
        'repo_count', e.cnt,
        'total_stars', e.total,
        'top_repos', COALESCE(
          (SELECT json_agg(row_to_json(r2) ORDER BY r2.stars DESC)
           FROM (
             SELECT s3.id, s3.repo_name, s3.repo_full_name, s3.repo_url,
                    s3.description, s3.stars, s3.score, s3.category
             FROM skills s3
             WHERE s3.author_name = e.author_name
             ORDER BY s3.stars DESC
             LIMIT 5
           ) r2),
          '[]'::json
        ),
        'discovered', true
      )
    ) FROM emerging e
  )
  SELECT json_build_object(
    'masters', COALESCE((SELECT * FROM master_results), '[]'::json),
    'emerging', COALESCE((SELECT * FROM emerging_results), '[]'::json)
  ) INTO result;

  RETURN result;
END;
$$;

-- health_check: simple health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  skill_count INTEGER;
  last_sync TIMESTAMPTZ;
  sync_status TEXT;
BEGIN
  SELECT COUNT(*) INTO skill_count FROM skills;
  SELECT started_at, status INTO last_sync, sync_status
    FROM sync_logs ORDER BY started_at DESC LIMIT 1;

  RETURN json_build_object(
    'status', 'ok',
    'skill_count', skill_count,
    'last_sync_at', last_sync,
    'last_sync_status', sync_status
  );
END;
$$;

-- get_last_sync_at: for cache invalidation
CREATE OR REPLACE FUNCTION get_last_sync_at()
RETURNS TIMESTAMPTZ
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT started_at FROM sync_logs
  WHERE status = 'completed'
  ORDER BY started_at DESC
  LIMIT 1;
$$;
