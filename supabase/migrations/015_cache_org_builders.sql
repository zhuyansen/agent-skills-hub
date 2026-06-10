-- 015_cache_org_builders.sql
-- Date: 2026-06-09
-- Issue: the homepage "Organizations" module intermittently disappears.
--
-- Root cause: same class as 013 (masters) and 014 (landing). get_org_builders()
-- runs a GROUP BY author_name with a per-group json_agg of top repos, filtered
-- by HAVING COUNT(*) >= 3 AND SUM(stars) >= 10000, over the full 104K-row skills
-- table. It sits right at Supabase's statement_timeout: sometimes 200, sometimes
-- 57014. SkillsMasters.tsx only renders the org section when orgs.length > 0,
-- so every time the RPC times out, the whole module vanishes.
--
-- Fix: pre-compute into a one-row cache, refreshed by sync every 8h. The getter
-- returns the cached JSON instantly.

SET LOCAL statement_timeout = 0;

CREATE TABLE IF NOT EXISTS org_builders_cache (
  id           int PRIMARY KEY DEFAULT 1,
  payload      json NOT NULL,
  refreshed_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT org_builders_single_row CHECK (id = 1)
);

-- Heavy aggregation moved to a private compute function (unchanged logic).
CREATE OR REPLACE FUNCTION compute_org_builders()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
BEGIN
  SELECT COALESCE(json_agg(row_to_json(org)), '[]'::json)
  INTO result
  FROM (
    SELECT
      s.author_name AS github,
      s.author_name AS name,
      s.author_avatar_url AS avatar_url,
      COUNT(*) AS repo_count,
      SUM(s.stars) AS total_stars,
      json_agg(
        json_build_object(
          'id', s.id,
          'repo_name', s.repo_name,
          'repo_full_name', s.repo_full_name,
          'repo_url', s.repo_url,
          'description', COALESCE(s.description, ''),
          'stars', s.stars,
          'score', COALESCE(s.quality_score, 0),
          'category', s.category
        ) ORDER BY s.stars DESC
      ) AS top_repos
    FROM skills s
    WHERE s.author_name NOT IN (SELECT sm.github FROM skill_masters sm WHERE sm.is_active = TRUE)
      AND s.author_name NOT IN (
        SELECT jsonb_array_elements_text(sm.github_aliases::jsonb)
        FROM skill_masters sm WHERE sm.is_active = TRUE
      )
    GROUP BY s.author_name, s.author_avatar_url
    HAVING COUNT(*) >= 3 AND SUM(s.stars) >= 10000
    ORDER BY SUM(s.stars) DESC
    LIMIT 20
  ) org;
  RETURN result;
END;
$$;

-- Refresh: compute + store (lifts statement_timeout). Called by sync_runner.
CREATE OR REPLACE FUNCTION refresh_org_builders()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  SET LOCAL statement_timeout = 0;
  INSERT INTO org_builders_cache (id, payload, refreshed_at)
  VALUES (1, compute_org_builders(), now())
  ON CONFLICT (id) DO UPDATE
    SET payload = EXCLUDED.payload,
        refreshed_at = EXCLUDED.refreshed_at;
END;
$$;

-- Fast getter — returns the cached payload; live-computes only if cache empty.
CREATE OR REPLACE FUNCTION get_org_builders()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
BEGIN
  SELECT payload INTO result FROM org_builders_cache WHERE id = 1;
  IF result IS NULL THEN
    result := compute_org_builders();
  END IF;
  RETURN result;
END;
$$;

GRANT EXECUTE ON FUNCTION get_org_builders()     TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION compute_org_builders() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION refresh_org_builders() TO anon, authenticated, service_role;
GRANT SELECT ON org_builders_cache               TO anon, authenticated, service_role;

SELECT refresh_org_builders();
NOTIFY pgrst, 'reload schema';
