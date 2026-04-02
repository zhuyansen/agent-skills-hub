/**
 * Build-time sitemap generator — V2 (Split + Quality-Filtered).
 *
 * Changes from V1:
 *   - Sitemap index with split sub-sitemaps (top/mid/standard/categories)
 *   - Only includes indexed pages (stars >= 50, or stars >= 20 with content)
 *   - Excludes noindex pages to match generate-skill-pages.mjs logic
 *
 * Output:
 *   public/sitemap.xml           — sitemap index
 *   public/sitemap-static.xml    — homepage
 *   public/sitemap-categories.xml — category pages
 *   public/sitemap-top.xml       — stars >= 100
 *   public/sitemap-mid.xml       — stars 50-99
 *   public/sitemap-rest.xml      — stars 20-49 (with content)
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
 *  Pages meeting these criteria get indexed (no noindex meta) AND submitted in sitemap. */
function shouldIndex(skill) {
  if (skill.stars >= 50) return true;
  if (skill.stars >= 20 && skill.readme_size && skill.readme_size > 100) return true;
  if (skill.stars >= 20 && skill.description && skill.description.length > 80) return true;
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

  // Split by tier
  const topSkills = indexedSkills.filter((s) => s.stars >= 100);
  const midSkills = indexedSkills.filter((s) => s.stars >= 50 && s.stars < 100);
  const restSkills = indexedSkills.filter((s) => s.stars < 50);

  // 1. sitemap-static.xml
  const staticEntries = [
    `  <url>
    <loc>${SITE}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
    <lastmod>${today}</lastmod>
  </url>`,
    `  <url>
    <loc>${SITE}/blog/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
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

  // 3. sitemap-top.xml (stars >= 100)
  const topEntries = buildUrlEntries(topSkills);
  writeFileSync("dist/sitemap-top.xml", wrapUrlset(topEntries));
  console.log(`sitemap-top.xml: ${topSkills.length} URLs (stars >= 100)`);

  // 4. sitemap-mid.xml (stars 50-99)
  const midEntries = buildUrlEntries(midSkills);
  writeFileSync("dist/sitemap-mid.xml", wrapUrlset(midEntries));
  console.log(`sitemap-mid.xml: ${midSkills.length} URLs (stars 50-99)`);

  // 5. sitemap-rest.xml (stars 20-49 with good README/description — newly indexed)
  const restEntries = buildUrlEntries(restSkills);
  writeFileSync("dist/sitemap-rest.xml", wrapUrlset(restEntries));
  console.log(`sitemap-rest.xml: ${restSkills.length} URLs (stars 20-49, quality qualified)`);

  // 6. sitemap-scenarios.xml — scenario landing pages (/best/{slug}/)
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

  // 7. sitemap-comparisons.xml — comparison landing pages (/compare/{slug}/)
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

  // 8. sitemap.xml (index) — all tiers of indexed skills
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
  if (comparisonCount > 0) {
    sitemapFiles.push("sitemap-comparisons.xml");
  }

  writeFileSync("dist/sitemap.xml", buildSitemapIndex(sitemapFiles));
  console.log(`\nsitemap.xml (index): ${sitemapFiles.length} sub-sitemaps`);

  const totalUrls = 1 + catsWithSkills.length + indexedSkills.length + scenarioCount + comparisonCount;
  console.log(`Total sitemap URLs: ${totalUrls} (indexed: top ${topSkills.length} + mid ${midSkills.length} + rest ${restSkills.length} + scenarios ${scenarioCount} + comparisons ${comparisonCount}, excluded ${noindexCount} low-quality pages)`);
}

main().catch(console.error);
