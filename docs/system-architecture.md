# Agent Skills Hub - System Architecture

> Complete data pipeline: Collection -> Cleaning -> Evaluation -> Presentation

## Overview

Agent Skills Hub is an automated platform that discovers, evaluates, and presents 6,000+ open-source Agent Skills from GitHub. The system runs a fully automated pipeline every 8 hours:

```
GitHub API ──> Data Collection ──> Data Cleaning ──> Quality Analysis ──> Scoring ──> Presentation
                (Phase 1-5)        (DataCleaner)    (6 dimensions)    (0-100)     (Web + API)
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, httpx |
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS v4 |
| **Database** | Supabase (PostgreSQL) + SQLite (local dev) |
| **Deployment** | GitHub Pages (frontend) + GitHub Actions (sync) |
| **Email** | Resend API + Supabase pg_net |
| **Search** | PostgreSQL Full-Text Search (tsvector/GIN) |

---

## 1. Data Collection

### 1.1 Search Strategy

**File**: `backend/app/scheduler/jobs.py`

The system uses a two-tier search strategy to discover Agent Skills on GitHub:

**Core Queries** (run every sync cycle):
```
mcp-server, claude-mcp, model-context-protocol,
mcp in:topics (Python), mcp in:topics (TypeScript),
claude-skill, claude-code in:topics, agent-skill, ai-agent-tool
```

**Extended Queries** (weekly full sync on Sundays):
```
mcp-plugin, codex-skills, llm-tool, ai-tools, youmind,
gemini-agent, function-calling, tool-use, ai-automation, ...
```

### 1.2 Collection Phases

The sync process (`sync_all_skills()`) runs in 6 phases:

| Phase | Description | API Budget |
|-------|-------------|------------|
| **Phase 1: Search** | Execute GitHub search queries with pagination (up to 3 pages/query) | ~30 calls |
| **Phase 2: Masters** | Fetch repos from known Skill Masters (e.g., op7418, joeseesun) | ~18 calls |
| **Phase 3: Extra Repos** | Fetch manually curated / community-submitted repos | ~14 calls |
| **Phase 4: Enrichment** | Fetch owner profiles for follower counts | max 500 calls |
| **Phase 5: README** | Fetch full README.md content (up to 50KB per repo) | max 300 calls |
| **Phase 6: Upsert** | Clean, score, and save to database | 0 calls |

### 1.3 Rate Limit Management

```python
# GitHub API Limits:
# - Core API: 5,000 requests/hour
# - Search API: 30 requests/minute

# Strategy: Smart wait - sleeps until actual reset time instead of failing
def _wait_for_rate_limit(headers):
    reset_ts = int(headers.get("X-RateLimit-Reset", 0))
    wait = max(reset_ts - time.time(), 0) + 5  # 5s safety buffer
    # Waits up to 61 minutes if needed
```

### 1.4 Incremental Sync

- **Weekdays**: Only fetches repos updated since last sync (`pushed:>TIMESTAMP`)
- **Sundays**: Full sync with all extended queries
- **Reduces API usage** by 60-80% on incremental runs

### 1.5 Sync Schedule

**File**: `.github/workflows/sync.yml`

```yaml
schedule:
  - cron: '0 */8 * * *'  # Every 8 hours
```

GitHub Actions runs `sync_runner.py` with a 120-minute timeout. On failure, an issue is automatically created with the `sync-failure` label.

---

## 2. Data Cleaning

### 2.1 Data Cleaner

**File**: `backend/app/services/data_cleaner.py`

`DataCleaner.process(raw_repos)` performs:

1. **Deduplication**: By `repo_full_name`
2. **Field Extraction & Normalization**:
   - Repository metadata: name, URL, description (max 500 chars)
   - Author info: username, avatar URL, followers
   - GitHub metrics: stars, forks, issues, commits, contributors
   - Timestamps: ISO 8601 parsing with timezone handling
   - Project metadata: language, topics (JSON), license, repo size

### 2.2 Category Classification

Keywords-based classification scans `repo_name + description + topics`:

| Category | Keywords |
|----------|----------|
| `mcp-server` | mcp, model-context-protocol, claude-mcp |
| `claude-skill` | claude-skill, claude-tool |
| `codex-skill` | codex, openai-codex |
| `agent-tool` | agent-tool, ai-agent, langchain-tool, crewai-tool |
| `ai-skill` | ai-skill, cursor-skill, windsurf-skill |
| `llm-plugin` | llm-tool, llm-plugin |
| `youmind-plugin` | youmind |

Fallback: `uncategorized`

### 2.3 Project Type Inference

**Function**: `_infer_project_type()`

Determines project type based on category + name + stars:
- **framework**: stars > 5,000 + framework keywords
- **skill**: name contains skill/agent keywords
- **tool**: default fallback

### 2.4 Size Categorization

| Category | Size |
|----------|------|
| micro | <= 50 KB |
| small | <= 500 KB |
| medium | <= 5,000 KB |
| large | > 5,000 KB |

---

## 3. Data Evaluation

### 3.1 Quality Analysis (6 Dimensions)

**File**: `backend/app/services/quality_analyzer.py`

Each skill is evaluated on 6 independent dimensions (0.0 - 1.0 each):

#### Dimension 1: Completeness (weight: 15%)
| Signal | Score |
|--------|-------|
| README > 5KB | +0.35 |
| README > 2KB | +0.25 |
| Description > 50 chars | +0.20 |
| License present | +0.15 |
| Homepage URL | +0.10 |
| Stars >= 100 | +0.20 |

#### Dimension 2: Clarity (weight: 15%)
| Signal | Score |
|--------|-------|
| Description 30-300 chars (optimal) | +0.25 |
| README > 3KB | +0.30 |
| Topics >= 3 | +0.20 |
| Clean repo name (hyphen/underscore) | +0.15 |
| Is not a fork | +0.10 |

#### Dimension 3: Specificity (weight: 15%)
| Signal | Score |
|--------|-------|
| Has primary language | +0.25 |
| 2-8 topics (optimal range) | +0.25 |
| Has category | +0.20 |
| Repo size 10-500KB (sweet spot) | +0.20 |
| Name contains skill/tool/mcp keywords | +0.10 |

#### Dimension 4: Examples (weight: 12%)
| Signal | Score |
|--------|-------|
| README > 5KB | +0.30 |
| Description mentions examples | +0.25 |
| Commits > 50 | +0.15 |
| Contributors > 3 | +0.15 |
| Topics mention examples | +0.15 |

#### Dimension 5: README Structure (weight: 23%)
| Signal | Score |
|--------|-------|
| Valuable sections (installation, usage, API, etc.) | +0.04 each (max 0.40) |
| Code blocks >= 3 | +0.25 |
| Badges present | +0.10 |
| Table of contents | +0.10 |
| Length >= 3KB | +0.15 |

**Valuable sections detected**: Installation, Usage, API, Configuration, Examples, Contributing, License, Changelog, Requirements, Features, Troubleshooting

#### Dimension 6: Agent Readiness (weight: 20%)
| Signal | Score |
|--------|-------|
| API/tools documentation | +0.20 |
| Configuration docs | +0.15 |
| Installation section | +0.15 |
| Description quality | +0.15 |
| Usage examples | +0.10 |
| Skill/MCP compliance markers | +0.10 |

### 3.2 Platform Inference

**File**: `backend/app/services/platform_inferrer.py`

Detects compatible platforms through 6 signals:

1. **Language mapping**: Python -> python, TypeScript -> node, Go -> go, Rust -> rust
2. **Topic keywords**: docker, kubernetes, aws, claude, mcp, vscode
3. **Description keywords**: CLI, browser, API
4. **Repo name keywords**: docker, cloud, etc.
5. **File hints**: `dockerfile`, `package.json`, `pyproject.toml`, `mcp.json`, `cargo.toml`
6. **Negation patterns**: "not compatible with X" (removes false positives)

**Supported Platforms**: python, node, go, rust, ruby, java, dotnet, cli, docker, k8s, aws, vscode, browser, claude-code, codex, gemini, mcp

### 3.3 Token Estimation

**File**: `backend/app/services/token_estimator.py`

Estimates LLM token count for each skill:

```
code_tokens = repo_size_kb * 150 * language_coefficient * (1 - binary_overhead)
readme_tokens = readme_chars * 0.25
estimated_tokens = code_tokens + readme_tokens
```

**Language coefficients**: Python: 0.8, TypeScript/JS: 1.0, Go: 0.87, Rust: 1.33, Java: 1.1

### 3.4 Composite Scoring

**File**: `backend/app/services/scorer.py`

`ScoringEngine.score_all()` computes a final 0-100 score using weighted signals:

| Signal | Weight | Normalization |
|--------|--------|---------------|
| Stars | 18% | log1p (compresses outliers) |
| Quality Score | 20% | Direct (0-100 -> 0-1) |
| Recency | 11% | Exponential decay: e^(-0.01 * age_days) |
| Forks | 10% | log1p |
| Commits | 10% | log1p |
| Issue Resolution | 10% | resolved_rate = (total - open) / total |
| Momentum | 8% | Z-score based: 0.5 + 0.25 * z |
| Author Followers | 8% | log1p |
| Size Bonus | 5% | micro: 1.0, small: 0.8, medium: 0.5, large: 0.2 |

**Key Design Decisions**:
- **Log normalization**: 100K stars is only ~2.3x more than 1K stars (reduces mega-repo dominance)
- **Recency decay**: 30 days old = 0.74, 90 days = 0.41, 365 days = 0.03 (favors active projects)
- **Size bonus rewards focused repos**: Small, well-scoped tools score higher than monoliths

### 3.5 Composability Analysis

**File**: `backend/app/services/composability.py`

Finds compatible skill pairs using 8 signals:

| Signal | Max Score |
|--------|-----------|
| TF-IDF semantic similarity | 0.25 |
| Complementarity (different categories) | 0.20 |
| Shared framework (langchain, crewai, etc.) | 0.20 |
| Shared rare topics | 0.15 |
| Same language | 0.10 |
| Similar popularity (star ratio <= 10x) | 0.10 |
| Shared platforms | 0.05 |
| Quality bonus (quality_score >= 50) | 0.05 |

**Threshold**: minimum 0.45 to be recommended. Max 5 recommendations per skill.

---

## 4. Data Presentation

### 4.1 API Layer

**Backend File**: `backend/app/api/routes.py`

#### Core Endpoints

| Endpoint | Description | Cache |
|----------|-------------|-------|
| `GET /api/skills` | Paginated list with search/filter/sort | 5 min |
| `GET /api/skills/{id}` | Skill detail + compatible skills | 5 min |
| `GET /api/stats` | Total count, avg score, categories | 1 hour |
| `GET /api/trending` | High star velocity (last 7 days) | 5 min |
| `GET /api/rising` | New repos this week, sorted by stars | 5 min |
| `GET /api/top-rated` | Highest scored (all-time) | 10 min |
| `GET /api/most-starred` | Community classics (6+ months, 100+ stars) | 10 min |
| `GET /api/recently-updated` | Latest commits | 5 min |
| `GET /api/masters` | Verified skill creators + organizations | 10 min |
| `GET /api/landing` | **Bundled**: single call for homepage data | 10 min |
| `GET /api/feed.xml` | RSS 2.0 feed | 5 min |
| `GET /api/sitemap.xml` | XML sitemap for SEO | 1 hour |

#### Community Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/submit-skill` | Submit GitHub repo URL |
| `POST /api/subscribe` | Newsletter signup + verification email |
| `GET /api/verify-email` | Email verification + welcome email |
| `GET /api/unsubscribe` | One-click unsubscribe |

### 4.2 Frontend Architecture

**Dual API Client**: `frontend/src/api/client.ts`

```
Production:  Supabase (PostgREST + RPCs) ──> Direct to database
Development: FastAPI backend ──> Python API ──> Database
```

Auto-switching logic: `USE_SUPABASE = !!supabase && !API_BASE`

### 4.3 Supabase Optimization

**File**: `frontend/src/api/supabaseClient.ts`

**Database Views** for common queries:
- `v_stats`, `v_categories`, `v_trending`, `v_rising`, `v_top_rated`
- `v_community_classics`, `v_recently_updated`, `v_language_stats`

**Server-side RPCs** for complex operations:
- `get_landing_data()` - Returns 7 datasets in 1 call (replaces 7+ API requests)
- `get_masters()` - Verified + organization builders with repo aggregation
- `send_verification_email()` - Uses pg_net to call Resend API

### 4.4 Full-Text Search

**Search Vector**: `search_vector tsvector` column with GIN index

```sql
-- Weight: repo_name(A) > author_name(B) > description(C) > topics(D)
to_tsvector('english',
  coalesce(repo_name, '') || ' ' ||
  coalesce(author_name, '') || ' ' ||
  coalesce(description, '') || ' ' ||
  coalesce(topics, '')
)
```

**Frontend Strategy**:
- Multi-word queries: PostgreSQL `websearch` mode via `.textSearch()`
- Single word/short queries: ILIKE fallback for fuzzy matching

### 4.5 Frontend Pages

| Page | Description |
|------|-------------|
| **Home** (`/`) | Landing page with stats, trending, masters, categories, workflows |
| **Explore** (`/?tab=explore`) | Full skill browser with filters and search |
| **Skill Detail** (`/skill/:owner/:repo`) | Individual skill page with metadata + compatible skills |
| **Verify Email** (`/verify-email`) | Email verification handler |
| **Admin** (`/admin`) | Dashboard for managing masters, repos, queries, subscribers |

### 4.6 Newsletter System

**Subscribe Flow**:
```
User enters email ──> Insert subscriber (unverified)
                  ──> send_verification_email RPC (pg_net -> Resend API)
                  ──> User clicks verify link
                  ──> Mark verified + send welcome email with trending skills
```

**Weekly Newsletter** (every Monday):
```
GitHub Actions ──> newsletter_runner.py
               ──> Query verified subscribers
               ──> Get new-this-week skills (created_at >= 7 days ago, ORDER BY stars)
               ──> Send via Resend API (per-recipient with unsubscribe token)
```

**File**: `backend/newsletter_runner.py` + `backend/app/services/email_service.py`

---

## 5. Database Schema

### Core Tables

```
skills (6,000+ rows)
├── Identity: id, repo_full_name (unique), repo_name, repo_url
├── Author: author_name, author_avatar_url, author_followers
├── GitHub Metrics: stars, forks, open_issues, watchers, total_commits
├── Timestamps: created_at, last_commit_at, pushed_at, first_seen, last_synced
├── Classification: category, language, topics[], license, project_type, size_category
├── Scoring: score (0-100), prev_stars, star_momentum
├── Quality: quality_completeness/clarity/specificity/examples/agent_readiness/score
├── Content: description, homepage_url, readme_content, readme_size
├── Analysis: platforms[], estimated_tokens, search_vector (tsvector)
└── Indexes: (category, score), (stars), (last_commit_at), (created_at), GIN(search_vector)
```

### Supporting Tables

```
skill_masters        → Verified skill creators (github, name, x_handle, bio, tags)
extra_repos          → Community-submitted repos (full_name, status: pending/approved/rejected)
search_queries       → Configurable GitHub search queries
subscribers          → Newsletter subscribers (email, verified, tokens)
master_applications  → Skill Master certification requests
sync_logs            → Sync history (status, repos_found, repos_new, errors)
skill_compositions   → Compatible skill pairs (skill_id, compatible_id, score, reason)
```

---

## 6. Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Actions                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ sync.yml     │  │ deploy.yml   │  │ newsletter.yml│  │
│  │ Every 8h     │  │ On push      │  │ Weekly Monday │  │
│  │ -> sync data │  │ -> build+push│  │ -> send emails│  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬────────┘  │
└─────────┼──────────────────┼──────────────────┼──────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Supabase        │  │ GitHub Pages │  │ Resend API       │
│ (PostgreSQL)    │  │ (Static SPA) │  │ (Email delivery) │
│                 │  │              │  │                  │
│ - PostgREST API │  │ - React app  │  │ - Verification   │
│ - RPCs          │  │ - Custom     │  │ - Welcome        │
│ - pg_net        │  │   domain     │  │ - Newsletter     │
│ - Views         │  │ - SSL/HTTPS  │  │                  │
└─────────────────┘  └──────────────┘  └──────────────────┘
```

### Key Configuration

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub API authentication (5000 req/hr) |
| `SUPABASE_DB_URL` | PostgreSQL connection (port 5432 direct, 6543 pooler) |
| `RESEND_API_KEY` | Email service API key |
| `ADMIN_TOKEN` | Admin API authentication |
| `SYNC_INTERVAL_HOURS` | Sync frequency (default: 8) |

---

## 7. Data Flow Diagram

```
                        ┌──────────────┐
                        │  GitHub API  │
                        └──────┬───────┘
                               │
                    ┌──────────▼──────────┐
                    │  Phase 1-5: Collect  │
                    │  (search + masters   │
                    │   + enrichment +     │
                    │   README fetch)      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼──────────┐
                    │   DataCleaner       │
                    │  - Deduplicate      │
                    │  - Normalize fields │
                    │  - Classify category│
                    │  - Infer type       │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Database Upsert    │
                    │  (batch size: 200)  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌──────▼───────┐ ┌──────▼──────┐
    │ QualityAnalyzer│ │PlatformInfer │ │TokenEstimate│
    │ (6 dimensions) │ │ (17 platforms)│ │ (LLM tokens)│
    └─────────┬──────┘ └──────┬───────┘ └──────┬──────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   ScoringEngine     │
                    │  (9 weighted signals │
                    │   -> 0-100 score)   │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼──────────┐
                    │ ComposabilityEngine │
                    │ (8 signals -> skill │
                    │  pair recommendations│
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌──────▼───────┐ ┌──────▼──────┐
    │  Supabase RPCs │ │   REST API   │ │  Newsletter  │
    │  (production)  │ │  (dev/admin) │ │  (weekly)    │
    └─────────┬──────┘ └──────┬───────┘ └──────┬──────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   React Frontend    │
                    │  (agentskillshub.top)│
                    └─────────────────────┘
```

---

## 8. Key Files Reference

| Stage | File | Key Functions |
|-------|------|---------------|
| **Collection** | `backend/app/scheduler/jobs.py` | `sync_all_skills()`, `_github_request()` |
| **Cleaning** | `backend/app/services/data_cleaner.py` | `DataCleaner.process()`, `_classify()` |
| **Quality** | `backend/app/services/quality_analyzer.py` | `QualityAnalyzer.analyze_all()` |
| **Platform** | `backend/app/services/platform_inferrer.py` | `PlatformInferrer.infer_all()` |
| **Tokens** | `backend/app/services/token_estimator.py` | `TokenEstimator.estimate_all()` |
| **Scoring** | `backend/app/services/scorer.py` | `ScoringEngine.score_all()` |
| **Composability** | `backend/app/services/composability.py` | `ComposabilityEngine.compute_all()` |
| **API Routes** | `backend/app/api/routes.py` | 30+ endpoint definitions |
| **Admin API** | `backend/app/api/admin_routes.py` | CRUD operations |
| **Models** | `backend/app/models/skill.py` | Table definitions + indexes |
| **Config** | `backend/app/config.py` | Environment settings |
| **Frontend API** | `frontend/src/api/client.ts` | Hybrid Supabase/FastAPI router |
| **Supabase Client** | `frontend/src/api/supabaseClient.ts` | PostgREST + RPC calls |
| **Email Service** | `backend/app/services/email_service.py` | Newsletter templates + Resend |
| **Sync Runner** | `backend/sync_runner.py` | CLI entry point for GitHub Actions |
| **Newsletter** | `backend/newsletter_runner.py` | Weekly newsletter sender |
| **Sync Workflow** | `.github/workflows/sync.yml` | Cron schedule + error handling |
| **Migrations** | `supabase/migrations/*.sql` | Schema evolution |

---

## 9. Performance Optimizations

1. **Incremental Sync**: Only fetches repos updated since last sync (60-80% API savings)
2. **Batch Upsert**: Inserts/updates in batches of 200 to avoid DB overload
3. **Smart Rate Limit**: Waits for actual GitHub reset time instead of failing
4. **Landing RPC**: Single Supabase call replaces 7+ frontend API requests
5. **Database Views**: Pre-defined views for common queries (trending, top-rated, etc.)
6. **Full-Text Search**: GIN-indexed tsvector for fast multi-word search
7. **HTTP Caching**: Cache-Control headers (1hr for stats, 5min for trending)
8. **Connection Pooling**: NullPool for Supabase PgBouncer compatibility
9. **TF-IDF Caching**: Pre-computed similarity matrix for composability
10. **README Truncation**: Max 50KB per README to limit storage and transfer

---

*Last updated: 2026-03-07*
