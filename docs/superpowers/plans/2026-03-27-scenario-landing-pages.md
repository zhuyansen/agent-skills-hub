# Scenario Landing Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-generate 200+ long-tail scenario landing pages (`/best/{slug}/`) to capture "best AI tool for X" search traffic.

**Architecture:** Build-time static HTML generation (same pattern as existing `generate-skill-pages.mjs`). A JSON keyword bank defines scenarios with match rules. A new build script queries Supabase, matches skills per scenario, and outputs static HTML pages. Sitemap is extended to include scenario pages.

**Tech Stack:** Node.js (ESM), Supabase PostgREST API, static HTML (inline CSS), JSON-LD structured data.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/scripts/shared-utils.mjs` | CREATE | Shared utilities extracted from generate-skill-pages.mjs: `esc()`, `starsK()`, `formatDate()`, `stripMarkdown()`, `truncate()`, `fetchAllSkills()`, `extractAssetTags()`, `shouldIndex()`, Supabase constants |
| `frontend/scripts/scenario-keywords.json` | CREATE | Scenario word bank: slug, title, description, match rules, related scenarios |
| `frontend/scripts/generate-scenario-pages.mjs` | CREATE | Build-time generator: reads keywords, matches skills, outputs `/best/{slug}/index.html` |
| `frontend/scripts/generate-skill-pages.mjs` | MODIFY | Import shared utilities from `shared-utils.mjs` instead of inline definitions |
| `frontend/scripts/generate-sitemap.mjs` | MODIFY | Add `sitemap-scenarios.xml` to sitemap index |
| `frontend/package.json` | MODIFY | Add scenario generation step to build script |

---

### Task 1: Extract Shared Utilities

**Files:**
- Create: `frontend/scripts/shared-utils.mjs`
- Modify: `frontend/scripts/generate-skill-pages.mjs`

- [ ] **Step 1: Create shared-utils.mjs with extracted functions**

Create `frontend/scripts/shared-utils.mjs`:

```javascript
/**
 * Shared utilities for build-time page generators.
 */

export const SUPABASE_URL = "https://vknzzecmzsfmohglpfgm.supabase.co";
export const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo";
export const SITE = "https://agentskillshub.top";

export const CATEGORY_LABELS = {
  "mcp-server": "MCP Server",
  "claude-skill": "Claude Skill",
  "codex-skill": "Codex Skill",
  "agent-tool": "Agent Tool",
  "ai-skill": "AI Skill",
  "llm-plugin": "LLM Plugin",
  "youmind-plugin": "YouMind Plugin",
  "education": "Education",
  uncategorized: "AI Tool",
};

export function esc(s) {
  if (!s) return "";
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function starsK(n) {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);
}

export function formatDate(iso) {
  if (!iso) return "";
  return iso.split("T")[0];
}

export function stripMarkdown(md) {
  if (!md) return "";
  return md
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`[^`\n]+`/g, "")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "")
    .replace(/\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/\|[^\n]*\|/g, "")
    .replace(/<[^>]+>/g, "")
    .replace(/-{3,}/g, "")
    .replace(/[*_~`>]/g, "")
    .replace(/\n{2,}/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function truncate(text, maxLen = 600) {
  if (!text || text.length <= maxLen) return text || "";
  const sub = text.slice(0, maxLen);
  const sentEnd = sub.lastIndexOf(". ");
  if (sentEnd > maxLen * 0.5) return sub.slice(0, sentEnd + 1);
  const wordEnd = sub.lastIndexOf(" ");
  return wordEnd > 0 ? sub.slice(0, wordEnd) + "..." : sub + "...";
}

export function parseJsonArray(s) {
  if (!s) return [];
  try {
    const arr = JSON.parse(s);
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

export function extractAssetTags(html) {
  const scriptTags = [];
  const linkTags = [];
  for (const m of html.matchAll(/<script[^>]+src="[^"]*"[^>]*><\/script>/g)) {
    scriptTags.push(m[0]);
  }
  for (const m of html.matchAll(/<link[^>]+>/g)) {
    const tag = m[0];
    if (tag.includes("modulepreload") || tag.includes("stylesheet")) {
      linkTags.push(tag);
    }
  }
  return { scriptTags, linkTags };
}

export function shouldIndex(skill) {
  if (skill.stars >= 50) return true;
  if (skill.stars >= 20 && skill.readme_content && skill.readme_content.length > 100) return true;
  if (skill.stars >= 20 && skill.description && skill.description.length > 80) return true;
  return false;
}

export async function fetchAllSkills() {
  const skills = [];
  let offset = 0;
  const limit = 1000;
  const fields = [
    "id", "repo_full_name", "repo_name", "author_name", "author_avatar_url",
    "stars", "forks", "description", "category", "language", "score", "license",
    "readme_content", "last_commit_at", "created_at", "topics",
    "quality_score", "platforms", "star_momentum", "estimated_tokens",
    "open_issues", "total_commits",
  ].join(",");

  while (true) {
    const url = `${SUPABASE_URL}/rest/v1/skills?select=${fields}&order=stars.desc&offset=${offset}&limit=${limit}`;
    const res = await fetch(url, {
      headers: {
        apikey: SUPABASE_ANON_KEY,
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
      },
    });
    const data = await res.json();
    if (!data.length) break;
    for (const row of data) {
      if (row.readme_content) {
        row.readme_content = row.readme_content.slice(0, 1500);
      }
      skills.push(row);
    }
    offset += limit;
    if (data.length < limit) break;
  }
  return skills;
}
```

- [ ] **Step 2: Update generate-skill-pages.mjs to import from shared-utils**

Replace the top section of `frontend/scripts/generate-skill-pages.mjs` (lines 14-154, the constants + utility functions + fetchAllSkills) with imports:

```javascript
import {
  SUPABASE_URL, SUPABASE_ANON_KEY, SITE, CATEGORY_LABELS,
  esc, starsK, formatDate, stripMarkdown, truncate, parseJsonArray,
  extractAssetTags, shouldIndex, fetchAllSkills,
} from "./shared-utils.mjs";
```

Keep everything else (fetchAllCompositions, buildSkillHtml, buildCategoryHtml, main) unchanged.

- [ ] **Step 3: Verify build still works**

Run: `cd frontend && npm run build`

Expected: Build succeeds, same output as before. Check console for "Skill pages: X generated" and "Category pages: Y generated".

- [ ] **Step 4: Commit**

```bash
cd frontend
git add scripts/shared-utils.mjs scripts/generate-skill-pages.mjs
git commit -m "refactor: extract shared utilities from generate-skill-pages into shared-utils.mjs"
```

---

### Task 2: Create Scenario Keywords JSON

**Files:**
- Create: `frontend/scripts/scenario-keywords.json`

- [ ] **Step 1: Create the scenario keywords file**

Create `frontend/scripts/scenario-keywords.json` with initial 50+ scenarios. Each entry has:
- `slug`: URL path segment (lowercase, hyphenated)
- `title`: Human-readable name
- `description`: 1-2 sentence SEO description
- `match.categories`: array of category slugs to match
- `match.keywords`: array of keywords to match against description/repo_name/topics
- `match.min_results`: minimum skills needed to generate page (default 5)
- `match.max_results`: max skills to show (default 10)
- `related`: array of related scenario slugs for cross-linking

```json
[
  {
    "slug": "web-scraping",
    "title": "Web Scraping",
    "description": "Discover the best AI agent skills and MCP tools for web scraping, data extraction, and automated crawling from websites.",
    "match": {
      "categories": ["web-scraping", "crawler"],
      "keywords": ["scrape", "scraping", "crawl", "crawler", "spider", "selenium", "playwright", "puppeteer", "headless"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["browser-automation", "data-pipeline", "rss-monitoring"]
  },
  {
    "slug": "code-review",
    "title": "Code Review",
    "description": "Find the top AI-powered code review tools that help you catch bugs, enforce style, and improve code quality automatically.",
    "match": {
      "categories": ["code-review"],
      "keywords": ["code review", "code-review", "lint", "linter", "static analysis", "code quality", "review"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["test-generation", "code-completion", "debugging"]
  },
  {
    "slug": "mcp-database",
    "title": "MCP Database Tools",
    "description": "Browse the best MCP server tools for database access, SQL queries, and data management with AI agents.",
    "match": {
      "categories": ["mcp-server"],
      "keywords": ["database", "sql", "postgres", "mysql", "sqlite", "mongodb", "redis", "supabase", "prisma", "db"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["mcp-api", "data-pipeline", "mcp-filesystem"]
  },
  {
    "slug": "mcp-browser",
    "title": "MCP Browser Automation",
    "description": "Explore MCP tools that let AI agents control browsers, navigate pages, and automate web interactions.",
    "match": {
      "categories": ["mcp-server"],
      "keywords": ["browser", "chrome", "playwright", "puppeteer", "selenium", "web automation", "CDP", "headless"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["web-scraping", "browser-automation", "mcp-api"]
  },
  {
    "slug": "mcp-filesystem",
    "title": "MCP Filesystem Tools",
    "description": "Find MCP server tools for file management, directory operations, and local filesystem access from AI agents.",
    "match": {
      "categories": ["mcp-server"],
      "keywords": ["filesystem", "file", "directory", "folder", "path", "fs", "storage", "disk"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["mcp-database", "mcp-memory", "mcp-api"]
  },
  {
    "slug": "mcp-api",
    "title": "MCP API Integration",
    "description": "Discover MCP tools that connect AI agents to external APIs, REST endpoints, and third-party services.",
    "match": {
      "categories": ["mcp-server"],
      "keywords": ["api", "rest", "graphql", "http", "endpoint", "webhook", "integration", "openapi", "swagger"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["mcp-database", "mcp-browser", "workflow-automation"]
  },
  {
    "slug": "mcp-memory",
    "title": "MCP Memory & Knowledge",
    "description": "Browse MCP tools for persistent memory, knowledge graphs, and context management in AI agent workflows.",
    "match": {
      "categories": ["mcp-server"],
      "keywords": ["memory", "knowledge", "context", "graph", "rag", "embedding", "vector", "recall", "persistent"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["semantic-search", "vector-database", "mcp-database"]
  },
  {
    "slug": "test-generation",
    "title": "Test Generation",
    "description": "Find AI tools that automatically generate unit tests, integration tests, and test suites for your codebase.",
    "match": {
      "categories": [],
      "keywords": ["test generation", "test-generation", "unit test", "testing", "test suite", "tdd", "coverage", "jest", "pytest", "vitest"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["code-review", "debugging", "code-completion"]
  },
  {
    "slug": "code-completion",
    "title": "Code Completion & Generation",
    "description": "Discover AI-powered code completion and generation tools that help you write code faster with intelligent suggestions.",
    "match": {
      "categories": [],
      "keywords": ["code completion", "code generation", "copilot", "autocomplete", "code assist", "coding", "codegen"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["code-review", "test-generation", "refactoring"]
  },
  {
    "slug": "security-audit",
    "title": "Security Auditing",
    "description": "Find the best AI agent tools for security auditing, vulnerability scanning, and automated penetration testing.",
    "match": {
      "categories": [],
      "keywords": ["security", "audit", "vulnerability", "pentest", "penetration", "scan", "cve", "exploit", "devsecops", "sast", "dast"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["secret-detection", "vulnerability-scanning", "code-review"]
  },
  {
    "slug": "secret-detection",
    "title": "Secret Detection",
    "description": "Discover tools that detect leaked secrets, API keys, and credentials in your codebase before they cause security incidents.",
    "match": {
      "categories": [],
      "keywords": ["secret", "credential", "api key", "token", "password", "leak", "gitleaks", "trufflehog"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["security-audit", "vulnerability-scanning"]
  },
  {
    "slug": "content-writing",
    "title": "Content Writing",
    "description": "Find AI agent skills for automated content writing, blog generation, copywriting, and text creation.",
    "match": {
      "categories": [],
      "keywords": ["content", "writing", "blog", "article", "copywriting", "text generation", "markdown", "documentation"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["translation", "summarization", "document-parsing"]
  },
  {
    "slug": "translation",
    "title": "Translation",
    "description": "Explore AI translation tools and agent skills for multilingual content, i18n, and language conversion.",
    "match": {
      "categories": [],
      "keywords": ["translat", "i18n", "multilingual", "language", "localization", "l10n"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["content-writing", "summarization"]
  },
  {
    "slug": "summarization",
    "title": "Summarization",
    "description": "Find AI tools that automatically summarize documents, articles, code, and conversations.",
    "match": {
      "categories": [],
      "keywords": ["summariz", "summary", "digest", "tldr", "abstract", "condense"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["content-writing", "document-parsing", "translation"]
  },
  {
    "slug": "document-parsing",
    "title": "Document Parsing",
    "description": "Discover tools for parsing PDFs, Word documents, spreadsheets, and extracting structured data from unstructured files.",
    "match": {
      "categories": [],
      "keywords": ["document", "parsing", "pdf", "docx", "xlsx", "ocr", "extract", "parser", "markdown"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["content-writing", "summarization", "data-pipeline"]
  },
  {
    "slug": "workflow-automation",
    "title": "Workflow Automation",
    "description": "Find AI tools for automating repetitive workflows, task orchestration, and process management.",
    "match": {
      "categories": [],
      "keywords": ["workflow", "automation", "automate", "orchestrat", "pipeline", "scheduler", "cron", "task"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["ci-cd", "email-automation", "social-media"]
  },
  {
    "slug": "ci-cd",
    "title": "CI/CD & DevOps",
    "description": "Browse AI agent tools for continuous integration, deployment automation, and DevOps workflows.",
    "match": {
      "categories": [],
      "keywords": ["ci/cd", "cicd", "ci-cd", "deploy", "github actions", "devops", "pipeline", "build", "release"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["workflow-automation", "monitoring", "container-management"]
  },
  {
    "slug": "monitoring",
    "title": "Monitoring & Observability",
    "description": "Find AI tools for monitoring applications, logs, metrics, and system health with intelligent alerting.",
    "match": {
      "categories": [],
      "keywords": ["monitor", "observability", "alert", "metric", "log", "trace", "dashboard", "health"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["ci-cd", "debugging", "workflow-automation"]
  },
  {
    "slug": "semantic-search",
    "title": "Semantic Search",
    "description": "Discover AI-powered semantic search tools that understand meaning, not just keywords, for code and documents.",
    "match": {
      "categories": [],
      "keywords": ["semantic search", "vector search", "embedding", "similarity", "retrieval", "rag", "search engine"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["vector-database", "document-parsing", "mcp-memory"]
  },
  {
    "slug": "vector-database",
    "title": "Vector Database",
    "description": "Find vector database tools and integrations for storing and querying AI embeddings at scale.",
    "match": {
      "categories": [],
      "keywords": ["vector", "embedding", "pinecone", "weaviate", "qdrant", "chroma", "milvus", "faiss", "vector db"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["semantic-search", "mcp-memory", "mcp-database"]
  },
  {
    "slug": "browser-automation",
    "title": "Browser Automation",
    "description": "Explore tools for automated browser testing, web interaction, and UI automation with AI agents.",
    "match": {
      "categories": [],
      "keywords": ["browser", "automation", "playwright", "puppeteer", "selenium", "cypress", "e2e", "ui test"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["web-scraping", "mcp-browser", "test-generation"]
  },
  {
    "slug": "data-pipeline",
    "title": "Data Pipeline",
    "description": "Find AI tools for building data pipelines, ETL processes, and data transformation workflows.",
    "match": {
      "categories": [],
      "keywords": ["data pipeline", "etl", "data transform", "data processing", "batch", "stream", "ingest"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["web-scraping", "document-parsing", "mcp-database"]
  },
  {
    "slug": "rss-monitoring",
    "title": "RSS & Feed Monitoring",
    "description": "Discover tools for RSS feed monitoring, news aggregation, and content tracking with AI agents.",
    "match": {
      "categories": [],
      "keywords": ["rss", "feed", "news", "monitor", "aggregat", "atom", "syndication"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["web-scraping", "content-writing", "social-media"]
  },
  {
    "slug": "prompt-engineering",
    "title": "Prompt Engineering",
    "description": "Find tools for prompt design, testing, optimization, and management for LLM applications.",
    "match": {
      "categories": [],
      "keywords": ["prompt", "prompt engineering", "prompt template", "prompt management", "langchain", "llamaindex"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["model-evaluation", "content-writing", "code-completion"]
  },
  {
    "slug": "model-evaluation",
    "title": "Model Evaluation",
    "description": "Discover tools for evaluating, benchmarking, and comparing AI model performance and outputs.",
    "match": {
      "categories": [],
      "keywords": ["eval", "benchmark", "evaluat", "compare", "leaderboard", "quality", "accuracy", "metric"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["prompt-engineering", "test-generation"]
  },
  {
    "slug": "slack-integration",
    "title": "Slack Integration",
    "description": "Find AI agent tools that integrate with Slack for notifications, chatbots, and workflow automation.",
    "match": {
      "categories": [],
      "keywords": ["slack", "slack bot", "slack integration", "slack mcp"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["discord-bot", "notification", "workflow-automation"]
  },
  {
    "slug": "discord-bot",
    "title": "Discord Bot",
    "description": "Explore AI-powered Discord bot tools for community management, moderation, and automated responses.",
    "match": {
      "categories": [],
      "keywords": ["discord", "discord bot", "discord integration"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["slack-integration", "telegram-bot", "notification"]
  },
  {
    "slug": "telegram-bot",
    "title": "Telegram Bot",
    "description": "Find tools for building AI-powered Telegram bots with agent capabilities.",
    "match": {
      "categories": [],
      "keywords": ["telegram", "telegram bot", "telegram integration"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["discord-bot", "slack-integration", "notification"]
  },
  {
    "slug": "email-automation",
    "title": "Email Automation",
    "description": "Discover AI tools for email automation, inbox management, and intelligent email processing.",
    "match": {
      "categories": [],
      "keywords": ["email", "mail", "smtp", "inbox", "newsletter", "email automation"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["workflow-automation", "notification", "content-writing"]
  },
  {
    "slug": "social-media",
    "title": "Social Media Tools",
    "description": "Find AI tools for social media management, posting, analytics, and content scheduling.",
    "match": {
      "categories": [],
      "keywords": ["social media", "twitter", "x.com", "instagram", "linkedin", "social", "posting", "tweet"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["content-writing", "rss-monitoring", "email-automation"]
  },
  {
    "slug": "debugging",
    "title": "Debugging",
    "description": "Find AI-powered debugging tools that help identify, diagnose, and fix bugs in your code automatically.",
    "match": {
      "categories": [],
      "keywords": ["debug", "debugger", "troubleshoot", "error", "fix", "diagnos", "trace"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["code-review", "test-generation", "monitoring"]
  },
  {
    "slug": "refactoring",
    "title": "Code Refactoring",
    "description": "Discover AI tools for automated code refactoring, optimization, and architectural improvements.",
    "match": {
      "categories": [],
      "keywords": ["refactor", "restructur", "clean code", "optimize", "modernize", "migration"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["code-review", "code-completion", "debugging"]
  },
  {
    "slug": "container-management",
    "title": "Container & Docker Tools",
    "description": "Find AI tools for Docker container management, Kubernetes orchestration, and cloud infrastructure.",
    "match": {
      "categories": [],
      "keywords": ["docker", "container", "kubernetes", "k8s", "helm", "compose", "cloud", "infrastructure"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["ci-cd", "monitoring", "workflow-automation"]
  },
  {
    "slug": "git-tools",
    "title": "Git & Version Control",
    "description": "Explore AI tools for Git workflow automation, commit message generation, and version control management.",
    "match": {
      "categories": [],
      "keywords": ["git", "commit", "branch", "merge", "pull request", "version control", "github", "gitlab"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["code-review", "ci-cd", "workflow-automation"]
  },
  {
    "slug": "image-generation",
    "title": "Image Generation",
    "description": "Find AI image generation tools that create, edit, and manipulate images programmatically.",
    "match": {
      "categories": [],
      "keywords": ["image generation", "image", "dall-e", "stable diffusion", "midjourney", "generate image", "vision", "screenshot"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["content-writing", "document-parsing"]
  },
  {
    "slug": "notification",
    "title": "Notification & Alerting",
    "description": "Find tools for sending notifications, alerts, and messages across multiple channels from AI agents.",
    "match": {
      "categories": [],
      "keywords": ["notification", "alert", "notify", "push", "webhook", "message"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["slack-integration", "email-automation", "monitoring"]
  },
  {
    "slug": "cli-tools",
    "title": "CLI Tools",
    "description": "Discover command-line AI tools and terminal utilities for developers.",
    "match": {
      "categories": [],
      "keywords": ["cli", "command line", "terminal", "shell", "bash", "console"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["workflow-automation", "git-tools", "debugging"]
  },
  {
    "slug": "authentication",
    "title": "Authentication & Identity",
    "description": "Find AI agent tools for authentication, OAuth, SSO, and identity management.",
    "match": {
      "categories": [],
      "keywords": ["auth", "oauth", "sso", "login", "identity", "jwt", "token", "session"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["security-audit", "secret-detection", "mcp-api"]
  },
  {
    "slug": "data-visualization",
    "title": "Data Visualization",
    "description": "Explore AI tools for creating charts, dashboards, and visual representations of data.",
    "match": {
      "categories": [],
      "keywords": ["visualization", "chart", "graph", "dashboard", "plot", "d3", "recharts", "echarts"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["data-pipeline", "monitoring", "document-parsing"]
  },
  {
    "slug": "claude-code-skills",
    "title": "Claude Code Skills",
    "description": "Browse the best skills and extensions for Claude Code, Anthropic's AI coding assistant.",
    "match": {
      "categories": ["claude-skill"],
      "keywords": ["claude code", "claude skill", "claude extension", "anthropic"],
      "min_results": 5,
      "max_results": 10
    },
    "related": ["mcp-database", "mcp-browser", "code-completion"]
  },
  {
    "slug": "codex-skills",
    "title": "OpenAI Codex Skills",
    "description": "Find the best skills and plugins for OpenAI Codex, the AI coding agent.",
    "match": {
      "categories": ["codex-skill"],
      "keywords": ["codex", "openai", "codex skill", "codex plugin"],
      "min_results": 3,
      "max_results": 10
    },
    "related": ["claude-code-skills", "code-completion", "mcp-api"]
  }
]
```

- [ ] **Step 2: Commit**

```bash
cd frontend
git add scripts/scenario-keywords.json
git commit -m "feat: add scenario keywords bank (40 scenarios) for landing page generation"
```

---

### Task 3: Build Scenario Page Generator

**Files:**
- Create: `frontend/scripts/generate-scenario-pages.mjs`

- [ ] **Step 1: Create the generator script**

Create `frontend/scripts/generate-scenario-pages.mjs`:

```javascript
/**
 * Build-time scenario landing page generator.
 *
 * Generates static HTML pages at /best/{slug}/ for SEO long-tail traffic.
 * Reads scenario definitions from scenario-keywords.json, matches skills
 * from Supabase, and outputs static HTML with JSON-LD structured data.
 *
 * Run: node scripts/generate-scenario-pages.mjs  (after vite build)
 */

import { readFileSync, mkdirSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import {
  SITE, CATEGORY_LABELS,
  esc, starsK, stripMarkdown, truncate, parseJsonArray,
  extractAssetTags, shouldIndex, fetchAllSkills,
} from "./shared-utils.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DIST = "dist";

/* ── Skill matching ──────────────────────────────── */

function matchSkills(scenario, allSkills) {
  const { categories, keywords, min_results = 5, max_results = 10 } = scenario.match;

  const kwLower = keywords.map((k) => k.toLowerCase());

  const scored = [];
  for (const skill of allSkills) {
    if (!shouldIndex(skill)) continue;

    let matchScore = 0;

    // Category match (highest weight)
    if (categories.length > 0 && categories.includes(skill.category)) {
      matchScore += 10;
    }

    // Keyword matches in description
    const desc = (skill.description || "").toLowerCase();
    const name = (skill.repo_name || "").toLowerCase();
    const topics = parseJsonArray(skill.topics).map((t) => t.toLowerCase());
    const allText = `${desc} ${name} ${topics.join(" ")}`;

    for (const kw of kwLower) {
      if (allText.includes(kw)) {
        matchScore += 3;
      }
    }

    if (matchScore > 0) {
      // Boost by quality score
      const qualityBoost = (skill.score || 0) / 100;
      scored.push({ skill, matchScore: matchScore + qualityBoost });
    }
  }

  // Sort by matchScore desc, then by stars desc
  scored.sort((a, b) => b.matchScore - a.matchScore || b.skill.stars - a.skill.stars);

  const results = scored.slice(0, max_results).map((s) => s.skill);
  if (results.length < min_results) return null; // Not enough matches

  return results;
}

/* ── Quick Start extraction ──────────────────────── */

function extractQuickStart(readmeContent) {
  if (!readmeContent) return null;

  const patterns = [
    /## (?:Installation|Install|Getting Started|Quick Start|Setup)\s*\n([\s\S]*?)(?=\n## |\n$)/i,
    /## (?:Usage|How to Use|Examples?)\s*\n([\s\S]*?)(?=\n## |\n$)/i,
  ];

  for (const pat of patterns) {
    const match = readmeContent.match(pat);
    if (match && match[1].trim().length > 30) {
      const codeMatch = match[1].match(/```[\w]*\n([\s\S]*?)```/);
      const code = codeMatch ? codeMatch[0] : null;
      const text = stripMarkdown(match[1]).slice(0, 300);
      return { text, code };
    }
  }

  return null;
}

/* ── HTML builder ────────────────────────────────── */

function buildScenarioHtml(scenario, skills, assetTags, allScenarios) {
  const pageUrl = `${SITE}/best/${scenario.slug}/`;
  const year = new Date().getFullYear();
  const title = `Best ${skills.length} AI Tools for ${scenario.title} (${year}) | Agent Skills Hub`;
  const metaDesc = scenario.description;
  const ogImage = `${SITE}/og-image.png`;

  const { scriptTags, linkTags } = assetTags;

  // JSON-LD: ItemList
  const itemListLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: `Best AI Tools for ${scenario.title}`,
    description: scenario.description,
    url: pageUrl,
    numberOfItems: skills.length,
    itemListElement: skills.map((s, i) => ({
      "@type": "ListItem",
      position: i + 1,
      url: `${SITE}/skill/${s.repo_full_name}/`,
      name: s.repo_name,
      description: s.description || `${s.repo_name} by ${s.author_name}`,
    })),
  }, null, 2);

  // JSON-LD: BreadcrumbList
  const breadcrumbLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE },
      { "@type": "ListItem", position: 2, name: "Best Tools", item: `${SITE}/best/` },
      { "@type": "ListItem", position: 3, name: scenario.title, item: pageUrl },
    ],
  });

  // FAQ
  const faqItems = [
    {
      q: `What are the best AI tools for ${scenario.title.toLowerCase()}?`,
      a: `The top ${scenario.title.toLowerCase()} tools include ${skills.slice(0, 3).map((s) => s.repo_name).join(", ")}. These are ranked by our composite score based on GitHub stars, community activity, and code quality.`,
    },
    {
      q: `Are these ${scenario.title.toLowerCase()} tools free to use?`,
      a: `Most tools listed here are open-source. ${skills.filter((s) => s.license && s.license !== "NOASSERTION").length} out of ${skills.length} have explicit open-source licenses, making them free to use and modify.`,
    },
    {
      q: `How do I choose the right ${scenario.title.toLowerCase()} tool?`,
      a: `Consider your tech stack (language compatibility), project scale (stars indicate community trust), and specific features you need. Use the comparison table above to evaluate side by side.`,
    },
  ];

  const faqLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqItems.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  });

  // Skill cards HTML
  const skillCardsHtml = skills.map((s, i) => {
    const catLabel = CATEGORY_LABELS[s.category] || "AI Tool";
    const qs = extractQuickStart(s.readme_content);
    const qsHtml = qs
      ? `<div style="margin-top:8px;padding:8px 12px;background:#f8fafc;border-radius:6px;font-size:13px">
          <strong style="color:#334155">Quick Start:</strong>
          <span style="color:#475569"> ${esc(qs.text.slice(0, 150))}${qs.text.length > 150 ? "..." : ""}</span>
          ${qs.code ? `<pre style="margin:6px 0 0;padding:8px;background:#1e293b;color:#e2e8f0;border-radius:4px;overflow-x:auto;font-size:12px"><code>${esc(qs.code.slice(0, 300))}</code></pre>` : ""}
        </div>`
      : "";

    return `<div style="margin:16px 0;padding:16px 20px;border:1px solid #e2e8f0;border-radius:12px;background:#fff">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
          <div>
            <span style="display:inline-block;width:28px;height:28px;line-height:28px;text-align:center;border-radius:50%;background:${i < 3 ? "#f59e0b" : "#94a3b8"};color:#fff;font-weight:700;font-size:14px;margin-right:8px">${i + 1}</span>
            <a href="/skill/${esc(s.repo_full_name)}/" style="color:#1e293b;text-decoration:none;font-size:18px;font-weight:600">${esc(s.repo_name)}</a>
            <span style="color:#94a3b8;font-size:13px;margin-left:8px">by ${esc(s.author_name)}</span>
          </div>
          <div style="display:flex;gap:12px;font-size:14px;color:#64748b">
            <span>⭐ ${starsK(s.stars)}</span>
            ${s.language ? `<span>${esc(s.language)}</span>` : ""}
            <span style="color:#4f46e5;font-size:12px;padding:2px 8px;background:#f0f0ff;border-radius:8px">${esc(catLabel)}</span>
          </div>
        </div>
        <p style="margin:8px 0 0;color:#475569;line-height:1.5;font-size:14px">${esc(s.description || "")}</p>
        ${qsHtml}
        <div style="margin-top:10px;display:flex;gap:12px">
          <a href="/skill/${esc(s.repo_full_name)}/" style="color:#4f46e5;font-size:13px;text-decoration:none">View Details →</a>
          <a href="https://github.com/${esc(s.repo_full_name)}" style="color:#64748b;font-size:13px;text-decoration:none">GitHub →</a>
        </div>
      </div>`;
  }).join("\n      ");

  // Comparison table
  const compRows = skills.map((s) => {
    const catLabel = CATEGORY_LABELS[s.category] || "AI Tool";
    return `<tr style="border-bottom:1px solid #f1f5f9">
          <td style="padding:8px"><a href="/skill/${esc(s.repo_full_name)}/" style="color:#4f46e5;text-decoration:none;font-weight:500">${esc(s.repo_name)}</a></td>
          <td style="padding:8px;text-align:right">⭐ ${starsK(s.stars)}</td>
          <td style="padding:8px">${esc(s.language || "—")}</td>
          <td style="padding:8px">${esc(s.license && s.license !== "NOASSERTION" ? s.license : "—")}</td>
          <td style="padding:8px;text-align:right">${s.score ? Math.round(s.score) : "—"}</td>
        </tr>`;
  }).join("\n        ");

  // Related scenarios
  const relatedHtml = (scenario.related || [])
    .map((slug) => {
      const rel = allScenarios.find((s) => s.slug === slug);
      if (!rel) return null;
      return `<a href="/best/${esc(slug)}/" style="display:inline-block;padding:6px 14px;margin:4px;border-radius:20px;background:#f0f0ff;color:#4f46e5;font-size:13px;text-decoration:none;border:1px solid #e0e0ff">${esc(rel.title)}</a>`;
    })
    .filter(Boolean)
    .join("\n        ");

  // FAQ HTML
  const faqHtml = faqItems.map((f) => `<details style="margin:8px 0;border:1px solid #e2e8f0;border-radius:8px;padding:12px">
        <summary style="cursor:pointer;font-weight:500;color:#1e293b">${esc(f.q)}</summary>
        <p style="margin:8px 0 0;color:#475569;line-height:1.6">${esc(f.a)}</p>
      </details>`).join("\n      ");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(metaDesc)}" />
  <meta name="keywords" content="${esc(scenario.title)}, AI tools, agent skills, MCP tools, ${scenario.slug}" />

  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(metaDesc)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="${esc(pageUrl)}" />
  <meta property="og:site_name" content="Agent Skills Hub" />
  <meta property="og:image" content="${esc(ogImage)}" />

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${esc(title)}" />
  <meta name="twitter:description" content="${esc(metaDesc)}" />
  <meta name="twitter:site" content="@GoSailGlobal" />
  <meta name="twitter:image" content="${esc(ogImage)}" />

  <link rel="canonical" href="${esc(pageUrl)}" />

  <script type="application/ld+json">
${itemListLd}
  </script>
  <script type="application/ld+json">
${breadcrumbLd}
  </script>
  <script type="application/ld+json">
${faqLd}
  </script>

  <link rel="preconnect" href="https://vknzzecmzsfmohglpfgm.supabase.co" />
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com" />
  ${scriptTags.join("\n  ")}
  ${linkTags.join("\n  ")}
</head>
<body>
  <div id="root">
    <div style="max-width:900px;margin:40px auto;font-family:system-ui,-apple-system,sans-serif;padding:0 20px;color:#1e293b">
      <!-- Breadcrumb -->
      <nav style="font-size:13px;color:#64748b;margin-bottom:16px">
        <a href="/" style="color:#4f46e5;text-decoration:none">Home</a>
        <span style="margin:0 6px">&gt;</span>
        <span>Best Tools for ${esc(scenario.title)}</span>
      </nav>

      <!-- Title -->
      <h1 style="font-size:28px;margin:0 0 8px">Best AI Agent Skills for ${esc(scenario.title)}</h1>
      <p style="color:#64748b;margin:0 0 20px;line-height:1.6">${esc(scenario.description)}</p>

      <!-- Skill Cards -->
      <section>
        <h2 style="font-size:20px;margin:0 0 12px">Top ${skills.length} ${esc(scenario.title)} Tools</h2>
      ${skillCardsHtml}
      </section>

      <!-- Comparison Table -->
      <section style="margin-top:32px">
        <h2 style="font-size:20px;margin:0 0 12px">Comparison</h2>
        <div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:14px">
            <thead>
              <tr style="border-bottom:2px solid #e2e8f0;text-align:left">
                <th style="padding:8px;color:#64748b">Tool</th>
                <th style="padding:8px;color:#64748b;text-align:right">Stars</th>
                <th style="padding:8px;color:#64748b">Language</th>
                <th style="padding:8px;color:#64748b">License</th>
                <th style="padding:8px;color:#64748b;text-align:right">Score</th>
              </tr>
            </thead>
            <tbody>
        ${compRows}
            </tbody>
          </table>
        </div>
      </section>

      <!-- Related Scenarios -->
      ${relatedHtml ? `<section style="margin-top:32px">
        <h2 style="font-size:18px;margin:0 0 12px">Related Categories</h2>
        <div style="display:flex;flex-wrap:wrap;gap:4px">
        ${relatedHtml}
        </div>
      </section>` : ""}

      <!-- FAQ -->
      <section style="margin-top:32px">
        <h2 style="font-size:18px;margin:0 0 12px">Frequently Asked Questions</h2>
      ${faqHtml}
      </section>

      <!-- CTA -->
      <div style="margin:32px 0;text-align:center">
        <a href="/" style="display:inline-block;padding:10px 24px;background:#4f46e5;color:#fff;border-radius:8px;text-decoration:none;font-size:14px">Explore All ${skills.length > 1000 ? "25,000+" : "Skills"} on Agent Skills Hub</a>
      </div>
    </div>
  </div>
  <noscript>
    <p style="text-align:center;padding:20px">Enable JavaScript for the full interactive experience.</p>
  </noscript>
</body>
</html>`;
}

/* ── Main ────────────────────────────────────────── */

async function main() {
  console.log("=== Scenario Landing Page Generator ===\n");

  // Load scenario keywords
  const keywordsPath = join(__dirname, "scenario-keywords.json");
  if (!existsSync(keywordsPath)) {
    console.error("scenario-keywords.json not found!");
    process.exit(1);
  }
  const scenarios = JSON.parse(readFileSync(keywordsPath, "utf-8"));
  console.log(`Loaded ${scenarios.length} scenario definitions`);

  // Load asset tags from built index.html
  const indexHtml = readFileSync(join(DIST, "index.html"), "utf-8");
  const assetTags = extractAssetTags(indexHtml);

  // Fetch skills
  console.log("Fetching skills from Supabase...");
  const allSkills = await fetchAllSkills();
  console.log(`Fetched ${allSkills.length} skills`);

  // Generate pages
  let generated = 0;
  let skipped = 0;
  const t0 = Date.now();

  for (const scenario of scenarios) {
    const skills = matchSkills(scenario, allSkills);
    if (!skills) {
      console.log(`  SKIP ${scenario.slug}: fewer than ${scenario.match.min_results} matches`);
      skipped++;
      continue;
    }

    const dir = join(DIST, "best", scenario.slug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(
      join(dir, "index.html"),
      buildScenarioHtml(scenario, skills, assetTags, scenarios),
    );
    console.log(`  ✓ /best/${scenario.slug}/ (${skills.length} skills)`);
    generated++;
  }

  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`\nScenario pages: ${generated} generated, ${skipped} skipped (${elapsed}s)`);
}

main().catch((err) => {
  console.error("Failed to generate scenario pages:", err);
  process.exit(1);
});
```

- [ ] **Step 2: Test the generator standalone**

Run: `cd frontend && node scripts/generate-scenario-pages.mjs`

Expected: Output showing fetched skills count, then each scenario with ✓ or SKIP, and a summary like "Scenario pages: 30 generated, 10 skipped".

- [ ] **Step 3: Verify generated HTML**

Run: `ls dist/best/ | head -10` to confirm directories were created.
Run: `head -30 dist/best/web-scraping/index.html` to verify HTML structure.

- [ ] **Step 4: Commit**

```bash
cd frontend
git add scripts/generate-scenario-pages.mjs
git commit -m "feat: add scenario landing page generator for /best/{slug}/ SEO pages"
```

---

### Task 4: Update Sitemap to Include Scenario Pages

**Files:**
- Modify: `frontend/scripts/generate-sitemap.mjs`

- [ ] **Step 1: Add scenario sitemap generation**

In `frontend/scripts/generate-sitemap.mjs`, add after the category sitemap section (after line 143, `console.log(sitemap-categories.xml...)`):

```javascript
  // 3b. sitemap-scenarios.xml — scenario landing pages
  const { readdirSync } = await import("fs");
  const scenarioDir = "dist/best";
  let scenarioCount = 0;
  try {
    const scenarioSlugs = readdirSync(scenarioDir);
    const scenarioEntries = scenarioSlugs
      .filter((slug) => !slug.startsWith("."))
      .map((slug) => `  <url>
    <loc>${SITE}/best/${slug}/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.85</priority>
    <lastmod>${today}</lastmod>
  </url>`);
    writeFileSync("dist/sitemap-scenarios.xml", wrapUrlset(scenarioEntries));
    scenarioCount = scenarioEntries.length;
    console.log(`sitemap-scenarios.xml: ${scenarioCount} URLs`);
  } catch {
    console.log("sitemap-scenarios.xml: skipped (no dist/best/ directory)");
  }
```

- [ ] **Step 2: Add sitemap-scenarios.xml to sitemap index**

Update the `sitemapFiles` array to include the new sitemap (only if it was generated):

```javascript
  const sitemapFiles = [
    "sitemap-static.xml",
    "sitemap-categories.xml",
    "sitemap-top.xml",
    "sitemap-mid.xml",
    "sitemap-rest.xml",
  ];
  if (scenarioCount > 0) {
    sitemapFiles.push("sitemap-scenarios.xml");
  }
```

- [ ] **Step 3: Verify sitemap includes scenario URLs**

Run: `cd frontend && node scripts/generate-sitemap.mjs`

Expected: Console shows "sitemap-scenarios.xml: N URLs" and the sitemap index includes it.

- [ ] **Step 4: Commit**

```bash
cd frontend
git add scripts/generate-sitemap.mjs
git commit -m "feat: add sitemap-scenarios.xml for scenario landing pages"
```

---

### Task 5: Update Build Pipeline

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Update the build script**

In `frontend/package.json`, change the `build` script to include scenario generation. The order must be: vite build → skill pages → scenario pages → sitemap → indexnow.

```json
"build": "tsc -b && vite build && node scripts/generate-skill-pages.mjs && node scripts/generate-scenario-pages.mjs && node scripts/generate-sitemap.mjs && node scripts/submit-indexnow.mjs"
```

Note: `generate-scenario-pages.mjs` runs AFTER `generate-skill-pages.mjs` (both need `dist/index.html` for asset tags) and BEFORE `generate-sitemap.mjs` (so sitemap can discover the `/best/` directories).

- [ ] **Step 2: Run full build**

Run: `cd frontend && npm run build`

Expected: Build succeeds with all stages:
1. TypeScript compilation
2. Vite build
3. Skill pages generated (5000+ pages)
4. **Scenario pages generated (30+ pages)**
5. Sitemap generated (includes sitemap-scenarios.xml)
6. IndexNow submission

- [ ] **Step 3: Spot-check output**

Run: `ls dist/best/ | wc -l` — should be 30+
Run: `grep "sitemap-scenarios" dist/sitemap.xml` — should appear in index
Run: `grep "/best/" dist/sitemap-scenarios.xml | head -3` — should show scenario URLs

- [ ] **Step 4: Commit**

```bash
cd frontend
git add package.json
git commit -m "feat: integrate scenario page generation into build pipeline"
```

---

### Task 6: End-to-End Verification

- [ ] **Step 1: Clean build test**

```bash
cd frontend && rm -rf dist && npm run build
```

Expected: Full build succeeds from scratch.

- [ ] **Step 2: Verify page content quality**

Open `dist/best/web-scraping/index.html` in browser and check:
- H1 contains "Best AI Agent Skills for Web Scraping"
- Skill cards show ranked results with stars
- Comparison table renders correctly
- Related scenarios link to other `/best/` pages
- FAQ section has 3 items
- JSON-LD is valid (check with browser devtools)

- [ ] **Step 3: Verify no broken internal links**

```bash
# Check that skill links in scenario pages point to existing skill pages
grep -oh 'href="/skill/[^"]*"' dist/best/web-scraping/index.html | head -5
# Verify those paths exist
ls dist/skill/$(grep -oh 'href="/skill/[^"]*"' dist/best/web-scraping/index.html | head -1 | sed 's|href="/skill/||;s|/"||') 2>/dev/null
```

- [ ] **Step 4: Final commit with all files**

```bash
cd frontend
git add -A scripts/ package.json
git commit -m "feat: scenario landing pages — complete /best/{slug}/ SEO system

- Extract shared-utils.mjs from generate-skill-pages.mjs
- 40 scenario keywords with match rules
- Static HTML generator with JSON-LD, FAQ, comparison tables
- Sitemap integration (sitemap-scenarios.xml)
- Build pipeline: vite → skill pages → scenario pages → sitemap → indexnow"
```
