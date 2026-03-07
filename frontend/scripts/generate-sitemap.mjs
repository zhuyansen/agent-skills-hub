/**
 * Build-time sitemap generator.
 * Fetches all skill slugs from Supabase and generates sitemap.xml.
 * Run: node scripts/generate-sitemap.mjs
 */

const SUPABASE_URL = "https://vknzzecmzsfmohglpfgm.supabase.co";
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo";
const SITE = "https://agentskillshub.top";

async function fetchAllSlugs() {
  const slugs = [];
  let offset = 0;
  const limit = 1000;

  while (true) {
    const url = `${SUPABASE_URL}/rest/v1/skills?select=repo_full_name&order=stars.desc&offset=${offset}&limit=${limit}`;
    const res = await fetch(url, {
      headers: {
        apikey: SUPABASE_ANON_KEY,
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
      },
    });
    const data = await res.json();
    if (!data.length) break;
    slugs.push(...data.map((s) => s.repo_full_name));
    offset += limit;
    if (data.length < limit) break;
  }
  return slugs;
}

function buildSitemap(slugs) {
  const today = new Date().toISOString().split("T")[0];
  const urls = [
    `  <url>\n    <loc>${SITE}/</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n    <lastmod>${today}</lastmod>\n  </url>`,
  ];

  for (const slug of slugs) {
    const encoded = encodeURI(`${SITE}/skill/${slug}`);
    urls.push(
      `  <url>\n    <loc>${encoded}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.7</priority>\n  </url>`,
    );
  }

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join("\n")}
</urlset>`;
}

async function main() {
  console.log("Fetching skill slugs from Supabase...");
  const slugs = await fetchAllSlugs();
  console.log(`Found ${slugs.length} skills`);

  const { writeFileSync } = await import("fs");
  const xml = buildSitemap(slugs);
  writeFileSync("public/sitemap.xml", xml);
  console.log(`Sitemap written with ${slugs.length + 1} URLs`);
}

main().catch(console.error);
