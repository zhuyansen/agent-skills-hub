# AgentSkillsHub

> Discover, evaluate, and compare 55,000+ open-source Agent Skills, MCP servers, and AI tools.

🌐 **Live**: [agentskillshub.top](https://agentskillshub.top) · 📰 [Newsletter](https://agentskillshub.top/#newsletter) · 𝕏 [Follow](https://x.com/GoSailGlobal)

## Architecture

```
GitHub API ──▸ Collection ──▸ Cleaning ──▸ Evaluation ──▸ Scoring ──▸ Presentation
               (6 phases)    (classify)   (6 dimensions)  (0-100)    (Web + API)
```

| Layer | Stack |
|-------|-------|
| Backend | Python 3.12 · FastAPI · SQLAlchemy · httpx |
| Frontend | React 18 · TypeScript · Vite · TailwindCSS v4 |
| Database | Supabase (PostgreSQL) / SQLite (local) |
| Deploy | GitHub Pages + GitHub Actions (every 8h) |
| Email | Resend API · Supabase pg_net |

## Data Pipeline

### 1. Collection (`scheduler/jobs.py`)

Every 8 hours, GitHub Actions triggers a 6-phase sync:

| Phase | What | Budget |
|-------|------|--------|
| Search | 10+ GitHub queries (mcp-server, claude-skill, agent-tool...) | ~30 |
| Masters | Fetch repos from verified skill creators | ~18 |
| Extra | Community-submitted + curated repos | ~14 |
| Enrich | Owner profiles (followers) | ≤500 |
| README | Full README content (≤50KB each) | ≤300 |
| Upsert | Clean → score → save | 0 |

- **Incremental sync** on weekdays (only new/updated repos), **full sync** on Sundays
- Smart rate-limit handling: waits for actual GitHub reset time

### 2. Cleaning (`services/data_cleaner.py`)

- Deduplication by `repo_full_name`
- Keyword-based category classification: `mcp-server` · `claude-skill` · `codex-skill` · `agent-tool` · `ai-skill` · `llm-plugin` · `youmind-plugin`
- Project type inference (framework / skill / tool)
- Size categorization (micro ≤50KB → large >5MB)

### 3. Evaluation

**Quality Analysis** — 6 dimensions (`services/quality_analyzer.py`):

| Dimension | Weight | Key Signals |
|-----------|--------|-------------|
| Completeness | 15% | README size, license, description, stars |
| Clarity | 15% | Description quality, topics, naming |
| Specificity | 15% | Language, topic count, category, size |
| Examples | 12% | Code examples, commits, contributors |
| README Structure | 23% | Sections, code blocks, badges, TOC |
| Agent Readiness | 20% | API docs, config, install, MCP compliance |

**Composite Score** — 9 weighted signals (`services/scorer.py`):

| Signal | Weight | Method |
|--------|--------|--------|
| Quality | 20% | 6-dimension aggregate |
| Stars | 18% | log₁₊ₓ normalization |
| Recency | 11% | Exponential decay e⁻⁰·⁰¹ᵈ |
| Forks | 10% | log₁₊ₓ |
| Commits | 10% | log₁₊ₓ |
| Issue Resolution | 10% | resolved / total |
| Momentum | 8% | Z-score star growth |
| Author Followers | 8% | log₁₊ₓ |
| Size Bonus | 5% | Smaller = higher |

Also: **Platform Inference** (17 platforms), **Token Estimation**, **Composability** (TF-IDF + 8-signal skill pairing).

### 4. Presentation

**Dual-mode API client**: Production uses Supabase PostgREST + RPCs directly; dev uses FastAPI backend.

Key optimizations:
- `get_landing_data()` RPC replaces 7+ API calls
- Database views: `v_trending`, `v_top_rated`, `v_rising`, etc.
- Full-text search via PostgreSQL tsvector + GIN index
- HTTP caching: 5min (trending) → 1hr (stats)

## Quick Start

### Backend

```bash
cd backend
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Add GITHUB_TOKEN
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/skills` | Paginated list (search, filter, sort) |
| GET | `/api/skills/{id}` | Skill detail + compatible skills |
| GET | `/api/trending` | Star velocity leaders (7 days) |
| GET | `/api/rising` | New this week |
| GET | `/api/top-rated` | Highest scored |
| GET | `/api/most-starred` | Community classics (6+ months) |
| GET | `/api/masters` | Verified creators + org builders |
| GET | `/api/landing` | Bundled homepage data |
| GET | `/api/stats` | Summary statistics |
| GET | `/api/feed.xml` | RSS 2.0 feed |
| GET | `/api/sitemap.xml` | SEO sitemap (6,000+ URLs) |
| POST | `/api/submit-skill` | Submit a GitHub repo |
| POST | `/api/subscribe` | Newsletter signup |

## Deployment

```
┌─────────── GitHub Actions ───────────┐
│  sync.yml (8h) · deploy.yml · newsletter.yml (Mon) │
└──────┬──────────────┬────────────────┬──┘
       ▼              ▼                ▼
   Supabase      GitHub Pages     Resend API
  (PostgreSQL)    (React SPA)     (Emails)
```

## Environment Variables

```bash
GITHUB_TOKEN=ghp_xxx          # GitHub API (required)
SUPABASE_DB_URL=postgresql://  # Production database
RESEND_API_KEY=re_xxx          # Email service
ADMIN_TOKEN=sk-xxx             # Admin API auth
SYNC_INTERVAL_HOURS=8          # Sync frequency
```

## Docs

- [Scoring Algorithm](docs/scoring-algorithm.md) — Full scoring design
- [System Architecture](docs/system-architecture.md) — Detailed pipeline reference
