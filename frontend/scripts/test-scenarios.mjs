#!/usr/bin/env node
/**
 * test-scenarios.mjs — deterministic regression test for scenario search quality.
 *
 * WHY: scenario tagging precision (84 scenarios across ZH + EN queries) used to be
 * verified by hand, one `npx ... search "X"` at a time. This freezes that work into
 * a runnable pass/fail check so future edits to scenario-keywords.json /
 * scenario-zh.json can't silently regress.
 *
 * HOW: reuses the raw catalog snapshot from the already-built index
 * (dist/search-index.json.gz) for the 20K rows, but RE-DERIVES each row's scenario
 * tags (`w`) from the CURRENT JSON files in memory — so editing the JSONs and
 * re-running shows the effect WITHOUT regenerating from Supabase. The scenarioKw
 * scoring and the CLI scoreRow/tokenize ranking are replicated exactly.
 *
 * Four assertion layers:
 *   1. Distribution sanity  — no dead (0-row) or over-broad (>cap% of catalog) scenario
 *   2. Precision self-check — each scenario's canonical ZH query is reachable & on-topic
 *   3. Edge cases           — emoji-only no-match, latin/CJK tokenization, stopword-only
 *   4. Golden regressions   — specific fixed bugs stay fixed (must-include / must-exclude)
 *
 * Exit 1 if any HARD failure; WARN items are printed but don't fail the build.
 * Usage: node frontend/scripts/test-scenarios.mjs [--scenario <slug>] [--verbose]
 */

import { gunzipSync } from "node:zlib";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");

// ─── tunables (named, no magic numbers) ──────────────────────────────────────
const KW_MAX_SCENARIOS = 6; // must match generate-search-index.mjs
const OVERBROAD_PCT = 0.3; // a scenario tagging >30% of the catalog is too broad
const PRECISION_TOPK = 5; // how many top results to judge precision over
const PRECISION_MIN = 0.4; // <40% on-topic in top-K → WARN (noisy, not a hard fail)
const GOLDEN_TOPN = 8; // golden must-include/exclude judged over top-N results

const args = process.argv.slice(2);
const ONLY = args.includes("--scenario") ? args[args.indexOf("--scenario") + 1] : null;
const VERBOSE = args.includes("--verbose");

// ─── load catalog snapshot + current scenario JSONs ──────────────────────────
const INDEX_PATH = ["dist/search-index.json.gz", "public/search-index.json.gz"]
  .map((p) => join(ROOT, p))
  .find(existsSync);
if (!INDEX_PATH) {
  console.error("✗ no built index found (run `npm run build` first to produce dist/search-index.json.gz)");
  process.exit(2);
}
const INDEX = JSON.parse(gunzipSync(readFileSync(INDEX_PATH)).toString("utf8"));
const ROWS = INDEX.skills;
const SCENARIOS = JSON.parse(readFileSync(join(__dirname, "scenario-keywords.json"), "utf-8"));
const SCENARIO_ZH = JSON.parse(readFileSync(join(__dirname, "scenario-zh.json"), "utf-8"));

// ─── replicate generate-search-index.mjs scenario tagging ────────────────────
const MATCHERS = SCENARIOS.map((s) => {
  const m = s.match || {};
  const zh = SCENARIO_ZH[s.slug] || {};
  return {
    slug: s.slug,
    // Browse-facet scenarios (language/platform/meta groupings like
    // python-mcp-servers) are INTENTIONALLY broad SEO landing pages — they're
    // marked `"broad": true` in scenario-keywords.json and exempted from the
    // over-broad distribution check (the policy lives in data, not a threshold).
    broad: s.broad === true,
    cats: new Set(m.categories || []),
    tagMatches: (m.tag_matches || []).map((k) => k.toLowerCase()),
    primaryKw: (m.primary_keywords || []).map((k) => k.toLowerCase()),
    secondaryKw: [...(m.secondary_keywords || []), ...(m.keywords || [])].map((k) => k.toLowerCase()),
    excludeKw: (m.exclude_keywords || []).map((k) => k.toLowerCase()),
    kw: [zh.t, ...(zh.k || [])].filter(Boolean).join(" "),
  };
});
const MATCHER_BY_SLUG = new Map(MATCHERS.map((m) => [m.slug, m]));

/** Return the scenario slugs (strongest first, capped) a row matches — mirrors scenarioKw. */
function scenariosFor(row) {
  const cat = row.c || "";
  const tags = (Array.isArray(row.t) ? row.t : []).map((t) => String(t).toLowerCase());
  const text = `${row.n || ""} ${row.d || ""} ${tags.join(" ")}`.toLowerCase();
  const scored = [];
  for (const sc of MATCHERS) {
    if (sc.excludeKw.some((k) => text.includes(k))) continue;
    const tagHits = sc.tagMatches.filter((t) => tags.includes(t)).length;
    const primHits = sc.primaryKw.filter((k) => text.includes(k)).length;
    const secHits = sc.secondaryKw.filter((k) => text.includes(k)).length;
    if (tagHits + primHits + secHits === 0) continue;
    const score = (sc.cats.has(cat) ? 3 : 0) + tagHits * 3 + primHits * 3 + secHits;
    scored.push({ slug: sc.slug, score });
  }
  return scored.sort((a, b) => b.score - a.score).slice(0, KW_MAX_SCENARIOS).map((x) => x.slug);
}

// Re-derive `w` (joined scenario kw blob) per row from CURRENT JSONs, cache scenario slugs.
for (const row of ROWS) {
  const slugs = scenariosFor(row);
  row._scenarios = slugs;
  row.w = slugs.map((sg) => MATCHER_BY_SLUG.get(sg).kw).join(" ");
}

// ─── replicate CLI tokenize + scoreRow ───────────────────────────────────────
const CJK = /[一-鿿]/;
const STOPWORDS = new Set([
  "ai", "mcp", "mcps", "agent", "agents", "tool", "tools", "skill", "skills",
  "server", "servers", "app", "apps", "工具", "服务器", "服务",
]);
function tokenize(q) {
  return q
    .toLowerCase()
    .replace(/([a-z0-9])([一-鿿])/g, "$1 $2")
    .replace(/([一-鿿])([a-z0-9])/g, "$1 $2")
    .split(/\s+/)
    .filter(Boolean);
}
function scoreRow(row, tokens) {
  if (!tokens.length) return row.q || 0;
  const name = (row.n || "").toLowerCase();
  const full = (row.f || "").toLowerCase();
  const desc = (row.d || "").toLowerCase();
  const tags = (row.t || []).join(" ").toLowerCase();
  const scen = (row.w || "").toLowerCase();
  const hasContent = tokens.some((t) => !STOPWORDS.has(t));
  let score = 0;
  for (const tok of tokens) {
    if (hasContent && STOPWORDS.has(tok)) continue;
    if (name === tok) score += 50;
    else if (name.includes(tok)) score += 20;
    if (full.includes(tok)) score += 8;
    if (scen.includes(tok)) score += 12;
    if (tags.includes(tok)) score += 10;
    if (desc.includes(tok)) score += 5;
    if (CJK.test(tok) && tok.length >= 3) {
      for (let i = 0; i + 2 <= tok.length; i++) {
        if (scen.includes(tok.slice(i, i + 2))) { score += 9; break; }
      }
    }
  }
  if (score === 0) return -1;
  return score + (row.q || 0) / 20 + Math.min(row.s, 50000) / 25000;
}
function search(query, limit = 10) {
  const tokens = tokenize(query);
  return ROWS
    .map((row) => ({ row, s: scoreRow(row, tokens) }))
    .filter((x) => x.s > 0)
    .sort((a, b) => b.s - a.s)
    .slice(0, limit)
    .map((x) => x.row);
}

// ─── results collector ───────────────────────────────────────────────────────
const fails = [];
const warns = [];
let checks = 0;
const fail = (layer, msg) => { fails.push(`[${layer}] ${msg}`); };
const warn = (layer, msg) => { warns.push(`[${layer}] ${msg}`); };

// precompute tag counts per scenario
const tagCount = new Map(MATCHERS.map((m) => [m.slug, 0]));
for (const row of ROWS) for (const sg of row._scenarios) tagCount.set(sg, tagCount.get(sg) + 1);

const targetSlugs = ONLY ? [ONLY] : MATCHERS.map((m) => m.slug);
if (ONLY && !MATCHER_BY_SLUG.has(ONLY)) {
  console.error(`✗ unknown scenario slug: ${ONLY}`);
  process.exit(2);
}

// ─── layer 1: distribution sanity ────────────────────────────────────────────
for (const slug of targetSlugs) {
  checks++;
  const n = tagCount.get(slug);
  const pct = n / ROWS.length;
  const broad = MATCHER_BY_SLUG.get(slug).broad;
  if (n === 0) fail("dist", `${slug}: 0 skills tagged (dead scenario — no row matches its keywords/tags)`);
  else if (pct > OVERBROAD_PCT && !broad)
    fail("dist", `${slug}: tags ${n} skills (${(pct * 100).toFixed(1)}% of catalog) — over-broad, tighten keywords/excludes`);
  else if (pct > OVERBROAD_PCT && broad)
    warn("dist", `${slug}: ${n} skills (${(pct * 100).toFixed(1)}%) — broad facet (exempt by design)`);
  else if (VERBOSE) console.log(`  dist ✓ ${slug}: ${n} skills (${(pct * 100).toFixed(1)}%)`);
}

// ─── layer 2: precision self-check (canonical ZH query reachable & on-topic) ──
for (const slug of targetSlugs) {
  const zh = SCENARIO_ZH[slug] || {};
  if (!zh.t) { warn("prec", `${slug}: no ZH title in scenario-zh.json — skipped`); continue; }
  checks++;
  const hits = search(zh.t, PRECISION_TOPK);
  if (hits.length === 0) {
    fail("prec", `${slug}: ZH query "${zh.t}" returns 0 results — scenario unreachable in Chinese`);
    continue;
  }
  const onTopic = hits.filter((r) => r._scenarios.includes(slug)).length;
  const precision = onTopic / hits.length;
  if (precision < PRECISION_MIN)
    warn("prec", `${slug}: "${zh.t}" precision@${hits.length}=${(precision * 100).toFixed(0)}% (top: ${hits.slice(0, 3).map((r) => r.f).join(", ")})`);
  else if (VERBOSE) console.log(`  prec ✓ ${slug}: "${zh.t}" → ${onTopic}/${hits.length} on-topic`);
}

// ─── layer 3: edge cases (deterministic) ─────────────────────────────────────
if (!ONLY) {
  checks++;
  // emoji / punctuation-only query must NOT browse-dump the whole catalog
  const emoji = search("🎉🎊", 10);
  if (emoji.length > 0)
    warn("edge", `emoji-only query "🎉🎊" returned ${emoji.length} results (expected 0 — known browse-mode edge)`);

  checks++;
  // latin/CJK boundary tokenization
  const tk = tokenize("ppt制作");
  if (JSON.stringify(tk) !== JSON.stringify(["ppt", "制作"]))
    fail("edge", `tokenize("ppt制作") = ${JSON.stringify(tk)} (expected ["ppt","制作"])`);
  else if (VERBOSE) console.log(`  edge ✓ tokenize("ppt制作") → ["ppt","制作"]`);

  checks++;
  // stopword-only query is allowed to browse (quality-ranked) but must not crash
  const sw = search("ai mcp tool", 5);
  if (!Array.isArray(sw)) fail("edge", `stopword-only query crashed`);
  else if (VERBOSE) console.log(`  edge ✓ stopword-only "ai mcp tool" → ${sw.length} results (browse ok)`);
}

// ─── layer 4: golden regressions (specific fixed bugs stay fixed) ────────────
// Each: a query, plus repos that MUST or MUST NOT appear in the top-N. Cases auto-skip
// (with notice) if a referenced repo isn't in the catalog snapshot, so catalog drift
// doesn't break the test silently.
const GOLDEN = [
  { q: "网页抓取", include: ["browser-use/browser-use", "huginn/huginn"], exclude: [] },
  { q: "抓取网站", include: ["browser-use/browser-use", "huginn/huginn"], exclude: [] },
  { q: "图像生成", include: [], exclude: ["oobabooga/textgen"] },
  { q: "文生图", include: [], exclude: ["oobabooga/textgen"] },
];
const catalogHas = (full) => ROWS.some((r) => r.f === full);
if (!ONLY) {
  for (const g of GOLDEN) {
    const top = new Set(search(g.q, GOLDEN_TOPN).map((r) => r.f));
    // must-include: at least one referenced repo present (skip refs not in catalog)
    const incRefs = g.include.filter(catalogHas);
    if (g.include.length && incRefs.length === 0) {
      console.log(`  golden ⊘ "${g.q}": include refs not in catalog (${g.include.join(", ")}) — skipped`);
    } else if (incRefs.length) {
      checks++;
      if (!incRefs.some((f) => top.has(f)))
        fail("golden", `"${g.q}": none of [${incRefs.join(", ")}] in top ${GOLDEN_TOPN}`);
      else if (VERBOSE) console.log(`  golden ✓ "${g.q}" includes one of ${incRefs.join(", ")}`);
    }
    // must-exclude: referenced repo present in catalog must NOT appear
    for (const f of g.exclude.filter(catalogHas)) {
      checks++;
      if (top.has(f)) fail("golden", `"${g.q}": ${f} should NOT appear in top ${GOLDEN_TOPN} (known false-positive)`);
      else if (VERBOSE) console.log(`  golden ✓ "${g.q}" excludes ${f}`);
    }
  }
}

// ─── report ──────────────────────────────────────────────────────────────────
console.log(`\n${"─".repeat(60)}`);
console.log(`scenarios: ${targetSlugs.length}  ·  checks: ${checks}  ·  catalog: ${ROWS.length} rows  ·  index: ${INDEX.generated_at || "?"}`);
if (warns.length) {
  console.log(`\n⚠ ${warns.length} warning(s):`);
  for (const w of warns) console.log(`  ${w}`);
}
if (fails.length) {
  console.log(`\n✗ ${fails.length} FAILURE(S):`);
  for (const f of fails) console.log(`  ${f}`);
  console.log(`\nFAIL`);
  process.exit(1);
}
console.log(`\n✓ all ${checks} hard checks passed${warns.length ? ` (${warns.length} warnings)` : ""}`);
