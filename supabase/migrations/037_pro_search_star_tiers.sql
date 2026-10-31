-- 037_pro_search_star_tiers.sql
-- PERF FIX (2026-10-31, on top of 035 and 036): stop README searches from
-- reading one heap page per match.
--
-- 035 sends a query down one of two paths, chosen by the planner's match
-- estimate (>= 2,000 rows):
--   walk:   ORDER BY stars DESC over ix_skills_stars, testing each row's README
--           tsvector (avg 13 KB compressed, about 6.5 pages per row) until LIMIT;
--   bitmap: every GIN match, then a top-N sort (one heap page per match).
-- Both go wrong for terms the estimate misjudges. Measured on prod after 035
-- (pages touched = shared hit + read, LIMIT 200):
--   bitmap: 'rust' 9,993 (10,003 matches, estimated 1,278), 'trading' 7,258,
--           'telegram' 5,695, 'legal' 5,659: 3-6 s cold through the API.
--   walk:   'resume' 10,500, 'prompt injection' 10,169, 'browser automation' 5,824.
--   quoted phrases, which GIN cannot check, so every candidate is decompressed:
--           '"security audit"' 5.3 s, '"best practices"' 11.1 s,
--           '"skill marketplace"' 18.7 s, '"code review agent"' over 20 s.
--
-- The catalog is a long tail: 53% of rows have 0 stars, about 1% have 1,000 or
-- more. So the top of a result list comes from a small slice of the table.
-- _pro_search_tier_ids asks for matches tier by tier, most-starred first:
--   [10000, inf) [1000, 10000) [100, 1000) [10, 100) [3, 10), then 2, 1 and 0
-- and stops once the page is full. With index walks and seq scans switched off
-- for its own queries, each tier is a GIN + ix_skills_stars BitmapAnd (or, for
-- the one-value tiers, a GIN bitmap that stops at the limit): it reads only the
-- rows that match inside the tier and never walks a tier row by row.
-- Same rows and order as before: every tier holds strictly more stars than the
-- next, rows inside a tier are sorted by stars DESC (ties, as before, in no
-- particular order), and NULL stars, if any ever appear, come last.
--
-- The walk stays for queries it is good at: no phrase, and the estimate says
-- the walk should find the page within c_walk_rows rows (LIMIT x table rows /
-- estimated matches). At 255k rows that is an estimate of about 1.3k at LIMIT 5,
-- 5.1k at LIMIT 20 and 51k at LIMIT 200 ('mcp', 'agent', 'skill', 'server').
--
-- MEASURED on prod after VACUUM (ANALYZE), 037 applied inside a transaction
-- that was rolled back; same rows as 035 in every case (tie order aside).
-- Pages touched (shared hit + read), server time:
--   'rust' L200 9,110 -> 1,174 (L20: 9,110 -> 181); 'trading' 6,786 -> 1,556;
--   'telegram' 5,254 -> 1,099; 'rust' + mcp-server 4,857 -> 1,369.
--   Walked by 035, now tiers: 'prompt injection' L200 10,169 -> 1,309
--   (0.81 s -> 0.07 s), 'resume' 10,500 -> 1,196, 'browser automation'
--   5,824 -> 1,460 (0.65 s -> 0.07 s).
--   Phrases, L200: '"best practices"' 54,454 -> 3,810 (7.7 s -> 0.09 s; at L20
--   035 timed out at 12 s, 037 0.02 s), '"security audit"' 41,384 -> 12,254
--   (6.4 s -> 1.4 s), '"skill marketplace"' over 12 s -> 4.2 s (29,092 pages).
--   'mcp', 'agent', 'workflow' and the other walks: unchanged.
--   Costs: rare terms scan a small GIN posting list once per tier ('homework'
--   L200 389 -> 1,251 pages, 0.14 s); phrases common among top repos lose the
--   walk ('"agent skill"' L200 0.02 s -> 0.42 s).
--   Still slow: '"code review agent"' (three common words, rarely adjacent):
--   1.0 s -> 1.2 s at L20 and about 20 s at L200 either way. GIN keeps no word
--   positions, so every candidate is decompressed to check word order.
-- Checked on a local Postgres 17 copy of 034-036 with synthetic long-tail data:
-- 26 queries (filters, offsets, phrases, stop words, LIMIT 500) return the same
-- rows in the same order as the original ORDER BY stars DESC NULLS LAST query.
--
-- SECURITY: new helper _pro_search_tier_ids takes no key and applies no caps,
-- so EXECUTE is revoked from PUBLIC, anon and authenticated, like the 035
-- helpers; it runs only inside _pro_search_core. CREATE OR REPLACE keeps
-- _pro_search_core's owner and ACL. The key check, trial caps, row caps and
-- returned columns are unchanged. No table, index, policy or RLS change.

-- Ids of the first p_need matches, most-starred first.
CREATE OR REPLACE FUNCTION _pro_search_tier_ids(
  p_tsq          tsquery,
  p_category     text,
  p_min_security text,
  p_need         int
)
RETURNS int[]
LANGUAGE plpgsql
STABLE                       -- one snapshot for every tier
SET search_path = public
SET enable_indexscan = off   -- bitmap plans only: never test tsvectors row by row
SET enable_seqscan = off
AS $$
DECLARE
  c_floors CONSTANT int[] := ARRAY[10000, 1000, 100, 10, 3, 2, 1, 0];  -- see header
  v_filter text := '';
  v_ids    int[] := '{}';
  v_tier   int[];
  v_floor  int;
  v_hi     int;   -- exclusive upper bound of the current tier; NULL = none
BEGIN
  IF p_category IS NOT NULL THEN
    v_filter := v_filter || ' AND s.category = $2';
  END IF;
  IF p_min_security IS NOT NULL THEN
    v_filter := v_filter || ' AND s.security_grade = $3';
  END IF;

  FOREACH v_floor IN ARRAY c_floors LOOP
    EXECUTE
      'SELECT array_agg(t.id ORDER BY t.stars DESC) FROM (
         SELECT s.id, s.stars FROM skills s
         WHERE s.readme_search_vector @@ $1' || v_filter || ' AND s.stars >= $4'
      || CASE WHEN v_hi IS NULL THEN '' ELSE ' AND s.stars < $5' END
      -- a one-value tier needs no sort, so its scan stops at the limit
      || CASE WHEN v_hi - v_floor = 1 THEN '' ELSE ' ORDER BY s.stars DESC' END
      || ' LIMIT $6) t'
    INTO v_tier
    USING p_tsq, p_category, p_min_security, v_floor, v_hi, p_need - cardinality(v_ids);
    v_ids := v_ids || coalesce(v_tier, '{}');
    IF cardinality(v_ids) >= p_need THEN
      RETURN v_ids;
    END IF;
    v_hi := v_floor;
  END LOOP;

  -- The old ORDER BY put NULL stars last; there are none today.
  EXECUTE
    'SELECT array_agg(t.id) FROM (
       SELECT s.id FROM skills s
       WHERE s.readme_search_vector @@ $1' || v_filter || ' AND s.stars IS NULL LIMIT $4) t'
  INTO v_tier
  USING p_tsq, p_category, p_min_security, p_need - cardinality(v_ids);
  RETURN v_ids || coalesce(v_tier, '{}');
END;
$$;

REVOKE ALL ON FUNCTION _pro_search_tier_ids(tsquery, text, text, int) FROM PUBLIC, anon, authenticated;

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
  c_walk_rows CONSTANT numeric := 1000;  -- rows a walk may expect to test; see header
  v_tsq  tsquery;
  v_need int := p_limit + p_offset;
  v_walk boolean := true;
  v_ids  int[];
BEGIN
  IF coalesce(p_query, '') <> '' THEN
    v_tsq := websearch_to_tsquery('english', p_query);
    IF numnode(v_tsq) = 0 THEN
      RETURN;  -- only stop words: nothing can match
    END IF;
    -- A quoted phrase ("<->", "<2>") is checked row by row, so it never walks.
    v_walk := v_tsq::text !~ '<[0-9-]+>'
      AND v_need * (SELECT c.reltuples FROM pg_class c WHERE c.oid = 'skills'::regclass)
          <= c_walk_rows * _pro_search_match_estimate(v_tsq);
  END IF;

  IF v_walk THEN
    RETURN QUERY EXECUTE
      'SELECT s.id, s.repo_full_name::text, s.repo_name::text, s.stars, s.category::text,
              s.security_grade, s.quality_score, s.repo_url::text, s.description
       FROM skills s WHERE true'
      || CASE WHEN v_tsq IS NOT NULL THEN ' AND s.readme_search_vector @@ $1' ELSE '' END
      || CASE WHEN p_category IS NOT NULL THEN ' AND s.category = $2' ELSE '' END
      || CASE WHEN p_min_security IS NOT NULL THEN ' AND s.security_grade = $3' ELSE '' END
      || ' ORDER BY s.stars DESC LIMIT $4 OFFSET $5'
    USING v_tsq, p_category, p_min_security, p_limit, p_offset;
    RETURN;
  END IF;

  v_ids := _pro_search_tier_ids(v_tsq, p_category, p_min_security, v_need);
  RETURN QUERY
    SELECT s.id, s.repo_full_name::text, s.repo_name::text, s.stars, s.category::text,
           s.security_grade, s.quality_score, s.repo_url::text, s.description
    FROM unnest(v_ids[p_offset + 1 : v_need]) WITH ORDINALITY AS r(id, ord)
    JOIN skills s ON s.id = r.id
    ORDER BY r.ord;
END;
$$;

REVOKE ALL ON FUNCTION _pro_search_core(text, text, text, int, int) FROM PUBLIC, anon, authenticated;

-- Make PostgREST pick up the changes right away.
NOTIFY pgrst, 'reload schema';
