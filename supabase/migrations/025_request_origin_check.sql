-- 025: only browsers on our own site may call the REST API.
--
-- Why (2026-10-03): www.6erskills.com copied the frontend, anon key included, and serves
-- our catalog to its visitors by calling this database from their browsers, with ads on
-- top. Every visit there is a query here, on an instance that already struggles.
--
-- How: PostgREST calls public.check_request() before every request (db_pre_request).
-- It rejects a request whose Origin header names another site. Browsers always send
-- Origin on a cross-origin request and a page cannot forge it, so a copied frontend on
-- another domain stops working. Requests without an Origin header (the site's build,
-- the sync, the MCP server, scripts, curl) are unaffected, as is the service role.
--
-- SECURITY IMPACT
-- - Access is narrowed, nothing is opened: no RLS policy, grant or key changes.
-- - Not a secret-based control. A third party can still call the API from its own
--   server (no Origin header) with the public anon key; this stops browser-side reuse
--   only. Data the anon role can read is still public by design.
-- - Covers PostgREST (tables, views, RPCs). Auth (/auth/v1) and Storage do not run it.
-- - If an allowed origin is missing, our own site fails to load data: the list below
--   must hold every domain the frontend is served from.
--
-- Rollback (immediate, no deploy):
--   ALTER ROLE authenticator RESET pgrst.db_pre_request;
--   NOTIFY pgrst, 'reload config';

CREATE OR REPLACE FUNCTION public.check_request()
RETURNS void
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  headers json := nullif(current_setting('request.headers', true), '')::json;
  origin text := lower(coalesce(headers ->> 'origin', ''));
  role text := coalesce(nullif(current_setting('request.jwt.claims', true), '')::json ->> 'role', '');
BEGIN
  IF origin = '' OR role = 'service_role' THEN
    RETURN;   -- not a browser page, or our own backend
  END IF;
  IF origin IN ('https://agentskillshub.top', 'https://www.agentskillshub.top', 'https://zhuyansen.github.io')
     OR origin ~ '^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$' THEN
    RETURN;
  END IF;
  RAISE EXCEPTION 'requests from % are not allowed', origin
    USING ERRCODE = '42501',
          HINT = 'This API serves agentskillshub.top. See https://github.com/zhuyansen/agent-skills-hub';
END;
$$;

GRANT EXECUTE ON FUNCTION public.check_request() TO anon, authenticated, service_role;

ALTER ROLE authenticator SET pgrst.db_pre_request = 'public.check_request';
NOTIFY pgrst, 'reload config';
