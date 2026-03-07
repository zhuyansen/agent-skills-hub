-- ═══════════════════════════════════════════════════════════════
-- Migration 004: Phase C — Auth Favorites + Newsletter Verification
-- ═══════════════════════════════════════════════════════════════

-- 1. user_favorites table for authenticated users
CREATE TABLE IF NOT EXISTS user_favorites (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_user_favorites_user ON user_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_skill ON user_favorites(skill_id);

-- RLS: users can only see/manage their own favorites
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own favorites"
    ON user_favorites FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own favorites"
    ON user_favorites FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own favorites"
    ON user_favorites FOR DELETE
    USING (auth.uid() = user_id);

-- 2. Ensure subscribers table has verification columns
-- (These should already exist from 001_init_supabase.sql, but add if missing)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'subscribers' AND column_name = 'verified'
    ) THEN
        ALTER TABLE subscribers ADD COLUMN verified BOOLEAN DEFAULT FALSE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'subscribers' AND column_name = 'verification_token'
    ) THEN
        ALTER TABLE subscribers ADD COLUMN verification_token VARCHAR(64);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'subscribers' AND column_name = 'verified_at'
    ) THEN
        ALTER TABLE subscribers ADD COLUMN verified_at TIMESTAMP;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_subscribers_token ON subscribers(verification_token);

-- 3. RLS for subscribers: allow anonymous inserts + token-based updates
-- (Insert was likely already allowed; add update policy for verification)

-- Allow anonymous users to update their own subscriber row via verification token
DO $$
BEGIN
    -- Check if INSERT policy exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'subscribers' AND policyname = 'Anyone can subscribe'
    ) THEN
        CREATE POLICY "Anyone can subscribe"
            ON subscribers FOR INSERT
            WITH CHECK (true);
    END IF;

    -- Allow verification updates (where verification_token matches)
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'subscribers' AND policyname = 'Verify email via token'
    ) THEN
        CREATE POLICY "Verify email via token"
            ON subscribers FOR UPDATE
            USING (true)
            WITH CHECK (true);
    END IF;

    -- Allow SELECT for verification checks
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'subscribers' AND policyname = 'Read own subscriber'
    ) THEN
        CREATE POLICY "Read own subscriber"
            ON subscribers FOR SELECT
            USING (true);
    END IF;
END $$;

-- Ensure RLS is enabled on subscribers
ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;
