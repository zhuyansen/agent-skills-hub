-- Track whether a catalog entry's GitHub repo still exists.
--
-- Why (2026-08-05): incremental sync searches `pushed:>LAST_SYNC`, so a DELETED
-- repo looks identical to a merely quiet one — it stops being returned and
-- lingers forever with a dead GitHub link. `/skill/Manavarya09/design-extract/`
-- (3,334 stars) sat like that for six weeks while still ranking pos 4.3 for its
-- own repo name. Nothing in the pipeline ever asked "does this still exist?".
--
-- Deliberately NOT deleting dead rows: those pages answer a real query ("what
-- happened to this repo?") that nobody else on the web answers. We keep them
-- indexed and label them, rather than 404ing away live search demand.
--
-- Populated by ops/probe_dead_repos.py (read-only probe → this column).

ALTER TABLE skills
  ADD COLUMN IF NOT EXISTS repo_status text NOT NULL DEFAULT 'live',
  ADD COLUMN IF NOT EXISTS repo_status_checked_at timestamptz;

-- 'live'    — 200 from the GitHub API at last check
-- 'gone'    — 404: deleted, or the owning account was removed
-- 'unknown' — probe was inconclusive (network/auth); never treat as 'live'
ALTER TABLE skills
  DROP CONSTRAINT IF EXISTS skills_repo_status_check;
ALTER TABLE skills
  ADD CONSTRAINT skills_repo_status_check
  CHECK (repo_status IN ('live', 'gone', 'unknown'));

-- Partial index: 'gone' is a tiny minority (17 of 895 in the first high-star
-- sweep), and every consumer filters for exactly that, so indexing only those
-- rows keeps it small.
CREATE INDEX IF NOT EXISTS idx_skills_repo_status_gone
  ON skills (repo_status)
  WHERE repo_status <> 'live';

COMMENT ON COLUMN skills.repo_status IS
  'GitHub liveness at last probe. Set by ops/probe_dead_repos.py. Dead entries are labelled, not deleted — their pages still answer "what happened to this repo?".';
