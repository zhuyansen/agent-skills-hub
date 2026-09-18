-- Day-one semantic priors for genuinely new repos, and their 14-day star outcome.
--
-- Why (2026-09-18): we want to know whether a TypeSafe Jev prior read from a repo's README
-- on the day we first see it predicts its next 14 days of stars better than the star count
-- it had at that moment. That cannot be measured after the fact any more: GitHub's
-- stargazer listing now returns 404, and the public event firehose that star-history
-- services rebuild from has been severely degraded since 2026-05-01. So we record it
-- going forward: score on entry, read the outcome from skills.stars 14 days later.
--
-- Written only by backend/cold_start_priors.py, a post-sync step in sync.yml, using the
-- service connection. Nothing in the product reads it yet.
--
-- Security impact: RLS is enabled with NO policies, so the anon and authenticated roles
-- (the public frontend) can neither read nor write it; only the service/owner connection
-- used by the sync job can. The table holds public GitHub metadata only — no user data.

CREATE TABLE IF NOT EXISTS cold_start_priors (
  repo_full_name   text PRIMARY KEY,
  scored_at        timestamptz NOT NULL DEFAULT now(),
  repo_created_at  timestamptz,
  first_seen       timestamptz,
  stars_at_score   integer NOT NULL,
  model            text NOT NULL,             -- resolved Jev model id, e.g. typesafe/jev-1.13-20260917
  prior            jsonb NOT NULL,            -- flattened answers of the typed questions
  stars_at_14d     integer,                   -- NULL until the outcome window has elapsed
  outcome_at       timestamptz,               -- when stars_at_14d was read
  outcome_stale    boolean                    -- true if skills.last_synced was older than the window end
);

CREATE INDEX IF NOT EXISTS idx_cold_start_priors_pending
  ON cold_start_priors (scored_at)
  WHERE stars_at_14d IS NULL;

ALTER TABLE cold_start_priors ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE cold_start_priors IS
  'Jev day-one prior + 14-day star outcome for new repos (prospective cold-start experiment). Service-only: RLS on, no policies.';
