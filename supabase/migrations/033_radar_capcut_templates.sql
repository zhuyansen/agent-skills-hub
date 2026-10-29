-- 033: radar_capcut_templates, a shadow record for the new-term radar (ops/radar/capcut.py): CapCut's
-- Most Used templates as GoAnyAPI snapshots them every hour, one row per template per snapshot (best
-- position, title, use count). Nothing shows it; a review two weeks on checks whether the listing shows
-- the AI video trends the radar finds (memes.py) before their posts do, and trends the radar missed,
-- before it may replace a source of that signal (2026-10-29).
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
-- - The rows are a public listing (template titles, use counts, links): nothing personal, but nothing to
--   serve through the anon key either.
-- - Nothing else changes: no existing table, policy, function, grant or key is touched.
--
-- Rollback: DROP TABLE public.radar_capcut_templates; NOTIFY pgrst, 'reload schema';

CREATE TABLE IF NOT EXISTS public.radar_capcut_templates (
    day            date NOT NULL,                -- the snapshot's day, Asia/Shanghai
    hour           smallint NOT NULL,            -- the snapshot's hour, Asia/Shanghai (0-23)
    template_id    text NOT NULL,                -- CapCut's id, kept as text
    position       integer NOT NULL,             -- best place in the snapshot, 1-based (cards repeat)
    title          text NOT NULL DEFAULT '',
    slug           text NOT NULL DEFAULT '',
    use_count_text text NOT NULL DEFAULT '',     -- as CapCut shows it ("2.2M")
    use_count      bigint,                       -- GoAnyAPI's estimate of it
    template_url   text NOT NULL DEFAULT '',
    recorded_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (day, hour, template_id)
);

ALTER TABLE public.radar_capcut_templates ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.radar_capcut_templates FROM anon, authenticated;

NOTIFY pgrst, 'reload schema';
