-- 030: the request check (025) also lets our own site's http:// origins through.
--
-- Why (2026-10-27): on 2026-10-26 at 07:07 UTC check_request() refused 7 requests whose
-- Origin was http://agentskillshub.top. The gateway log puts them on headless Chrome in
-- Google LLC's network (Linux, Chrome/156) with Referer http://agentskillshub.top/: Google
-- rendering the homepage at its http address, and getting no catalog data. Visitors never
-- load that address: GitHub Pages enforces HTTPS (https_enforced: true) and answers
-- http://agentskillshub.top and http://www.agentskillshub.top with a 301 to
-- https://agentskillshub.top/.
--
-- What changes: the allow list gains http://agentskillshub.top and
-- http://www.agentskillshub.top. Requests without an Origin header and the service role
-- pass as before; every other origin is still refused.
--
-- SECURITY IMPACT
-- - Widens browser access by two origins, both our own hostnames over http. No RLS policy,
--   grant or key changes.
-- - A page can only send these origins if it is served from our hostnames, and a request
--   without an Origin header (any server, any script) was never refused, so no third party
--   gains access it lacked. www.6erskills.com and every other origin are still refused.
--
-- Rollback (immediate, no deploy): re-run the CREATE OR REPLACE FUNCTION block of
-- 025_request_origin_check.sql, which restores the https-only list.

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
  IF origin IN ('https://agentskillshub.top', 'https://www.agentskillshub.top',
                'http://agentskillshub.top', 'http://www.agentskillshub.top',
                'https://zhuyansen.github.io')
     OR origin ~ '^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$' THEN
    RETURN;
  END IF;
  RAISE EXCEPTION 'requests from % are not allowed', origin
    USING ERRCODE = '42501',
          HINT = 'This API serves agentskillshub.top. See https://github.com/zhuyansen/agent-skills-hub';
END;
$$;
