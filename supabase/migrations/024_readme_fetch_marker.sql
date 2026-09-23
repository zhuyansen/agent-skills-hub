-- Grading coverage (docs/superpowers/specs/2026-09-23-grading-coverage-design.md).
--
-- readme_fetched_at — when a README fetch last got a definite answer from GitHub.
--   readme_content NULL                       → never fetched
--   readme_content ''  + readme_fetched_at    → GitHub had no README; retried after 30 days
--   readme_content text + readme_fetched_at   → fetched
-- Without it a repo with no README was re-fetched by every sync and backfill run, forever,
-- and every surface showed "not yet audited" for a repo that can never be audited.
--
-- security_scanned_at / scanner_version — when a row was last graded and by which rules
-- (sha256 of backend/app/services/security_scanner.py). grade_refresh.py uses them to
-- re-grade only rows whose inputs changed instead of all ~31K README'd rows every sync.
--
-- Additive: three nullable columns with no default, a metadata-only ALTER on 199K rows.
-- The 426 existing '' rows are deliberately left unstamped: some are ingestion artifacts
-- for repos that do have a README, so each is re-checked once by the backfill.
--
-- Security impact: none. Timestamps and a hash, readable through the existing
-- skills_public_read policy like every other skills column. RLS unchanged.

ALTER TABLE skills
  ADD COLUMN IF NOT EXISTS readme_fetched_at   timestamptz,
  ADD COLUMN IF NOT EXISTS security_scanned_at timestamptz,
  ADD COLUMN IF NOT EXISTS scanner_version     text;
