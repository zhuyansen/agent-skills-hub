-- 035_pro_search_fast_order.sql
-- PERF FIX (2026-10-31): broad README queries timed out (anon statement_timeout = 3s).
--
-- pro_search and pro_search_trial both ran
--   WHERE readme_search_vector @@ q ORDER BY stars DESC NULLS LAST LIMIT n
-- ix_skills_stars is btree(stars) ascending, so a backward scan yields
-- DESC NULLS FIRST and cannot serve NULLS LAST. Every query was therefore a GIN
-- bitmap scan over all matching rows plus a top-N sort, which for a common term
-- reads most of the 374 MB heap. Measured on prod, cold: 'mcp' (99,957 matches)
-- 9.9 s at LIMIT 20 and 13.6 s at LIMIT 200; 'workflow' 7.5 s; 'llm' 3.6 s.
-- An empty query (category/grade filters only) sorted all 255k rows the same way.
--
-- Walking ix_skills_stars backward and stopping at LIMIT is fast for common terms
-- (mcp 1-5 ms, llm 44-440 ms) but slow for terms that are rare among top-starred
-- repos (solana 866 ms, zotero 461 ms at LIMIT 20), where the bitmap path takes
-- under 10 ms. So the shared core below picks the path from the planner's own
-- match estimate:
--   no query, or estimate >= 2,000 rows -> ORDER BY stars DESC (index walk allowed;
--                                          the planner still may choose a bitmap)
--   otherwise                            -> ORDER BY stars DESC NULLS LAST (no index
--                                          can serve it, so bitmap + top-N sort)
-- The threshold is low on purpose: the planner underestimates multi-word queries
-- ('prompt injection' 4,910 estimated), and terms outside the tsvector statistics
-- get the default 1,278, which is exactly the rare case the bitmap path handles.
-- stars has no NULLs (0 of 255,520 rows), so both orders return the same rows.
--
-- Two composite indexes give filtered searches a star-ordered path inside one
-- category or grade. Without them, 'mcp' + claude-skill + safe took 8 s and an
-- empty query with grade = reject took 2.2 s.
--
-- Dry run on prod inside a rolled-back transaction, 47 terms at LIMIT 20 and 200
-- plus 15 filter combinations: slowest call 0.99 s including ~0.23 s network
-- round trip; top results identical to the old query.
-- The query runs through EXECUTE ... USING, so every call is planned with the
-- actual values (no generic plan that cannot see the search term).
-- A query made only of stop words returns no rows right away, as before, without
-- walking the table.
--
-- SECURITY: the two new helpers take no key and apply no caps, so EXECUTE is
-- revoked from PUBLIC, anon and authenticated; they run only inside pro_search and
-- pro_search_trial (both SECURITY DEFINER). The key check, trial caps, row caps
-- and returned columns are unchanged. Two new btree indexes on skills; no table,
-- policy or RLS change.

-- Star order inside one category or one grade, so filtered searches can walk just
-- those rows by stars. Small btrees; plain CREATE INDEX blocks writes to skills for
-- the few seconds each build takes (reads are not blocked).
CREATE INDEX IF NOT EXISTS ix_skills_category_stars ON skills (category, stars);
CREATE INDEX IF NOT EXISTS ix_skills_grade_stars ON skills (security_grade, stars);

CREATE OR REPLACE FUNCTION _pro_search_match_estimate(p_tsq tsquery)
RETURNS numeric
LANGUAGE plpgsql
VOLATILE   -- Postgres refuses EXPLAIN inside a STABLE/IMMUTABLE function
SET search_path = public
AS $$
DECLARE
  v_plan json;
BEGIN
  EXECUTE format(
    'EXPLAIN (FORMAT JSON) SELECT 1 FROM skills s WHERE s.readme_search_vector @@ %L::tsquery',
    p_tsq::text)
  INTO v_plan;
  RETURN (v_plan -> 0 -> 'Plan' ->> 'Plan Rows')::numeric;
END;
$$;

REVOKE ALL ON FUNCTION _pro_search_match_estimate(tsquery) FROM PUBLIC, anon, authenticated;

CREATE OR REPLACE FUNCTION _pro_search_core(
  p_query        text,
  p_category     text,
  p_min_security text,
  p_limit        int,
  p_offset       int
)
RETURNS TABLE (
  id             integer,
  repo_full_name text,
  repo_name      text,
  stars          integer,
  category       text,
  security_grade text,
  quality_score  double precision,
  repo_url       text,
  description    text
)
LANGUAGE plpgsql
SET search_path = public
AS $$
DECLARE
  c_index_walk_min CONSTANT numeric := 2000;  -- estimated matches; see header
  v_tsq  tsquery;
  v_walk boolean := true;
BEGIN
  IF coalesce(p_query, '') <> '' THEN
    v_tsq := websearch_to_tsquery('english', p_query);
    IF numnode(v_tsq) = 0 THEN
      RETURN;  -- only stop words: nothing can match
    END IF;
    v_walk := _pro_search_match_estimate(v_tsq) >= c_index_walk_min;
  END IF;

  RETURN QUERY EXECUTE
    'SELECT s.id, s.repo_full_name::text, s.repo_name::text, s.stars, s.category::text,
            s.security_grade, s.quality_score, s.repo_url::text, s.description
     FROM skills s WHERE true'
    || CASE WHEN v_tsq IS NOT NULL THEN ' AND s.readme_search_vector @@ $1' ELSE '' END
    || CASE WHEN p_category IS NOT NULL THEN ' AND s.category = $2' ELSE '' END
    || CASE WHEN p_min_security IS NOT NULL THEN ' AND s.security_grade = $3' ELSE '' END
    || CASE WHEN v_walk THEN ' ORDER BY s.stars DESC' ELSE ' ORDER BY s.stars DESC NULLS LAST' END
    || ' LIMIT $4 OFFSET $5'
  USING v_tsq, p_category, p_min_security, p_limit, p_offset;
END;
$$;

REVOKE ALL ON FUNCTION _pro_search_core(text, text, text, int, int) FROM PUBLIC, anon, authenticated;

-- pro_search: same signature, key gate and caps as 020; the query moves to the core.
CREATE OR REPLACE FUNCTION pro_search(
  p_key          text,
  p_query        text    DEFAULT NULL,
  p_category     text    DEFAULT NULL,
  p_min_security text    DEFAULT NULL,
  p_limit        int     DEFAULT 200,
  p_offset       int     DEFAULT 0
)
RETURNS TABLE (
  id             integer,
  repo_full_name text,
  repo_name      text,
  stars          integer,
  category       text,
  security_grade text,
  quality_score  double precision,
  repo_url       text,
  description    text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM member_keys
    WHERE key_hash = encode(sha256(p_key::bytea), 'hex')
      AND revoked = false
      AND (expires_at IS NULL OR expires_at > now())
  ) THEN
    RAISE EXCEPTION 'invalid_or_expired_key' USING errcode = '42501';
  END IF;

  RETURN QUERY SELECT * FROM _pro_search_core(
    p_query, p_category, p_min_security,
    LEAST(GREATEST(p_limit, 1), 500),   -- hard cap 500 even for Pro
    GREATEST(p_offset, 0));
END;
$$;

-- pro_search_trial: same caps as 034; the query moves to the core.
CREATE OR REPLACE FUNCTION pro_search_trial(
  p_query        text DEFAULT NULL,
  p_category     text DEFAULT NULL,
  p_min_security text DEFAULT NULL,   -- exact grade: 'safe' | 'caution' | ...
  p_limit        int  DEFAULT 20
)
RETURNS TABLE (
  id             integer,
  repo_full_name text,
  repo_name      text,
  stars          integer,
  category       text,
  security_grade text,
  quality_score  double precision,
  repo_url       text,
  description    text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  c_per_ip_daily CONSTANT int := 6;     -- 3 trial searches + 3 share bonus on /pro/
  c_global_daily CONSTANT int := 1000;  -- backstop for rotated or spoofed IPs
  c_max_rows     CONSTANT int := 20;    -- free-tier page size; Pro gets 200
  v_headers json := coalesce(current_setting('request.headers', true), '{}')::json;
  v_ip      text := coalesce(
    nullif(v_headers->>'cf-connecting-ip', ''),
    nullif(trim(split_part(v_headers->>'x-forwarded-for', ',', 1)), ''),
    'unknown');
  v_day     date := (now() AT TIME ZONE 'utc')::date;
  v_uses    int;
BEGIN
  INSERT INTO pro_trial_usage AS u (bucket, day, uses)
  VALUES (encode(sha256(convert_to(v_ip || ':' || v_day, 'UTF8')), 'hex'), v_day, 1)
  ON CONFLICT (bucket, day) DO UPDATE SET uses = u.uses + 1
  RETURNING u.uses INTO v_uses;
  IF v_uses > c_per_ip_daily THEN
    RAISE EXCEPTION 'trial_exhausted' USING errcode = 'PT429';
  END IF;

  INSERT INTO pro_trial_usage AS u (bucket, day, uses)
  VALUES ('all', v_day, 1)
  ON CONFLICT (bucket, day) DO UPDATE SET uses = u.uses + 1
  RETURNING u.uses INTO v_uses;
  IF v_uses > c_global_daily THEN
    RAISE EXCEPTION 'trial_exhausted' USING errcode = 'PT429';
  END IF;

  RETURN QUERY SELECT * FROM _pro_search_core(
    p_query, p_category, p_min_security,
    LEAST(GREATEST(p_limit, 1), c_max_rows),
    0);
END;
$$;

-- Make PostgREST pick up the changes right away.
NOTIFY pgrst, 'reload schema';
