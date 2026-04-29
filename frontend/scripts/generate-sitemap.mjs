/**
 * Build-time sitemap generator — V3 (Aggressive crawl-budget conservation).
 *
 * Changes from V2 (2026-04-29):
 *   - sitemap-top.xml threshold: stars >= 100 → stars >= 500
 *   - sitemap-authors.xml threshold: all 500 authors → only total_stars >= 1000
 *     OR ≥ 5 skills (~50-150 authors)
 *   - Reason: GSC showed 4,592 "Discovered – not indexed" pages — Google's
 *     quality bar exceeded average page quality. Goal: shrink sitemap from
 *     ~6,400 → ~2,000 URLs to redirect crawl budget to higher-signal pages.
 *
 * Output:
 *   dist/sitemap.xml           — sitemap index
 *   dist/sitemap-static.xml    — homepage + static routes
 *   dist/sitemap-categories.xml — category pages
 *   dist/sitemap-top.xml       — Skills with stars >= 500
 *   dist/sitemap-mid.xml       — SKIPPED (stars 50-499 reachable via internal links)
 *   dist/sitemap-scenarios.xml — /best/{slug}/ pages
 *   dist/sitemap-comparisons.xml — /compare/{slug}/ pages
 *   dist/sitemap-authors.xml   — /author/{username}/ for total_stars >= 1000 OR ≥5 skills
 *   dist/sitemap-book.xml      — /book/ + 12 chapters + 4 appendices
 *
 * Run: node scripts/generate-sitemap.mjs
 */

import { writeFileSync, readdirSync } from "fs";

const SUPABASE_URL = "https://vknzzecmzsfmohglpfgm.supabase.co";
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo";
const SITE = "https://agentskillshub.top";

// Dynamically fetched from DB — no hardcoded list needed
// Old hardcoded list removed to prevent 404s from empty categories

function getPriority(stars) {
  if (stars >= 1000) return "0.9";
  if (stars >= 500) return "0.8";
  if (stars >= 100) return "0.7";
  if (stars >= 50) return "0.6";
  return "0.5";
}

/** Unified indexing logic — matches generate-skill-pages.mjs shouldIndex().
 *  Only 50+ star pages get indexed and submitted in sitemap. */
function shouldIndex(skill) {
  if (skill.stars >= 50) return true;
  return false;
}

async function fetchAllSkills() {
  const skills = [];
  let offset = 0;
  const limit = 1000;

  while (true) {
    const url = `${SUPABASE_URL}/rest/v1/skills?select=repo_full_name,stars,last_commit_at,category,description,readme_size&order=stars.desc&offset=${offset}&limit=${limit}`;
    const res = await fetch(url, {
      headers: {
        apikey: SUPABASE_ANON_KEY,
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
      },
    });
    const data = await res.json();
    if (!data.length) break;
    skills.push(...data);
    offset += limit;
    if (data.length < limit) break;
  }
  return skills;
}

function buildUrlEntries(skills) {
  const today = new Date().toISOString().split("T")[0];
  return skills.map((skill) => {
    const encoded = encodeURI(`${SITE}/skill/${skill.repo_full_name}/`);
    const priority = getPriority(skill.stars);
    const changefreq = skill.stars >= 500 ? "weekly" : "monthly";
    const lastmod = skill.last_commit_at ? skill.last_commit_at.split("T")[0] : today;
    return `  <url>
    <loc>${encoded}</loc>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
    <lastmod>${lastmod}</lastmod>
  </url>`;
  });
}

function wrapUrlset(entries) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${entries.join("\n")}
</urlset>`;
}

function buildSitemapIndex(files) {
  const today = new Date().toISOString().split("T")[0];
  const entries = files.map((f) => `  <sitemap>
    <loc>${SITE}/${f}</loc>
    <lastmod>${today}</lastmod>
  </sitemap>`);

  return `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${entries.join("\n")}
</sitemapindex>`;
}

async function main() {
  console.log("Fetching skills from Supabase...");
  const allSkills = await fetchAllSkills();
  console.log(`Found ${allSkills.length} total skills`);

  // Filter to only indexed skills
  const indexedSkills = allSkills.filter(shouldIndex);
  const noindexCount = allSkills.length - indexedSkills.length;
  console.log(`Indexed: ${indexedSkills.length}, Noindex: ${noindexCount}`);

  const today = new Date().toISOString().split("T")[0];

  // Split by tier — prioritize crawl budget for higher-value pages.
  // 2026-04-29 update: GSC showed 4,592 "Discovered – not indexed" pages.
  // Tightened threshold from 100 → 500 to redirect Google's crawl budget to
  // the top ~1,500 pages instead of spreading across 4,000+ similar-looking
  // template pages. Expected effect: indexing rate 30% → 60-70% within 30 days.
  const topSkills = indexedSkills.filter((s) => s.stars >= 500);
  const midSkills = indexedSkills.filter((s) => s.stars >= 50 && s.stars < 500);

  // 1. sitemap-static.xml
  const staticEntries = [
    `  <url>
    <loc>${SITE}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
    <lastmod>${today}</lastmod>
  </url>`,
    `  <url>
    <loc>${SITE}/about/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
    <lastmod>${today}</lastmod>
  </url>`,
    `  <url>
    <loc>${SITE}/privacy/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.4</priority>
    <lastmod>${today}</lastmod>
  </url>`,
    `  <url>
    <loc>${SITE}/terms/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.4</priority>
    <lastmod>${today}</lastmod>
  </url>`,
    `  <url>
    <loc>${SITE}/verified-creator/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
    <lastmod>${today}</lastmod>
  </url>`,
    `  <url>
    <loc>${SITE}/business/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
    <lastmod>${today}</lastmod>
  </url>`,
    `  <url>
    <loc>${SITE}/about/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
    <lastmod>${today}</lastmod>
  </url>`,
  ];
  writeFileSync("dist/sitemap-static.xml", wrapUrlset(staticEntries));
  console.log(`sitemap-static.xml: ${staticEntries.length} URLs`);

  // 2. sitemap-categories.xml — derive categories from actual data (no hardcoded list)
  const catsWithSkills = [...new Set(allSkills.map((s) => s.category))].filter(Boolean);
  const catEntries = catsWithSkills.map((cat) => `  <url>
    <loc>${SITE}/category/${cat}/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.85</priority>
    <lastmod>${today}</lastmod>
  </url>`);
  writeFileSync("dist/sitemap-categories.xml", wrapUrlset(catEntries));
  console.log(`sitemap-categories.xml: ${catsWithSkills.length} URLs (derived from data)`);

  // 3. sitemap-top.xml (stars >= 500)
  const topEntries = buildUrlEntries(topSkills);
  writeFileSync("dist/sitemap-top.xml", wrapUrlset(topEntries));
  console.log(`sitemap-top.xml: ${topSkills.length} URLs (stars >= 500)`);

  // Clean up any stale sitemap-mid.xml from previous builds so Google stops
  // seeing it. (GitHub Pages serves whatever is in dist/; orphan files persist.)
  try {
    const { unlinkSync, existsSync } = await import("fs");
    if (existsSync("dist/sitemap-mid.xml")) {
      unlinkSync("dist/sitemap-mid.xml");
      console.log("  (removed stale dist/sitemap-mid.xml from previous build)");
    }
  } catch (e) {
    // non-fatal
  }

  // NOTE: sitemap-mid.xml is intentionally NOT generated.
  // Decision 2026-04-29 (v2): GSC showed 4,592 "discovered-not-indexed" even
  // with the prior 100-star threshold — Google's quality bar exceeded our
  // average page quality. Tightened to stars >= 500 to give Google a leaner,
  // higher-signal set. Mid pages (stars 50-499) are still reachable via
  // internal links + /category/ + /best/ pages — Google just isn't pushed
  // to crawl them via sitemap. Revisit in 30 days; if "discovered-not-indexed"
  // drops below 1,500 we may relax back to 200 or 300.
  console.log(`sitemap-mid.xml: SKIPPED (${midSkills.length} URLs intentionally excluded, stars 50-499)`);

  // 5. sitemap-scenarios.xml — scenario landing pages (/best/{slug}/)
  let scenarioCount = 0;
  try {
    const scenarioSlugs = readdirSync("dist/best");
    const scenarioEntries = scenarioSlugs
      .filter((slug) => !slug.startsWith(".") && slug !== "index.html")
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

  // 6b. sitemap-book.xml — Blue Book index + chapter pages
  let bookCount = 0;
  try {
    const { readdirSync: rds, existsSync: exs } = await import("fs");
    if (exs("dist/book")) {
      const bookEntries = [];
      // Index page first
      bookEntries.push(`  <url>
    <loc>${SITE}/book/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.85</priority>
    <lastmod>${today}</lastmod>
  </url>`);
      // Chapter pages
      const chapterSlugs = rds("dist/book").filter(
        (slug) => !slug.startsWith(".") && slug !== "index.html" && slug !== "assets",
      );
      for (const slug of chapterSlugs) {
        bookEntries.push(`  <url>
    <loc>${SITE}/book/${slug}/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.80</priority>
    <lastmod>${today}</lastmod>
  </url>`);
      }
      writeFileSync("dist/sitemap-book.xml", wrapUrlset(bookEntries));
      bookCount = bookEntries.length;
      console.log(`sitemap-book.xml: ${bookCount} URLs`);
    }
  } catch (e) {
    console.log(`sitemap-book.xml: skipped (${e.message})`);
  }

  // 6a. sitemap-authors.xml — top-N author aggregation pages (/author/{username}/)
  // 2026-04-29 update: tightened from 500 → only authors with total_stars >= 1000
  // OR ≥ 5 skills (combined the stars + prolific signal). Goal: redirect Google's
  // crawl budget to ~50-150 high-signal author pages.
  let authorCount = 0;
  try {
    const { readFileSync: rfs, existsSync } = await import("fs");
    if (existsSync("dist/_authors-manifest.json")) {
      const manifest = JSON.parse(rfs("dist/_authors-manifest.json", "utf-8"));
      const filtered = manifest.filter(
        (a) => a.total_stars >= 1000 || (a.skill_count && a.skill_count >= 5),
      );
      const authorEntries = filtered.map((a) => {
        // Priority scales with total_stars: 5K+ → 0.80, 1K-5K → 0.70, rest → 0.65
        const priority = a.total_stars >= 5000 ? "0.80" : a.total_stars >= 1000 ? "0.70" : "0.65";
        return `  <url>
    <loc>${SITE}/author/${encodeURIComponent(a.author_name)}/</loc>
    <changefreq>weekly</changefreq>
    <priority>${priority}</priority>
    <lastmod>${today}</lastmod>
  </url>`;
      });
      writeFileSync("dist/sitemap-authors.xml", wrapUrlset(authorEntries));
      authorCount = authorEntries.length;
      console.log(`sitemap-authors.xml: ${authorCount} URLs (filtered from ${manifest.length})`);
    }
  } catch (e) {
    console.log(`sitemap-authors.xml: skipped (${e.message})`);
  }

  // 6. sitemap-comparisons.xml — comparison landing pages (/compare/{slug}/)
  let comparisonCount = 0;
  try {
    const compareSlugs = readdirSync("dist/compare");
    const comparisonEntries = compareSlugs
      .filter((slug) => !slug.startsWith(".") && slug !== "index.html")
      .map((slug) => `  <url>
    <loc>${SITE}/compare/${slug}/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.80</priority>
    <lastmod>${today}</lastmod>
  </url>`);
    // Also add the /compare/ index page
    comparisonEntries.unshift(`  <url>
    <loc>${SITE}/compare/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.85</priority>
    <lastmod>${today}</lastmod>
  </url>`);
    writeFileSync("dist/sitemap-comparisons.xml", wrapUrlset(comparisonEntries));
    comparisonCount = comparisonEntries.length;
    console.log(`sitemap-comparisons.xml: ${comparisonCount} URLs`);
  } catch {
    console.log("sitemap-comparisons.xml: skipped (no dist/compare/ directory)");
  }

  // 7. sitemap.xml (index) — only top-tier to conserve crawl budget
  const sitemapFiles = [
    "sitemap-static.xml",
    "sitemap-categories.xml",
    "sitemap-top.xml",
    // "sitemap-mid.xml" intentionally excluded — see comment above
  ];
  if (scenarioCount > 0) {
    sitemapFiles.push("sitemap-scenarios.xml");
  }
  if (comparisonCount > 0) {
    sitemapFiles.push("sitemap-comparisons.xml");
  }
  if (authorCount > 0) {
    sitemapFiles.push("sitemap-authors.xml");
  }
  if (bookCount > 0) {
    sitemapFiles.push("sitemap-book.xml");
  }

  writeFileSync("dist/sitemap.xml", buildSitemapIndex(sitemapFiles));
  console.log(`\nsitemap.xml (index): ${sitemapFiles.length} sub-sitemaps`);

  const totalUrls = 1 + catsWithSkills.length + indexedSkills.length + scenarioCount + comparisonCount + authorCount + bookCount;
  console.log(`Total sitemap URLs: ${totalUrls} (indexed: top ${topSkills.length} + mid ${midSkills.length} + scenarios ${scenarioCount} + comparisons ${comparisonCount} + authors ${authorCount} + book ${bookCount}, excluded ${noindexCount} low-quality pages)`);
}

main().catch(console.error);
