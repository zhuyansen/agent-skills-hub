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

/* ── Bilingual (zh/en) helpers for full-static SEO pages ──────────────────────
 * Static pages can't use the React i18n runtime, so they ship BOTH languages in
 * `data-en` / `data-zh` attributes and the header's toggle script swaps
 * `textContent`. Default visible text = English (html starts lang="en"). */

/** Attribute pair to drop onto an element whose inner text is the English copy:
 *  `<h2 ${biAttrs("Comparison", "对比")}>Comparison</h2>` */
export function biAttrs(en, zh) {
  return `data-en="${esc(en)}" data-zh="${esc(zh)}"`;
}

/** Self-contained bilingual element. `biSpan("Home", "首页")` →
 *  `<span data-en="Home" data-zh="首页">Home</span>`. Pass `tag`/`attrs` for
 *  headings, links, buttons, etc. */
export function biSpan(en, zh, { tag = "span", attrs = "" } = {}) {
  const a = attrs ? attrs + " " : "";
  return `<${tag} ${a}${biAttrs(en, zh)}>${esc(en)}</${tag}>`;
}

/** Shared bilingual page chrome (header + dark-mode + language toggle + the
 *  apply-saved-prefs script that swaps every [data-zh] node on load). Used by
 *  every full-static generator so the language button exists and works.
 *  `active` ∈ {"home","best",null} highlights the matching nav link. */
export function buildStaticHeader({ active = null } = {}) {
  const navActive = (key) =>
    active === key ? " bp-nav-link--active" : "";
  return `<header id="site-header" class="bp-header">
    <div class="bp-header-inner">
      <a href="/" style="display:flex;align-items:center;gap:8px;text-decoration:none">
        <svg style="width:24px;height:24px;color:#3b82f6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2" stroke-width="1.5"/><circle cx="9" cy="16" r="1.5" fill="currentColor"/><circle cx="15" cy="16" r="1.5" fill="currentColor"/><path d="M12 2v4M8 7h8a2 2 0 012 2v2H6V9a2 2 0 012-2z" stroke-width="1.5" stroke-linecap="round"/></svg>
        <span class="bp-brand">Agent Skills Hub</span>
      </a>
      <nav class="bp-nav-links">
        <a href="/" class="bp-nav-link${navActive("home")}" data-en="Home" data-zh="首页">Home</a>
        <a href="/best/" class="bp-nav-link${navActive("best")}" data-en="Best Tools" data-zh="最佳工具">Best Tools</a>
        <a href="https://github.com/ZhuYansen/agent-skills-hub" target="_blank" rel="noopener noreferrer" class="bp-nav-link" style="display:flex;align-items:center;gap:4px">
          <svg style="width:16px;height:16px" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
          GitHub
        </a>
        <span style="color:var(--bp-border);font-size:16px">|</span>
        <button id="theme-toggle" onclick="(function(){var d=document.documentElement,t=d.classList.toggle('dark');localStorage.setItem('theme',t?'dark':'light');document.getElementById('theme-icon-light').style.display=t?'none':'block';document.getElementById('theme-icon-dark').style.display=t?'block':'none'})()" class="bp-icon-btn" title="Toggle dark mode" style="display:flex;align-items:center">
          <svg id="theme-icon-light" style="width:16px;height:16px" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
          <svg id="theme-icon-dark" style="width:16px;height:16px;display:none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
        </button>
        <button id="lang-toggle" onclick="(function(){var c=document.documentElement.lang==='zh-CN'?'en':'zh';localStorage.setItem('lang',c);document.documentElement.lang=c==='zh'?'zh-CN':'en';document.querySelectorAll('[data-zh]').forEach(function(el){el.textContent=c==='zh'?el.getAttribute('data-zh'):el.getAttribute('data-en')});document.getElementById('lang-toggle').textContent=c==='zh'?'EN':'中文'})()" class="bp-icon-btn" style="font-size:12px;font-weight:600">中文</button>
      </nav>
    </div>
  </header>
  <script>
    (function(){
      var t=localStorage.getItem('theme');
      if(t!=='light'){
        document.documentElement.classList.add('dark');
        var il=document.getElementById('theme-icon-light');
        var id=document.getElementById('theme-icon-dark');
        if(il)il.style.display='none';
        if(id)id.style.display='block';
      }
      var l=localStorage.getItem('lang')||'en';
      document.documentElement.lang=l==='zh'?'zh-CN':'en';
      var lb=document.getElementById('lang-toggle');
      if(lb)lb.textContent=l==='zh'?'EN':'中文';
      document.querySelectorAll('[data-zh]').forEach(function(el){
        el.textContent=l==='zh'?el.getAttribute('data-zh'):el.getAttribute('data-en');
      });
    })();
  </script>`;
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
  // 300, not 1000: a 1000-row keyset page takes 3–8s when Supabase is slow
  // (warming after a restart, autovacuum, load) — right at the ~8s anon
  // statement_timeout, so pages intermittently 57014 and fail the deploy.
  // 300 rows stays ~2s even on a degraded instance. More round-trips, but the
  // build SURVIVES a slow DB instead of aborting. Keyset scan is O(limit) so
  // smaller pages aren't meaningfully more total work.
  const limit = 300;
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
    "open_issues", "total_commits", "security_grade",
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
  const limit = 200; // readmes are large; small pages stay well under the timeout
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
