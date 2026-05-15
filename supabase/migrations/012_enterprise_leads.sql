-- Enterprise demo request form (the /enterprise/ page CTA submits here).
--
-- WHY:
--   B-path pivot to enterprise trust layer ($10K-$30K/yr). We need a place
--   to capture inbound enterprise leads BEFORE Stripe is integrated. This
--   table feeds the manual sales/POC pipeline for the first 5-10 customers.
--
-- DESIGN NOTES (lessons from the build):
--   - PostgREST + supabase-js INSERT with RLS WITH CHECK kept failing for
--     this table even with permissive policy = true. Same pattern works on
--     arena_votes. Root cause not isolated (some PostgREST schema-cache
--     quirk specific to this table's column shape), so we wrap inserts in
--     a SECURITY DEFINER RPC `submit_enterprise_lead` and grant EXECUTE
--     to anon. RPC enforces bounds in PL/pgSQL, identical to what the RLS
--     policy would have done.
--   - Direct INSERT via service_role still works (admin reads/writes).
--   - Column `role` was renamed to `role_title` because `role` is a SQL
--     reserved word that confuses PostgREST in some edge cases.

CREATE TABLE IF NOT EXISTS enterprise_leads (
  id BIGSERIAL PRIMARY KEY,

  -- Identity
  full_name TEXT NOT NULL,
  email TEXT NOT NULL,
  company TEXT NOT NULL,
  role_title TEXT,                                 -- "VP Engineering", "CTO", etc.

  -- Qualification
  team_size TEXT,
  industry TEXT,
  use_case TEXT NOT NULL,
  current_stack TEXT,
  compliance_requirements TEXT,

  -- Engagement
  message TEXT,
  timeline TEXT,
  estimated_budget TEXT,

  -- Pipeline tracking
  status TEXT NOT NULL DEFAULT 'new'
    CHECK (status IN ('new', 'contacted', 'qualified', 'demo_scheduled',
                      'poc_active', 'won', 'lost', 'unqualified')),
  source TEXT DEFAULT 'enterprise_page',
  reviewed_at TIMESTAMPTZ,
  review_notes TEXT,
  assigned_to TEXT,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_enterprise_leads_status
  ON enterprise_leads (status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_enterprise_leads_email
  ON enterprise_leads (email);

CREATE OR REPLACE FUNCTION public.touch_enterprise_leads_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_enterprise_leads_touch ON enterprise_leads;
CREATE TRIGGER trg_enterprise_leads_touch
  BEFORE UPDATE ON enterprise_leads
  FOR EACH ROW EXECUTE FUNCTION public.touch_enterprise_leads_updated_at();

-- RLS: enabled, but anon does NOT submit directly. Anon uses the
-- SECURITY DEFINER RPC `submit_enterprise_lead` below. service_role
-- bypasses RLS for admin reads.
ALTER TABLE enterprise_leads ENABLE ROW LEVEL SECURITY;

-- ────────────────────────────────────────────────────────────────────
-- SECURITY DEFINER submit function
--   Called from /enterprise/ page demo form. Runs as table owner so it
--   bypasses RLS. Length validation kept in PL/pgSQL (mirrors prior policy).
-- ────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.submit_enterprise_lead(
  p_full_name TEXT,
  p_email TEXT,
  p_company TEXT,
  p_use_case TEXT,
  p_role_title TEXT DEFAULT NULL,
  p_team_size TEXT DEFAULT NULL,
  p_industry TEXT DEFAULT NULL,
  p_current_stack TEXT DEFAULT NULL,
  p_compliance_requirements TEXT DEFAULT NULL,
  p_message TEXT DEFAULT NULL,
  p_timeline TEXT DEFAULT NULL,
  p_estimated_budget TEXT DEFAULT NULL,
  p_source TEXT DEFAULT 'enterprise_page'
) RETURNS BIGINT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  new_id BIGINT;
BEGIN
  IF length(p_full_name) NOT BETWEEN 1 AND 100 THEN RAISE EXCEPTION 'invalid full_name length'; END IF;
  IF length(p_email) NOT BETWEEN 5 AND 200 THEN RAISE EXCEPTION 'invalid email length'; END IF;
  IF p_email NOT LIKE '%@%' THEN RAISE EXCEPTION 'invalid email format'; END IF;
  IF length(p_company) NOT BETWEEN 1 AND 200 THEN RAISE EXCEPTION 'invalid company length'; END IF;
  IF length(p_use_case) NOT BETWEEN 1 AND 2000 THEN RAISE EXCEPTION 'invalid use_case length'; END IF;
  IF length(COALESCE(p_role_title, '')) > 100 THEN RAISE EXCEPTION 'invalid role length'; END IF;
  IF length(COALESCE(p_team_size, '')) > 50 THEN RAISE EXCEPTION 'invalid team_size'; END IF;
  IF length(COALESCE(p_industry, '')) > 100 THEN RAISE EXCEPTION 'invalid industry'; END IF;
  IF length(COALESCE(p_current_stack, '')) > 500 THEN RAISE EXCEPTION 'invalid current_stack'; END IF;
  IF length(COALESCE(p_compliance_requirements, '')) > 500 THEN RAISE EXCEPTION 'invalid compliance'; END IF;
  IF length(COALESCE(p_message, '')) > 2000 THEN RAISE EXCEPTION 'invalid message'; END IF;
  IF length(COALESCE(p_timeline, '')) > 50 THEN RAISE EXCEPTION 'invalid timeline'; END IF;
  IF length(COALESCE(p_estimated_budget, '')) > 50 THEN RAISE EXCEPTION 'invalid budget'; END IF;

  INSERT INTO enterprise_leads (
    full_name, email, company, use_case, role_title, team_size, industry,
    current_stack, compliance_requirements, message, timeline, estimated_budget, source
  ) VALUES (
    p_full_name, p_email, p_company, p_use_case, p_role_title, p_team_size, p_industry,
    p_current_stack, p_compliance_requirements, p_message, p_timeline, p_estimated_budget, p_source
  ) RETURNING id INTO new_id;

  RETURN new_id;
END;
$$;

GRANT EXECUTE ON FUNCTION public.submit_enterprise_lead(
  TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT,TEXT
) TO anon, authenticated;

COMMENT ON TABLE enterprise_leads IS
  'Inbound enterprise demo requests from /enterprise/ page. Manual sales pipeline until Stripe integrated.';
COMMENT ON FUNCTION public.submit_enterprise_lead IS
  'SECURITY DEFINER wrapper for anon inserts (bypasses RLS quirk specific to this table).';
