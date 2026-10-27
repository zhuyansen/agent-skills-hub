-- 031: index_pages and index_checks, for the index watch (ops/index/index_watch.py): which of our
-- pages Google has indexed, and how many days that took after a page first showed up in our
-- sitemaps. One row per page in index_pages, one row per URL Inspection in index_checks.
--
-- Callers: only that job (.github/workflows/index-watch.yml), daily, through SUPABASE_DB_URL as
-- postgres, and `index_watch.py report` by hand. Nothing in the frontend, the API or the build
-- reads them.
--
-- SECURITY IMPACT
-- - Two new tables, closed to the API. A table created in public starts with RLS off and every
--   privilege granted to anon and authenticated (the schema's default privileges, see 029), so
--   this file turns RLS on with no policy and revokes those privileges, on both tables and on
--   index_checks' id sequence.
-- - postgres (owner; BYPASSRLS) and service_role (BYPASSRLS, keeps its grants) are unaffected.
-- - The rows are our own public URLs and what Search Console says about them: nothing personal,
--   but nothing to serve through the anon key either.
-- - Nothing else changes: no existing table, policy, function, grant or key is touched.
--
-- Rollback: DROP TABLE public.index_checks, public.index_pages; NOTIFY pgrst, 'reload schema';

CREATE TABLE IF NOT EXISTS public.index_pages (
    url           text PRIMARY KEY,
    site          text NOT NULL,                -- the Search Console property, sc-domain:...
    kind          text NOT NULL,                -- first path segment after a locale: skill, best, blog, prompts ...
    first_seen    date,                         -- first day our sitemaps listed it; NULL: listed before the watch began
    lastmod       date,                         -- the sitemap's lastmod at the last read
    in_sitemap    boolean NOT NULL DEFAULT true,
    search_seen   date,                         -- last day a 28-day Search Analytics read had impressions for it
    last_checked  date,                         -- day of the last URL Inspection
    last_state    text,                         -- its coverageState
    first_indexed date                          -- first day an inspection or an impression showed it indexed
);
CREATE INDEX IF NOT EXISTS index_pages_site_idx ON public.index_pages (site);

CREATE TABLE IF NOT EXISTS public.index_checks (
    id               bigserial PRIMARY KEY,
    url              text NOT NULL REFERENCES public.index_pages (url) ON DELETE CASCADE,
    checked_at       timestamptz NOT NULL DEFAULT now(),
    verdict          text,
    coverage_state   text,
    indexing_state   text,
    page_fetch_state text,
    robots_state     text,
    last_crawl       timestamptz,
    google_canonical text,
    user_canonical   text,
    sitemaps         text[]
);
CREATE INDEX IF NOT EXISTS index_checks_url_idx ON public.index_checks (url, checked_at DESC);

ALTER TABLE public.index_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.index_checks ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.index_pages, public.index_checks FROM anon, authenticated;
REVOKE ALL ON SEQUENCE public.index_checks_id_seq FROM anon, authenticated;

NOTIFY pgrst, 'reload schema';
