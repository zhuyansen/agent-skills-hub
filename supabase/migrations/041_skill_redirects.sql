-- 041: skill_redirects, the old names of renamed or transferred GitHub repositories.
--
-- Why (2026-10-31): GitHub answers an old repository name with a redirect to the
-- repository it became, and every client in this project follows it without noticing.
-- The sync writes rows under the name GitHub returns, so the row under the old name was
-- never matched again: it kept repo_status 'live' and numbers frozen on the day of the
-- rename. 277 of the 4,108 rows with 500+ stars were old names (655 more from 50 to 499
-- stars), e.g. affaan-m/everything-claude-code at 186,550 stars while affaan-m/ECC had
-- 293,000. 243 of the 277 duplicated the row under the new name; 34 were the
-- repository's only row. Their /skill/ pages still ranked: 5,961 impressions in 90 days,
-- against 2,681 for the new names' pages.
--
-- backend/renamed_repos.py finds old names (GraphQL resolves an old name to the
-- repository it became) and keeps one row per repository: it deletes the old row when
-- the new name has one, and renames it in place otherwise. Each old name is recorded
-- here; the build writes a redirect page at its /skill/ URL and the React page follows
-- it, so the old URL's search history passes to the new one instead of becoming a 404.
--
-- SECURITY IMPACT
-- - skill_redirects: RLS on with one policy, public SELECT; anon and authenticated lose
--   every write privilege the schema's default privileges grant them. The build and the
--   React page read it with the anon key; only backend/renamed_repos.py
--   (SUPABASE_DB_URL, as postgres) writes. The rows are public GitHub names.
-- - Nothing else changes: no existing table, policy, function or key is touched.
--
-- Rollback: DROP TABLE public.skill_redirects; (old URLs then stop getting redirect
-- pages at the next build; nothing else reads this table).

CREATE TABLE IF NOT EXISTS public.skill_redirects (
  old_full_name text PRIMARY KEY,           -- owner/repo as the catalog stored it
  new_full_name text NOT NULL,              -- owner/repo GitHub answers with today
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.skill_redirects ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public read skill_redirects" ON public.skill_redirects;
CREATE POLICY "Public read skill_redirects" ON public.skill_redirects FOR SELECT USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.skill_redirects FROM anon, authenticated;
GRANT SELECT ON public.skill_redirects TO anon, authenticated;
