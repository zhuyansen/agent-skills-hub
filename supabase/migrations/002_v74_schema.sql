-- V7.4 Schema Migration: Write support for GitHub Pages deployment
-- Adds columns/tables needed for community submissions via Supabase direct

-- ═══ 1. extra_repos: add status tracking columns ═══
ALTER TABLE extra_repos ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE extra_repos ADD COLUMN IF NOT EXISTS submitted_by VARCHAR(255);
ALTER TABLE extra_repos ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

-- Allow anonymous inserts for community submissions
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'extra_repos' AND policyname = 'extra_repos_anon_insert') THEN
    CREATE POLICY "extra_repos_anon_insert" ON extra_repos FOR INSERT WITH CHECK (true);
  END IF;
END $$;

-- ═══ 2. master_applications: new table for master certification requests ═══
CREATE TABLE IF NOT EXISTS master_applications (
  id BIGSERIAL PRIMARY KEY,
  github VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  bio TEXT,
  repo_urls TEXT DEFAULT '[]',
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE master_applications ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'master_applications' AND policyname = 'master_apps_anon_insert') THEN
    CREATE POLICY "master_apps_anon_insert" ON master_applications FOR INSERT WITH CHECK (true);
  END IF;
END $$;

-- ═══ 3. subscribers: ensure anon insert policy ═══
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'subscribers' AND policyname = 'subscribers_anon_insert') THEN
    CREATE POLICY "subscribers_anon_insert" ON subscribers FOR INSERT WITH CHECK (true);
  END IF;
END $$;

-- ═══ 4. Seed data ═══
-- Approved skill submission
INSERT INTO extra_repos (full_name, is_active, status)
VALUES ('zhuyansen/ai-hotspot-dailyreport-skill', true, 'approved')
ON CONFLICT (full_name) DO UPDATE SET is_active = true, status = 'approved';

-- New Skills Master: abczsl520
INSERT INTO skill_masters (github, name, bio, tags, is_active)
VALUES ('abczsl520', 'abczsl520', 'Node.js架构规范/系统化调试/代码质量防线作者', '["nodejs","debugging","code-review","quality","game-dev"]', true)
ON CONFLICT (github) DO UPDATE SET name = EXCLUDED.name, bio = EXCLUDED.bio, tags = EXCLUDED.tags, is_active = true;

-- abczsl520's repos
INSERT INTO extra_repos (full_name, is_active, status) VALUES
  ('abczsl520/nodejs-project-arch', true, 'approved'),
  ('abczsl520/openclaw-memory-cn', true, 'approved'),
  ('abczsl520/debug-methodology', true, 'approved'),
  ('abczsl520/bug-audit-skill', true, 'approved'),
  ('abczsl520/codex-review', true, 'approved'),
  ('abczsl520/browser-use-skill', true, 'approved'),
  ('abczsl520/game-quality-gates', true, 'approved')
ON CONFLICT (full_name) DO UPDATE SET is_active = true, status = 'approved';
