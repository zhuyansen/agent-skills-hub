-- ============================================================
-- V7.5 Schema Migration
-- Skills Master fix + Landing RPC + Full Text Search
-- ============================================================

-- ═══ 1. force_verified column for skill_masters ═══

ALTER TABLE skill_masters ADD COLUMN IF NOT EXISTS force_verified BOOLEAN DEFAULT FALSE;

-- Set force_verified for zarazhangrui and Panniantong (Neo)
UPDATE skill_masters SET force_verified = TRUE WHERE github IN ('zarazhangrui', 'Panniantong');

-- ═══ 2. Updated get_masters RPC with force_verified logic ═══

CREATE OR REPLACE FUNCTION get_masters()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'masters', COALESCE((
            SELECT json_agg(row_to_json(m))
            FROM (
                SELECT
                    sm.github,
                    sm.name,
                    sm.x_handle,
                    sm.bio,
                    sm.tags::json AS tags,
                    sm.github_aliases::json AS github_aliases,
                    sm.x_followers,
                    sm.x_posts_count,
                    sm.x_notes,
                    COALESCE(agg.total_stars, 0) AS total_stars,
                    COALESCE(agg.skill_count, 0) AS skill_count,
                    COALESCE(agg.avg_score, 0) AS avg_score,
                    TRUE AS is_verified
                FROM skill_masters sm
                LEFT JOIN LATERAL (
                    SELECT
                        SUM(s.stars) AS total_stars,
                        COUNT(*) AS skill_count,
                        ROUND(AVG(s.score)::numeric, 1) AS avg_score
                    FROM skills s
                    WHERE s.author_name = sm.github
                       OR s.author_name = ANY(
                            SELECT jsonb_array_elements_text(sm.github_aliases::jsonb)
                       )
                ) agg ON TRUE
                WHERE sm.is_active = TRUE
                  AND (sm.x_followers >= 1000 OR sm.force_verified = TRUE)
                ORDER BY sm.x_followers DESC
            ) m
        ), '[]'::json),
        'emerging', COALESCE((
            SELECT json_agg(row_to_json(e))
            FROM (
                SELECT
                    sm.github,
                    sm.name,
                    sm.x_handle,
                    sm.bio,
                    sm.tags::json AS tags,
                    sm.github_aliases::json AS github_aliases,
                    sm.x_followers,
                    sm.x_posts_count,
                    sm.x_notes,
                    COALESCE(agg.total_stars, 0) AS total_stars,
                    COALESCE(agg.skill_count, 0) AS skill_count,
                    COALESCE(agg.avg_score, 0) AS avg_score,
                    FALSE AS is_verified
                FROM skill_masters sm
                LEFT JOIN LATERAL (
                    SELECT
                        SUM(s.stars) AS total_stars,
                        COUNT(*) AS skill_count,
                        ROUND(AVG(s.score)::numeric, 1) AS avg_score
                    FROM skills s
                    WHERE s.author_name = sm.github
                       OR s.author_name = ANY(
                            SELECT jsonb_array_elements_text(sm.github_aliases::jsonb)
                       )
                ) agg ON TRUE
                WHERE sm.is_active = TRUE
                  AND sm.x_followers < 1000
                  AND (sm.force_verified IS NULL OR sm.force_verified = FALSE)
                ORDER BY COALESCE(agg.total_stars, 0) DESC
            ) e
        ), '[]'::json)
    ) INTO result;

    RETURN result;
END;
$$;

-- ═══ 3. master_applications SELECT RLS ═══

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'master_applications' AND policyname = 'master_apps_public_read') THEN
    CREATE POLICY "master_apps_public_read" ON master_applications FOR SELECT USING (true);
  END IF;
END $$;

-- ═══ 4. Landing page RPC (combines 7+ views into 1 call) ═══

CREATE OR REPLACE FUNCTION get_landing_data()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'stats', (SELECT row_to_json(v) FROM v_stats v LIMIT 1),
        'categories', COALESCE((SELECT json_agg(row_to_json(c)) FROM v_categories c), '[]'::json),
        'trending', COALESCE((SELECT json_agg(row_to_json(t)) FROM (SELECT * FROM v_trending LIMIT 10) t), '[]'::json),
        'rising', COALESCE((SELECT json_agg(row_to_json(r)) FROM (SELECT * FROM v_rising LIMIT 10) r), '[]'::json),
        'top_rated', COALESCE((SELECT json_agg(row_to_json(tr)) FROM (SELECT * FROM v_top_rated LIMIT 10) tr), '[]'::json),
        'hall_of_fame', COALESCE((SELECT json_agg(row_to_json(hf)) FROM (SELECT * FROM v_community_classics LIMIT 10) hf), '[]'::json),
        'recently_updated', COALESCE((SELECT json_agg(row_to_json(ru)) FROM (SELECT * FROM v_recently_updated LIMIT 10) ru), '[]'::json),
        'languages', COALESCE((SELECT json_agg(row_to_json(l)) FROM v_language_stats l), '[]'::json)
    ) INTO result;

    RETURN result;
END;
$$;

-- ═══ 5. Full Text Search ═══

ALTER TABLE skills ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE INDEX IF NOT EXISTS idx_skills_search_vector ON skills USING gin(search_vector);

-- Populate search_vector for existing rows
UPDATE skills SET search_vector =
    setweight(to_tsvector('english', COALESCE(repo_name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(author_name, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(description, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(topics, '')), 'D');

-- Auto-update trigger
CREATE OR REPLACE FUNCTION update_skills_search_vector()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.repo_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.author_name, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.topics, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_skills_search_vector ON skills;
CREATE TRIGGER trg_skills_search_vector
    BEFORE INSERT OR UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_skills_search_vector();
