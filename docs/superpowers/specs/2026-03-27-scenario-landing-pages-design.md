# Scenario Landing Pages — SEO Discovery Engine (Phase 1)

**Date**: 2026-03-27
**Goal**: Auto-generate 200+ long-tail scenario landing pages to capture "best [tool] for [scenario]" search traffic.

## Context

Agent Skills Hub has 25K+ skills but GSC shows 1,071 discovered-but-not-indexed pages. Current SEO only covers individual skill pages. Missing: scenario-based aggregation pages that match user search intent like "best mcp tool for web scraping".

## Design

### URL Structure

```
/best/{scenario-slug}/     ← trailing slash required (GitHub Pages convention)
```

Examples:
- `/best/web-scraping/`
- `/best/code-review/`
- `/best/mcp-database/`

### Page Layout

```
┌──────────────────────────────────────────────┐
│ <h1> Best AI Agent Skills for {Scenario}     │
│ <p> AI-generated scenario description        │
│     (2-3 sentences, includes keyword)        │
├──────────────────────────────────────────────┤
│ Top {N} Skills (5-10 cards)                  │
│ ┌──────────────────────────────────────────┐ │
│ │ #1 {skill_name}              ⭐ {stars}  │ │
│ │ {description}                             │ │
│ │ Quick Start: {extracted from README}      │ │
│ │ → View Details  → GitHub                  │ │
│ └──────────────────────────────────────────┘ │
│ ... repeat for each skill ...                │
├──────────────────────────────────────────────┤
│ Comparison Table                             │
│ | Name | Stars | Language | License | Score |│
│ |------|-------|----------|---------|-------|│
├──────────────────────────────────────────────┤
│ Related Scenarios                            │
│ [Web Scraping] [API Testing] [Data Pipeline] │
├──────────────────────────────────────────────┤
│ FAQ (auto-generated, 3-4 items)              │
│ JSON-LD: ItemList + FAQPage                  │
└──────────────────────────────────────────────┘
```

### Scenario Keywords JSON

File: `frontend/scripts/scenario-keywords.json`

```json
[
  {
    "slug": "web-scraping",
    "title": "Web Scraping",
    "description": "Discover the best AI agent skills and MCP tools for web scraping, data extraction, and automated crawling.",
    "match": {
      "categories": ["web-scraping", "crawler"],
      "keywords": ["scrape", "crawl", "spider", "selenium", "playwright", "puppeteer"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["api-testing", "data-pipeline", "rss-monitoring"]
  }
]
```

Matching logic:
1. Category exact match (highest priority)
2. Keywords match against `description` + `repo_name` + `topics` (case-insensitive)
3. Results sorted by `score` descending
4. Skip scenario if fewer than `min_results` matches

### Initial Scenario Categories (~200)

Derived from 3 sources:
1. **Existing categories** in skills table (~30) → expand into sub-scenarios
2. **High-frequency keywords** from skill descriptions (automated extraction)
3. **Google autocomplete** suggestions for "mcp tool for *", "ai agent for *"

Top-priority scenarios (manual seed):

| Category | Scenarios |
|----------|-----------|
| Data | web-scraping, rss-monitoring, data-pipeline, database-tools, data-visualization |
| Code | code-review, test-generation, code-completion, refactoring, debugging |
| MCP | mcp-database, mcp-browser, mcp-filesystem, mcp-api, mcp-memory |
| Security | security-audit, vulnerability-scanning, secret-detection, penetration-testing |
| Content | content-writing, translation, summarization, document-parsing |
| DevOps | ci-cd, deployment, monitoring, logging, container-management |
| Search | semantic-search, knowledge-graph, document-retrieval, vector-database |
| Automation | workflow-automation, task-scheduling, email-automation, social-media |
| AI/ML | model-training, prompt-engineering, fine-tuning, evaluation, embedding |
| Communication | slack-integration, discord-bot, telegram-bot, notification |

### Quick Start Extraction

From `readme_content`, regex-based extraction at build time:

```javascript
function extractQuickStart(readmeContent) {
  if (!readmeContent) return null;

  // Try to find installation/usage sections
  const patterns = [
    /## (?:Installation|Install|Getting Started|Quick Start|Setup)\s*\n([\s\S]*?)(?=\n## |\n$)/i,
    /## (?:Usage|How to Use|Examples?)\s*\n([\s\S]*?)(?=\n## |\n$)/i,
  ];

  for (const pat of patterns) {
    const match = readmeContent.match(pat);
    if (match && match[1].trim().length > 30) {
      // Extract first code block if present
      const codeMatch = match[1].match(/```[\w]*\n([\s\S]*?)```/);
      const code = codeMatch ? codeMatch[0] : null;
      const text = stripMarkdown(match[1]).slice(0, 300);
      return { text, code };
    }
  }

  return null;
}
```

### SEO Elements Per Page

- `<title>`: `Best {N} AI Tools for {Scenario} (2026) | Agent Skills Hub`
- `<meta name="description">`: AI-generated, includes scenario keyword + tool count + top tool name
- `<link rel="canonical" href="https://agentskillshub.top/best/{slug}/">`
- `<meta name="robots" content="index, follow">`
- JSON-LD `ItemList` with `ListItem` entries for each skill
- JSON-LD `FAQPage` with 3-4 auto-generated Q&As
- Internal links: each skill → `/skill/{full_name}/`, related scenarios → `/best/{slug}/`

### FAQ Auto-Generation

```javascript
function generateFAQ(scenario, skills) {
  return [
    {
      q: `What are the best AI tools for ${scenario.title}?`,
      a: `The top ${scenario.title.toLowerCase()} tools include ${skills.slice(0,3).map(s=>s.repo_name).join(', ')}. These are ranked by our composite score based on GitHub stars, community activity, and code quality.`
    },
    {
      q: `Are these ${scenario.title.toLowerCase()} tools free to use?`,
      a: `Most tools listed here are open-source. ${skills.filter(s=>s.license&&s.license!=='NOASSERTION').length} out of ${skills.length} have explicit open-source licenses.`
    },
    {
      q: `How do I choose the right ${scenario.title.toLowerCase()} tool?`,
      a: `Consider your tech stack (language compatibility), project scale (stars indicate maturity), and specific features. Use our comparison table above to evaluate side by side.`
    }
  ];
}
```

## Integration With Existing Build Pipeline

### package.json build script

```
"build": "tsc -b && vite build && node scripts/generate-skill-pages.mjs && node scripts/generate-scenario-pages.mjs && node scripts/generate-sitemap.mjs && node scripts/submit-indexnow.mjs"
```

Order matters:
1. `vite build` → produces `dist/index.html` (asset tags needed)
2. `generate-skill-pages.mjs` → individual skill pages (existing)
3. `generate-scenario-pages.mjs` → **NEW**: scenario landing pages
4. `generate-sitemap.mjs` → updated to include `/best/*` URLs
5. `submit-indexnow.mjs` → pushes new URLs (no changes needed)

### Sitemap Changes (generate-sitemap.mjs)

Add new sub-sitemap `sitemap-scenarios.xml`:

```javascript
// After category sitemap generation, add:
const scenarioDir = join(DIST, "best");
if (existsSync(scenarioDir)) {
  const scenarioSlugs = readdirSync(scenarioDir);
  const scenarioEntries = scenarioSlugs.map(slug => `  <url>
    <loc>${SITE}/best/${slug}/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.85</priority>
    <lastmod>${today}</lastmod>
  </url>`);
  writeFileSync("dist/sitemap-scenarios.xml", wrapUrlset(scenarioEntries));
}

// Add to sitemap index:
sitemapFiles.push("sitemap-scenarios.xml");
```

### Router (React Router)

No SPA route needed — these are static HTML pages. GitHub Pages serves `best/{slug}/index.html` directly. Each page includes a link back to the SPA for the full interactive experience.

### Shared Code

Reuse from `generate-skill-pages.mjs`:
- `esc()`, `starsK()`, `formatDate()`, `stripMarkdown()`, `truncate()`
- `fetchAllSkills()` (same Supabase query)
- `extractAssetTags()` (same Vite asset injection)
- `shouldIndex()` (only include indexed skills in scenario results)

Extract these into a shared `scripts/shared-utils.mjs` module.

## File Summary

| File | Action | Purpose |
|------|--------|---------|
| `scripts/scenario-keywords.json` | NEW | Scenario word bank (slug + match rules) |
| `scripts/generate-scenario-pages.mjs` | NEW | Build-time scenario page generator |
| `scripts/shared-utils.mjs` | NEW | Shared utilities (esc, starsK, fetchAllSkills, etc.) |
| `scripts/generate-sitemap.mjs` | MODIFY | Add `sitemap-scenarios.xml` |
| `scripts/generate-skill-pages.mjs` | MODIFY | Import from shared-utils.mjs |
| `package.json` | MODIFY | Add scenario step to build script |
| `.github/workflows/deploy.yml` | NO CHANGE | Already runs `npm run build` |

## Out of Scope (Phase 2+)

- AI-generated scenario descriptions (Phase 1 uses templates)
- Question-answer recommendation UI
- Scenario tree navigation on SPA
- UGC reviews/ratings
- Programmatic keyword discovery via Google API

## Success Metrics

- GSC: scenario pages indexed within 2-4 weeks
- Search Console impressions for "best * for *" queries
- Click-through from scenario pages to skill detail pages
- Target: 50+ scenario pages indexed by week 4
