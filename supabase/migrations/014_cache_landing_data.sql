-- 014_cache_landing_data.sql
-- Date: 2026-06-09
-- Issue: the homepage shows STALE stats (e.g. 77,476 skills / "updated 1mo
-- ago") while the skills table actually holds 104,806 fresh rows.
--
-- Root cause: get_landing_data() aggregates 8 views (v_stats, v_categories,
-- v_trending, v_rising, v_top_rated, v_community_classics, v_recently_updated,
-- v_language_stats) over the full 104K-row skills table in a single statement.
-- As the table grew it began exceeding Supabase's statement_timeout (57014).
-- The frontend then falls back to a stale cached snapshot — hence 77K / "1mo".
-- Same class of bug as get_masters() (fixed in 013).
--
-- Fix: pre-compute the whole landing payload into a one-row cache table,
-- refreshed by sync (every 8h — which is exactly the homepage's freshness SLA).
-- get_landing_data() now returns the cached JSON instantly. Fixing the RPC
-- also stops the frontend from falling back to the (separately broken)
-- per-view queries, so the homepage Trending/Rising sections recover too.

SET LOCAL statement_timeout = 0;

-- ----------------------------------------------------------------------------
-- 1) One-row cache table for the landing payload
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS landing_data_cache (
  id           int PRIMARY KEY DEFAULT 1,
  payload      json NOT NULL,
  refreshed_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT landing_cache_single_row CHECK (id = 1)
);

-- ----------------------------------------------------------------------------
-- 2) Heavy aggregation moved to a private compute function (unchanged logic)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION compute_landing_data()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
BEGIN
  -- Strip readme_content from the list items: the homepage cards never render
  -- it, but at 10 rows × 5 lists it bloated the payload to multiple MB and made
  -- the response ~7s. `to_jsonb(row) - 'readme_content'` drops the field.
  SELECT json_build_object(
    'stats', (SELECT row_to_json(v) FROM v_stats v LIMIT 1),
    'categories', COALESCE((SELECT json_agg(row_to_json(c)) FROM v_categories c), '[]'::json),
    'trending', COALESCE((SELECT json_agg(to_jsonb(t) - 'readme_content') FROM (SELECT * FROM v_trending LIMIT 10) t), '[]'::json),
    'rising', COALESCE((SELECT json_agg(to_jsonb(r) - 'readme_content') FROM (SELECT * FROM v_rising LIMIT 10) r), '[]'::json),
    'top_rated', COALESCE((SELECT json_agg(to_jsonb(tr) - 'readme_content') FROM (SELECT * FROM v_top_rated LIMIT 10) tr), '[]'::json),
    'hall_of_fame', COALESCE((SELECT json_agg(to_jsonb(hf) - 'readme_content') FROM (SELECT * FROM v_community_classics LIMIT 10) hf), '[]'::json),
    'recently_updated', COALESCE((SELECT json_agg(to_jsonb(ru) - 'readme_content') FROM (SELECT * FROM v_recently_updated LIMIT 10) ru), '[]'::json),
    'languages', COALESCE((SELECT json_agg(row_to_json(l)) FROM v_language_stats l), '[]'::json)
  ) INTO result;
  RETURN result;
END;
$$;

-- ----------------------------------------------------------------------------
-- 3) Refresh function — compute once and store. Lifts statement_timeout so the
--    heavy aggregation can finish; called by sync_runner after each sync.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION refresh_landing_data()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  SET LOCAL statement_timeout = 0;
  INSERT INTO landing_data_cache (id, payload, refreshed_at)
  VALUES (1, compute_landing_data(), now())
  ON CONFLICT (id) DO UPDATE
    SET payload = EXCLUDED.payload,
        refreshed_at = EXCLUDED.refreshed_at;
END;
$$;

-- ----------------------------------------------------------------------------
-- 4) Fast getter — returns the cached payload instantly. Falls back to a live
--    compute only if the cache is somehow empty (first call before any sync).
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_landing_data()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
BEGIN
  SELECT payload INTO result FROM landing_data_cache WHERE id = 1;
  IF result IS NULL THEN
    result := compute_landing_data();
  END IF;
  RETURN result;
END;
$$;

GRANT EXECUTE ON FUNCTION get_landing_data()     TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION compute_landing_data() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION refresh_landing_data() TO anon, authenticated, service_role;
GRANT SELECT ON landing_data_cache               TO anon, authenticated, service_role;

-- Populate the cache immediately so the homepage is fresh right away.
SELECT refresh_landing_data();

-- Make PostgREST pick up the rewritten function signature immediately.
NOTIFY pgrst, 'reload schema';
