/**
 * generate-search-index.mjs
 *
 * Build-time generator for the CDN search index that powers the
 * AgentSkillsHub skill / CLI (`@agentskillshub` skill, `ash search`).
 *
 * WHY THIS EXISTS
 * ---------------
 * A distributed skill that queried Supabase directly on every search would
 * hammer the same fragile 106K-row table that already times out (57014) on
 * homepage aggregations. Instead we materialize a compact, quality-filtered
 * index at deploy time and serve it as a static file from the existing
 * GitHub Pages CDN. The CLI downloads it once, caches it locally, refreshes
 * every few hours, and searches *locally*. Result: zero Supabase load per
 * search, zero new infra, infinite scale (it's a static file).
 *
 * OUTPUTS (into frontend/dist/, the deploy artifact — like the sitemaps. dist/
 * is gitignored, so a 6MB JSON regenerated every deploy never bloats git.)
 *   - search-index.json      plain JSON (browsers / website fetch; the CDN
 *                             gzips it on the fly). Human-inspectable.
 *   - search-index.json.gz    pre-gzipped (the CLI fetches this for a
 *                             deterministic ~1.7MB transfer + Node gunzip).
 *   - search-index-meta.json  tiny: { v, generated_at, count, min_stars }.
 *                             The CLI GETs this first to decide if its cache
 *                             is stale before pulling the full index.
 *
 * Runs AFTER `vite build` (post-build, like generate-sitemap.mjs), so dist/
 * already exists. Standalone runs create dist/ if missing.
 *
 * SCHEMA  (compact keys to keep raw size + parse time down; gzip handles the
 *          rest). One object per skill:
 *   f  repo_full_name      "owner/repo"  (key — used for url + install)
 *   n  repo_name
 *   a  author_name
 *   s  stars
 *   d  description         (truncated to DESC_MAX chars)
 *   c  category
 *   p  platforms           string[]
 *   t  tags                string[]   (only the first TAGS_MAX)
 *   q  quality_score       0-100
 *   g  security_grade      "safe" | "caution" | "unsafe" | "reject" | "unknown"
 *   k  estimated_tokens
 *   o  is_official         0 | 1
 */

import { writeFileSync, mkdirSync, readFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { SUPABASE_URL, SUPABASE_ANON_KEY, parseJsonArray } from "./shared-utils.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Curated scenario definitions (English) + their Chinese titles/keywords. We use
// these to tag each indexed skill with the bilingual keywords of the scenarios it
// belongs to (field `kw`), so the CLI can match Chinese queries — most repo
// descriptions are English-only — and rank scenario-relevant skills higher.
const SCENARIOS = JSON.parse(
  readFileSync(join(__dirname, "scenario-keywords.json"), "utf-8"),
);
const SCENARIO_ZH = JSON.parse(
  readFileSync(join(__dirname, "scenario-zh.json"), "utf-8"),
);
const KW_MAX_SCENARIOS = 4; // cap scenarios merged per skill to bound index size

const SCENARIO_MATCHERS = SCENARIOS.map((s) => {
  const m = s.match || {};
  const zh = SCENARIO_ZH[s.slug] || {};
  return {
    cats: new Set(m.categories || []),
    tagMatches: (m.tag_matches || []).map((k) => k.toLowerCase()),
    keywords: [
      ...(m.primary_keywords || []),
      ...(m.secondary_keywords || []),
      ...(m.keywords || []),
    ].map((k) => k.toLowerCase()),
    // Keyword blob this scenario contributes: EN title + ZH title + ZH keywords.
    kw: [s.title, zh.t, ...(zh.k || [])].filter(Boolean).join(" "),
  };
});

/** Bilingual scenario keywords for the scenarios a skill belongs to. */
function scenarioKw(r) {
  const cat = r.category || "";
  const tags = (Array.isArray(r.tags) ? r.tags : parseJsonArray(r.tags)).map(
    (t) => String(t).toLowerCase(),
  );
  const text =
    `${r.repo_name || ""} ${r.description || ""} ${tags.join(" ")}`.toLowerCase();
  const hits = [];
  for (const sc of SCENARIO_MATCHERS) {
    const match =
      sc.cats.has(cat) ||
      sc.tagMatches.some((t) => tags.includes(t)) ||
      sc.keywords.some((k) => text.includes(k));
    if (match) {
      hits.push(sc.kw);
      if (hits.length >= KW_MAX_SCENARIOS) break;
    }
  }
  return hits.join(" ");
}

// Same convention as generate-sitemap.mjs: write into dist/ (cwd === frontend/
// during `npm run build`). dist/ is gitignored → no git bloat from the 6MB file.
const OUT_DIR = "dist";

// --- tunables ----------------------------------------------------------------
const MIN_STARS = 5; // quality floor: 0-star tail is abandoned/noise, never searched
const DESC_MAX = 160; // description char cap (keeps each row ~260B)
const TAGS_MAX = 6; // keep only the most relevant tags
const PAGE = 1000; // keyset page size
const MIN_EXPECTED = 8000; // CI guard: refuse to ship a suspiciously small index
const MAX_RETRIES = 3;
// -----------------------------------------------------------------------------

const FIELDS = [
  "id",
  "repo_full_name",
  "repo_name",
  "author_name",
  "stars",
  "description",
  "category",
  "platforms",
  "tags",
  "quality_score",
  "security_grade",
  "estimated_tokens",
  "is_official",
].join(",");

async function fetchPageWithRetry(url, attempt = 1) {
  try {
    const res = await fetch(url, {
      headers: { apikey: SUPABASE_ANON_KEY, Authorization: `Bearer ${SUPABASE_ANON_KEY}` },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${(await res.text()).slice(0, 160)}`);
    }
    const data = await res.json();
    if (!Array.isArray(data)) throw new Error(`Expected array, got ${JSON.stringify(data).slice(0, 160)}`);
    return data;
  } catch (err) {
    if (attempt >= MAX_RETRIES) throw new Error(`fetchPage failed after ${MAX_RETRIES}: ${err.message}`);
    const wait = 1000 * 2 ** (attempt - 1);
    console.warn(`  ⚠ attempt ${attempt} failed (${err.message.slice(0, 70)}); retry in ${wait}ms`);
    await new Promise((r) => setTimeout(r, wait));
    return fetchPageWithRetry(url, attempt + 1);
  }
}

function normTags(raw) {
  const arr = Array.isArray(raw) ? raw : parseJsonArray(raw);
  return arr.filter(Boolean).slice(0, TAGS_MAX);
}

function normPlatforms(raw) {
  const arr = Array.isArray(raw) ? raw : parseJsonArray(raw);
  return arr.filter(Boolean);
}

function truncDesc(d) {
  if (!d) return "";
  const s = d.replace(/\s+/g, " ").trim();
  return s.length <= DESC_MAX ? s : s.slice(0, DESC_MAX - 1).trimEnd() + "…";
}

function toRow(r) {
  return {
    f: r.repo_full_name,
    n: r.repo_name,
    a: r.author_name,
    s: r.stars ?? 0,
    d: truncDesc(r.description),
    c: r.category || "uncategorized",
    p: normPlatforms(r.platforms),
    t: normTags(r.tags),
    q: r.quality_score ?? 0,
    g: r.security_grade || "unknown",
    k: r.estimated_tokens ?? 0,
    o: r.is_official ? 1 : 0,
    w: scenarioKw(r), // bilingual scenario keywords (Chinese search + scenario boost)
  };
}

async function fetchIndexRows() {
  const rows = [];
  let lastId = 0;
  let scanned = 0;
  // Plain id-keyset, NO server-side filter — the exact query fetchAllSkills runs
  // reliably every deploy. Each page is an O(limit) PK index range scan that
  // never times out. A `stars=gte.5` filter, by contrast, made Postgres scan +
  // filter and intermittently hit statement_timeout (57014). We pull all ~106K
  // lightweight rows (no readme → far lighter than fetchAllSkills) and apply the
  // stars floor in JS. Reliability in the deploy path beats a smaller fetch.
  while (true) {
    const url =
      `${SUPABASE_URL}/rest/v1/skills?select=${FIELDS}` +
      `&order=id.asc&id=gt.${lastId}&limit=${PAGE}`;
    const data = await fetchPageWithRetry(url);
    if (!data.length) break;
    scanned += data.length;
    for (const r of data) {
      if (r.repo_full_name && (r.stars ?? 0) >= MIN_STARS) rows.push(toRow(r));
    }
    lastId = data[data.length - 1].id;
    if (data.length < PAGE) break;
  }
  console.log(`  · scanned ${scanned} rows → ${rows.length} pass stars >= ${MIN_STARS}`);
  return rows;
}

async function main() {
  console.log(`  → generating search index (stars >= ${MIN_STARS})…`);
  const skills = await fetchIndexRows();

  if (skills.length < MIN_EXPECTED) {
    throw new Error(
      `search index has only ${skills.length} rows (expected >= ${MIN_EXPECTED}). ` +
        `Likely a Supabase transient failure. Refusing to ship a broken index.`,
    );
  }

  // Stable, useful default order: stars desc. The CLI re-ranks per query anyway.
  skills.sort((a, b) => b.s - a.s);

  // Date.now() is fine in a build script (Node), unlike the workflow sandbox.
  const generated_at = new Date().toISOString();
  const meta = { v: 1, generated_at, count: skills.length, min_stars: MIN_STARS };
  const index = { ...meta, skills };

  const json = JSON.stringify(index);
  const gz = gzipSync(Buffer.from(json), { level: 9 });

  mkdirSync(OUT_DIR, { recursive: true }); // standalone runs may lack dist/
  writeFileSync(`${OUT_DIR}/search-index.json`, json);
  writeFileSync(`${OUT_DIR}/search-index.json.gz`, gz);
  writeFileSync(`${OUT_DIR}/search-index-meta.json`, JSON.stringify(meta));

  const mb = (n) => (n / 1024 / 1024).toFixed(2);
  console.log(
    `  ✓ search index: ${skills.length} skills · ` +
      `raw ${mb(json.length)}MB · gzip ${mb(gz.length)}MB`,
  );
}

main().catch((err) => {
  console.error("✗ generate-search-index failed:", err.message);
  process.exit(1);
});
