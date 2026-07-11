-- 017_pro_membership.sql
-- Pro membership gate for AgentSkillsHub club (¥599 tier).
--
-- Freemium principle: basic search stays 100% open (SEO/traffic depend on it).
-- Only DEPTH is gated: README-inclusive full-text + higher page cap + export
-- payload. Enforcement lives in Postgres (SECURITY DEFINER RPC), NOT in the
-- static SPA — a JS-side key check is bypassable via the anon key + devtools.
--
-- ⚠️ IRREVERSIBLE SCHEMA + RLS CHANGE — see ops/pro-membership-security.md for
-- the security-impact review. Apply in the documented chunked order; the
-- readme_search_vector backfill touches ~133K rows and MUST be chunked
-- (scan_all single-transaction timeout scar, migration 003 era).

-- ── 1. Extensions ────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- digest() for key hashing

-- ── 2. Member keys (PII: email) ──────────────────────────────────
-- Keys are stored HASHED (sha256). A DB leak never exposes usable keys.
CREATE TABLE IF NOT EXISTS member_keys (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  key_hash    text NOT NULL UNIQUE,          -- encode(digest(raw_key,'sha256'),'hex')
  email       text NOT NULL,
  tier        text NOT NULL DEFAULT 'pro',
  created_at  timestamptz NOT NULL DEFAULT now(),
  expires_at  timestamptz,                   -- NULL = no expiry
  revoked     boolean NOT NULL DEFAULT false,
  note        text
);

-- Deny-all RLS: no policy => anon & authenticated roles get ZERO rows.
-- Only service_role (which bypasses RLS) can read/write. The pro_search RPC
-- reads it via SECURITY DEFINER, so the client never touches this table.
ALTER TABLE member_keys ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON member_keys FROM anon, authenticated;

-- ── 3. README-inclusive search vector (the paid depth) ───────────
-- The free search_vector (migration 003) weights name/author/desc/topics only.
-- This SEPARATE column adds readme_content so README search is a real Pro-only
-- capability, not a reselling of an existing free feature.
ALTER TABLE skills ADD COLUMN IF NOT EXISTS readme_search_vector tsvector;
CREATE INDEX IF NOT EXISTS idx_skills_readme_search_vector
  ON skills USING gin(readme_search_vector);

CREATE OR REPLACE FUNCTION update_skills_readme_search_vector()
RETURNS trigger AS $$
BEGIN
  NEW.readme_search_vector :=
      setweight(to_tsvector('english', COALESCE(NEW.repo_name, '')), 'A') ||
      setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
      setweight(to_tsvector('english', COALESCE(NEW.readme_content, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_skills_readme_search_vector ON skills;
CREATE TRIGGER trg_skills_readme_search_vector
  BEFORE INSERT OR UPDATE OF repo_name, description, readme_content ON skills
  FOR EACH ROW EXECUTE FUNCTION update_skills_readme_search_vector();

-- NOTE: existing rows are backfilled OUT-OF-BAND, chunked, off-peak —
-- see ops/backfill_readme_search_vector.py. Do NOT `UPDATE skills SET ...`
-- in one statement here (57014 timeout / full rollback risk on 133K rows).

-- ── 4. pro_search RPC — the gate ─────────────────────────────────
-- Validates the caller's key server-side, then runs README-depth FTS with a
-- higher cap. Invalid/expired/revoked key -> 42501 (client shows upgrade card).
CREATE OR REPLACE FUNCTION pro_search(
  p_key          text,
  p_query        text    DEFAULT NULL,
  p_category     text    DEFAULT NULL,
  p_min_security text    DEFAULT NULL,   -- 'safe' | 'caution' | ...(exact grade)
  p_limit        int     DEFAULT 200,
  p_offset       int     DEFAULT 0
)
RETURNS SETOF skills
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_valid boolean;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM member_keys
    WHERE key_hash = encode(digest(p_key, 'sha256'), 'hex')
      AND revoked = false
      AND (expires_at IS NULL OR expires_at > now())
  ) INTO v_valid;

  IF NOT v_valid THEN
    RAISE EXCEPTION 'invalid_or_expired_key' USING errcode = '42501';
  END IF;

  RETURN QUERY
    SELECT s.* FROM skills s
    WHERE (p_query IS NULL OR p_query = ''
           OR s.readme_search_vector @@ websearch_to_tsquery('english', p_query))
      AND (p_category IS NULL OR s.category = p_category)
      AND (p_min_security IS NULL OR s.security_grade = p_min_security)
    ORDER BY s.stars DESC NULLS LAST
    LIMIT  LEAST(GREATEST(p_limit, 1), 500)   -- hard cap 500 even for Pro
    OFFSET GREATEST(p_offset, 0);
END;
$$;

-- Callable by the anon role, but useless without a valid key (checked inside).
GRANT EXECUTE ON FUNCTION pro_search(text, text, text, text, int, int)
  TO anon, authenticated;
