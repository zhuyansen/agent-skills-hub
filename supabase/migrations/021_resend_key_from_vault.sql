-- 021_resend_key_from_vault.sql
-- SECURITY INCIDENT REMEDIATION (2026-07-16):
-- Migration 006 hardcoded the Resend API key in send_verification_email's
-- Authorization header. The repo is public, so secret scanning flagged it and
-- Resend auto-revoked the key — which killed the analytics digest, newsletter,
-- and email verification (all share that one key). See ops/pro-membership-security
-- postmortem style: never put a live secret in a tracked file.
--
-- Fix: read the key from Supabase Vault at call time instead of hardcoding.
-- The key itself lives ONLY in Vault + GitHub Secrets, never in git.
--
-- PREREQUISITE (run once in Supabase SQL editor, with the NEW key — not here):
--   select vault.create_secret('re_your_new_key', 'resend_api_key');
-- Until that secret exists this function raises a clear error instead of
-- silently sending with a dead/absent key.

CREATE OR REPLACE FUNCTION send_verification_email(p_email TEXT, p_token TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $func$
DECLARE
  verify_url  TEXT;
  email_html  TEXT;
  site_url    TEXT := 'https://agentskillshub.top';
  resend_key  TEXT;
  request_id  BIGINT;
BEGIN
  SELECT decrypted_secret INTO resend_key
  FROM vault.decrypted_secrets
  WHERE name = 'resend_api_key';

  IF resend_key IS NULL OR resend_key = '' THEN
    RAISE EXCEPTION 'resend_api_key not found in Vault — run: select vault.create_secret(''<key>'', ''resend_api_key'')';
  END IF;

  verify_url := site_url || '/verify-email?token=' || p_token;

  email_html := '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
    || '<body style="margin:0;padding:0;background:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">'
    || '<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 20px;"><tr><td align="center">'
    || '<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
    || '<tr><td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:32px 40px;text-align:center;">'
    || '<h1 style="color:#fff;margin:0;font-size:24px;">Agent Skills Hub</h1>'
    || '<p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px;">Discover Agent Skills, Tools & MCP Servers</p>'
    || '</td></tr>'
    || '<tr><td style="padding:40px;">'
    || '<h2 style="color:#1a1a2e;margin:0 0 16px;font-size:20px;">Confirm your subscription</h2>'
    || '<p style="color:#4a5568;line-height:1.6;margin:0 0 24px;">Thanks for subscribing to the Agent Skills Hub weekly newsletter! Click the button below to verify your email address.</p>'
    || '<table cellpadding="0" cellspacing="0" style="margin:0 auto 24px;"><tr><td style="background:#4f46e5;border-radius:8px;">'
    || '<a href="' || verify_url || '" style="display:inline-block;padding:14px 32px;color:#fff;text-decoration:none;font-weight:600;font-size:16px;">Verify Email Address</a>'
    || '</td></tr></table>'
    || '<p style="color:#718096;font-size:13px;">If you didn''t subscribe, ignore this email.</p>'
    || '</td></tr>'
    || '<tr><td style="background:#f8fafc;padding:20px 40px;text-align:center;border-top:1px solid #e2e8f0;">'
    || '<p style="color:#a0aec0;font-size:12px;margin:0;"><a href="' || site_url || '" style="color:#4f46e5;">Agent Skills Hub</a></p>'
    || '</td></tr>'
    || '</table></td></tr></table></body></html>';

  SELECT net.http_post(
    url := 'https://api.resend.com/emails'::text,
    body := jsonb_build_object(
      'from', 'Agent Skills Hub <noreply@agentskillshub.top>',
      'to', jsonb_build_array(p_email),
      'subject', 'Confirm your Agent Skills Hub subscription',
      'html', email_html
    ),
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || resend_key,
      'Content-Type', 'application/json'
    )
  ) INTO request_id;

  RAISE LOG 'Verification email queued for % (request_id: %)', p_email, request_id;
END;
$func$;
