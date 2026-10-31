-- 038_pro_search_phrase_budget.sql
-- PERF FIX (2026-10-31, on top of 037): give each search a time budget, and
-- check quoted phrases on a short, star-ordered list of candidates.
--
-- After 037, phrases made of common words that rarely appear side by side were
-- the last searches that still timed out. GIN keeps no word positions, so
-- every row holding all the words had its README tsvector decompressed (about
-- 13 KB) to check word order. Through the public API: '"skill marketplace"'
-- LIMIT 200 took 7.8 s cold, against the 8 s limit set in 036; '"code review
-- agent"' LIMIT 200 needed about 20 s and failed.
--
-- Two changes, both inside the star tiers of 037:
-- 1. Phrases: the candidates of a tier come from the GIN index with the
--    phrase's words ANDed ('code' <-> 'review' becomes 'code' & 'review'). That
--    form matches every row the phrase matches, and GIN answers it without
--    decompressing anything. The candidates are taken best-starred first, and
--    word order is then checked on c_chunk of them at a time
--    (_pro_search_phrase_tier). A negated phrase ('-"open source"') keeps the
--    037 path, because dropping word order there would drop matches.
-- 2. A budget: no tier, and no further batch of candidates, is started once
--    the search has run for c_budget. It then returns the matches found so
--    far. Tiers and candidates are visited most-starred first, so what comes
--    back is the start of the full list in the same order, only shorter.
--
-- MEASURED on prod (read-only replay of the new path, server time). Every
-- result that 037 could finish matched 037's first rows (tie order aside).
--   '"code review agent"' LIMIT 20: 1.2 s -> 0.45 s (24k -> 14.6k pages)
--   '"code review agent"' LIMIT 200: about 20 s, failed -> 60 rows in 2.6 s
--   '"skill marketplace"' LIMIT 200: 4.2 s -> 191 of 200 rows in 2.5 s
--     (all 200 in 2.7 s when nothing stops it)
--   '"security audit"', '"agent skill"', '"best practices"', '"claude code"',
--   '"open source"', '"model context protocol"' LIMIT 200: all 200 rows,
--     0.1-1.3 s, about as fast as 037.
-- Searches without a phrase already finish well inside the budget; for them
-- the only change is the deadline check before each tier.
-- Live after applying (2026-10-31 10:14 UTC), through the public API with a
-- temporary member key: '"code review agent"' LIMIT 200 in 3.6 s with its
-- first 36 rows, '"skill marketplace"' LIMIT 200 in 3.2 s with all 200.
--
-- Trade-off: a search that runs out of time returns fewer rows than asked
-- for, and how many depends on how warm the cache is. In exchange it answers
-- instead of failing at 8 s. A trial search that answers also counts against
-- the daily caps, whereas one that times out rolls its count back.
--
-- SECURITY: new helper _pro_search_phrase_tier takes no key and applies no
-- caps, so EXECUTE is revoked from PUBLIC, anon and authenticated; it runs only
-- inside _pro_search_tier_ids. CREATE OR REPLACE keeps that function's owner
-- and ACL (revoked in 037). pro_search, pro_search_trial and _pro_search_core
-- are not touched: key check, trial caps, row caps and returned columns are
-- unchanged. No table, index, policy or RLS change.

-- Phrase matches in one star tier, best-starred first. complete is false when
-- the tier was not fully checked (deadline, or more than c_max_candidates).
CREATE OR REPLACE FUNCTION _pro_search_phrase_tier(
  p_tsq          tsquery,
  p_and          tsquery,
  p_category     text,
  p_min_security text,
  p_floor        int,
  p_hi           int,
  p_need         int,
  p_deadline     timestamptz,
  OUT ids        int[],
  OUT complete   boolean
)
LANGUAGE plpgsql
STABLE
SET search_path = public
SET enable_indexscan = off   -- bitmap plans only, as in _pro_search_tier_ids
SET enable_seqscan = off
AS $$
DECLARE
  c_max_candidates CONSTANT int := 5000;  -- per tier
  c_chunk          CONSTANT int := 50;    -- candidates checked between deadline checks
  v_cand int[];
  v_hit  int[];
  v_next int := 1;
BEGIN
  EXECUTE
    'SELECT array_agg(t.id ORDER BY t.stars DESC) FROM (
       SELECT s.id, s.stars FROM skills s
       WHERE s.readme_search_vector @@ $1'
    || CASE WHEN p_category IS NOT NULL THEN ' AND s.category = $2' ELSE '' END
    || CASE WHEN p_min_security IS NOT NULL THEN ' AND s.security_grade = $3' ELSE '' END
    || ' AND s.stars >= $4'
    || CASE WHEN p_hi IS NULL THEN '' ELSE ' AND s.stars < $5' END
    || CASE WHEN p_hi - p_floor = 1 THEN '' ELSE ' ORDER BY s.stars DESC' END
    || ' LIMIT $6) t'
  INTO v_cand
  USING p_and, p_category, p_min_security, p_floor, p_hi, c_max_candidates + 1;
  v_cand := coalesce(v_cand, '{}');
  ids := '{}';

  WHILE v_next <= least(cardinality(v_cand), c_max_candidates) LOOP
    -- ts_match_vq is the function behind @@. Calling it directly keeps the GIN
    -- index out of this lookup, so only these candidates are decompressed.
    SELECT array_agg(u.id ORDER BY u.ord) INTO v_hit
    FROM unnest(v_cand[v_next : v_next + c_chunk - 1]) WITH ORDINALITY AS u(id, ord)
    JOIN skills s ON s.id = u.id
    WHERE ts_match_vq(s.readme_search_vector, p_tsq);
    ids := ids || coalesce(v_hit, '{}');
    v_next := v_next + c_chunk;
    EXIT WHEN cardinality(ids) >= p_need OR clock_timestamp() > p_deadline;
  END LOOP;
  complete := v_next > cardinality(v_cand) AND cardinality(v_cand) <= c_max_candidates;
END;
$$;

REVOKE ALL ON FUNCTION _pro_search_phrase_tier(tsquery, tsquery, text, text, int, int, int, timestamptz)
  FROM PUBLIC, anon, authenticated;

-- Ids of the first p_need matches, most-starred first (037), now within c_budget.
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
  c_floors   CONSTANT int[] := ARRAY[10000, 1000, 100, 10, 3, 2, 1, 0];  -- see 037
  c_budget   CONSTANT interval := '2.5 seconds';  -- per search; see header
  v_deadline timestamptz := clock_timestamp() + c_budget;
  v_filter   text := '';
  v_and      tsquery;
  v_ids      int[] := '{}';
  v_tier     int[];
  v_complete boolean;
  v_floor    int;
  v_hi       int;   -- exclusive upper bound of the current tier; NULL = none
BEGIN
  IF p_category IS NOT NULL THEN
    v_filter := v_filter || ' AND s.category = $2';
  END IF;
  IF p_min_security IS NOT NULL THEN
    v_filter := v_filter || ' AND s.security_grade = $3';
  END IF;
  -- A phrase not under a NOT: its words ANDed match at least the same rows.
  IF p_tsq::text ~ '<[0-9-]+>' AND p_tsq::text !~ '!\s*\(' THEN
    v_and := regexp_replace(p_tsq::text, '<[0-9-]+>', '&', 'g')::tsquery;
  END IF;

  FOREACH v_floor IN ARRAY c_floors LOOP
    IF clock_timestamp() > v_deadline THEN
      RETURN v_ids;  -- out of time: the best-starred matches found so far
    END IF;
    IF v_and IS NULL THEN
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
      v_complete := true;
    ELSE
      SELECT r.ids, r.complete INTO v_tier, v_complete
      FROM _pro_search_phrase_tier(p_tsq, v_and, p_category, p_min_security, v_floor, v_hi,
                                   p_need - cardinality(v_ids), v_deadline) r;
    END IF;
    v_ids := v_ids || coalesce(v_tier, '{}');
    IF cardinality(v_ids) >= p_need THEN
      RETURN v_ids[1 : p_need];
    END IF;
    IF NOT v_complete THEN
      RETURN v_ids;  -- a tier left unfinished: lower tiers would break the order
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

-- Make PostgREST pick up the changes right away.
NOTIFY pgrst, 'reload schema';
