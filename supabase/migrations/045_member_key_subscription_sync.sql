-- 045_member_key_subscription_sync.sql
-- Stripe subscriptions now drive key validity, and /pro/ can tell when the $29/yr
-- early-supporter tier has sold out.
--
-- 1. sync_member_key_expiry: the order poller (ops/stripe/poll_stripe.py, every 30 min)
--    reads each Agent Skills Hub subscription and sends the expiry its key should have:
--    end of the paid period + 3 days while active, the cancel date once cancelled, the
--    start of the unpaid period + 3 days while a renewal is past due. Before this, every
--    key ran a fixed year from issue (019), so a $49/mo CI Gate buyer who cancelled after
--    one month kept a working key for eleven more.
--    Access model is the same as issue_pro_key (019): p_secret is the only credential,
--    this file holds just its sha256, and the GRANT to anon is useless without it.
--    If the secret ever leaks, the damage stays bounded: only keys issued for a Stripe
--    Checkout Session (order_id 'cs_…') are touched, revoked keys stay revoked, and an
--    expiry more than 400 days out is refused (the longest plan is yearly).
--
-- 2. pro_early_bird_status: public, returns only {sold_out: bool}, never the count.
--    Stripe caps the $29/yr Payment Link at 100 completed payments; this lets the page
--    switch its offer to the $49/yr link at the same point (100 'pro-usd-29' keys).
--
-- No table or RLS change: member_keys keeps its deny-all RLS (017); both functions are
-- SECURITY DEFINER with a pinned search_path, like 019.

CREATE OR REPLACE FUNCTION sync_member_key_expiry(
  p_secret text,
  p_items  jsonb   -- [{"order_id": "cs_live_…", "expires_at": "2026-12-20T00:00:00Z"}, …]
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
  v_expected_secret_hash text := '332a0e4d55027893bc48f2513c8cc9dfe9fcb68ff1ba1a01f2367b01406f0d20';
  v_updated int;
BEGIN
  IF p_secret IS NULL OR encode(sha256(p_secret::bytea), 'hex') <> v_expected_secret_hash THEN
    RAISE EXCEPTION 'invalid_secret' USING errcode = '42501';
  END IF;

  IF p_items IS NULL OR jsonb_typeof(p_items) <> 'array' OR jsonb_array_length(p_items) > 1000 THEN
    RAISE EXCEPTION 'invalid_items' USING errcode = '22023';
  END IF;

  IF EXISTS (
    SELECT 1 FROM jsonb_array_elements(p_items) AS i
    WHERE NOT (i ? 'order_id' AND i ? 'expires_at')
       OR (i->>'expires_at')::timestamptz > now() + interval '400 days'
  ) THEN
    RAISE EXCEPTION 'invalid_items' USING errcode = '22023';
  END IF;

  UPDATE member_keys AS m
     SET expires_at = (i->>'expires_at')::timestamptz
    FROM jsonb_array_elements(p_items) AS i
   WHERE m.order_id = i->>'order_id'
     AND m.order_id LIKE 'cs\_%'
     AND m.revoked = false
     AND m.expires_at IS DISTINCT FROM (i->>'expires_at')::timestamptz;
  GET DIAGNOSTICS v_updated = ROW_COUNT;

  RETURN json_build_object(
    'status', 'ok',
    'received', jsonb_array_length(p_items),
    'updated', v_updated
  );
END;
$$;

GRANT EXECUTE ON FUNCTION sync_member_key_expiry(text, jsonb) TO anon, authenticated;

CREATE OR REPLACE FUNCTION pro_early_bird_status()
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT json_build_object('sold_out', count(*) >= 100)
  FROM member_keys
  WHERE note = 'pro-usd-29';
$$;

GRANT EXECUTE ON FUNCTION pro_early_bird_status() TO anon, authenticated;

NOTIFY pgrst, 'reload schema';
