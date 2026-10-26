-- 029: the API can no longer read or write access_tokens, mcp_request_log or blocked_repos.
--
-- Why (noticed 2026-10-25 while auditing 028): RLS was off on these three tables, and anon
-- and authenticated held every table privilege on them through the schema's default
-- privileges. Anyone with the anon key, which ships in the frontend, could read, insert,
-- update and delete their rows through PostgREST from a server, since check_request()
-- (025) lets a request without an Origin header through.
-- - access_tokens and mcp_request_log belong to GBrain (garrytan/gbrain 0.6.1), whose CLI
--   is set up against this database. Its schema turns RLS on for its other ten tables but
--   not for these two. access_tokens holds the bearer tokens of GBrain's remote MCP server
--   as sha256 hashes: an inserted row is a working token, and clearing revoked_at revives
--   a revoked one. mcp_request_log is that server's request log.
-- - blocked_repos (created by hand on 2026-07-19, with no migration) lists repositories the
--   sync must never ingest again. Deleting a row lets a removed repository back in the next
--   time a sync finds it; inserting one keeps a legitimate repository out.
--
-- Callers (checked 2026-10-26):
-- - blocked_repos: only the sync, `SELECT full_name FROM blocked_repos` in
--   backend/app/scheduler/jobs.py, through SUPABASE_DB_URL as postgres, the owner of all
--   three tables. That read swallows errors: if it ever fails, the sync runs with an empty
--   block list, so check that it still reads its rows after a change here.
-- - access_tokens and mcp_request_log: only GBrain. Its CLI (including the token commands in
--   src/commands/auth.ts) connects with a database URL as postgres, and its gbrain-mcp Edge
--   Function with SUPABASE_DB_URL, also as postgres. Neither uses the anon key or PostgREST.
-- - Nothing in this repository, the frontend or the build reads any of them through the API.
--
-- SECURITY IMPACT
-- - Access is narrowed, nothing is opened. anon and authenticated lose every privilege on the
--   three tables (they held SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER and
--   MAINTAIN) and on the sequence behind mcp_request_log.id (USAGE, SELECT, UPDATE).
-- - RLS is turned on for all three, with no policy: if a grant comes back (a broad
--   GRANT ... ON ALL TABLES IN SCHEMA public, say), anon and authenticated still see no rows
--   and cannot write any.
-- - postgres (owner; also BYPASSRLS) and service_role (BYPASSRLS, keeps its grants) are
--   unaffected, so the sync, GBrain and the SQL editor work as before.
-- - Unchanged: GBrain's other ten tables (RLS already on, no policy), every other table,
--   policies, functions, keys, and the default privileges. A table created later in public
--   again starts with RLS off and every privilege granted to anon and authenticated, unless
--   its migration revokes that or turns RLS on.
-- - Re-running GBrain's schema or migrations keeps this (they only CREATE TABLE IF NOT
--   EXISTS these tables). DROP and CREATE starts over with RLS off and the default
--   privileges, so run this file again after that.
--
-- Rollback (re-opens the hole; restores RLS off and the grants exactly as they were):
--   ALTER TABLE public.access_tokens DISABLE ROW LEVEL SECURITY;
--   ALTER TABLE public.mcp_request_log DISABLE ROW LEVEL SECURITY;
--   ALTER TABLE public.blocked_repos DISABLE ROW LEVEL SECURITY;
--   GRANT ALL ON TABLE public.access_tokens, public.mcp_request_log, public.blocked_repos TO anon, authenticated;
--   GRANT ALL ON SEQUENCE public.mcp_request_log_id_seq TO anon, authenticated;
--   NOTIFY pgrst, 'reload schema';

-- ENABLE ROW LEVEL SECURITY takes an ACCESS EXCLUSIVE lock. If anything holds a lock on one
-- of these tables (a sync mid-transaction may still hold one on blocked_repos), fail after
-- 5 s instead of waiting in the queue and blocking the readers behind it.
SET LOCAL lock_timeout = '5s';

ALTER TABLE public.access_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_request_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blocked_repos ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.access_tokens, public.mcp_request_log, public.blocked_repos
FROM anon, authenticated;
REVOKE ALL ON SEQUENCE public.mcp_request_log_id_seq FROM anon, authenticated;

NOTIFY pgrst, 'reload schema';
