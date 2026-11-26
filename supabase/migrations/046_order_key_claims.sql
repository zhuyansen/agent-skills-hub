-- 046_order_key_claims.sql
--
-- The Pro / CI Gate key, kept for the buyer's own success page for 24 hours.
--
-- issue_pro_key (019) returns the plaintext key exactly once and stores only its hash, so the
-- buyer email was the only copy. On 2026-11-26 the first early-bird buyer's email domain
-- stopped resolving (DNS SERVFAIL): the email sat in "delivery delayed" and he had no other
-- way to get the key he paid for. The Stripe webhook (supabase/functions/stripe-fulfill) now
-- also stores the key here, encrypted (AES-GCM, key in the functions' CLAIM_KEY secret), and
-- the success page Stripe redirects to (/pro/success/?session_id=...) fetches it through the
-- claim-key function with the Checkout Session id, which only the buyer's browser has.
--
-- Access: nobody but the service role. RLS on with no policies, and anon/authenticated lose
-- every privilege, so neither PostgREST role can read or write it even if a policy is added
-- by mistake. Rows expire after 24 hours; claim-key ignores expired rows and the webhook
-- deletes them on its next run.

CREATE TABLE IF NOT EXISTS order_key_claims (
  order_id   text PRIMARY KEY CHECK (order_id LIKE 'cs\_%'),
  iv         text NOT NULL,
  ciphertext text NOT NULL,
  note       text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL DEFAULT now() + interval '24 hours'
);

ALTER TABLE order_key_claims ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON order_key_claims FROM anon, authenticated;
