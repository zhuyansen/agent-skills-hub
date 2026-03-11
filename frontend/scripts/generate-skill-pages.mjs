/**
 * Build-time static HTML generator for SEO — V2 (Quality-First).
 *
 * Key changes from V1:
 *   - noindex for low-quality pages (stars < 50 or no README + no description)
 *   - README excerpt expanded to 600+ chars for Google's 500-word quality gate
 *   - FAQ section auto-generated per page
 *   - "Same Category" links block (top 10 by stars in same category)
 *   - "Same Language" links block (top 5 by stars in same language)
 *   - Content word-count targets: 500+ for indexed pages
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

function formatDate(iso) {
  if (!iso) return "";
  return iso.split("T")[0];
}

/** Strip Markdown syntax → plain text (no external deps) */
function stripMarkdown(md) {
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
function truncate(text, maxLen = 600) {
  if (!text || text.length <= maxLen) return text || "";
  const sub = text.slice(0, maxLen);
  const sentEnd = sub.lastIndexOf(". ");
  if (sentEnd > maxLen * 0.5) return sub.slice(0, sentEnd + 1);
  const wordEnd = sub.lastIndexOf(" ");
  return wordEnd > 0 ? sub.slice(0, wordEnd) + "..." : sub + "...";
}

function parseJsonArray(s) {
  if (!s) return [];
  try {
    const arr = JSON.parse(s);
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

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

/** Decide if a page should be indexed */
function shouldIndex(skill) {
  // Index if: stars >= 50, OR (stars >= 20 AND has readme or description > 80 chars)
  if (skill.stars >= 50) return true;
  if (skill.stars >= 20 && skill.readme_content && skill.readme_content.length > 100) return true;
  if (skill.stars >= 20 && skill.description && skill.description.length > 80) return true;
  return false;
}

/* ── fetch skills from Supabase ────────────────── */

async function fetchAllSkills() {
  const skills = [];
  let offset = 0;
  const limit = 1000;
  const fields = [
    "id", "repo_full_name", "repo_name", "author_name", "author_avatar_url",
    "stars", "forks", "description", "category", "language", "score", "license",
    "readme_content", "last_commit_at", "created_at", "topics",
    "quality_score", "platforms", "star_momentum", "estimated_tokens",
    "open_issues", "total_commits",
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
    if (!data.length) break;
    for (const row of data) {
      // Keep more README for expanded content (1500 chars)
      if (row.readme_content) {
        row.readme_content = row.readme_content.slice(0, 1500);
      }
      skills.push(row);
    }
    offset += limit;
    if (data.length < limit) break;
  }
  return skills;
}

async function fetchAllCompositions() {
  const comps = new Map();
  let offset = 0;
  const limit = 1000;

  while (true) {
    const url = `${SUPABASE_URL}/rest/v1/skill_compositions?select=skill_id,compatible_skill_id,compatibility_score,reason&order=skill_id.asc,compatibility_score.desc&offset=${offset}&limit=${limit}`;
    const res = await fetch(url, {
      headers: {
        apikey: SUPABASE_ANON_KEY,
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
      },
    });
    const data = await res.json();
    if (!Array.isArray(data) || !data.length) break;
    for (const row of data) {
      if (!comps.has(row.skill_id)) comps.set(row.skill_id, []);
      comps.get(row.skill_id).push(row);
    }
    offset += limit;
    if (data.length < limit) break;
  }
  return comps;
}

/* ── build HTML for one skill ──────────────────── */

function buildSkillHtml(skill, assetTags, compositions, skillById, categoryIndex, languageIndex) {
  const {
    repo_full_name, repo_name, author_name, author_avatar_url,
    stars, forks, description, category, language, score, license,
    readme_content, last_commit_at, created_at, topics,
    quality_score, platforms, estimated_tokens, open_issues, total_commits,
  } = skill;

  const indexed = shouldIndex(skill);
  const catLabel = CATEGORY_LABELS[category] || "AI Tool";
  const pageUrl = `${SITE}/skill/${repo_full_name}`;
  const ghUrl = `https://github.com/${repo_full_name}`;
  const ogImage = `${SITE}/og-image.png`;

  const title = `${repo_name} - ${catLabel} by ${author_name} | Agent Skills Hub`;
  const metaDesc = description
    ? `${description.slice(0, 140)}${description.length > 140 ? "..." : ""} ${starsK(stars)} stars.`
    : `${repo_name} is a ${catLabel.toLowerCase()} by ${author_name} with ${starsK(stars)} stars on GitHub.`;

  // README excerpt — expanded to 600 chars for content depth
  const readmeText = stripMarkdown(readme_content);
  const excerpt = readmeText
    ? truncate(readmeText, 600)
    : (description || `${repo_name} is a ${catLabel.toLowerCase()} by ${author_name}.`);

  const topicsList = parseJsonArray(topics);
  const platformsList = parseJsonArray(platforms);
  const keywords = [repo_name, author_name, catLabel, ...topicsList.slice(0, 5), "Agent Skills", "GitHub"].join(", ");

  // Compatible skills internal links
  const compLinks = compositions.slice(0, 5).map((c) => {
    const target = skillById.get(c.compatible_skill_id);
    if (!target) return null;
    return { name: target.repo_name, slug: target.repo_full_name, score: c.compatibility_score, reason: c.reason };
  }).filter(Boolean);

  // Same-category links (top 10, excluding self)
  const sameCatSkills = (categoryIndex.get(category) || [])
    .filter((s) => s.repo_full_name !== repo_full_name)
    .slice(0, 10);

  // Same-language links (top 5, excluding self)
  const sameLangSkills = language
    ? (languageIndex.get(language) || [])
      .filter((s) => s.repo_full_name !== repo_full_name)
      .slice(0, 5)
    : [];

  // Auto-generated FAQ
  const faqItems = [];
  faqItems.push({
    q: `What is ${repo_name}?`,
    a: description
      ? `${repo_name} is ${description.slice(0, 200)}. It is categorized as a ${catLabel} with ${starsK(stars)} GitHub stars.`
      : `${repo_name} is an open-source ${catLabel.toLowerCase()} by ${author_name} with ${starsK(stars)} GitHub stars.`,
  });
  if (language) {
    faqItems.push({
      q: `What programming language is ${repo_name} written in?`,
      a: `${repo_name} is primarily written in ${language}. ${topicsList.length > 0 ? `It covers topics such as ${topicsList.slice(0, 3).join(", ")}.` : ""}`,
    });
  }
  faqItems.push({
    q: `How do I install or use ${repo_name}?`,
    a: `You can find installation instructions and usage details in the ${repo_name} GitHub repository at github.com/${repo_full_name}. The project has ${starsK(stars)} stars and ${forks} forks, indicating an active community.`,
  });
  if (license && license !== "NOASSERTION") {
    faqItems.push({
      q: `What license does ${repo_name} use?`,
      a: `${repo_name} is released under the ${license} license, making it free to use and modify according to the license terms.`,
    });
  }

  // JSON-LD: SoftwareSourceCode
  const jsonLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    name: repo_name,
    url: pageUrl,
    codeRepository: ghUrl,
    description: description || `${catLabel} by ${author_name}`,
    author: { "@type": "Person", name: author_name, url: `https://github.com/${author_name}` },
    programmingLanguage: language || undefined,
    license: license && license !== "NOASSERTION" ? `https://spdx.org/licenses/${license}` : undefined,
    dateCreated: created_at ? formatDate(created_at) : undefined,
    dateModified: last_commit_at ? formatDate(last_commit_at) : undefined,
    keywords: topicsList.length ? topicsList.join(", ") : undefined,
    applicationCategory: catLabel,
    aggregateRating: stars > 0 ? {
      "@type": "AggregateRating",
      ratingValue: Math.min(5, (score || 0) / 20).toFixed(1),
      bestRating: "5",
      ratingCount: stars,
    } : undefined,
  }, null, 2);

  // JSON-LD: BreadcrumbList
  const breadcrumbLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE },
      { "@type": "ListItem", position: 2, name: catLabel, item: `${SITE}/category/${category}` },
      { "@type": "ListItem", position: 3, name: repo_name, item: pageUrl },
    ],
  });

  // JSON-LD: FAQPage
  const faqLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqItems.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  });

  const { scriptTags, linkTags } = assetTags;

  // Quick Facts rows — expanded
  const factsRows = [
    `<tr><td>Stars</td><td>${stars.toLocaleString()}</td></tr>`,
    `<tr><td>Forks</td><td>${(forks || 0).toLocaleString()}</td></tr>`,
    language ? `<tr><td>Language</td><td>${esc(language)}</td></tr>` : "",
    `<tr><td>Category</td><td><a href="/category/${esc(category)}">${esc(catLabel)}</a></td></tr>`,
    license && license !== "NOASSERTION" ? `<tr><td>License</td><td>${esc(license)}</td></tr>` : "",
    quality_score ? `<tr><td>Quality Score</td><td>${quality_score}/100</td></tr>` : "",
    total_commits ? `<tr><td>Total Commits</td><td>${total_commits.toLocaleString()}</td></tr>` : "",
    open_issues ? `<tr><td>Open Issues</td><td>${open_issues}</td></tr>` : "",
    last_commit_at ? `<tr><td>Last Updated</td><td>${formatDate(last_commit_at)}</td></tr>` : "",
    created_at ? `<tr><td>Created</td><td>${formatDate(created_at)}</td></tr>` : "",
    platformsList.length ? `<tr><td>Platforms</td><td>${esc(platformsList.join(", "))}</td></tr>` : "",
    estimated_tokens ? `<tr><td>Est. Tokens</td><td>~${(estimated_tokens / 1000).toFixed(0)}k</td></tr>` : "",
  ].filter(Boolean).join("\n          ");

  // Topics HTML
  const topicsHtml = topicsList.length > 0
    ? `<div style="margin:12px 0;display:flex;flex-wrap:wrap;gap:6px">${topicsList.slice(0, 10).map((t) => `<a href="/?search=${encodeURIComponent(t)}" style="display:inline-block;padding:2px 10px;border-radius:12px;background:#f0f0ff;color:#4f46e5;font-size:13px;text-decoration:none">${esc(t)}</a>`).join("")}</div>`
    : "";

  // Compatible skills HTML
  const compsHtml = compLinks.length > 0
    ? `<section style="margin-top:20px">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">Compatible Skills</h2>
        <p style="color:#64748b;font-size:14px;margin-bottom:8px">These tools work well together with ${esc(repo_name)} for enhanced workflows:</p>
        <ul style="list-style:none;padding:0">${compLinks.map((c) => `
          <li style="margin:6px 0"><a href="/skill/${esc(c.slug)}" style="color:#4f46e5;text-decoration:none;font-weight:500">${esc(c.name)}</a> <span style="color:#94a3b8;font-size:13px">— ${esc(c.reason)} (${Math.round(c.score * 100)}%)</span></li>`).join("")}
        </ul>
      </section>`
    : "";

  // Same-category links HTML
  const sameCatHtml = sameCatSkills.length > 0
    ? `<section style="margin-top:20px">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">More ${esc(catLabel)} Tools</h2>
        <p style="color:#64748b;font-size:14px;margin-bottom:8px">Explore other popular ${esc(catLabel.toLowerCase())} tools:</p>
        <ul style="list-style:none;padding:0">${sameCatSkills.map((s) => `
          <li style="margin:4px 0"><a href="/skill/${esc(s.repo_full_name)}" style="color:#4f46e5;text-decoration:none">${esc(s.repo_name)}</a> <span style="color:#94a3b8;font-size:13px">⭐ ${starsK(s.stars)}</span></li>`).join("")}
        </ul>
        <a href="/category/${esc(category)}" style="color:#4f46e5;font-size:14px">View all ${esc(catLabel)} tools →</a>
      </section>`
    : "";

  // Same-language links HTML
  const sameLangHtml = sameLangSkills.length > 0
    ? `<section style="margin-top:20px">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">Popular ${esc(language)} Agent Tools</h2>
        <ul style="list-style:none;padding:0">${sameLangSkills.map((s) => `
          <li style="margin:4px 0"><a href="/skill/${esc(s.repo_full_name)}" style="color:#4f46e5;text-decoration:none">${esc(s.repo_name)}</a> <span style="color:#94a3b8;font-size:13px">⭐ ${starsK(s.stars)} · ${esc(CATEGORY_LABELS[s.category] || "AI Tool")}</span></li>`).join("")}
        </ul>
      </section>`
    : "";

  // FAQ HTML
  const faqHtml = `<section style="margin-top:24px">
      <h2 style="font-size:18px;color:#1e293b;margin-bottom:12px">Frequently Asked Questions</h2>
      ${faqItems.map((f) => `<details style="margin:8px 0;border:1px solid #e2e8f0;border-radius:8px;padding:12px">
        <summary style="cursor:pointer;font-weight:500;color:#1e293b">${esc(f.q)}</summary>
        <p style="margin:8px 0 0;color:#475569;line-height:1.6">${esc(f.a)}</p>
      </details>`).join("\n      ")}
    </section>`;

  // noindex meta tag for low-quality pages
  const robotsMeta = indexed
    ? ""
    : `\n  <meta name="robots" content="noindex, follow" />`;

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/vite.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />${robotsMeta}
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(metaDesc)}" />
  <meta name="keywords" content="${esc(keywords)}" />

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

  <!-- JSON-LD: SoftwareSourceCode -->
  <script type="application/ld+json">
${jsonLd}
  </script>
  <!-- JSON-LD: BreadcrumbList -->
  <script type="application/ld+json">
${breadcrumbLd}
  </script>
  <!-- JSON-LD: FAQPage -->
  <script type="application/ld+json">
${faqLd}
  </script>

  <link rel="preconnect" href="https://vknzzecmzsfmohglpfgm.supabase.co" />
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com" />
  ${scriptTags.join("\n  ")}
  ${linkTags.join("\n  ")}
</head>
<body>
  <div id="root">
    <!-- Static SEO content — replaced by React on hydration -->
    <div style="max-width:800px;margin:40px auto;font-family:system-ui,-apple-system,sans-serif;padding:0 20px;color:#1e293b">
      <!-- Breadcrumb -->
      <nav style="font-size:13px;color:#64748b;margin-bottom:16px">
        <a href="/" style="color:#4f46e5;text-decoration:none">Home</a>
        <span style="margin:0 6px">&gt;</span>
        <a href="/category/${esc(category)}" style="color:#4f46e5;text-decoration:none">${esc(catLabel)}</a>
        <span style="margin:0 6px">&gt;</span>
        <span>${esc(repo_name)}</span>
      </nav>

      <!-- Title & Author -->
      <h1 style="font-size:28px;margin:0 0 8px">${esc(repo_name)}</h1>
      <p style="color:#64748b;margin:0 0 16px">
        by <a href="https://github.com/${esc(author_name)}" style="color:#4f46e5;text-decoration:none">${esc(author_name)}</a>
        &middot; <a href="/category/${esc(category)}" style="color:#4f46e5;text-decoration:none">${esc(catLabel)}</a>
        &middot; &#9733; ${starsK(stars)}
      </p>

      <!-- README Excerpt -->
      <section style="margin:20px 0">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">About ${esc(repo_name)}</h2>
        <p style="line-height:1.6;color:#475569">${esc(excerpt)}</p>
      </section>

      <!-- Topics -->
      ${topicsHtml}

      <!-- Quick Facts -->
      <section style="margin:20px 0">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">Quick Facts</h2>
        <table style="border-collapse:collapse;width:100%">
          ${factsRows}
        </table>
      </section>

      <!-- Compatible Skills -->
      ${compsHtml}

      <!-- Same Category -->
      ${sameCatHtml}

      <!-- Same Language -->
      ${sameLangHtml}

      <!-- FAQ -->
      ${faqHtml}

      <!-- Links -->
      <div style="margin:24px 0;display:flex;gap:16px;flex-wrap:wrap">
        <a href="${esc(ghUrl)}" style="display:inline-block;padding:8px 20px;background:#1e293b;color:#fff;border-radius:8px;text-decoration:none;font-size:14px">View on GitHub &rarr;</a>
        <a href="/category/${esc(category)}" style="display:inline-block;padding:8px 20px;background:#f0f0ff;color:#4f46e5;border-radius:8px;text-decoration:none;font-size:14px">Browse ${esc(catLabel)} tools</a>
      </div>
    </div>
  </div>
  <noscript>
    <p style="text-align:center;padding:20px">Enable JavaScript for the full interactive experience, or browse the content above.</p>
  </noscript>
</body>
</html>`;
}

/* ── build category page ──────────────────────── */

function buildCategoryHtml(catSlug, catSkills, assetTags, allCategories) {
  const catLabel = CATEGORY_LABELS[catSlug] || "AI Tool";
  const pageUrl = `${SITE}/category/${catSlug}`;
  const title = `Best ${catLabel} Tools - Open Source Agent Skills | Agent Skills Hub`;
  const metaDesc = `Discover the top ${catSkills.length}+ open-source ${catLabel} tools. Browse by stars, quality, and compatibility on Agent Skills Hub.`;

  const { scriptTags, linkTags } = assetTags;

  const jsonLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: `${catLabel} Tools`,
    url: pageUrl,
    description: metaDesc,
    mainEntity: {
      "@type": "ItemList",
      numberOfItems: catSkills.length,
      itemListElement: catSkills.slice(0, 20).map((s, i) => ({
        "@type": "ListItem",
        position: i + 1,
        url: `${SITE}/skill/${s.repo_full_name}`,
        name: s.repo_name,
      })),
    },
  }, null, 2);

  const breadcrumbLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE },
      { "@type": "ListItem", position: 2, name: catLabel, item: pageUrl },
    ],
  });

  const skillRows = catSkills.slice(0, 100).map((s, i) => {
    const desc = s.description ? esc(s.description.slice(0, 100)) : "";
    return `<tr>
        <td style="padding:8px 4px;font-size:14px;color:#64748b">${i + 1}</td>
        <td style="padding:8px"><a href="/skill/${esc(s.repo_full_name)}" style="color:#4f46e5;text-decoration:none;font-weight:500">${esc(s.repo_name)}</a><br><span style="color:#94a3b8;font-size:13px">${desc}</span></td>
        <td style="padding:8px;text-align:right;white-space:nowrap;font-size:14px">&#9733; ${starsK(s.stars)}</td>
        <td style="padding:8px;color:#64748b;font-size:13px">${esc(s.language || "")}</td>
      </tr>`;
  }).join("\n      ");

  const otherCats = allCategories
    .filter((c) => c !== catSlug)
    .map((c) => `<a href="/category/${esc(c)}" style="display:inline-block;padding:4px 12px;margin:3px;border-radius:16px;background:#f8fafc;border:1px solid #e2e8f0;color:#475569;font-size:13px;text-decoration:none">${esc(CATEGORY_LABELS[c] || c)}</a>`)
    .join("");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/vite.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(metaDesc)}" />
  <meta name="keywords" content="${esc(catLabel)}, Agent Skills, open source, AI tools, ${catSlug}" />

  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(metaDesc)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="${esc(pageUrl)}" />
  <meta property="og:site_name" content="Agent Skills Hub" />

  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="${esc(title)}" />
  <meta name="twitter:description" content="${esc(metaDesc)}" />
  <meta name="twitter:site" content="@GoSailGlobal" />

  <link rel="canonical" href="${esc(pageUrl)}" />

  <script type="application/ld+json">
${jsonLd}
  </script>
  <script type="application/ld+json">
${breadcrumbLd}
  </script>

  <link rel="preconnect" href="https://vknzzecmzsfmohglpfgm.supabase.co" />
  ${scriptTags.join("\n  ")}
  ${linkTags.join("\n  ")}
</head>
<body>
  <div id="root">
    <div style="max-width:900px;margin:40px auto;font-family:system-ui,-apple-system,sans-serif;padding:0 20px;color:#1e293b">
      <nav style="font-size:13px;color:#64748b;margin-bottom:16px">
        <a href="/" style="color:#4f46e5;text-decoration:none">Home</a>
        <span style="margin:0 6px">&gt;</span>
        <span>${esc(catLabel)}</span>
      </nav>

      <h1 style="font-size:28px;margin:0 0 8px">${esc(catLabel)} Tools</h1>
      <p style="color:#64748b;margin:0 0 20px">${catSkills.length}+ open-source ${esc(catLabel.toLowerCase())} tools ranked by stars</p>

      <div style="margin-bottom:24px">
        <span style="font-size:13px;color:#94a3b8;margin-right:8px">Also browse:</span>
        ${otherCats}
      </div>

      <table style="width:100%;border-collapse:collapse">
        <thead>
          <tr style="border-bottom:2px solid #e2e8f0;text-align:left">
            <th style="padding:8px 4px;font-size:13px;color:#94a3b8;width:40px">#</th>
            <th style="padding:8px;font-size:13px;color:#94a3b8">Skill</th>
            <th style="padding:8px;font-size:13px;color:#94a3b8;text-align:right">Stars</th>
            <th style="padding:8px;font-size:13px;color:#94a3b8">Lang</th>
          </tr>
        </thead>
        <tbody>
      ${skillRows}
        </tbody>
      </table>

      <div style="margin:32px 0;text-align:center">
        <a href="/" style="display:inline-block;padding:10px 24px;background:#4f46e5;color:#fff;border-radius:8px;text-decoration:none;font-size:14px">Explore All Skills on Agent Skills Hub</a>
      </div>
    </div>
  </div>
  <noscript>
    <p style="text-align:center;padding:20px">Enable JavaScript for the full interactive experience.</p>
  </noscript>
</body>
</html>`;
}

/* ── main ──────────────────────────────────────── */

async function main() {
  const distDir = "dist";

  const indexHtml = readFileSync(join(distDir, "index.html"), "utf-8");
  const assetTags = extractAssetTags(indexHtml);
  console.log(`Assets: ${assetTags.scriptTags.length} scripts, ${assetTags.linkTags.length} links`);

  console.log("Fetching skills from Supabase...");
  const skills = await fetchAllSkills();
  console.log(`Fetched ${skills.length} skills`);

  console.log("Fetching compositions...");
  const compositions = await fetchAllCompositions();
  console.log(`Fetched compositions for ${compositions.size} skills`);

  // Build lookup maps
  const skillById = new Map(skills.map((s) => [s.id, s]));

  // Build category index: category → top skills (by stars)
  const categoryIndex = new Map();
  for (const s of skills) {
    if (!categoryIndex.has(s.category)) categoryIndex.set(s.category, []);
    const arr = categoryIndex.get(s.category);
    if (arr.length < 15) arr.push(s); // already sorted by stars desc
  }

  // Build language index: language → top skills (by stars)
  const languageIndex = new Map();
  for (const s of skills) {
    if (!s.language) continue;
    if (!languageIndex.has(s.language)) languageIndex.set(s.language, []);
    const arr = languageIndex.get(s.language);
    if (arr.length < 10) arr.push(s);
  }

  // Generate skill pages
  let ok = 0;
  let skipped = 0;
  let indexedCount = 0;
  let noindexCount = 0;
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

    const skillComps = compositions.get(skill.id) || [];
    writeFileSync(
      join(dir, "index.html"),
      buildSkillHtml(skill, assetTags, skillComps, skillById, categoryIndex, languageIndex),
    );
    ok++;

    if (shouldIndex(skill)) indexedCount++;
    else noindexCount++;
  }

  const elapsed1 = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`Skill pages: ${ok} generated (${indexedCount} indexed, ${noindexCount} noindex), ${skipped} skipped (${elapsed1}s)`);

  // Generate category pages
  const t1 = Date.now();
  const allCategories = Object.keys(CATEGORY_LABELS);
  let catCount = 0;

  for (const catSlug of allCategories) {
    const catSkills = skills
      .filter((s) => s.category === catSlug)
      .sort((a, b) => b.stars - a.stars);
    if (!catSkills.length) continue;

    const dir = join(distDir, "category", catSlug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(
      join(dir, "index.html"),
      buildCategoryHtml(catSlug, catSkills, assetTags, allCategories),
    );
    catCount++;
  }

  const elapsed2 = ((Date.now() - t1) / 1000).toFixed(1);
  console.log(`Category pages: ${catCount} generated (${elapsed2}s)`);

  const totalElapsed = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`Total: ${ok + catCount} pages in ${totalElapsed}s`);
}

main().catch((err) => {
  console.error("Failed to generate pages:", err);
  process.exit(1);
});
