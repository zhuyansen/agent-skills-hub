-- 044: radar_homepage_links, a shadow record for the new-term radar (ops/radar/homepage_promos.py): what
-- ten AI video and image sites link to from their own homepages, once a day, one row per link to the
-- site itself (its place on the page, label, and whether it sits in the header, body or footer). Nothing
-- shows it; a review on 11-28 checks whether a big site's homepage slots show the trends the radar finds
-- (memes.py) before their posts do, and whether a slot that lasts marks a trend that earns, before it may
-- replace the comments' "x% want their own" in the mail (2026-10-31).
--
-- Callers: only the radar's 8-hourly source run (.github/workflows/radar-source.yml, radar.py
-- sources_main()), through SUPABASE_DB_URL as postgres, and reads by hand for the review. Nothing in the
-- frontend, the API or the build reads it.
--
-- SECURITY IMPACT
-- - One new table, closed to the API. A table created in public starts with RLS off and every privilege
--   granted to anon and authenticated (the schema's default privileges, see 029), so this file turns RLS
--   on with no policy and revokes those privileges.
-- - postgres (owner; BYPASSRLS) and service_role (BYPASSRLS, keeps its grants) are unaffected.
-- - The rows are public pages (link paths and their labels on ten homepages): nothing personal, but
--   nothing to serve through the anon key either.
-- - Nothing else changes: no existing table, policy, function, grant or key is touched.
--
-- Rollback: DROP TABLE public.radar_homepage_links; NOTIFY pgrst, 'reload schema';

CREATE TABLE IF NOT EXISTS public.radar_homepage_links (
    day         date NOT NULL,                -- the run's day, UTC
    site        text NOT NULL,                -- the site as homepage_promos.SITES names it ("pollo.ai")
    position    integer NOT NULL,             -- where the page first shows the link, 1-based
    link        text NOT NULL,                -- path on the homepage's host, or host + path on another
                                              -- host of its domain; no query or fragment
    label       text NOT NULL DEFAULT '',     -- the link's words (text, image alt or aria-label)
    area        text NOT NULL,                -- header or nav: 'nav'; footer: 'footer'; else 'body'
    recorded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (day, site, link)
);

ALTER TABLE public.radar_homepage_links ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.radar_homepage_links FROM anon, authenticated;

NOTIFY pgrst, 'reload schema';
