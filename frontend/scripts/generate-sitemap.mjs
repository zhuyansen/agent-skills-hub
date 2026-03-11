/**
 * Build-time sitemap generator.
 * Fetches all skill data from Supabase and generates sitemap.xml.
 *
 * Features:
 *   - Tiered priority based on star count
 *   - <lastmod> from last_commit_at for every skill page
 *   - Category pages included as intermediate hierarchy
 *   - Differentiated changefreq (weekly for popular, monthly for rest)
 *
 * Run: node scripts/generate-sitemap.mjs
 */

const SUPABASE_URL = "https://vknzzecmzsfmohglpfgm.supabase.co";
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo";
const SITE = "https://agentskillshub.top";

const CATEGORIES = [
  "mcp-server", "claude-skill", "codex-skill", "agent-tool",
  "prompt-library", "ai-coding-assistant", "uncategorized",
];

/** Get tiered priority based on star count */
function getPriority(stars) {
  if (stars >= 1000) return "0.9";
  if (stars >= 500) return "0.8";
  if (stars >= 100) return "0.7";
  if (stars >= 50) return "0.6";
  return "0.5";
}

async function fetchAllSkills() {
  const skills = [];
  let offset = 0;
  const limit = 1000;

  while (true) {
    const url = `${SUPABASE_URL}/rest/v1/skills?select=repo_full_name,stars,last_commit_at,category&order=stars.desc&offset=${offset}&limit=${limit}`;
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

function buildSitemap(skills) {
  const today = new Date().toISOString().split("T")[0];
  const urls = [];

  // 1. Homepage — highest priority
  urls.push(`  <url>
    <loc>${SITE}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
    <lastmod>${today}</lastmod>
  </url>`);

  // 2. Category pages — high priority intermediate layer
  for (const cat of CATEGORIES) {
    urls.push(`  <url>
    <loc>${SITE}/category/${cat}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.85</priority>
    <lastmod>${today}</lastmod>
  </url>`);
  }

  // 3. Skill pages — tiered priority + lastmod
  for (const skill of skills) {
    const encoded = encodeURI(`${SITE}/skill/${skill.repo_full_name}`);
    const priority = getPriority(skill.stars);
    const changefreq = skill.stars >= 500 ? "weekly" : "monthly";
    const lastmod = skill.last_commit_at
      ? skill.last_commit_at.split("T")[0]
      : today;

    urls.push(`  <url>
    <loc>${encoded}</loc>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
    <lastmod>${lastmod}</lastmod>
  </url>`);
  }

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join("\n")}
</urlset>`;
}

async function main() {
  console.log("Fetching skills from Supabase...");
  const skills = await fetchAllSkills();
  console.log(`Found ${skills.length} skills`);

  const { writeFileSync } = await import("fs");
  const xml = buildSitemap(skills);
  writeFileSync("public/sitemap.xml", xml);

  // Stats
  const high = skills.filter((s) => s.stars >= 1000).length;
  const mid = skills.filter((s) => s.stars >= 100 && s.stars < 1000).length;
  const low = skills.length - high - mid;
  console.log(`Sitemap: ${skills.length + CATEGORIES.length + 1} URLs`);
  console.log(`  Priority tiers: ${high} high (0.9), ${mid} mid (0.7-0.8), ${low} standard (0.5-0.6)`);
  console.log(`  Category pages: ${CATEGORIES.length}`);
}

main().catch(console.error);
