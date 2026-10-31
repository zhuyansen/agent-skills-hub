-- 042_pro_search_incomplete_results.sql
-- FEATURE (2026-10-31): tell callers when a search ran out of 038's time budget.
-- Applied to production on 2026-10-31 as 041; renumbered to 042 because
-- 041_skill_redirects.sql reached main first.
--
-- Since 038, a search that runs out of its 2.5 s budget returns the
-- best-starred matches found so far. The returned columns did not change, so
-- nothing told the caller the list was short: through the public API,
-- '"code review agent"' LIMIT 200 came back with 36 rows, and the page, the
-- CSV/JSON export and API members all read that as the full result. A caller
-- cannot infer it from "fewer rows than the limit" either, since a genuinely
-- short result looks the same.
--
-- Now every row carries incomplete_results, the same value on every row of a
-- call (the name follows the flag in GitHub's search API):
--   false  the search finished: these are all the matches for this page
--   true   the search stopped at its time limit, or at a phrase tier's
--          candidate cap, so this page holds only the best-starred matches it
--          found, in the same order; there may be more
-- A search that stops before it has a single row for the page has no row to
-- carry the flag, and an empty page would read as "no matches". It raises
-- search_incomplete instead (SQLSTATE PT422, HTTP 422 through PostgREST), with
-- a hint on how to narrow the search. A trial call that fails this way is not
-- counted, like any failed call.
--
-- Searches that finish return the same rows in the same order as before, with
-- the flag false. The index walk for common terms (037) always runs to its
-- LIMIT, so it is never incomplete.
--
-- MEASURED on a local Postgres 17 copy (034-040 as on prod, then this migration), with the
-- 15 search cases used for 037 and 038:
--   - as written: every case returned the same rows as before it, flag false,
--     'zotero' LIMIT 200 included (it has only 188 matches)
--   - phrase tiers capped at 20 candidates: every phrase case came back
--     flagged true, each a prefix of the full result; the negated phrase and
--     the plain words stayed false and complete
--   - no time budget at all: every search through the tiers raised PT422,
--     while 'mcp' (index walk) still returned 200 rows, flag false; a trial
--     call that raised was not counted
--   - owner, ACL, SET clauses and SECURITY DEFINER of all four functions were
--     the same before and after; anon still cannot call the helpers
-- Live after applying (2026-10-31 13:05 UTC): owner, grants, SET clauses,
-- SECURITY DEFINER and input signatures unchanged. Through the public API with
-- a temporary member key: '"code review agent"' LIMIT 200 returned 24 rows
-- flagged true in 3.9 s, and HTTP 422 search_incomplete at offset 200;
-- '"skill marketplace"' LIMIT 200 returned 149 rows flagged true; 'rust' and
-- 'mcp' at LIMIT 200 and '"security audit"' in claude-skill at LIMIT 50 came
-- back full, flagged false.
--
-- An output column changes the return type, which CREATE OR REPLACE cannot
-- do, so the four functions on this path are dropped and created again in
-- this one transaction: _pro_search_tier_ids (it now also says whether every
-- tier was searched), _pro_search_core, pro_search and pro_search_trial. Apart
-- from the flag, their bodies are those of 038, 037, 035 and 040.
--
-- SECURITY: DROP + CREATE resets a function's ACL and SET clauses, so both are
-- restated below. The two RPCs keep SECURITY DEFINER, search_path = public and
-- 036's statement_timeout = '8s', and EXECUTE for anon and authenticated
-- (PUBLIC and service_role come back from the schema defaults, as they are
-- today). Both helpers keep EXECUTE revoked from PUBLIC, anon and
-- authenticated. Key check, trial caps, row caps and the other columns are
-- unchanged. No table, index, policy or RLS change.

DROP FUNCTION pro_search(text, text, text, text, int, int);
DROP FUNCTION pro_search_trial(text, text, text, int);
DROP FUNCTION _pro_search_core(text, text, text, int, int);
DROP FUNCTION _pro_search_tier_ids(tsquery, text, text, int);

-- Ids of the first p_need matches, most-starred first, within c_budget (038).
-- complete is false when the search stopped before every tier was searched.
CREATE FUNCTION _pro_search_tier_ids(
  p_tsq          tsquery,
  p_category     text,
  p_min_security text,
  p_need         int,
  OUT ids        int[],
  OUT complete   boolean
)
LANGUAGE plpgsql
STABLE                       -- one snapshot for every tier
SET search_path = public
SET enable_indexscan = off   -- bitmap plans only: never test tsvectors row by row
SET enable_seqscan = off
AS $$
DECLARE
  c_floors   CONSTANT int[] := ARRAY[10000, 1000, 100, 10, 3, 2, 1, 0];  -- see 037
  c_budget   CONSTANT interval := '2.5 seconds';  -- per search; see 038
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
      ids := v_ids;  -- out of time: the best-starred matches found so far
      complete := false;
      RETURN;
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
      ids := v_ids[1 : p_need];
      complete := true;
      RETURN;
    END IF;
    IF NOT v_complete THEN
      ids := v_ids;  -- a tier left unfinished: lower tiers would break the order
      complete := false;
      RETURN;
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
  ids := v_ids || coalesce(v_tier, '{}');
  complete := true;
END;
$$;

REVOKE ALL ON FUNCTION _pro_search_tier_ids(tsquery, text, text, int) FROM PUBLIC, anon, authenticated;

CREATE FUNCTION _pro_search_core(
  p_query        text,
  p_category     text,
  p_min_security text,
  p_limit        int,
  p_offset       int
)
RETURNS TABLE (
  id                 integer,
  repo_full_name     text,
  repo_name          text,
  stars              integer,
  category           text,
  security_grade     text,
  quality_score      double precision,
  repo_url           text,
  description        text,
  incomplete_results boolean
)
LANGUAGE plpgsql
SET search_path = public
AS $$
DECLARE
  c_walk_rows CONSTANT numeric := 1000;  -- rows a walk may expect to test; see 037
  v_tsq        tsquery;
  v_need       int := p_limit + p_offset;
  v_walk       boolean := true;
  v_ids        int[];
  v_incomplete boolean;
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
    -- One query that runs to its LIMIT, so never incomplete.
    RETURN QUERY EXECUTE
      'SELECT s.id, s.repo_full_name::text, s.repo_name::text, s.stars, s.category::text,
              s.security_grade, s.quality_score, s.repo_url::text, s.description, false
       FROM skills s WHERE true'
      || CASE WHEN v_tsq IS NOT NULL THEN ' AND s.readme_search_vector @@ $1' ELSE '' END
      || CASE WHEN p_category IS NOT NULL THEN ' AND s.category = $2' ELSE '' END
      || CASE WHEN p_min_security IS NOT NULL THEN ' AND s.security_grade = $3' ELSE '' END
      || ' ORDER BY s.stars DESC LIMIT $4 OFFSET $5'
    USING v_tsq, p_category, p_min_security, p_limit, p_offset;
    RETURN;
  END IF;

  SELECT t.ids, NOT t.complete INTO v_ids, v_incomplete
  FROM _pro_search_tier_ids(v_tsq, p_category, p_min_security, v_need) t;
  -- Stopped before this page had a single row: an empty page would read as
  -- "no matches", so say what happened instead.
  IF v_incomplete AND cardinality(v_ids) <= p_offset THEN
    RAISE EXCEPTION 'search_incomplete' USING errcode = 'PT422',
      DETAIL = 'The search reached its time limit before it found a match for this page.',
      HINT = 'Pick a category or grade, or remove the quotes, so the search can finish.';
  END IF;
  RETURN QUERY
    SELECT s.id, s.repo_full_name::text, s.repo_name::text, s.stars, s.category::text,
           s.security_grade, s.quality_score, s.repo_url::text, s.description, v_incomplete
    FROM unnest(v_ids[p_offset + 1 : v_need]) WITH ORDINALITY AS r(id, ord)
    JOIN skills s ON s.id = r.id
    ORDER BY r.ord;
END;
$$;

REVOKE ALL ON FUNCTION _pro_search_core(text, text, text, int, int) FROM PUBLIC, anon, authenticated;

-- pro_search: key gate and caps as in 035.
CREATE FUNCTION pro_search(
  p_key          text,
  p_query        text    DEFAULT NULL,
  p_category     text    DEFAULT NULL,
  p_min_security text    DEFAULT NULL,
  p_limit        int     DEFAULT 200,
  p_offset       int     DEFAULT 0
)
RETURNS TABLE (
  id                 integer,
  repo_full_name     text,
  repo_name          text,
  stars              integer,
  category           text,
  security_grade     text,
  quality_score      double precision,
  repo_url           text,
  description        text,
  incomplete_results boolean
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
SET statement_timeout = '8s'   -- from 036
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

GRANT EXECUTE ON FUNCTION pro_search(text, text, text, text, int, int) TO anon, authenticated;

-- pro_search_trial: caps and counting as in 040.
CREATE FUNCTION pro_search_trial(
  p_query        text DEFAULT NULL,
  p_category     text DEFAULT NULL,
  p_min_security text DEFAULT NULL,   -- exact grade: 'safe' | 'caution' | ...
  p_limit        int  DEFAULT 20
)
RETURNS TABLE (
  id                 integer,
  repo_full_name     text,
  repo_name          text,
  stars              integer,
  category           text,
  security_grade     text,
  quality_score      double precision,
  repo_url           text,
  description        text,
  incomplete_results boolean
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
SET statement_timeout = '8s'   -- from 036
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
  v_bucket  text := encode(sha256(convert_to(v_ip || ':' || v_day, 'UTF8')), 'hex');
  v_uses    int;
BEGIN
  -- Over a cap: refuse before searching. A plain read takes no row lock.
  IF EXISTS (SELECT 1 FROM pro_trial_usage u
             WHERE u.bucket = v_bucket AND u.day = v_day AND u.uses >= c_per_ip_daily)
     OR EXISTS (SELECT 1 FROM pro_trial_usage u
                WHERE u.bucket = 'all' AND u.day = v_day AND u.uses >= c_global_daily) THEN
    RAISE EXCEPTION 'trial_exhausted' USING errcode = 'PT429';
  END IF;

  RETURN QUERY SELECT * FROM _pro_search_core(
    p_query, p_category, p_min_security,
    LEAST(GREATEST(p_limit, 1), c_max_rows),
    0);

  -- Count the search only now: these upserts lock their rows until the call
  -- commits, so taking them after the search keeps trial calls from queueing.
  INSERT INTO pro_trial_usage AS u (bucket, day, uses)
  VALUES (v_bucket, v_day, 1)
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
END;
$$;

GRANT EXECUTE ON FUNCTION pro_search_trial(text, text, text, int) TO anon, authenticated;

-- Make PostgREST pick up the new return types right away.
NOTIFY pgrst, 'reload schema';
