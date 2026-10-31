-- 043_site_search_shadow_log.sql
-- Shadow record of on-site searches (2026-10-31).
--
-- Why: the database held no visitor behaviour. GA keeps only searches that
-- reach a ?search= URL, and nothing recorded which searches return nothing,
-- the plainest sign of what the catalog lacks. This adds a write-only log of
-- typed searches and their result counts. Shadow mode: nothing on the site
-- reads it, and it is not shown or mailed anywhere until the review on
-- 2026-11-28 decides whether it earns a place.
--
-- The frontend (frontend/src/lib/searchLog.ts) sends one call per settled
-- term that a visitor typed on agentskillshub.top: the term, how many results
-- it returned, and which box it came from ('list' = the Explore list,
-- 'suggest' = a search box dropdown). Searches loaded from a URL, filtered
-- list searches and automated browsers are not sent.
--
-- SECURITY / RLS review (Hard Stop requirement):
-- - New tables site_searches and site_search_quota: RLS ENABLE + zero policies
--   (deny-all) + REVOKE from anon/authenticated, the identity sequence too.
--   Only the SECURITY DEFINER RPC below writes them; the API has no read path.
-- - site_searches stores the term, a result count, the box and a timestamp:
--   no IP, user agent, account or session id. The client drops email-shaped
--   terms; both sides drop terms over 100 characters.
-- - site_search_quota keeps sha256(ip || ':' || day) counters, as
--   pro_trial_usage does (034). The first counted call of each day deletes
--   earlier days' rows, so no hash outlives its day.
-- - New RPC log_site_search: SECURITY DEFINER + fixed search_path. It inserts
--   at most one bounded row and returns nothing. Calls whose Origin is not the
--   production site are ignored, and so are calls past 60 per IP per day or
--   2,000 in total per day. Client IP comes from cf-connecting-ip, else the
--   first X-Forwarded-For entry. Anyone can forge Origin and X-Forwarded-For,
--   so a spammer can still add up to 2,000 junk rows a day and crowd out that
--   day's real ones: shadow data only, and the review must check for bursts.
-- - EXECUTE is revoked from PUBLIC and granted to anon and authenticated.
-- - No existing table, policy or function changes.
--
-- Rollback:
--   DROP FUNCTION IF EXISTS log_site_search(text, int, text);
--   DROP TABLE IF EXISTS site_searches, site_search_quota;
--   and remove the trackSearch calls in frontend/src/api/client.ts.

CREATE TABLE IF NOT EXISTS site_searches (
  id         bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  term       text        NOT NULL,
  results    integer     NOT NULL,
  surface    text        NOT NULL CHECK (surface IN ('list', 'suggest')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS site_search_quota (
  bucket text    NOT NULL,            -- sha256(ip || ':' || day), or 'all' for the global count
  day    date    NOT NULL,
  uses   integer NOT NULL DEFAULT 0,
  PRIMARY KEY (bucket, day)
);

ALTER TABLE site_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE site_search_quota ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON site_searches, site_search_quota FROM anon, authenticated;
REVOKE ALL ON SEQUENCE site_searches_id_seq FROM anon, authenticated;

CREATE OR REPLACE FUNCTION log_site_search(
  p_term    text,
  p_results int,
  p_surface text
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  c_per_ip_daily CONSTANT int := 60;       -- far above one visitor's day of searching
  c_global_daily CONSTANT int := 2000;     -- backstop for rotated or spoofed IPs
  c_max_term     CONSTANT int := 100;      -- same limit as frontend/src/lib/searchLog.ts
  c_max_results  CONSTANT int := 1000000;  -- above the whole catalog
  v_headers json := coalesce(nullif(current_setting('request.headers', true), ''), '{}')::json;
  v_origin  text := lower(coalesce(v_headers->>'origin', ''));
  v_ip      text := coalesce(
    nullif(v_headers->>'cf-connecting-ip', ''),
    nullif(trim(split_part(v_headers->>'x-forwarded-for', ',', 1)), ''),
    'unknown');
  v_day     date := (now() AT TIME ZONE 'utc')::date;
  v_term    text := lower(regexp_replace(btrim(coalesce(p_term, '')), '\s+', ' ', 'g'));
  v_uses    int;
BEGIN
  IF v_origin NOT IN ('https://agentskillshub.top', 'https://www.agentskillshub.top')
     OR v_term = '' OR length(v_term) > c_max_term
     OR p_surface IS NULL OR p_surface NOT IN ('list', 'suggest') THEN
    RETURN;
  END IF;

  -- Per IP first, so one address past its cap cannot use up the global count.
  INSERT INTO site_search_quota AS q (bucket, day, uses)
  VALUES (encode(sha256(convert_to(v_ip || ':' || v_day, 'UTF8')), 'hex'), v_day, 1)
  ON CONFLICT (bucket, day) DO UPDATE SET uses = q.uses + 1
  RETURNING q.uses INTO v_uses;
  IF v_uses > c_per_ip_daily THEN
    RETURN;
  END IF;

  INSERT INTO site_search_quota AS q (bucket, day, uses)
  VALUES ('all', v_day, 1)
  ON CONFLICT (bucket, day) DO UPDATE SET uses = q.uses + 1
  RETURNING q.uses INTO v_uses;
  IF v_uses = 1 THEN
    DELETE FROM site_search_quota WHERE day < v_day;  -- earlier days' hashes go
  END IF;
  IF v_uses > c_global_daily THEN
    RETURN;
  END IF;

  INSERT INTO site_searches (term, results, surface)
  VALUES (v_term, LEAST(GREATEST(coalesce(p_results, 0), 0), c_max_results), p_surface);
END;
$$;

REVOKE ALL ON FUNCTION log_site_search(text, int, text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION log_site_search(text, int, text) TO anon, authenticated;

-- Make PostgREST pick up the new function right away.
NOTIFY pgrst, 'reload schema';
