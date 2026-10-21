-- 027: each radar lead keeps the evidence it was reported on.
--
-- Why (2026-10-21): radar_leads kept a lead's report lines (notes) and nothing more, so once
-- the mail was sent the posts that named a term, an AI video trend's description and dates,
-- the keyword table's reading of a name and the posts linking a new site were gone. Another
-- project reads them to draft a page for a lead. ops/radar/review.py record() now writes
-- them to `evidence` (JSONB; the shape is documented in review.py) and merges a lead's new
-- evidence into the old: posts are unioned by URL (the 10 most-liked kept), every other key
-- takes the newest value. Until this column exists the radar writes leads without it.
--
-- SECURITY IMPACT
-- - One nullable column on an existing table. RLS stays on with no policy: anon and
--   authenticated roles still cannot read or write radar_leads. The radar connects with
--   SUPABASE_DB_URL (table owner), which bypasses RLS.
-- - The column holds public posts (text, links, author handles) and the radar's own
--   readings. No change to policies, grants or keys.
--
-- Rollback: ALTER TABLE public.radar_leads DROP COLUMN IF EXISTS evidence;

ALTER TABLE public.radar_leads ADD COLUMN IF NOT EXISTS evidence JSONB;
