-- 007: Weekly Trending Snapshots
-- Stores weekly Star Velocity rankings for historical browsing.
-- Each week's top skills are captured once during sync.

-- 1. Create the snapshots table
CREATE TABLE IF NOT EXISTS weekly_trending_snapshots (
  id BIGSERIAL PRIMARY KEY,
  week_start DATE NOT NULL,
  week_end DATE NOT NULL,
  rank INTEGER NOT NULL,
  skill_id INTEGER NOT NULL,
  repo_full_name VARCHAR(255) NOT NULL,
  repo_name VARCHAR(255) NOT NULL,
  author_name VARCHAR(255) NOT NULL,
  author_avatar_url VARCHAR(512) DEFAULT '',
  stars INTEGER NOT NULL,
  star_velocity DOUBLE PRECISION NOT NULL,
  description TEXT DEFAULT '',
  repo_url VARCHAR(512) DEFAULT '',
  category VARCHAR(100) DEFAULT '',
  created_at_snap TIMESTAMPTZ,
  last_commit_at_snap TIMESTAMPTZ,
  snapshot_taken_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(week_start, rank)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS ix_wts_week_start ON weekly_trending_snapshots(week_start);

-- 2. RLS: public read access
ALTER TABLE weekly_trending_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read weekly_trending_snapshots"
  ON weekly_trending_snapshots
  FOR SELECT
  USING (true);

-- 3. RPC: get list of available weeks
CREATE OR REPLACE FUNCTION get_trending_weeks()
RETURNS TABLE(week_start DATE, week_end DATE, snapshot_count INT)
LANGUAGE sql STABLE
AS $$
  SELECT
    week_start,
    week_end,
    COUNT(*)::INT AS snapshot_count
  FROM weekly_trending_snapshots
  GROUP BY week_start, week_end
  ORDER BY week_start DESC;
$$;

-- 4. RPC: get trending history for a specific week
CREATE OR REPLACE FUNCTION get_trending_history(p_week_start DATE)
RETURNS TABLE(
  rank INT,
  skill_id INT,
  repo_full_name VARCHAR,
  repo_name VARCHAR,
  author_name VARCHAR,
  author_avatar_url VARCHAR,
  stars INT,
  star_velocity DOUBLE PRECISION,
  description TEXT,
  repo_url VARCHAR,
  category VARCHAR,
  created_at_snap TIMESTAMPTZ,
  last_commit_at_snap TIMESTAMPTZ
)
LANGUAGE sql STABLE
AS $$
  SELECT
    rank,
    skill_id,
    repo_full_name,
    repo_name,
    author_name,
    author_avatar_url,
    stars,
    star_velocity,
    description,
    repo_url,
    category,
    created_at_snap,
    last_commit_at_snap
  FROM weekly_trending_snapshots
  WHERE week_start = p_week_start
  ORDER BY rank;
$$;

-- 5. Seed: insert current week's data from v_trending
INSERT INTO weekly_trending_snapshots (
  week_start, week_end, rank, skill_id, repo_full_name, repo_name,
  author_name, author_avatar_url, stars, star_velocity,
  description, repo_url, category, created_at_snap, last_commit_at_snap
)
SELECT
  DATE_TRUNC('week', CURRENT_DATE)::DATE AS week_start,
  (DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 days')::DATE AS week_end,
  ROW_NUMBER() OVER (ORDER BY
    CASE WHEN created_at IS NOT NULL AND created_at > '2000-01-01'
      THEN stars::FLOAT / GREATEST(EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0, 1)
      ELSE 0 END DESC
  )::INT AS rank,
  id, repo_full_name, repo_name,
  author_name, author_avatar_url, stars,
  CASE WHEN created_at IS NOT NULL AND created_at > '2000-01-01'
    THEN stars::FLOAT / GREATEST(EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0, 1)
    ELSE 0 END AS star_velocity,
  description, repo_url, category, created_at, last_commit_at
FROM skills
WHERE stars >= 50 AND created_at IS NOT NULL AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY star_velocity DESC
LIMIT 20
ON CONFLICT (week_start, rank) DO NOTHING;
