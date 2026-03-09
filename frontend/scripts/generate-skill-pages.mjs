/**
 * Build-time static HTML generator for SEO.
 *
 * Problem: GitHub Pages SPA serves 404.html (HTTP 404) for /skill/* routes.
 *          Google sees 404 + empty <div id="root"> → refuses to index.
 *
 * Solution: Generate /skill/{owner}/{repo}/index.html for every skill at build time.
 *          - HTTP 200 (real file exists)
 *          - Unique <title>, description, OG/Twitter tags, JSON-LD
 *          - <noscript> readable content for crawlers
 *          - Same SPA JS loads → full interactivity for users
 *
 * Run: node scripts/generate-skill-pages.mjs  (after vite build)
 */

import { readFileSync, mkdirSync, writeFileSync } from "fs";
import { join } from "path";

const SUPABASE_URL = "https://vknzzecmzsfmohglpfgm.supabase.co";
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo";
const SITE = "https://agentskillshub.top";

const CATEGORY_LABELS = {
  "mcp-server": "MCP Server",
  "claude-skill": "Claude Skill",
  "codex-skill": "Codex Skill",
  "agent-tool": "Agent Tool",
  "prompt-library": "Prompt Library",
  "ai-coding-assistant": "AI Coding Assistant",
  uncategorized: "AI Tool",
};

/* ── helpers ───────────────────────────────────── */

function esc(s) {
  if (!s) return "";
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function starsK(n) {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);
}

/** Extract <script src>, <link rel="modulepreload|stylesheet"> from built index.html */
function extractAssetTags(html) {
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

/* ── fetch skills from Supabase ────────────────── */

async function fetchAllSkills() {
  const skills = [];
  let offset = 0;
  const limit = 1000;
  const fields =
    "repo_full_name,repo_name,author_name,author_avatar_url,stars,forks,description,category,language,score,license";

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
    skills.push(...data);
    offset += limit;
    if (data.length < limit) break;
  }
  return skills;
}

/* ── build HTML for one skill ──────────────────── */

function buildSkillHtml(skill, assetTags) {
  const {
    repo_full_name,
    repo_name,
    author_name,
    author_avatar_url,
    stars,
    forks,
    description,
    category,
    language,
    score,
    license,
  } = skill;

  const catLabel = CATEGORY_LABELS[category] || "AI Tool";
  const pageUrl = `${SITE}/skill/${repo_full_name}`;
  const ghUrl = `https://github.com/${repo_full_name}`;
  const ogImage = `${SITE}/og-image.png`;

  const title = `${repo_name} - ${catLabel} by ${author_name} | Agent Skills Hub`;
  const metaDesc = description
    ? `${description.slice(0, 140)}${description.length > 140 ? "..." : ""} ${starsK(stars)} stars.`
    : `${repo_name} is a ${catLabel.toLowerCase()} by ${author_name} with ${starsK(stars)} stars on GitHub.`;

  const jsonLd = JSON.stringify(
    {
      "@context": "https://schema.org",
      "@type": "SoftwareSourceCode",
      name: repo_name,
      url: pageUrl,
      codeRepository: ghUrl,
      description: description || `${catLabel} by ${author_name}`,
      author: {
        "@type": "Person",
        name: author_name,
        url: `https://github.com/${author_name}`,
      },
      programmingLanguage: language || undefined,
      license:
        license && license !== "NOASSERTION"
          ? `https://spdx.org/licenses/${license}`
          : undefined,
      aggregateRating: {
        "@type": "AggregateRating",
        ratingValue: Math.min(5, score / 20).toFixed(1),
        bestRating: "5",
        ratingCount: stars,
      },
    },
    null,
    2,
  );

  const { scriptTags, linkTags } = assetTags;

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/vite.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(metaDesc)}" />
  <meta name="keywords" content="${esc(repo_name)}, ${esc(author_name)}, ${esc(catLabel)}, Agent Skills, MCP Server, AI Tools, GitHub" />

  <!-- Open Graph -->
  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(metaDesc)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="${esc(pageUrl)}" />
  <meta property="og:site_name" content="Agent Skills Hub" />
  <meta property="og:image" content="${esc(ogImage)}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${esc(title)}" />
  <meta name="twitter:description" content="${esc(metaDesc)}" />
  <meta name="twitter:site" content="@GoSailGlobal" />
  <meta name="twitter:image" content="${esc(ogImage)}" />

  <!-- Canonical -->
  <link rel="canonical" href="${esc(pageUrl)}" />

  <!-- JSON-LD -->
  <script type="application/ld+json">
${jsonLd}
  </script>

  <link rel="preconnect" href="https://vknzzecmzsfmohglpfgm.supabase.co" />
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com" />
  ${scriptTags.join("\n  ")}
  ${linkTags.join("\n  ")}
</head>
<body>
  <div id="root"></div>
  <noscript>
    <div style="max-width:800px;margin:40px auto;font-family:system-ui,sans-serif;padding:0 20px">
      <nav><a href="/">← Agent Skills Hub</a></nav>
      <h1>${esc(repo_name)}</h1>
      <p>by <a href="https://github.com/${esc(author_name)}">${esc(author_name)}</a> · ${esc(catLabel)}</p>
      <p>${esc(description || "")}</p>
      <table>
        <tr><td>Stars</td><td>${stars.toLocaleString()}</td></tr>
        <tr><td>Forks</td><td>${forks.toLocaleString()}</td></tr>
        ${language ? `<tr><td>Language</td><td>${esc(language)}</td></tr>` : ""}
        ${license && license !== "NOASSERTION" ? `<tr><td>License</td><td>${esc(license)}</td></tr>` : ""}
        <tr><td>Score</td><td>${score}/100</td></tr>
      </table>
      <p><a href="${esc(ghUrl)}">View on GitHub →</a></p>
    </div>
  </noscript>
</body>
</html>`;
}

/* ── main ──────────────────────────────────────── */

async function main() {
  const distDir = "dist";

  // 1. Read built index.html → extract asset tags
  const indexHtml = readFileSync(join(distDir, "index.html"), "utf-8");
  const assetTags = extractAssetTags(indexHtml);
  console.log(
    `Assets: ${assetTags.scriptTags.length} scripts, ${assetTags.linkTags.length} links`,
  );

  // 2. Fetch skills
  console.log("Fetching skills from Supabase...");
  const skills = await fetchAllSkills();
  console.log(`Fetched ${skills.length} skills`);

  // 3. Generate HTML files
  let ok = 0;
  let skipped = 0;
  const t0 = Date.now();

  for (const skill of skills) {
    const parts = skill.repo_full_name.split("/");
    if (parts.length !== 2) {
      skipped++;
      continue;
    }
    const [owner, repo] = parts;
    const dir = join(distDir, "skill", owner, repo);
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, "index.html"), buildSkillHtml(skill, assetTags));
    ok++;
  }

  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(
    `Done: ${ok} pages generated, ${skipped} skipped (${elapsed}s)`,
  );
}

main().catch((err) => {
  console.error("Failed to generate skill pages:", err);
  process.exit(1);
});
