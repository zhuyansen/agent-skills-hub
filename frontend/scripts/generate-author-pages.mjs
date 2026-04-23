/**
 * Build-time static HTML generator for /author/{username}/ pages.
 *
 * Strategy:
 *   - Aggregate skills by author_name.
 *   - Pre-render the Top N authors by total_stars (N = AUTHOR_LIMIT).
 *   - Each file is index.html with customized <title>, description, canonical,
 *     and a <noscript> SEO body listing the author's top skills (for crawlers).
 *   - Everyone else still works via the SPA fallback at runtime.
 *
 * Run: node scripts/generate-author-pages.mjs  (after vite build)
 */

import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { SUPABASE_URL, SUPABASE_ANON_KEY, SITE, esc, starsK } from "./shared-utils.mjs";

const DIST = "dist";
const AUTHOR_LIMIT = 500;              // top N authors to pre-render
const MIN_SKILLS = 2;                  // must have at least this many skills
const MIN_TOTAL_STARS = 100;           // OR this many cumulative stars

/** Fetch skills with author data (minimum fields, all rows). */
async function fetchAuthorSkills() {
  const skills = [];
  let offset = 0;
  const limit = 1000;
  const fields = [
    "repo_full_name", "repo_name", "author_name", "author_avatar_url",
    "stars", "description", "category", "score",
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
    if (!Array.isArray(data) || !data.length) break;
    skills.push(...data);
    offset += limit;
    if (data.length < limit) break;
  }
  return skills;
}

/** Group skills by author_name, sorted by total stars. */
function groupByAuthor(skills) {
  const groups = new Map();
  for (const s of skills) {
    const key = s.author_name;
    if (!key) continue;
    if (!groups.has(key)) {
      groups.set(key, {
        author_name: key,
        author_avatar_url: s.author_avatar_url,
        skills: [],
        total_stars: 0,
        avg_score: 0,
      });
    }
    const g = groups.get(key);
    g.skills.push(s);
    g.total_stars += (s.stars || 0);
  }
  // Compute avg score, sort skills within each group, filter by threshold
  const qualified = [];
  for (const g of groups.values()) {
    g.skills.sort((a, b) => (b.stars || 0) - (a.stars || 0));
    const scored = g.skills.filter((s) => typeof s.score === "number");
    g.avg_score = scored.length
      ? scored.reduce((sum, s) => sum + s.score, 0) / scored.length
      : 0;
    const passesThreshold =
      g.skills.length >= MIN_SKILLS || g.total_stars >= MIN_TOTAL_STARS;
    if (passesThreshold) qualified.push(g);
  }
  qualified.sort((a, b) => b.total_stars - a.total_stars);
  return qualified.slice(0, AUTHOR_LIMIT);
}

/** Build an SEO-optimized <noscript> summary for crawlers. */
function buildSeoNoScript(group) {
  const top5 = group.skills.slice(0, 5);
  const listItems = top5
    .map((s) => {
      const safe = esc(s.repo_full_name);
      const desc = esc((s.description || "").slice(0, 120));
      return `<li><a href="${SITE}/skill/${safe}/">${esc(s.repo_name)}</a> — ${desc} (${starsK(s.stars || 0)}★)</li>`;
    })
    .join("");
  return `
    <noscript>
      <h1>${esc(group.author_name)} — ${group.skills.length} Open-Source AI Agent Skills</h1>
      <p>Browse all ${group.skills.length} skills by <strong>${esc(group.author_name)}</strong> on AgentSkillsHub, with a combined ${group.total_stars.toLocaleString()}+ GitHub stars across MCP servers, Claude skills, and agent tools.</p>
      <h2>Top skills by ${esc(group.author_name)}</h2>
      <ul>${listItems}</ul>
      <p><a href="https://github.com/${esc(group.author_name)}">View on GitHub</a> · <a href="${SITE}/">Explore all creators</a></p>
    </noscript>`;
}

/** Generate HTML file for one author. */
function writeAuthorHtml(group, baseHtml) {
  const title = `${group.author_name} — ${group.skills.length} Claude Skills & Agent Tools · AgentSkillsHub`;
  const description = `Browse all ${group.skills.length} open-source AI agent skills, MCP servers, and Claude skills by ${group.author_name}. ${group.total_stars.toLocaleString()}+ GitHub stars. Ranked by stars and quality score.`;
  const canonical = `${SITE}/author/${group.author_name}/`;
  const noscript = buildSeoNoScript(group);

  let html = baseHtml
    .replace(/<title>[^<]+<\/title>/, `<title>${esc(title)}</title>`)
    .replace(
      /<meta name="description" content="[^"]+"/,
      `<meta name="description" content="${esc(description)}"`,
    )
    .replace(
      /<link rel="canonical" href="[^"]+"/,
      `<link rel="canonical" href="${canonical}"`,
    )
    // og tags
    .replace(
      /<meta property="og:title" content="[^"]+"/,
      `<meta property="og:title" content="${esc(title)}"`,
    )
    .replace(
      /<meta property="og:description" content="[^"]+"/,
      `<meta property="og:description" content="${esc(description)}"`,
    )
    .replace(
      /<meta property="og:url" content="[^"]+"/,
      `<meta property="og:url" content="${canonical}"`,
    );

  if (group.author_avatar_url) {
    html = html.replace(
      /<meta property="og:image" content="[^"]+"/,
      `<meta property="og:image" content="${esc(group.author_avatar_url)}"`,
    );
  }

  // Inject SEO noscript right before closing </body>
  html = html.replace("</body>", `${noscript}\n  </body>`);

  const outDir = join(DIST, "author", group.author_name);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, "index.html"), html);
}

async function main() {
  console.log("👤 Generating author pages...");
  const baseHtml = readFileSync(join(DIST, "index.html"), "utf-8");
  console.log("  Fetching skills...");
  const skills = await fetchAuthorSkills();
  console.log(`  Loaded ${skills.length} skills`);

  const groups = groupByAuthor(skills);
  console.log(`  Qualified authors: ${groups.length} (threshold: ${MIN_SKILLS}+ skills OR ${MIN_TOTAL_STARS}+ stars)`);

  let generated = 0;
  for (const g of groups) {
    try {
      writeAuthorHtml(g, baseHtml);
      generated++;
    } catch (err) {
      console.warn(`  ⚠ Failed to generate ${g.author_name}: ${err.message}`);
    }
  }

  console.log(`✅ Generated ${generated} author pages → dist/author/`);

  // Write author list for sitemap generator to consume
  const sitemapList = groups.map((g) => ({
    author_name: g.author_name,
    total_stars: g.total_stars,
    skill_count: g.skills.length,
  }));
  writeFileSync(
    join(DIST, "_authors-manifest.json"),
    JSON.stringify(sitemapList, null, 2),
  );
}

main().catch((err) => {
  console.error("Author page generation failed:", err);
  process.exit(1);
});
