-- Fix critical RLS vulnerabilities on subscribers table
-- Previous policies allowed full read/write access via anon key

-- 1. Drop overly permissive policies
DROP POLICY IF EXISTS "Read own subscriber" ON subscribers;
DROP POLICY IF EXISTS "Verify email via token" ON subscribers;
DROP POLICY IF EXISTS "subscribers_anon_insert" ON subscribers;
DROP POLICY IF EXISTS "Anyone can subscribe" ON subscribers;

-- 2. Create secure RPC functions (SECURITY DEFINER = runs as table owner, bypasses RLS)

-- Subscribe: check if email exists, insert or return existing
CREATE OR REPLACE FUNCTION public.subscribe(p_email TEXT)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
  v_existing RECORD;
  v_token TEXT;
BEGIN
  -- Validate email format
  IF p_email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
    RETURN json_build_object('error', 'invalid_email');
  END IF;

  -- Check existing
  SELECT id, email, verified, is_active, verification_token
    INTO v_existing
    FROM subscribers
    WHERE email = lower(trim(p_email));

  IF v_existing.id IS NOT NULL THEN
    -- Already exists
    IF v_existing.verified AND v_existing.is_active THEN
      RETURN json_build_object('status', 'already_subscribed');
    ELSIF v_existing.verified AND NOT v_existing.is_active THEN
      -- Reactivate
      UPDATE subscribers SET is_active = true WHERE id = v_existing.id;
      RETURN json_build_object('status', 'reactivated');
    ELSE
      -- Not yet verified, return token for resend
      RETURN json_build_object('status', 'pending_verification', 'token', v_existing.verification_token);
    END IF;
  END IF;

  -- New subscriber
  v_token := encode(gen_random_bytes(32), 'hex');
  INSERT INTO subscribers (email, verification_token, verified, is_active)
    VALUES (lower(trim(p_email)), v_token, false, true);

  RETURN json_build_object('status', 'created', 'token', v_token);
END;
$$;

-- Verify email by token
CREATE OR REPLACE FUNCTION public.verify_email(p_token TEXT)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
  v_sub RECORD;
BEGIN
  IF p_token IS NULL OR length(p_token) < 10 THEN
    RETURN json_build_object('error', 'invalid_token');
  END IF;

  SELECT id, email, verified INTO v_sub
    FROM subscribers
    WHERE verification_token = p_token;

  IF v_sub.id IS NULL THEN
    RETURN json_build_object('error', 'token_not_found');
  END IF;

  IF v_sub.verified THEN
    RETURN json_build_object('status', 'already_verified', 'email', v_sub.email);
  END IF;

  UPDATE subscribers
    SET verified = true, verification_token = NULL
    WHERE id = v_sub.id;

  RETURN json_build_object('status', 'verified', 'email', v_sub.email);
END;
$$;

-- Unsubscribe by token (for email footer links)
CREATE OR REPLACE FUNCTION public.unsubscribe(p_token TEXT)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
  v_sub RECORD;
BEGIN
  SELECT id, email INTO v_sub
    FROM subscribers
    WHERE verification_token = p_token OR unsubscribe_token = p_token;

  IF v_sub.id IS NULL THEN
    RETURN json_build_object('error', 'not_found');
  END IF;

  UPDATE subscribers SET is_active = false WHERE id = v_sub.id;
  RETURN json_build_object('status', 'unsubscribed', 'email', v_sub.email);
END;
$$;

-- 3. Grant execute to anon role
GRANT EXECUTE ON FUNCTION public.subscribe(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION public.verify_email(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION public.unsubscribe(TEXT) TO anon;

-- 4. New restrictive RLS policies - anon can only INSERT (for backwards compat), no SELECT/UPDATE/DELETE
-- With RPC functions using SECURITY DEFINER, we don't need broad anon policies.
-- Keep a minimal INSERT policy as fallback.

CREATE POLICY "subscribers_anon_insert_only" ON subscribers
  FOR INSERT
  WITH CHECK (
    -- Only allow inserting with required fields
    email IS NOT NULL AND
    verification_token IS NOT NULL AND
    verified = false
  );

-- No SELECT for anon (RPC handles lookups)
-- No UPDATE for anon (RPC handles verification)
-- No DELETE for anon (only service_role can delete)

-- 5. Service role always has full access (implicit in Supabase)
-- Admin operations go through admin_action() RPC which uses service_role
