# System Architecture — Deep Reference

> For overview, see [README.md](../README.md). This doc covers implementation details.

## Data Flow

```
GitHub API
    │
    ▼
Phase 1-5: Collect (scheduler/jobs.py)
    │  search → masters → extra_repos → enrich → README
    ▼
DataCleaner (services/data_cleaner.py)
    │  deduplicate → normalize → classify → infer type
    ▼
Database Upsert (batch: 200)
    │
    ├──▸ QualityAnalyzer (6 dims → quality_score)
    ├──▸ PlatformInferrer (17 platforms)
    ├──▸ TokenEstimator (LLM token count)
    ▼
ScoringEngine (9 signals → 0-100)
    │
    ▼
ComposabilityEngine (TF-IDF + 8 signals → skill pairs)
    │
    ├──▸ Supabase Views + RPCs (production)
    ├──▸ FastAPI REST (dev/admin)
    └──▸ Newsletter (weekly via Resend)
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/scheduler/jobs.py` | `sync_all_skills()` — 6-phase GitHub collection |
| `backend/app/services/data_cleaner.py` | Dedup, normalize, classify, type inference |
| `backend/app/services/quality_analyzer.py` | 6-dimension quality scoring |
| `backend/app/services/scorer.py` | Composite 0-100 scoring engine |
| `backend/app/services/platform_inferrer.py` | 17-platform detection |
| `backend/app/services/token_estimator.py` | LLM token estimation |
| `backend/app/services/composability.py` | TF-IDF skill compatibility |
| `backend/app/api/routes.py` | 30+ API endpoints |
| `backend/app/api/admin_routes.py` | Admin CRUD operations |
| `backend/app/models/skill.py` | Database schema + indexes |
| `backend/sync_runner.py` | GitHub Actions entry point |
| `backend/newsletter_runner.py` | Weekly newsletter sender |
| `frontend/src/api/client.ts` | Dual-mode API client (Supabase / FastAPI) |
| `frontend/src/api/supabaseClient.ts` | PostgREST queries + RPC calls |
| `.github/workflows/sync.yml` | 8h sync cron + error handling |

## Database Schema

```
skills (6,000+ rows)
├── Identity: id, repo_full_name (unique), repo_name, repo_url
├── Author: author_name, author_avatar_url, author_followers
├── Metrics: stars, forks, open_issues, watchers, total_commits
├── Time: created_at, last_commit_at, pushed_at, first_seen, last_synced
├── Class: category, language, topics[], license, project_type, size_category
├── Score: score (0-100), prev_stars, star_momentum
├── Quality: quality_{completeness,clarity,specificity,examples,agent_readiness,score}
├── Content: description, homepage_url, readme_content, readme_size
├── Analysis: platforms[], estimated_tokens, search_vector (tsvector)
└── Indexes: (category,score), (stars), (last_commit_at), (created_at), GIN(search_vector)

skill_masters      — Verified creators (github, x_handle, bio, tags)
extra_repos        — Community-submitted repos (status: pending/approved/rejected)
search_queries     — Configurable GitHub search queries
subscribers        — Newsletter (email, verified, tokens)
sync_logs          — Sync history (status, repos_found, repos_new)
skill_compositions — Compatible skill pairs (score, reason)
```

## Category Keywords

| Category | Match Keywords |
|----------|---------------|
| `mcp-server` | mcp, model-context-protocol, claude-mcp |
| `claude-skill` | claude-skill, claude-tool |
| `codex-skill` | codex, openai-codex |
| `agent-tool` | agent-tool, ai-agent, langchain-tool, crewai-tool |
| `ai-skill` | ai-skill, cursor-skill, windsurf-skill |
| `llm-plugin` | llm-tool, llm-plugin |
| `youmind-plugin` | youmind |

Scans: `repo_name + description + topics`. Fallback: `uncategorized`.

## Scoring Details

### Quality Dimensions (each 0.0 – 1.0)

**Composite weights (with README)**: completeness 15% · clarity 15% · specificity 15% · examples 12% · readme_structure 23% · agent_readiness 20%

**Without README**: equal 20% across 5 dimensions.

### Score Normalization

| Signal | Method |
|--------|--------|
| Stars, Forks, Commits, Followers | `log1p()` — compresses outliers |
| Recency | `e^(-0.01 × age_days)` — 30d=0.74, 90d=0.41, 365d=0.03 |
| Momentum | Z-score: `0.5 + 0.25 × z` |
| Issue Resolution | `(total - open) / total`, clamped [0,1] |
| Size Bonus | micro:1.0, small:0.8, medium:0.5, large:0.2 |

### Composability Signals

| Signal | Max |
|--------|-----|
| TF-IDF semantic similarity | 0.25 |
| Complementarity (cross-category) | 0.20 |
| Shared framework | 0.20 |
| Shared rare topics | 0.15 |
| Same language | 0.10 |
| Similar popularity | 0.10 |
| Shared platforms | 0.05 |
| Quality bonus | 0.05 |

Threshold: ≥0.45. Max 5 per skill.

## Sync Details

### Rate Limit Strategy

```
Core API: 5,000 req/hr    Search API: 30 req/min
Strategy: wait for actual reset time (up to 61 min)
Pre-flight budget check before starting each phase
```

### Incremental vs Full

- **Incremental** (weekdays): `pushed:>LAST_SYNC_TIMESTAMP` filter
- **Full** (Sundays): All core + extended queries
- API savings: 60-80% on incremental runs

### GitHub Actions

```yaml
# .github/workflows/sync.yml
schedule: '0 */8 * * *'    # Every 8 hours
timeout-minutes: 120        # Allows rate limit waiting
on-failure: create issue with 'sync-failure' label
```

## Newsletter Flow

```
Subscribe → insert subscriber (unverified) → send_verification_email RPC
         → pg_net → Resend API → user clicks verify link → verified=true

Weekly (Monday): newsletter_runner.py → query verified subscribers
              → new-this-week skills (created_at ≥ 7d, ORDER BY stars)
              → send via Resend (per-recipient, with unsubscribe token)
```

## Supabase Views & RPCs

**Views**: `v_stats` · `v_categories` · `v_trending` · `v_rising` · `v_top_rated` · `v_community_classics` · `v_recently_updated` · `v_language_stats`

**RPCs**: `get_landing_data()` (7-in-1) · `get_masters()` · `get_org_builders()` · `send_verification_email()` · `admin_action()`

## Performance

1. Incremental sync saves 60-80% API calls
2. `get_landing_data()` RPC replaces 7+ requests
3. Batch upsert (200 per batch)
4. GIN-indexed full-text search
5. HTTP Cache-Control: 5min → 1hr
6. NullPool for PgBouncer compatibility
7. README truncation at 50KB
