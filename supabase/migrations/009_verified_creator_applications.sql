-- Verified Creator Application form (separate from older `master_applications`)
-- Captures: identity (display_name + GitHub), expertise (skill_categories), availability (timezone, hire toggle, rate range, bio)
-- Reviewed manually by admin within 5 business days.

CREATE TABLE IF NOT EXISTS verified_creator_applications (
  id BIGSERIAL PRIMARY KEY,
  display_name TEXT NOT NULL,
  github_username TEXT NOT NULL,
  skill_categories TEXT[] NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'UTC',
  available_for_hire BOOLEAN NOT NULL DEFAULT FALSE,
  rate_min INTEGER,
  rate_max INTEGER,
  bio TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  reviewed_at TIMESTAMPTZ,
  review_notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vca_status ON verified_creator_applications(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vca_github ON verified_creator_applications(github_username);

-- Auto-update timestamp on edit
CREATE OR REPLACE FUNCTION public.touch_vca_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_vca_touch ON verified_creator_applications;
CREATE TRIGGER trg_vca_touch
  BEFORE UPDATE ON verified_creator_applications
  FOR EACH ROW EXECUTE FUNCTION public.touch_vca_updated_at();

-- RLS: anon can INSERT (submit application), but cannot SELECT/UPDATE/DELETE.
-- Admin reads + reviews via service role key.
ALTER TABLE verified_creator_applications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "vca_anon_insert" ON verified_creator_applications;
CREATE POLICY "vca_anon_insert"
  ON verified_creator_applications
  FOR INSERT
  TO anon
  WITH CHECK (
    status = 'pending'
    AND length(display_name) BETWEEN 1 AND 100
    AND length(github_username) BETWEEN 1 AND 50
    AND array_length(skill_categories, 1) BETWEEN 1 AND 3
    AND length(bio) <= 200
    AND (rate_min IS NULL OR rate_min >= 0)
    AND (rate_max IS NULL OR rate_max >= 0)
  );

-- Admin (service role) full access — implicit via service_role key bypassing RLS.
