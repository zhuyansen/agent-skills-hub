-- 018_pro_board.sql
-- Pro members' curation board: nominate existing repos, vote, top-3 get reposted.
--
-- Design constraints (see ops/pro-board.md):
--  • "Upload a skill" = NOMINATE an existing GitHub repo (not arbitrary UGC).
--    The repo must already be in our catalog AND graded SAFE — the security
--    grade IS the eligibility gate, so the board can't promote unsafe content.
--  • One vote per (member, submission) — enforced by a UNIQUE constraint in
--    Postgres, not client JS.
--  • Writes are key-gated via SECURITY DEFINER RPCs (same member_keys table as
--    017). The board itself is PUBLIC-READ on purpose: non-members see what the
--    club is curating and get an upgrade nudge (conversion surface).
--  • Reposting top-3 is a HUMAN action (draft → review → post), never automated
--    — promoting member content to our channels is an outward publish.

-- ── shared key validator (reused by submit + vote) ───────────────
CREATE OR REPLACE FUNCTION pro_valid_hash(p_key text)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE v_hash text;
BEGIN
  v_hash := encode(sha256(p_key::bytea), 'hex');
  IF NOT EXISTS (
    SELECT 1 FROM member_keys
    WHERE key_hash = v_hash AND revoked = false
      AND (expires_at IS NULL OR expires_at > now())
  ) THEN
    RAISE EXCEPTION 'invalid_or_expired_key' USING errcode = '42501';
  END IF;
  RETURN v_hash;
END;
$$;

-- ── submissions (one board entry per repo) ───────────────────────
CREATE TABLE IF NOT EXISTS pro_submissions (
  id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  repo_full_name    text NOT NULL UNIQUE,
  submitted_by_hash text NOT NULL,          -- sha256 of nominating member key
  note              text,                    -- optional "why it's good" blurb
  created_at        timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE pro_submissions ENABLE ROW LEVEL SECURITY;
-- Public READ (board is a conversion surface); writes only via RPC.
DROP POLICY IF EXISTS pro_submissions_public_read ON pro_submissions;
CREATE POLICY pro_submissions_public_read ON pro_submissions
  FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE ON pro_submissions FROM anon, authenticated;

-- ── votes (one per member per submission) ────────────────────────
CREATE TABLE IF NOT EXISTS pro_votes (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  submission_id bigint NOT NULL REFERENCES pro_submissions(id) ON DELETE CASCADE,
  voter_hash    text NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (submission_id, voter_hash)         -- ballot-stuffing guard, in Postgres
);
ALTER TABLE pro_votes ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON pro_votes FROM anon, authenticated;  -- deny-all; only RPC touches it

-- ── pro_submit: member nominates a repo (must be indexed + SAFE) ──
CREATE OR REPLACE FUNCTION pro_submit(p_key text, p_repo text, p_note text DEFAULT NULL)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_hash  text;
  v_repo  text;
  v_grade text;
  v_id    bigint;
BEGIN
  v_hash := pro_valid_hash(p_key);
  -- normalize: accept full URL or owner/repo, strip trailing slash / .git
  v_repo := regexp_replace(p_repo, '^https?://github\.com/', '');
  v_repo := regexp_replace(v_repo, '(\.git)?/?$', '');
  IF v_repo !~ '^[^/]+/[^/]+$' THEN
    RAISE EXCEPTION 'bad_repo_format' USING errcode = '22023';
  END IF;

  SELECT security_grade INTO v_grade FROM skills WHERE repo_full_name = v_repo;
  IF v_grade IS NULL THEN
    RAISE EXCEPTION 'not_in_catalog' USING errcode = 'P0002';  -- submit via /submit/ to index it first
  END IF;
  IF lower(v_grade) <> 'safe' THEN
    RAISE EXCEPTION 'not_safe_grade' USING errcode = '23514';  -- only SAFE-graded repos are board-eligible
  END IF;

  INSERT INTO pro_submissions (repo_full_name, submitted_by_hash, note)
  VALUES (v_repo, v_hash, NULLIF(left(p_note, 280), ''))
  ON CONFLICT (repo_full_name) DO UPDATE SET repo_full_name = EXCLUDED.repo_full_name
  RETURNING id INTO v_id;

  -- nominating counts as your vote
  INSERT INTO pro_votes (submission_id, voter_hash) VALUES (v_id, v_hash)
  ON CONFLICT DO NOTHING;

  RETURN json_build_object('submission_id', v_id, 'repo_full_name', v_repo, 'status', 'ok');
END;
$$;

-- ── pro_vote: idempotent one-vote-per-member ─────────────────────
CREATE OR REPLACE FUNCTION pro_vote(p_key text, p_submission_id bigint)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_hash  text;
  v_count bigint;
BEGIN
  v_hash := pro_valid_hash(p_key);
  INSERT INTO pro_votes (submission_id, voter_hash) VALUES (p_submission_id, v_hash)
  ON CONFLICT DO NOTHING;  -- voting twice is a no-op, not an error
  SELECT count(*) INTO v_count FROM pro_votes WHERE submission_id = p_submission_id;
  RETURN json_build_object('submission_id', p_submission_id, 'votes', v_count);
END;
$$;

-- ── pro_board: PUBLIC ranked board (grade re-checked live) ───────
-- Reflects CURRENT security_grade — if a repo flips out of SAFE after nomination
-- the caller sees the real grade and can exclude it (repost step re-checks too).
CREATE OR REPLACE FUNCTION pro_board(p_limit int DEFAULT 50)
RETURNS TABLE (
  submission_id  bigint,
  repo_full_name text,
  note           text,
  votes          bigint,
  security_grade text,
  stars          int,
  category       text,
  description    text,
  created_at     timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER          -- reads pro_votes (deny-all RLS) to aggregate; board is public
SET search_path = public
AS $$
  SELECT ps.id, ps.repo_full_name, ps.note,
         count(pv.id) AS votes,
         s.security_grade, s.stars, s.category, s.description, ps.created_at
  FROM pro_submissions ps
  LEFT JOIN pro_votes pv ON pv.submission_id = ps.id
  LEFT JOIN skills s ON s.repo_full_name = ps.repo_full_name
  GROUP BY ps.id, s.security_grade, s.stars, s.category, s.description
  ORDER BY votes DESC, ps.created_at DESC
  LIMIT LEAST(GREATEST(p_limit, 1), 200);
$$;

GRANT EXECUTE ON FUNCTION pro_submit(text, text, text)  TO anon, authenticated;
GRANT EXECUTE ON FUNCTION pro_vote(text, bigint)        TO anon, authenticated;
GRANT EXECUTE ON FUNCTION pro_board(int)                TO anon, authenticated;
-- pro_valid_hash is an internal helper — not granted to anon.
