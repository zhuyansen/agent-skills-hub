-- 034_pro_search_trial.sql
-- Server-side free trial for /pro/ (2026-10-31).
--
-- Before: /pro/ shipped a shared member key (VITE_TRIAL_PRO_KEY) in the public
-- bundle and counted the "3 free searches" only in localStorage, while
-- pro_search never counts uses. Anyone who read the bundle could call
-- pro_search with that key without limit (500 rows per call, any offset).
--
-- After: visitors without a key call pro_search_trial, which takes no key,
-- returns at most 20 rows (no offset), and is capped per client IP per day and
-- globally per day. Once this ships, the shared trial key is revoked
-- (ops/issue_member_key.py --revoke), so pro_search is members-only again.
--
-- SECURITY / RLS review (Hard Stop requirement):
-- - New table pro_trial_usage: RLS ENABLE + zero policies (deny-all) + REVOKE
--   from anon/authenticated. Only the SECURITY DEFINER RPC below touches it.
--   It stores sha256(ip || ':' || day) and a counter: no raw IP, no other PII,
--   and the hash changes every day.
-- - New RPC pro_search_trial: SECURITY DEFINER + SET search_path = public.
--   Returns the same 9 public columns as pro_search, at most 20 rows, so it
--   exposes strictly less than pro_search. Over a cap -> SQLSTATE PT429, which
--   PostgREST returns as HTTP 429 with message 'trial_exhausted'. A rejected
--   call rolls back its own counter increments.
-- - Client IP comes from cf-connecting-ip, else the first X-Forwarded-For
--   entry (Supabase docs: request.headers). A caller can spoof X-Forwarded-For
--   if cf-connecting-ip is absent; the global daily cap bounds that case.
-- - pro_search, member_keys and all existing policies are unchanged.

CREATE TABLE IF NOT EXISTS pro_trial_usage (
  bucket text    NOT NULL,            -- sha256(ip || ':' || day), or 'all' for the global count
  day    date    NOT NULL,
  uses   integer NOT NULL DEFAULT 0,
  PRIMARY KEY (bucket, day)
);

ALTER TABLE pro_trial_usage ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON pro_trial_usage FROM anon, authenticated;

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
    LIMIT  LEAST(GREATEST(p_limit, 1), c_max_rows);
END;
$$;

-- No key needed: the caps inside are the gate.
GRANT EXECUTE ON FUNCTION pro_search_trial(text, text, text, int)
  TO anon, authenticated;

-- Make PostgREST pick up the new function right away.
NOTIFY pgrst, 'reload schema';
