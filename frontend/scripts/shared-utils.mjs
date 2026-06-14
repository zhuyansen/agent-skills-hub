/**
 * Shared utilities for build-time page generators.
 * Used by: generate-skill-pages.mjs, generate-scenario-pages.mjs
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

/** Strip Markdown syntax → plain text (no external deps) */
export function stripMarkdown(md) {
  if (!md) return "";
  return md
    .replace(/```[\s\S]*?```/g, "")            // fenced code blocks
    .replace(/`[^`\n]+`/g, "")                 // inline code
    .replace(/^#{1,6}\s+/gm, "")               // headings
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "")    // images
    .replace(/\[([^\]]*)\]\([^)]+\)/g, "$1")   // links → text
    .replace(/^\s*[-*+]\s+/gm, "")             // unordered list markers
    .replace(/^\s*\d+\.\s+/gm, "")             // ordered list markers
    .replace(/\|[^\n]*\|/g, "")                // table rows
    .replace(/<[^>]+>/g, "")                    // HTML tags
    .replace(/-{3,}/g, "")                      // horizontal rules
    .replace(/[*_~`>]/g, "")                    // bold/italic/strike markers
    .replace(/\n{2,}/g, " ")                    // collapse newlines
    .replace(/\s+/g, " ")                       // normalize whitespace
    .trim();
}

/** Truncate text to ~maxLen chars at word/sentence boundary */
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

/** Decide if a page should be indexed */
export function shouldIndex(skill) {
  if (skill.stars >= 50) return true;
  return false;
}

/** Minimum stars to generate a static page at all */
export const MIN_STARS_FOR_PAGE = 50;

/** Fetch all skills from Supabase (paginated) */
/**
 * Fetch all skills from Supabase with retry + threshold check.
 *
 * Why: 2026-05-04 and 2026-05-05 deploys silently shipped 0 scenarios
 * because Supabase returned a transient 500. Old code parsed the error
 * JSON, found `data.length === undefined`, broke out of the loop, and
 * returned an empty array. Sitemap then deployed with 0 URLs and all
 * /best/{slug}/ pages 404'd until manual redeploy.
 *
 * Fix: per-page retry (3x exponential backoff) + post-fetch threshold
 * check (skills.length >= MIN_EXPECTED_SKILLS). If fewer skills than
 * expected, throw → CI fails fast → no broken deploy.
 */
const MIN_EXPECTED_SKILLS = 5000;  // tighten as Hub grows; Hub is 70K+ as of 2026-05
// 6 retries with exponential backoff = up to ~63s of patience per page. The
// old 3 (~7s) gave up too soon when Supabase was briefly slow (e.g. warming
// after a restart, or autovacuum), failing the whole deploy on a transient
// 57014. Builds should ride out a slow DB, not abort.
const MAX_RETRIES = 6;

async function fetchPageWithRetry(url, headers, attempt = 1) {
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}: ${(await res.text()).slice(0, 200)}`);
    }
    const data = await res.json();
    if (!Array.isArray(data)) {
      throw new Error(`Expected array, got: ${JSON.stringify(data).slice(0, 200)}`);
    }
    return data;
  } catch (err) {
    if (attempt >= MAX_RETRIES) {
      throw new Error(`fetchPage failed after ${MAX_RETRIES} attempts: ${err.message}`);
    }
    const waitMs = 1000 * Math.pow(2, attempt - 1); // 1s, 2s, 4s
    console.warn(`  ⚠ fetch attempt ${attempt} failed (${err.message.slice(0, 80)}); retrying in ${waitMs}ms...`);
    await new Promise((r) => setTimeout(r, waitMs));
    return fetchPageWithRetry(url, headers, attempt + 1);
  }
}

export async function fetchAllSkills() {
  const skills = [];
  let lastId = 0;
  const limit = 1000;
  // NOTE: readme_content is deliberately NOT fetched here. It's a large TOASTed
  // column; pulling it for all 106K rows (especially after the README backfill
  // raised coverage to ~100%) made every keyset page exceed Supabase's
  // statement_timeout → 57014 → failed deploys. Generators that need readme
  // pull only the bounded high-star subset via fetchReadmeMap(minStars).
  const fields = [
    "id", "repo_full_name", "repo_name", "author_name", "author_avatar_url",
    "stars", "forks", "description", "category", "language", "score", "license",
    "last_commit_at", "created_at", "topics", "tags",
    "quality_score", "platforms", "star_momentum", "estimated_tokens",
    "open_issues", "total_commits",
  ].join(",");

  // Keyset pagination by primary key. Deep OFFSET (offset=77000&order=stars.desc)
  // forced Postgres to sort + skip ~77K rows on every page, exceeding Supabase's
  // statement_timeout → 57014 errors that blocked deploys. Ordering by the
  // indexed `id` PK turns each page into an O(limit) index range scan. No
  // consumer depends on fetch order — every generator re-sorts its own data.
  while (true) {
    const url = `${SUPABASE_URL}/rest/v1/skills?select=${fields}&order=id.asc&id=gt.${lastId}&limit=${limit}`;
    const data = await fetchPageWithRetry(url, {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    });
    if (!data.length) break;
    for (const row of data) {
      skills.push(row);
    }
    lastId = data[data.length - 1].id;
    if (data.length < limit) break;
  }

  // Threshold guard — fail fast in CI if Supabase returned suspiciously little
  if (skills.length < MIN_EXPECTED_SKILLS) {
    throw new Error(
      `fetchAllSkills returned only ${skills.length} skills (expected >= ${MIN_EXPECTED_SKILLS}). ` +
      `Likely Supabase transient failure. Refusing to deploy a broken sitemap. ` +
      `Re-run the workflow.`
    );
  }
  console.log(`  ✓ fetchAllSkills: ${skills.length} rows`);
  return skills;
}

/**
 * Fetch README excerpts (≤1500 chars) for skills with stars >= minStars.
 *
 * The heavy TOASTed readme_content column is kept OUT of fetchAllSkills so the
 * 106K-row catalog stays light. Only generators that render readme (skill +
 * scenario pages, both stars-gated) call this, and only for the bounded
 * high-star subset they actually display. Server-side stars + not-null filters
 * and a small page size keep each statement well under statement_timeout.
 *
 * Returns Map<id, readmeExcerpt>. Skills below the threshold (or without a
 * readme) are simply absent → callers degrade gracefully (no readme snippet).
 */
export async function fetchReadmeMap(minStars) {
  const map = new Map();
  let lastId = 0;
  const limit = 500; // readmes are large; smaller pages stay under the timeout
  while (true) {
    const url =
      `${SUPABASE_URL}/rest/v1/skills?select=id,readme_content` +
      `&stars=gte.${minStars}&readme_content=not.is.null` +
      `&order=id.asc&id=gt.${lastId}&limit=${limit}`;
    const data = await fetchPageWithRetry(url, {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    });
    if (!data.length) break;
    for (const row of data) {
      if (row.readme_content) map.set(row.id, row.readme_content.slice(0, 1500));
    }
    lastId = data[data.length - 1].id;
    if (data.length < limit) break;
  }
  console.log(`  ✓ fetchReadmeMap(stars>=${minStars}): ${map.size} readmes`);
  return map;
}
