-- 047_order_key_claims_claimed_at.sql
-- When the success page first fetched the key. claim-key serves a row for 15 minutes after
-- that (a reload, a second tab), then refuses it: the Checkout Session id is the only claim,
-- and an id copied from somewhere later should not keep opening the key for 24 hours.
ALTER TABLE order_key_claims ADD COLUMN IF NOT EXISTS claimed_at timestamptz;
