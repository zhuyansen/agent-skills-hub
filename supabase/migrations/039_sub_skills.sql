-- 039: sub_skills, one row per SKILL.md inside a repository that holds several skills.
-- Applied to production on 2026-10-31 (written as 037; renumbered because
-- 037_pro_search_star_tiers.sql and 038_pro_search_phrase_budget.sql took those numbers first).
--
-- Why (2026-10-31): the catalog is one row per repository, so a skill that lives in a
-- folder of a larger repository (mnapoli/skills holds unslop, implement, interview...)
-- has no page of its own and cannot rank for its own name. Competing directories rank on
-- exactly those names. backend/sub_skills_collect.py lists each repository's SKILL.md
-- files through the GitHub trees API, reads each file's frontmatter, grades the text with
-- the same scanner as READMEs, and writes the rows here; the build turns them into
-- /skill/<owner>/<repo>/<slug>/ pages.
--
-- sub_skill_scans records when each repository was last listed and how many SKILL.md
-- files it had, so a run skips repositories that have not changed since.
--
-- SECURITY IMPACT
-- - sub_skills: RLS on with one policy, public SELECT; anon and authenticated lose every
--   write privilege the schema's default privileges grant them. The build and the React
--   page read it with the anon key; only the collector (SUPABASE_DB_URL, as postgres)
--   writes. The rows are public GitHub content.
-- - sub_skill_scans: RLS on with no policy and no grants to anon or authenticated, so the
--   API can neither read nor write it. Only the collector uses it.
-- - Nothing else changes: no existing table, policy, function or key is touched.
--
-- Rollback: DROP TABLE public.sub_skills, public.sub_skill_scans; (the pages then stop
-- generating at the next build; nothing else reads these tables).

CREATE TABLE IF NOT EXISTS public.sub_skills (
  id bigserial PRIMARY KEY,
  repo_full_name text NOT NULL,          -- parent repository, as in skills.repo_full_name
  path text NOT NULL,                    -- folder holding the SKILL.md, '' for the root
  slug text NOT NULL,                    -- URL segment under /skill/<owner>/<repo>/
  name text NOT NULL,                    -- frontmatter name, else the folder name
  description text NOT NULL DEFAULT '',
  body_excerpt text NOT NULL DEFAULT '', -- opening paragraphs of the SKILL.md body, plain text
  security_grade text,                   -- scanner verdict on the SKILL.md text
  security_flags jsonb NOT NULL DEFAULT '[]'::jsonb,
  blob_sha text NOT NULL,
  fetched_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (repo_full_name, path),
  UNIQUE (repo_full_name, slug)
);

CREATE TABLE IF NOT EXISTS public.sub_skill_scans (
  repo_full_name text PRIMARY KEY,
  tree_sha text,
  skill_count integer NOT NULL DEFAULT 0,
  status text NOT NULL,                  -- ok | absent | error
  scanned_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.sub_skills ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public read sub_skills" ON public.sub_skills;
CREATE POLICY "Public read sub_skills" ON public.sub_skills FOR SELECT USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.sub_skills FROM anon, authenticated;
GRANT SELECT ON public.sub_skills TO anon, authenticated;
REVOKE ALL ON SEQUENCE public.sub_skills_id_seq FROM anon, authenticated;

ALTER TABLE public.sub_skill_scans ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.sub_skill_scans FROM anon, authenticated;

NOTIFY pgrst, 'reload schema';
