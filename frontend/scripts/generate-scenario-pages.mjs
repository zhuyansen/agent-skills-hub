/**
 * Build-time scenario landing page generator.
 *
 * Generates static HTML pages at /best/{slug}/ for SEO long-tail traffic.
 * Reads scenario definitions from scenario-keywords.json, matches skills
 * from Supabase, and outputs static HTML with JSON-LD structured data.
 *
 * Run: node scripts/generate-scenario-pages.mjs  (after vite build)
 */

import { readFileSync, mkdirSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import {
  SITE, CATEGORY_LABELS,
  esc, starsK, stripMarkdown, parseJsonArray,
  extractAssetTags, shouldIndex, fetchAllSkills,
} from "./shared-utils.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DIST = "dist";

/* ── Skill matching ──────────────────────────────── */

function matchSkills(scenario, allSkills) {
  const { categories, keywords, min_results = 5, max_results = 10 } = scenario.match;

  const kwLower = keywords.map((k) => k.toLowerCase());

  const scored = [];
  for (const skill of allSkills) {
    if (!shouldIndex(skill)) continue;

    let matchScore = 0;

    // Category match (highest weight)
    if (categories.length > 0 && categories.includes(skill.category)) {
      matchScore += 10;
    }

    // Keyword matches in description, repo_name, topics
    const desc = (skill.description || "").toLowerCase();
    const name = (skill.repo_name || "").toLowerCase();
    const topics = parseJsonArray(skill.topics).map((t) => t.toLowerCase());
    const allText = `${desc} ${name} ${topics.join(" ")}`;

    for (const kw of kwLower) {
      if (allText.includes(kw)) {
        matchScore += 3;
      }
    }

    if (matchScore > 0) {
      // Boost by quality score
      const qualityBoost = (skill.score || 0) / 100;
      scored.push({ skill, matchScore: matchScore + qualityBoost });
    }
  }

  // Sort by matchScore desc, then by stars desc
  scored.sort((a, b) => b.matchScore - a.matchScore || b.skill.stars - a.skill.stars);

  const results = scored.slice(0, max_results).map((s) => s.skill);
  if (results.length < min_results) return null; // Not enough matches

  return results;
}

/* ── Quick Start extraction ──────────────────────── */

function extractQuickStart(readmeContent) {
  if (!readmeContent) return null;

  const patterns = [
    /## (?:Installation|Install|Getting Started|Quick Start|Setup)\s*\n([\s\S]*?)(?=\n## |\n$)/i,
    /## (?:Usage|How to Use|Examples?)\s*\n([\s\S]*?)(?=\n## |\n$)/i,
  ];

  for (const pat of patterns) {
    const match = readmeContent.match(pat);
    if (match && match[1].trim().length > 30) {
      const codeMatch = match[1].match(/```[\w]*\n([\s\S]*?)```/);
      const code = codeMatch ? codeMatch[0] : null;
      const text = stripMarkdown(match[1]).slice(0, 300);
      return { text, code };
    }
  }

  return null;
}

/* ── HTML builder ────────────────────────────────── */

function buildScenarioHtml(scenario, skills, assetTags, allScenarios) {
  const pageUrl = `${SITE}/best/${scenario.slug}/`;
  const year = new Date().getFullYear();
  const title = `Best ${skills.length} AI Tools for ${scenario.title} (${year}) | Agent Skills Hub`;
  const metaDesc = scenario.description;
  const ogImage = `${SITE}/og-image.png`;

  const { scriptTags, linkTags } = assetTags;

  // JSON-LD: ItemList
  const itemListLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: `Best AI Tools for ${scenario.title}`,
    description: scenario.description,
    url: pageUrl,
    numberOfItems: skills.length,
    itemListElement: skills.map((s, i) => ({
      "@type": "ListItem",
      position: i + 1,
      url: `${SITE}/skill/${s.repo_full_name}/`,
      name: s.repo_name,
      description: s.description || `${s.repo_name} by ${s.author_name}`,
    })),
  }, null, 2);

  // JSON-LD: BreadcrumbList
  const breadcrumbLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE },
      { "@type": "ListItem", position: 2, name: `Best ${scenario.title} Tools`, item: pageUrl },
    ],
  });

  // FAQ
  const faqItems = [
    {
      q: `What are the best AI tools for ${scenario.title.toLowerCase()}?`,
      a: `The top ${scenario.title.toLowerCase()} tools include ${skills.slice(0, 3).map((s) => s.repo_name).join(", ")}. These are ranked by our composite score based on GitHub stars, community activity, and code quality.`,
    },
    {
      q: `Are these ${scenario.title.toLowerCase()} tools free to use?`,
      a: `Most tools listed here are open-source. ${skills.filter((s) => s.license && s.license !== "NOASSERTION").length} out of ${skills.length} have explicit open-source licenses, making them free to use and modify.`,
    },
    {
      q: `How do I choose the right ${scenario.title.toLowerCase()} tool?`,
      a: `Consider your tech stack (language compatibility), project scale (stars indicate community trust), and specific features you need. Use the comparison table above to evaluate side by side.`,
    },
  ];

  const faqLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqItems.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  });

  // Skill cards HTML
  const skillCardsHtml = skills.map((s, i) => {
    const catLabel = CATEGORY_LABELS[s.category] || "AI Tool";
    const qs = extractQuickStart(s.readme_content);
    const qsHtml = qs
      ? `<div style="margin-top:8px;padding:8px 12px;background:#f8fafc;border-radius:6px;font-size:13px">
          <strong style="color:#334155">Quick Start:</strong>
          <span style="color:#475569"> ${esc(qs.text.slice(0, 150))}${qs.text.length > 150 ? "..." : ""}</span>
          ${qs.code ? `<pre style="margin:6px 0 0;padding:8px;background:#1e293b;color:#e2e8f0;border-radius:4px;overflow-x:auto;font-size:12px"><code>${esc(qs.code.slice(0, 300))}</code></pre>` : ""}
        </div>`
      : "";

    return `<div style="margin:16px 0;padding:16px 20px;border:1px solid #e2e8f0;border-radius:12px;background:#fff">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
          <div>
            <span style="display:inline-block;width:28px;height:28px;line-height:28px;text-align:center;border-radius:50%;background:${i < 3 ? "#f59e0b" : "#94a3b8"};color:#fff;font-weight:700;font-size:14px;margin-right:8px">${i + 1}</span>
            <a href="/skill/${esc(s.repo_full_name)}/" style="color:#1e293b;text-decoration:none;font-size:18px;font-weight:600">${esc(s.repo_name)}</a>
            <span style="color:#94a3b8;font-size:13px;margin-left:8px">by ${esc(s.author_name)}</span>
          </div>
          <div style="display:flex;gap:12px;font-size:14px;color:#64748b">
            <span>&#9733; ${starsK(s.stars)}</span>
            ${s.language ? `<span>${esc(s.language)}</span>` : ""}
            <span style="color:#4f46e5;font-size:12px;padding:2px 8px;background:#f0f0ff;border-radius:8px">${esc(catLabel)}</span>
          </div>
        </div>
        <p style="margin:8px 0 0;color:#475569;line-height:1.5;font-size:14px">${esc(s.description || "")}</p>
        ${qsHtml}
        <div style="margin-top:10px;display:flex;gap:12px">
          <a href="/skill/${esc(s.repo_full_name)}/" style="color:#4f46e5;font-size:13px;text-decoration:none">View Details &rarr;</a>
          <a href="https://github.com/${esc(s.repo_full_name)}" style="color:#64748b;font-size:13px;text-decoration:none">GitHub &rarr;</a>
        </div>
      </div>`;
  }).join("\n      ");

  // Comparison table
  const compRows = skills.map((s) => {
    return `<tr style="border-bottom:1px solid #f1f5f9">
          <td style="padding:8px"><a href="/skill/${esc(s.repo_full_name)}/" style="color:#4f46e5;text-decoration:none;font-weight:500">${esc(s.repo_name)}</a></td>
          <td style="padding:8px;text-align:right">&#9733; ${starsK(s.stars)}</td>
          <td style="padding:8px">${esc(s.language || "\u2014")}</td>
          <td style="padding:8px">${esc(s.license && s.license !== "NOASSERTION" ? s.license : "\u2014")}</td>
          <td style="padding:8px;text-align:right">${s.score ? Math.round(s.score) : "\u2014"}</td>
        </tr>`;
  }).join("\n        ");

  // Related scenarios
  const relatedHtml = (scenario.related || [])
    .map((slug) => {
      const rel = allScenarios.find((s) => s.slug === slug);
      if (!rel) return null;
      return `<a href="/best/${esc(slug)}/" style="display:inline-block;padding:6px 14px;margin:4px;border-radius:20px;background:#f0f0ff;color:#4f46e5;font-size:13px;text-decoration:none;border:1px solid #e0e0ff">${esc(rel.title)}</a>`;
    })
    .filter(Boolean)
    .join("\n        ");

  // FAQ HTML
  const faqHtml = faqItems.map((f) => `<details style="margin:8px 0;border:1px solid #e2e8f0;border-radius:8px;padding:12px">
        <summary style="cursor:pointer;font-weight:500;color:#1e293b">${esc(f.q)}</summary>
        <p style="margin:8px 0 0;color:#475569;line-height:1.6">${esc(f.a)}</p>
      </details>`).join("\n      ");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(metaDesc)}" />
  <meta name="keywords" content="${esc(scenario.title)}, AI tools, agent skills, MCP tools, ${scenario.slug}" />

  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(metaDesc)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="${esc(pageUrl)}" />
  <meta property="og:site_name" content="Agent Skills Hub" />
  <meta property="og:image" content="${esc(ogImage)}" />

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${esc(title)}" />
  <meta name="twitter:description" content="${esc(metaDesc)}" />
  <meta name="twitter:site" content="@GoSailGlobal" />
  <meta name="twitter:image" content="${esc(ogImage)}" />

  <link rel="canonical" href="${esc(pageUrl)}" />

  <script type="application/ld+json">
${itemListLd}
  </script>
  <script type="application/ld+json">
${breadcrumbLd}
  </script>
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
    <div style="max-width:900px;margin:40px auto;font-family:system-ui,-apple-system,sans-serif;padding:0 20px;color:#1e293b">
      <!-- Breadcrumb -->
      <nav style="font-size:13px;color:#64748b;margin-bottom:16px">
        <a href="/" style="color:#4f46e5;text-decoration:none">Home</a>
        <span style="margin:0 6px">&gt;</span>
        <span>Best Tools for ${esc(scenario.title)}</span>
      </nav>

      <!-- Title -->
      <h1 style="font-size:28px;margin:0 0 8px">Best AI Agent Skills for ${esc(scenario.title)}</h1>
      <p style="color:#64748b;margin:0 0 20px;line-height:1.6">${esc(scenario.description)}</p>

      <!-- Skill Cards -->
      <section>
        <h2 style="font-size:20px;margin:0 0 12px">Top ${skills.length} ${esc(scenario.title)} Tools</h2>
      ${skillCardsHtml}
      </section>

      <!-- Comparison Table -->
      <section style="margin-top:32px">
        <h2 style="font-size:20px;margin:0 0 12px">Comparison</h2>
        <div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:14px">
            <thead>
              <tr style="border-bottom:2px solid #e2e8f0;text-align:left">
                <th style="padding:8px;color:#64748b">Tool</th>
                <th style="padding:8px;color:#64748b;text-align:right">Stars</th>
                <th style="padding:8px;color:#64748b">Language</th>
                <th style="padding:8px;color:#64748b">License</th>
                <th style="padding:8px;color:#64748b;text-align:right">Score</th>
              </tr>
            </thead>
            <tbody>
        ${compRows}
            </tbody>
          </table>
        </div>
      </section>

      <!-- Related Scenarios -->
      ${relatedHtml ? `<section style="margin-top:32px">
        <h2 style="font-size:18px;margin:0 0 12px">Related Categories</h2>
        <div style="display:flex;flex-wrap:wrap;gap:4px">
        ${relatedHtml}
        </div>
      </section>` : ""}

      <!-- FAQ -->
      <section style="margin-top:32px">
        <h2 style="font-size:18px;margin:0 0 12px">Frequently Asked Questions</h2>
      ${faqHtml}
      </section>

      <!-- CTA -->
      <div style="margin:32px 0;text-align:center">
        <a href="/" style="display:inline-block;padding:10px 24px;background:#4f46e5;color:#fff;border-radius:8px;text-decoration:none;font-size:14px">Explore All 25,000+ Skills on Agent Skills Hub</a>
      </div>
    </div>
  </div>
  <noscript>
    <p style="text-align:center;padding:20px">Enable JavaScript for the full interactive experience.</p>
  </noscript>
</body>
</html>`;
}

/* ── Main ────────────────────────────────────────── */

async function main() {
  console.log("=== Scenario Landing Page Generator ===\n");

  // Load scenario keywords
  const keywordsPath = join(__dirname, "scenario-keywords.json");
  if (!existsSync(keywordsPath)) {
    console.error("scenario-keywords.json not found!");
    process.exit(1);
  }
  const scenarios = JSON.parse(readFileSync(keywordsPath, "utf-8"));
  console.log(`Loaded ${scenarios.length} scenario definitions`);

  // Load asset tags from built index.html
  const indexHtml = readFileSync(join(DIST, "index.html"), "utf-8");
  const assetTags = extractAssetTags(indexHtml);

  // Fetch skills
  console.log("Fetching skills from Supabase...");
  const allSkills = await fetchAllSkills();
  console.log(`Fetched ${allSkills.length} skills`);

  // Generate pages
  let generated = 0;
  let skipped = 0;
  const t0 = Date.now();

  for (const scenario of scenarios) {
    const skills = matchSkills(scenario, allSkills);
    if (!skills) {
      console.log(`  SKIP ${scenario.slug}: fewer than ${scenario.match.min_results} matches`);
      skipped++;
      continue;
    }

    const dir = join(DIST, "best", scenario.slug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(
      join(dir, "index.html"),
      buildScenarioHtml(scenario, skills, assetTags, scenarios),
    );
    console.log(`  \u2713 /best/${scenario.slug}/ (${skills.length} skills)`);
    generated++;
  }

  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`\nScenario pages: ${generated} generated, ${skipped} skipped (${elapsed}s)`);
}

main().catch((err) => {
  console.error("Failed to generate scenario pages:", err);
  process.exit(1);
});
