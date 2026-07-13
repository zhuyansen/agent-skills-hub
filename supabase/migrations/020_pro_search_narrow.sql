-- 020_pro_search_narrow.sql
-- PERF FIX (2026-07-13): pro_search was `RETURNS SETOF skills` + `SELECT s.*`,
-- so PostgREST serialized readme_content (TOAST big text) AND readme_search_vector
-- (a tsvector that's tens of KB for a full README) for every returned row.
-- Measured: ~52KB/row → 10.4MB payload, 6.7s TTFB (all detoast + serialize).
-- The underlying FTS query is 15ms (GIN bitmap + top-N heapsort). All the cost
-- was fat columns the /pro/ UI never reads.
--
-- Fix: return only the 9 columns the results table + CSV export actually use.
-- Expected ~100x faster (~50ms, ~150KB). Changing the return type needs a DROP
-- first — CREATE OR REPLACE can't alter a function's return type.
--
-- SECURITY: no policy change. Narrower output = strictly LESS data exposure.
-- Key-gate (sha256 member_keys check) and the 500-row hard cap are unchanged.

DROP FUNCTION IF EXISTS pro_search(text, text, text, text, int, int);

CREATE FUNCTION pro_search(
  p_key          text,
  p_query        text    DEFAULT NULL,
  p_category     text    DEFAULT NULL,
  p_min_security text    DEFAULT NULL,   -- exact grade: 'safe' | 'caution' | ...
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

  RETURN QUERY
    SELECT s.id,
           s.repo_full_name::text,
           s.repo_name::text,
           s.stars,
           s.category::text,
           s.security_grade,
           s.quality_score,
           s.repo_url::text,
           s.description
    FROM skills s
    WHERE (p_query IS NULL OR p_query = ''
           OR s.readme_search_vector @@ websearch_to_tsquery('english', p_query))
      AND (p_category IS NULL OR s.category = p_category)
      AND (p_min_security IS NULL OR s.security_grade = p_min_security)
    ORDER BY s.stars DESC NULLS LAST
    LIMIT  LEAST(GREATEST(p_limit, 1), 500)   -- hard cap 500 even for Pro
    OFFSET GREATEST(p_offset, 0);
END;
$$;

GRANT EXECUTE ON FUNCTION pro_search(text, text, text, text, int, int)
  TO anon, authenticated;
