-- 040_pro_search_trial_count_after.sql
-- FIX (2026-10-31): stop free-trial searches from queueing behind each other.
--
-- pro_search_trial (034, 035) counted a search before running it: two
-- INSERT ... ON CONFLICT DO UPDATE on pro_trial_usage, one for the caller's
-- (ip, day) row and one for the global ('all', day) row. An upsert locks its
-- row until the call commits, so every trial call held the global row for its
-- whole search, and every other visitor's trial call waited for it. One slow
-- search (up to 2.5 s after 038) stalled all trials, and a burst of visitors
-- queued into the 8 s timeout from 036.
--
-- Now the caps are checked first with a plain read, which takes no lock, so a
-- caller over a cap still gets 429 before any search runs. The search runs,
-- and only then do the two counters go up, so the rows stay locked just from
-- the increment to the commit. A caller that slipped past the check while a
-- concurrent call used the last search is caught by the same check after its
-- increment, and its whole call rolls back as before, results included.
--
-- MEASURED on a local Postgres 17 copy of 034-038, with every search made to
-- take 1 s. Five trial calls from different IPs at once:
--   before: finished after 1.1, 2.1, 3.1, 4.1 and 5.1 s (each waited for the
--           global row), so a ninth caller would hit the 8 s timeout
--   after:  all finished after 1.07 s; twenty at once all within 1.3 s
-- The caps hold under races:
--   - three calls from an IP at 5 of 6: one result, two 429s, count 6
--   - three new IPs with the global count at 999 of 1,000: one result, two
--     429s, count 1,000
--   - a caller already at a cap: 429 in 0.05 s, with no search run
--   - eight calls in a row from one IP: six results, then 429
-- Live after applying (2026-10-31 12:25 UTC): owner, grants, signature,
-- SECURITY DEFINER and both SET clauses (search_path, statement_timeout=8s)
-- unchanged. Simulated as anon for TEST-NET IPs, then rolled back: a fresh
-- IP got 20 rows and was counted once (its count 1, the global count +1); an
-- IP at its cap got the 429 with neither count moving.
--
-- SECURITY: only the body of pro_search_trial changes: same signature,
-- returned columns, caps (6 per IP per day, 1,000 per day overall) and 429
-- error. CREATE OR REPLACE keeps the owner and grants, but replaces the SET
-- clauses, so the 8 s statement_timeout from 036 is restated below. No table,
-- index, policy or RLS change. In a race at a cap, a caller can run one search
-- that is then rejected (it costs at most 038's 2.5 s budget).

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
SET statement_timeout = '8s'   -- from 036; CREATE OR REPLACE would drop it
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

-- Make PostgREST pick up the changes right away.
NOTIFY pgrst, 'reload schema';
