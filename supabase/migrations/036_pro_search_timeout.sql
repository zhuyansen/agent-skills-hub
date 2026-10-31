-- 036_pro_search_timeout.sql
-- Give the two Pro search RPCs an 8 s statement timeout instead of anon's 3 s
-- (2026-10-31).
--
-- After 035, common terms return in well under a second, but mid-frequency terms
-- that are missing from the tsvector statistics still read 5k-15k heap rows when
-- the cache is cold. The planner estimates them at the default 1,278 rows, while
-- the real counts are far higher ('rust' 10,003, 'telegram' 5,552,
-- 'prompt injection' 15,406). Through the public API on prod they took 2.4-3.4 s,
-- and 'rust' at LIMIT 200 failed with 57014 at 3.4 s.
-- A cheap exact count would fix the estimate, but it is not cheap: only 47% of
-- the skills heap pages are all-visible, so counting 'rust' took 5.5 s.
--
-- PostgREST applies a function's own statement_timeout for that call (Supabase
-- docs, "Timeouts": function-level setting), so this raises the limit only for
-- these two RPCs; every other anon request keeps 3 s. 8 s matches the
-- authenticated role.
--
-- SECURITY: pro_search still needs a valid member key. pro_search_trial still has
-- its per-IP and global daily caps, but a call that times out rolls back its own
-- counter, so it never counted against the cap; the longer limit lets such a call
-- hold a connection for up to 8 s instead of 3 s. No grant, policy or RLS change.

ALTER FUNCTION pro_search(text, text, text, text, int, int) SET statement_timeout = '8s';
ALTER FUNCTION pro_search_trial(text, text, text, int) SET statement_timeout = '8s';

-- PostgREST caches function settings with the schema; reload it.
NOTIFY pgrst, 'reload schema';
