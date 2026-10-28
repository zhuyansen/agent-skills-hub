-- 032: radar_keyword_cpc, a shadow record for the new-term radar (ops/radar/cpc_shadow.py): what Google
-- Ads' search volume answer already says about each keyword the radar sizes (cost per click, top-of-page
-- bids, competition), which the radar used to throw away. Nothing shows it; a review 2-4 weeks on checks
-- whether CPC tells which terms turn into sites that earn, before it may replace a signal (2026-10-28).
--
-- Callers: only the radar's daily run (.github/workflows/radar-daily.yml, radar.py keywords()), through
-- SUPABASE_DB_URL as postgres, and reads by hand for the review. Nothing in the frontend, the API or the
-- build reads it.
--
-- SECURITY IMPACT
-- - One new table, closed to the API. A table created in public starts with RLS off and every privilege
--   granted to anon and authenticated (the schema's default privileges, see 029), so this file turns RLS
--   on with no policy and revokes those privileges.
-- - postgres (owner; BYPASSRLS) and service_role (BYPASSRLS, keeps its grants) are unaffected.
-- - The rows are public search terms and Google Ads figures: nothing personal, but nothing to serve
--   through the anon key either.
-- - Nothing else changes: no existing table, policy, function, grant or key is touched.
--
-- Rollback: DROP TABLE public.radar_keyword_cpc; NOTIFY pgrst, 'reload schema';

CREATE TABLE IF NOT EXISTS public.radar_keyword_cpc (
    day               date NOT NULL,                -- the radar run
    phrase            text NOT NULL,                -- the keyword as sized
    location          integer NOT NULL,             -- Google Ads location code (2840: United States)
    kind              text NOT NULL,                -- name or generic
    names             text[] NOT NULL DEFAULT '{}', -- the names a generic term sits behind
    volume            integer,                      -- monthly searches, the latest month
    cpc               real,                         -- average cost per click, USD
    bid_low           real,                         -- low top-of-page bid, USD
    bid_high          real,                         -- high top-of-page bid, USD
    competition       text,                         -- LOW, MEDIUM or HIGH
    competition_index integer,                      -- 0-100
    PRIMARY KEY (day, phrase, location)
);

ALTER TABLE public.radar_keyword_cpc ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.radar_keyword_cpc FROM anon, authenticated;

NOTIFY pgrst, 'reload schema';
