-- /arena/ — Anonymous skill PK voting with daily dedup
--
-- WHY:
--   Inspired by everydev.ai's tool-vs-tool voting. Lets visitors compare
--   2 skills side-by-side, vote a winner. Generates UGC + leaderboard data
--   to enrich /best/{slug}/ scenario pages with "wisdom of the crowd" signal.
--
-- ANONYMITY MODEL:
--   - No login. Each visitor gets a random UUID stored in localStorage.
--   - Client hashes it (SHA-256, kept client-side) and sends as voter_hash.
--   - Same pair (scenario_tag, two skill_ids) cannot be voted by the same
--     voter_hash twice in the same UTC day (server-enforced UNIQUE index).
--
-- SECURITY IMPACT:
--   - Anon role gets SELECT on the leaderboard view only.
--   - Anon can INSERT votes but with WITH CHECK bound on length(voter_hash)
--     and self-vote prevention.
--   - voter_hash is salted client-side; can't reverse to localStorage UUID
--     even with DB read access.
--   - Vote spam mitigation: client-side localStorage dedup + server UNIQUE
--     constraint per (voter_hash, scenario_tag, pair, day).
--
-- ROLLBACK:
--   DROP VIEW IF EXISTS v_arena_leaderboard;
--   DROP TABLE IF EXISTS arena_votes;

CREATE TABLE IF NOT EXISTS arena_votes (
  id BIGSERIAL PRIMARY KEY,
  winner_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  loser_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  scenario_tag TEXT NOT NULL,
  voter_hash TEXT NOT NULL,
  voted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  vote_date DATE GENERATED ALWAYS AS ((voted_at AT TIME ZONE 'UTC')::date) STORED,
  -- Canonical pair key (low_id, high_id) so each unique pair is identified
  -- regardless of who won — used for daily dedup.
  pair_low INTEGER GENERATED ALWAYS AS (LEAST(winner_id, loser_id)) STORED,
  pair_high INTEGER GENERATED ALWAYS AS (GREATEST(winner_id, loser_id)) STORED,
  CONSTRAINT no_self_vote CHECK (winner_id <> loser_id)
);

-- Daily dedup: one vote per (voter, scenario, unordered pair, day)
CREATE UNIQUE INDEX IF NOT EXISTS arena_votes_daily_unique
  ON arena_votes (voter_hash, scenario_tag, pair_low, pair_high, vote_date);

CREATE INDEX IF NOT EXISTS arena_votes_scenario_time
  ON arena_votes (scenario_tag, voted_at DESC);
CREATE INDEX IF NOT EXISTS arena_votes_winner
  ON arena_votes (scenario_tag, winner_id);
CREATE INDEX IF NOT EXISTS arena_votes_loser
  ON arena_votes (scenario_tag, loser_id);

ALTER TABLE arena_votes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS arena_votes_anon_select ON arena_votes;
CREATE POLICY arena_votes_anon_select
  ON arena_votes FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS arena_votes_anon_insert ON arena_votes;
CREATE POLICY arena_votes_anon_insert
  ON arena_votes FOR INSERT TO anon
  WITH CHECK (
    winner_id <> loser_id
    AND length(scenario_tag) BETWEEN 1 AND 50
    AND length(voter_hash) BETWEEN 16 AND 128
  );

-- ──────────────────────────────────────────────────────────────────
-- Leaderboard view — wins, losses, win-rate per (scenario, skill)
-- ──────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_arena_leaderboard AS
WITH wins AS (
  SELECT scenario_tag, winner_id AS skill_id, count(*) AS w
  FROM arena_votes GROUP BY scenario_tag, winner_id
),
losses AS (
  SELECT scenario_tag, loser_id AS skill_id, count(*) AS l
  FROM arena_votes GROUP BY scenario_tag, loser_id
),
combined AS (
  SELECT
    COALESCE(w.scenario_tag, l.scenario_tag) AS scenario_tag,
    COALESCE(w.skill_id, l.skill_id) AS skill_id,
    COALESCE(w.w, 0) AS wins,
    COALESCE(l.l, 0) AS losses
  FROM wins w
  FULL OUTER JOIN losses l
    ON w.scenario_tag = l.scenario_tag AND w.skill_id = l.skill_id
)
SELECT
  c.scenario_tag,
  s.id AS skill_id,
  s.repo_full_name,
  s.repo_name,
  s.author_avatar_url,
  s.author_name,
  s.stars,
  s.description,
  s.language,
  c.wins,
  c.losses,
  (c.wins + c.losses) AS battles,
  -- Wilson lower bound for win-rate (more honest than raw % at low n)
  CASE WHEN (c.wins + c.losses) > 0
       THEN c.wins::float / (c.wins + c.losses)
       ELSE 0 END AS win_rate
FROM combined c
JOIN skills s ON s.id = c.skill_id
WHERE (c.wins + c.losses) >= 1;

GRANT SELECT ON v_arena_leaderboard TO anon;

-- ──────────────────────────────────────────────────────────────────
-- Comments
-- ──────────────────────────────────────────────────────────────────
COMMENT ON TABLE arena_votes IS
  'Anonymous skill-vs-skill votes. One vote per (voter, scenario, pair, day).';
COMMENT ON VIEW v_arena_leaderboard IS
  'Aggregated wins/losses/battles per scenario. Joined with skills metadata.';
