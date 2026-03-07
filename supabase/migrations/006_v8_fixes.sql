-- ============================================================
-- V8 Fixes Migration
-- 1. JimLiu → dotey X handle mapping
-- 2. Fix avg_score to exclude score=0 items
-- 3. Ensure get_masters v7.5 version is active
-- 4. Community-submitted workflows table
-- ============================================================

-- ═══ 1. Fix JimLiu X handle → dotey ═══
UPDATE skill_masters SET x_handle = 'dotey' WHERE github = 'JimLiu';

-- ═══ 2. Fix v_stats avg_score (exclude score=0 items) ═══
CREATE OR REPLACE VIEW v_stats AS
SELECT
  COUNT(*)::INTEGER AS total_skills,
  COALESCE(ROUND(AVG(NULLIF(quality_score, 0))::NUMERIC, 1), 0)::DOUBLE PRECISION AS avg_score,
  COUNT(DISTINCT category)::INTEGER AS category_count,
  (SELECT started_at FROM sync_logs ORDER BY started_at DESC LIMIT 1) AS last_sync_at,
  (SELECT status FROM sync_logs ORDER BY started_at DESC LIMIT 1) AS last_sync_status
FROM skills;

-- ═══ 3. Ensure get_masters uses v7.5 version with force_verified ═══
-- (Re-apply from 003 in case it wasn't applied to production)
ALTER TABLE skill_masters ADD COLUMN IF NOT EXISTS force_verified BOOLEAN DEFAULT FALSE;

-- Ensure zarazhangrui and Panniantong are force_verified
UPDATE skill_masters SET force_verified = TRUE WHERE github IN ('zarazhangrui', 'Panniantong');

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
                        ROUND(AVG(NULLIF(s.score, 0))::numeric, 1) AS avg_score
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
                        ROUND(AVG(NULLIF(s.score, 0))::numeric, 1) AS avg_score
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

-- ═══ 4. Community-submitted workflows table ═══
CREATE TABLE IF NOT EXISTS submitted_workflows (
  id          SERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  description TEXT,
  steps       JSONB NOT NULL DEFAULT '[]'::jsonb,
  -- steps format: [{"name": "skill-name", "slug": "owner/repo", "description": "..."}]
  submitted_by TEXT DEFAULT 'community',
  status      TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
  reviewed_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE submitted_workflows ENABLE ROW LEVEL SECURITY;

-- Allow anyone to insert (community submissions)
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'submitted_workflows' AND policyname = 'workflows_public_insert') THEN
    CREATE POLICY "workflows_public_insert" ON submitted_workflows FOR INSERT WITH CHECK (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'submitted_workflows' AND policyname = 'workflows_service_all') THEN
    CREATE POLICY "workflows_service_all" ON submitted_workflows FOR ALL USING (auth.role() = 'service_role');
  END IF;
END $$;

-- ═══ 5. Update admin_action to support workflow management + expanded master edit ═══
CREATE OR REPLACE FUNCTION admin_action(
  admin_token TEXT,
  action      TEXT,
  payload     JSONB DEFAULT '{}'::jsonb
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSONB;
  v_id   BIGINT;
BEGIN
  -- Auth check
  IF NOT verify_admin_token(admin_token) THEN
    RAISE EXCEPTION 'Unauthorized: invalid admin token';
  END IF;

  v_id := (payload->>'id')::BIGINT;

  -- ════════════════════════════════════════════
  -- MASTERS
  -- ════════════════════════════════════════════
  IF action = 'fetch_masters' THEN
    SELECT COALESCE(jsonb_agg(row_to_json(m)::jsonb ORDER BY m.id), '[]'::jsonb)
    INTO result
    FROM skill_masters m;
    RETURN result;

  ELSIF action = 'create_master' THEN
    INSERT INTO skill_masters (github, name, github_aliases, x_handle, bio, tags)
    VALUES (
      payload->>'github',
      payload->>'name',
      COALESCE(payload->>'github_aliases', '[]'),
      payload->>'x_handle',
      payload->>'bio',
      COALESCE(payload->>'tags', '[]')
    )
    RETURNING row_to_json(skill_masters.*)::jsonb INTO result;
    RETURN result;

  ELSIF action = 'update_master' THEN
    UPDATE skill_masters SET
      name            = COALESCE(NULLIF(payload->>'name', ''), name),
      github_aliases  = COALESCE(NULLIF(payload->>'github_aliases', ''), github_aliases),
      x_handle        = CASE WHEN payload ? 'x_handle' THEN payload->>'x_handle' ELSE x_handle END,
      bio             = CASE WHEN payload ? 'bio' THEN payload->>'bio' ELSE bio END,
      tags            = COALESCE(NULLIF(payload->>'tags', ''), tags),
      is_active       = COALESCE((payload->>'is_active')::BOOLEAN, is_active),
      x_followers     = COALESCE((payload->>'x_followers')::INTEGER, x_followers),
      x_posts_count   = COALESCE((payload->>'x_posts_count')::INTEGER, x_posts_count),
      x_notes         = CASE WHEN payload ? 'x_notes' THEN payload->>'x_notes' ELSE x_notes END,
      force_verified  = COALESCE((payload->>'force_verified')::BOOLEAN, force_verified),
      updated_at      = NOW()
    WHERE id = v_id
    RETURNING row_to_json(skill_masters.*)::jsonb INTO result;
    RETURN COALESCE(result, '{"error":"not found"}'::jsonb);

  ELSIF action = 'delete_master' THEN
    DELETE FROM skill_masters WHERE id = v_id;
    RETURN jsonb_build_object('deleted', v_id);

  -- ════════════════════════════════════════════
  -- EXTRA REPOS
  -- ════════════════════════════════════════════
  ELSIF action = 'fetch_extra_repos' THEN
    SELECT COALESCE(jsonb_agg(row_to_json(r)::jsonb ORDER BY r.id DESC), '[]'::jsonb)
    INTO result
    FROM extra_repos r;
    RETURN result;

  ELSIF action = 'create_extra_repo' THEN
    INSERT INTO extra_repos (full_name, status, is_active)
    VALUES (payload->>'full_name', 'pending', TRUE)
    RETURNING row_to_json(extra_repos.*)::jsonb INTO result;
    RETURN result;

  ELSIF action = 'delete_extra_repo' THEN
    DELETE FROM extra_repos WHERE id = v_id;
    RETURN jsonb_build_object('deleted', v_id);

  ELSIF action = 'approve_extra_repo' THEN
    UPDATE extra_repos SET status = 'approved', is_active = TRUE, reviewed_at = NOW()
    WHERE id = v_id;
    RETURN jsonb_build_object('message', 'Approved');

  ELSIF action = 'reject_extra_repo' THEN
    UPDATE extra_repos SET status = 'rejected', is_active = FALSE, reviewed_at = NOW()
    WHERE id = v_id;
    RETURN jsonb_build_object('message', 'Rejected');

  -- ════════════════════════════════════════════
  -- SEARCH QUERIES
  -- ════════════════════════════════════════════
  ELSIF action = 'fetch_search_queries' THEN
    SELECT COALESCE(jsonb_agg(row_to_json(q)::jsonb ORDER BY q.id), '[]'::jsonb)
    INTO result
    FROM search_queries q;
    RETURN result;

  ELSIF action = 'create_search_query' THEN
    INSERT INTO search_queries (query)
    VALUES (payload->>'query')
    RETURNING row_to_json(search_queries.*)::jsonb INTO result;
    RETURN result;

  ELSIF action = 'delete_search_query' THEN
    DELETE FROM search_queries WHERE id = v_id;
    RETURN jsonb_build_object('deleted', v_id);

  -- ════════════════════════════════════════════
  -- SUBSCRIBERS
  -- ════════════════════════════════════════════
  ELSIF action = 'fetch_subscribers' THEN
    SELECT COALESCE(jsonb_agg(
      jsonb_build_object(
        'id', s.id,
        'email', s.email,
        'subscribed_at', s.subscribed_at,
        'is_active', s.is_active,
        'verified', COALESCE(s.verified, FALSE),
        'verified_at', s.verified_at
      ) ORDER BY s.id DESC
    ), '[]'::jsonb)
    INTO result
    FROM subscribers s;
    RETURN result;

  ELSIF action = 'delete_subscriber' THEN
    DELETE FROM subscribers WHERE id = v_id;
    RETURN jsonb_build_object('deleted', v_id);

  -- ════════════════════════════════════════════
  -- SYNC LOGS
  -- ════════════════════════════════════════════
  ELSIF action = 'fetch_sync_logs' THEN
    SELECT COALESCE(jsonb_agg(row_to_json(sl)::jsonb ORDER BY sl.started_at DESC), '[]'::jsonb)
    INTO result
    FROM sync_logs sl;
    RETURN result;

  ELSIF action = 'trigger_sync' THEN
    INSERT INTO sync_logs (status) VALUES ('pending')
    RETURNING jsonb_build_object('message', 'Sync queued', 'sync_id', id) INTO result;
    RETURN result;

  -- ════════════════════════════════════════════
  -- SKILLS
  -- ════════════════════════════════════════════
  ELSIF action = 'fetch_skills' THEN
    DECLARE
      v_page    INTEGER := COALESCE((payload->>'page')::INTEGER, 1);
      v_size    INTEGER := 50;
      v_search  TEXT    := payload->>'search';
      v_offset  INTEGER := (v_page - 1) * v_size;
    BEGIN
      IF v_search IS NOT NULL AND v_search <> '' THEN
        SELECT COALESCE(jsonb_agg(row_to_json(sk)::jsonb), '[]'::jsonb)
        INTO result
        FROM (
          SELECT id, repo_full_name, repo_name, repo_url, description,
                 author_name, author_avatar_url, category, stars, score,
                 language, last_commit_at
          FROM skills
          WHERE repo_name ILIKE '%' || v_search || '%'
             OR author_name ILIKE '%' || v_search || '%'
             OR description ILIKE '%' || v_search || '%'
          ORDER BY stars DESC
          LIMIT v_size OFFSET v_offset
        ) sk;
      ELSE
        SELECT COALESCE(jsonb_agg(row_to_json(sk)::jsonb), '[]'::jsonb)
        INTO result
        FROM (
          SELECT id, repo_full_name, repo_name, repo_url, description,
                 author_name, author_avatar_url, category, stars, score,
                 language, last_commit_at
          FROM skills
          ORDER BY stars DESC
          LIMIT v_size OFFSET v_offset
        ) sk;
      END IF;
      RETURN result;
    END;

  ELSIF action = 'delete_skill' THEN
    DELETE FROM skills WHERE id = v_id;
    DELETE FROM skill_compositions WHERE skill_id = v_id OR compatible_skill_id = v_id;
    RETURN jsonb_build_object('deleted', v_id);

  -- ════════════════════════════════════════════
  -- MASTER APPLICATIONS
  -- ════════════════════════════════════════════
  ELSIF action = 'fetch_master_applications' THEN
    SELECT COALESCE(jsonb_agg(row_to_json(ma)::jsonb ORDER BY ma.created_at DESC), '[]'::jsonb)
    INTO result
    FROM master_applications ma;
    RETURN result;

  ELSIF action = 'approve_master_application' THEN
    UPDATE master_applications SET status = 'approved' WHERE id = v_id;
    -- Auto-create master from application
    INSERT INTO skill_masters (github, name, bio, is_active)
    SELECT github, name, bio, TRUE
    FROM master_applications WHERE id = v_id
    ON CONFLICT (github) DO UPDATE SET is_active = TRUE, bio = EXCLUDED.bio;
    RETURN jsonb_build_object('message', 'Application approved and master created');

  ELSIF action = 'reject_master_application' THEN
    UPDATE master_applications SET status = 'rejected' WHERE id = v_id;
    RETURN jsonb_build_object('message', 'Application rejected');

  -- ════════════════════════════════════════════
  -- SUBMITTED WORKFLOWS
  -- ════════════════════════════════════════════
  ELSIF action = 'fetch_workflows' THEN
    SELECT COALESCE(jsonb_agg(row_to_json(w)::jsonb ORDER BY w.created_at DESC), '[]'::jsonb)
    INTO result
    FROM submitted_workflows w;
    RETURN result;

  ELSIF action = 'approve_workflow' THEN
    UPDATE submitted_workflows SET status = 'approved', reviewed_at = NOW()
    WHERE id = v_id;
    RETURN jsonb_build_object('message', 'Workflow approved');

  ELSIF action = 'reject_workflow' THEN
    UPDATE submitted_workflows SET status = 'rejected', reviewed_at = NOW()
    WHERE id = v_id;
    RETURN jsonb_build_object('message', 'Workflow rejected');

  ELSIF action = 'delete_workflow' THEN
    DELETE FROM submitted_workflows WHERE id = v_id;
    RETURN jsonb_build_object('deleted', v_id);

  ELSE
    RAISE EXCEPTION 'Unknown admin action: %', action;
  END IF;
END;
$$;

-- ═══ 6. Refresh get_landing_data to use corrected v_stats ═══
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

-- ═══ 7. Fix v_rising view (was incorrectly using star_momentum > 0) ═══
DROP VIEW IF EXISTS v_rising CASCADE;
CREATE OR REPLACE VIEW v_rising AS
SELECT *
FROM skills
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY stars DESC
LIMIT 20;

-- ═══ 8. Organization Builders RPC (aggregated from skills table) ═══
CREATE OR REPLACE FUNCTION get_org_builders()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
BEGIN
  SELECT COALESCE(json_agg(row_to_json(org)), '[]'::json)
  INTO result
  FROM (
    SELECT
      s.author_name AS github,
      s.author_name AS name,
      s.author_avatar_url AS avatar_url,
      COUNT(*) AS repo_count,
      SUM(s.stars) AS total_stars,
      json_agg(
        json_build_object(
          'id', s.id,
          'repo_name', s.repo_name,
          'repo_full_name', s.repo_full_name,
          'repo_url', s.repo_url,
          'description', COALESCE(s.description, ''),
          'stars', s.stars,
          'score', COALESCE(s.quality_score, 0),
          'category', s.category
        ) ORDER BY s.stars DESC
      ) AS top_repos
    FROM skills s
    WHERE s.author_name NOT IN (SELECT sm.github FROM skill_masters sm WHERE sm.is_active = TRUE)
      AND s.author_name NOT IN (
        SELECT jsonb_array_elements_text(sm.github_aliases::jsonb)
        FROM skill_masters sm WHERE sm.is_active = TRUE
      )
    GROUP BY s.author_name, s.author_avatar_url
    HAVING COUNT(*) >= 3 AND SUM(s.stars) >= 10000
    ORDER BY SUM(s.stars) DESC
    LIMIT 20
  ) org;

  RETURN result;
END;
$$;


-- ═══ 9. Enable pg_net + send_verification_email RPC (Resend integration) ═══

CREATE EXTENSION IF NOT EXISTS pg_net SCHEMA extensions;

CREATE OR REPLACE FUNCTION send_verification_email(p_email TEXT, p_token TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $func$
DECLARE
  verify_url TEXT;
  email_html TEXT;
  site_url TEXT := 'https://agentskillshub.top';
  request_id BIGINT;
BEGIN
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
    headers := '{"Authorization": "Bearer re_ZV7dTHfd_Ka52CSGn5Kg2uR4eY5MysANg", "Content-Type": "application/json"}'::jsonb
  ) INTO request_id;

  RAISE LOG 'Verification email queued for % (request_id: %)', p_email, request_id;
END;
$func$;
