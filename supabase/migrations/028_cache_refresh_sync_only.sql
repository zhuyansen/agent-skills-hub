-- 028: only the sync can rebuild the homepage and masters caches.
--
-- Why (noticed 2026-10-24): 013, 014 and 015 granted EXECUTE on the cache refresh
-- functions to anon and authenticated, and a function in public is executable by PUBLIC
-- until that is revoked. Anyone with the anon key, which ships in the frontend, could
-- POST /rest/v1/rpc/refresh_landing_data from a server, since check_request() (025) lets
-- a request without an Origin header through. Each call starts the full aggregation over
-- the skills table (8-60 s on a healthy instance), so a loop of them can keep the
-- instance busy. The compute_* functions behind them are SECURITY DEFINER and were open
-- the same way. anon could also DELETE the cached rows (RLS is off on both cache
-- tables), after which get_landing_data() and get_org_builders() recompute live on every
-- homepage view until the next sync.
--
-- Callers (checked 2026-10-25): refresh_* only from the sync, through SUPABASE_DB_URL
-- (backend/app/scheduler/jobs.py). It connects as postgres, the owner of every function
-- here, so it keeps EXECUTE. compute_* only from inside refresh_* and get_*, which are
-- SECURITY DEFINER and so call it as postgres. The frontend and the build
-- (frontend/scripts/generate-author-pages.mjs) call only get_masters, get_landing_data
-- and get_org_builders, which this file does not touch.
--
-- SECURITY IMPACT
-- - Access is narrowed, nothing is opened. PUBLIC, anon and authenticated lose EXECUTE on
--   refresh_master_aggregates, refresh_landing_data, refresh_org_builders,
--   compute_landing_data and compute_org_builders. postgres (owner) and service_role
--   keep it.
-- - anon and authenticated keep only SELECT on landing_data_cache and org_builders_cache.
--   They also held INSERT, UPDATE, DELETE and TRUNCATE there through the schema's default
--   privileges. Nothing reads these tables directly: the get_* functions read them as
--   postgres.
-- - Unchanged: the get_* grants, RLS and policies (RLS stays off on both cache tables),
--   keys, and mv_master_aggregates' grants (get_masters reads it as the caller; without
--   refresh_master_aggregates() the API has no way to REFRESH it). The default privileges
--   are unchanged too, so a function created later in public is again executable by
--   PUBLIC and anon unless its migration revokes that.
-- - CREATE OR REPLACE FUNCTION keeps these grants. DROP and CREATE resets them to the
--   default privileges, so run this file again after that.
--
-- Rollback (restores the grants 013, 014 and 015 left):
--   GRANT EXECUTE ON FUNCTION public.refresh_master_aggregates(), public.refresh_landing_data(),
--     public.refresh_org_builders(), public.compute_landing_data(), public.compute_org_builders()
--     TO PUBLIC, anon, authenticated;
--   GRANT ALL ON TABLE public.landing_data_cache, public.org_builders_cache TO anon, authenticated;
--   NOTIFY pgrst, 'reload schema';

-- If anything holds a lock this needs, fail after 5 s instead of waiting in the queue.
SET LOCAL lock_timeout = '5s';

REVOKE EXECUTE ON FUNCTION
  public.refresh_master_aggregates(),
  public.refresh_landing_data(),
  public.refresh_org_builders(),
  public.compute_landing_data(),
  public.compute_org_builders()
FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION
  public.refresh_master_aggregates(),
  public.refresh_landing_data(),
  public.refresh_org_builders(),
  public.compute_landing_data(),
  public.compute_org_builders()
TO service_role;

REVOKE ALL ON TABLE public.landing_data_cache, public.org_builders_cache FROM anon, authenticated;
GRANT SELECT ON TABLE public.landing_data_cache, public.org_builders_cache TO anon, authenticated;

NOTIFY pgrst, 'reload schema';
