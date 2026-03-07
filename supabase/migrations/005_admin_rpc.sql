-- ============================================================
-- V8 Admin Panel — Supabase RPC Migration
-- Replaces 21 FastAPI admin endpoints with a single RPC router
-- ============================================================

-- ═══ 1. Admin config table (stores hashed admin token) ═══
CREATE TABLE IF NOT EXISTS admin_config (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
ALTER TABLE admin_config ENABLE ROW LEVEL SECURITY;
-- No public read — only SECURITY DEFINER functions can access
CREATE POLICY "admin_config_service_all" ON admin_config FOR ALL
  USING (auth.role() = 'service_role');

INSERT INTO admin_config (key, value)
VALUES ('admin_token', 'sk-admin-hub-2024')
ON CONFLICT (key) DO NOTHING;

-- ═══ 2. Token verifier (internal helper) ═══
CREATE OR REPLACE FUNCTION verify_admin_token(token TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM admin_config WHERE key = 'admin_token' AND value = token
  );
END;
$$;

-- ═══ 3. Admin action router ═══
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
      name            = COALESCE(payload->>'name', name),
      github_aliases  = COALESCE(payload->>'github_aliases', github_aliases),
      x_handle        = COALESCE(payload->>'x_handle', x_handle),
      bio             = COALESCE(payload->>'bio', bio),
      tags            = COALESCE(payload->>'tags', tags),
      is_active       = COALESCE((payload->>'is_active')::BOOLEAN, is_active),
      x_followers     = COALESCE((payload->>'x_followers')::INTEGER, x_followers),
      x_posts_count   = COALESCE((payload->>'x_posts_count')::INTEGER, x_posts_count),
      x_notes         = COALESCE(payload->>'x_notes', x_notes),
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

  ELSE
    RAISE EXCEPTION 'Unknown admin action: %', action;
  END IF;
END;
$$;

-- ═══ 4. Ensure extra_repos and search_queries have public read for admin listing ═══
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'extra_repos' AND policyname = 'extra_repos_public_read') THEN
    CREATE POLICY "extra_repos_public_read" ON extra_repos FOR SELECT USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'search_queries' AND policyname = 'queries_public_read') THEN
    CREATE POLICY "queries_public_read" ON search_queries FOR SELECT USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'master_applications' AND policyname = 'master_apps_service_all') THEN
    CREATE POLICY "master_apps_service_all" ON master_applications FOR ALL USING (auth.role() = 'service_role');
  END IF;
END $$;
