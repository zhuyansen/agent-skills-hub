-- 026: the new-term radar remembers what it reported, so it can be checked later.
--
-- Why (2026-10-03): the radar (ops/radar, daily) posted a report and forgot it. Nobody
-- could say how many of its terms took off, or how many days before Google Trends it
-- saw them, so its thresholds could not be tuned on evidence. Each lead is now kept
-- here; 14 days after it was first seen, ops/radar/review.py checks its search terms in
-- Google Trends (DataForSEO via AIsa) and writes the verdict.
--
-- SECURITY IMPACT
-- - New table only. RLS on with no policy: anon and authenticated roles cannot read or
--   write it. The radar connects with SUPABASE_DB_URL (table owner), which bypasses RLS.
-- - No change to existing tables, policies, grants or keys.
--
-- Rollback: DROP TABLE public.radar_leads;

CREATE TABLE IF NOT EXISTS public.radar_leads (
  term         TEXT PRIMARY KEY,
  first_seen   DATE NOT NULL,
  last_seen    DATE NOT NULL,
  signals      TEXT[] NOT NULL DEFAULT '{}',   -- x, hf, breakout, github, sitemap
  notes        TEXT[] NOT NULL DEFAULT '{}',   -- the report lines that named it, latest last
  named        REAL,                           -- Jev's "is this a name" score, if it ran
  variants     TEXT[] NOT NULL DEFAULT '{}',   -- search terms to check; the term itself when empty
  reviewed_at  TIMESTAMPTZ,
  verdict      TEXT CHECK (verdict IN ('hit', 'miss', 'no_data')),
  lead_days    INTEGER,                        -- Trends' rise minus first_seen: > 0 = radar was early
  trends       JSONB                           -- per variant: base, peak, first_rise, rose
);

CREATE INDEX IF NOT EXISTS ix_radar_leads_due ON public.radar_leads (first_seen) WHERE reviewed_at IS NULL;

ALTER TABLE public.radar_leads ENABLE ROW LEVEL SECURITY;
