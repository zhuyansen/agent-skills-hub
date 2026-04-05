# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Dev Commands

```bash
# Frontend (React 19 + Vite, port 5173)
cd frontend && npm install && npm run dev

# Build (includes TypeScript check + sitemap + skill page generation)
cd frontend && npm run build

# Lint
cd frontend && npm run lint

# Backend (FastAPI, port 8000)
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Manual data sync
cd backend && python sync_runner.py

# Newsletter (only sends on Mondays; use --force for testing)
cd backend && python newsletter_runner.py --force
```

## Architecture

**Data flow**: GitHub API → `sync_runner.py` (6-phase collection) → Supabase PostgreSQL → Frontend SPA

**Dual-mode API client** (`frontend/src/api/client.ts`): Production uses Supabase PostgREST directly (no backend). When `VITE_API_BASE_URL` is set, falls back to FastAPI backend. The `supabaseClient.ts` has the actual query logic.

**Key RPC**: `get_landing_data()` in Supabase replaces 7+ API calls with a single round-trip for the homepage.

### Frontend (`frontend/`)
- React 19 + React Router 7 + Tailwind CSS 4 + Vite
- Pages: Home, SkillDetailPage, CategoryPage, ComparePage, VerifyEmailPage, Admin
- Dark mode: class-based via `@custom-variant dark (&:where(.dark, .dark *))` in `index.css`
- i18n: Chinese/English via `src/i18n/`
- SEO: Build-time sitemap generation (5 XML files) + pre-rendered skill pages via `scripts/`
- All category/skill URLs must use trailing slashes (GitHub Pages redirects without them → 301)

### Backend (`backend/`)
- FastAPI with SQLAlchemy 2.0, entry point: `app/main.py`
- Scheduler: `app/scheduler/jobs.py` → `sync_all_skills()` runs 6 phases (search, masters, extra repos, enrich, README fetch, upsert)
- Scoring: `app/services/scorer.py` (10 weighted signals → 0-100 composite score)
- Quality: `app/services/quality_analyzer.py` (6 dimensions: completeness, clarity, specificity, examples, readme_structure, agent_readiness)
- Email: `app/services/email_service.py` (Resend API, 1.2s delay between sends, 429 retry with backoff)

### Database (Supabase)
Core tables:
- `skills`: 25000+ repos with stars, score, category, quality metrics, readme_content
- `weekly_trending_snapshots`: weekly Top 20 by star_velocity (used for newsletter + Trending page)
- `skill_masters`: verified creators with GitHub + X profiles
- `subscribers`: newsletter (email verification via token)
- `extra_repos`: community-submitted repos (pending/approved/rejected)

Important: No `star_velocity` column on `skills` — compute as `(stars - prev_stars)`. The `first_seen` field = when skill was first indexed.

### CI/CD (`.github/workflows/`)
- `sync.yml`: Every 8 hours, runs `sync_runner.py` against Supabase
- `deploy.yml`: On push to main (or after sync), builds frontend and deploys to GitHub Pages
- `newsletter.yml`: Mondays 9:00 UTC, sends weekly trending email to verified subscribers

## Environment

Backend needs: `GITHUB_TOKEN`, `SUPABASE_DB_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `RESEND_API_KEY`, `EMAIL_FROM`, `SITE_URL`, `ADMIN_TOKEN`

Frontend needs: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (in `frontend/.env`)

GitHub Secrets mirror these for CI workflows.

## Conventions

- Supabase anon key is read-only (RLS). Writes require the service role key.
- Newsletter only sends to `verified=true AND is_active=true` subscribers.
- Sync is incremental on weekdays (`pushed:>LAST_SYNC_TIMESTAMP`), full on Sundays.
- Frontend build output goes to `frontend/dist/`, deployed via GitHub Pages with custom domain `agentskillshub.top`.
- Vite dev server proxies `/api` to `localhost:8000` (configured in `vite.config.ts`).

## Code Quality Red Lines

These are hard limits. Any PR or commit violating them must be fixed before merge.

### File & Function Size
- **Max file length**: 800 lines. If a file exceeds this, split into modules.
- **Max function length**: 20 lines (excluding blank lines and comments). Extract helpers.
- **Max indentation depth**: 3 levels. Use early returns, guard clauses, or extract functions.

### Code Smells Checklist
Before committing, verify zero occurrences of:
- [ ] `any` type in TypeScript (use proper types or generics)
- [ ] Magic numbers (extract to named constants)
- [ ] Hardcoded API keys or secrets (use env variables)
- [ ] `console.log` left in production code (use proper logging or remove)
- [ ] Duplicated logic blocks >5 lines (extract to shared utility)
- [ ] Deeply nested callbacks >2 levels (use async/await or extract)
- [ ] Unused imports or variables (run `npm run lint` to catch)
- [ ] Missing error handling on async operations (always try/catch or .catch())

### Naming Conventions
- Components: `PascalCase` (e.g., `SkillCard.tsx`)
- Utilities/hooks: `camelCase` (e.g., `useStats.ts`, `inferSubcategory.ts`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `OFFICIAL_ORGS`)
- CSS classes: `kebab-case` with `bp-` prefix for static pages

### Review Triggers
When modifying these critical files, require extra scrutiny:
- `supabaseClient.ts` — RLS bypass risk, query correctness
- `email_service.py` — rate limiting, subscriber privacy
- `sync_runner.py` — GitHub API quota, data integrity
- Any file in `supabase/migrations/` — irreversible schema changes
