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
// Tightened to stop thin author pages from diluting crawl budget. GSC showed
// ~500 author pages "discovered – currently not indexed": Google reads a flood
// of thin aggregation pages as a low-value site. Concentrate on substantive
// authors so the submitted set is smaller but worth indexing.
// The TIGHTENED THRESHOLD below (≥3 skills & ≥300★, or ≥1000★ solo) is what
// removes thin pages. The cap only guards against runaway — keep it generous
// so genuinely substantive authors (e.g. 16 skills / 4474★) aren't cut just by
// ranking past an arbitrary line.
const AUTHOR_LIMIT = 500;              // hard cap on pre-rendered authors
const MIN_SKILLS = 3;                  // multi-skill authors need ≥3 skills…
const MIN_TOTAL_STARS = 300;           // …AND ≥300 cumulative stars
const SOLO_STAR_FLOOR = 1000;          // OR a single famous author (≥1000 stars)

/** Fetch verified masters + org builders (the same RPCs the SPA uses) so
 *  creator pages can be enriched LobeHub-style: real display name, bio, X
 *  handle, verified status → Person/Organization JSON-LD + sameAs links.
 *  Both are optional — a failed RPC degrades to plain author pages. */
async function fetchCreatorProfiles() {
  const rpc = async (fn) => {
    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/rpc/${fn}`, {
        method: "POST",
        headers: {
          apikey: SUPABASE_ANON_KEY,
          Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
          "Content-Type": "application/json",
        },
        body: "{}",
      });
      return res.ok ? await res.json() : null;
    } catch {
      return null;
    }
  };

  const masterMap = new Map(); // lowercase github (or alias) → master row
  const mastersData = await rpc("get_masters");
  const allMasters = [
    ...(mastersData?.masters ?? []),
    ...(mastersData?.emerging ?? []),
  ];
  for (const m of allMasters) {
    if (m.github) masterMap.set(String(m.github).toLowerCase(), m);
    for (const alias of m.github_aliases ?? []) {
      masterMap.set(String(alias).toLowerCase(), m);
    }
  }

  const orgSet = new Set(); // lowercase github org names
  const orgsData = await rpc("get_org_builders");
  for (const o of Array.isArray(orgsData) ? orgsData : []) {
    if (o.github) orgSet.add(String(o.github).toLowerCase());
  }

  console.log(`  Creator profiles: ${masterMap.size} master keys, ${orgSet.size} orgs`);
  return { masterMap, orgSet };
}

/** Person/Organization JSON-LD — the entity signal LobeHub-style collection
 *  pages feed Google/LLMs. sameAs ties the page to GitHub + X profiles. */
function buildCreatorJsonLd(group, master, isOrg) {
  const canonical = `${SITE}/${isOrg ? "organization" : "author"}/${group.author_name}/`;
  const displayName = master?.name || group.author_name;
  const sameAs = [`https://github.com/${group.author_name}`];
  if (master?.x_handle) {
    sameAs.push(`https://x.com/${String(master.x_handle).replace(/^@/, "")}`);
  }
  const entity = {
    "@context": "https://schema.org",
    "@type": isOrg ? "Organization" : "Person",
    name: displayName,
    alternateName: group.author_name,
    url: canonical,
    ...(group.author_avatar_url ? { image: group.author_avatar_url } : {}),
    ...(master?.bio ? { description: master.bio } : {}),
    sameAs,
  };
  const list = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: `Top AI agent skills by ${displayName}`,
    itemListElement: group.skills.slice(0, 8).map((s, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: s.repo_name,
      url: `${SITE}/skill/${s.repo_full_name}/`,
    })),
  };
  return `\n  <script type="application/ld+json">\n${JSON.stringify(entity, null, 2)}\n  </script>\n  <script type="application/ld+json">\n${JSON.stringify(list, null, 2)}\n  </script>`;
}

/** Fetch skills with author data (minimum fields, all rows). */
async function fetchAuthorSkills() {
  const skills = [];
  let lastId = 0;
  // Keyset by id, NOT deep OFFSET on stars.desc. Deep OFFSET (offset=100000)
  // forces Postgres to sort + skip 100K rows every page → exceeds the ~8s
  // statement_timeout the moment Supabase is slow → 57014 → failed deploy.
  // Author grouping re-sorts anyway, so fetch order doesn't matter.
  const limit = 300;
  const fields = [
    "id", "repo_full_name", "repo_name", "author_name", "author_avatar_url",
    "stars", "description", "category", "score",
    "quality_score", "security_grade",
  ].join(",");

  while (true) {
    const url = `${SUPABASE_URL}/rest/v1/skills?select=${fields}&order=id.asc&id=gt.${lastId}&limit=${limit}`;
    const res = await fetch(url, {
      headers: {
        apikey: SUPABASE_ANON_KEY,
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
      },
    });
    const data = await res.json();
    if (!Array.isArray(data) || !data.length) break;
    skills.push(...data);
    lastId = data[data.length - 1].id;
    if (data.length < limit) break;
  }
  return skills;
}

/** Group skills by author_name, sorted by total stars.
 *  `forceInclude` (lowercase names) bypasses the thin-page threshold — curated
 *  masters/orgs always get a page (their bio/verified content isn't thin, and
 *  the creator-flywheel play depends on every master having a shareable page). */
function groupByAuthor(skills, forceInclude = new Set()) {
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
      (g.skills.length >= MIN_SKILLS && g.total_stars >= MIN_TOTAL_STARS) ||
      g.total_stars >= SOLO_STAR_FLOOR ||
      forceInclude.has(String(g.author_name).toLowerCase());
    if (passesThreshold) qualified.push(g);
  }
  qualified.sort((a, b) => b.total_stars - a.total_stars);
  return qualified.slice(0, AUTHOR_LIMIT);
}

/** Build an SEO-optimized <noscript> summary for crawlers. Unique per author
 *  (intro + trust summary + 8 skills) so Google has a reason to index it, not
 *  a thin near-duplicate list. */
function buildSeoNoScript(group, master = null, isOrg = false) {
  const top = group.skills.slice(0, 8);
  const listItems = top
    .map((s) => {
      const safe = esc(s.repo_full_name);
      const desc = esc((s.description || "").slice(0, 140));
      const q = typeof s.quality_score === "number" ? ` · quality ${Math.round(s.quality_score)}/100` : "";
      const grade = s.security_grade && s.security_grade !== "unknown" ? ` · security: ${esc(s.security_grade)}` : "";
      return `<li><a href="${SITE}/skill/${safe}/">${esc(s.repo_name)}</a> — ${desc} (${starsK(s.stars || 0)}★${q}${grade})</li>`;
    })
    .join("");
  // trust summary
  const cats = [...new Set(group.skills.map((s) => s.category).filter(Boolean))].slice(0, 4).join(", ");
  const safeN = group.skills.filter((s) => s.security_grade === "safe").length;
  const scored = group.skills.filter((s) => typeof s.quality_score === "number");
  const avgQ = scored.length ? Math.round(scored.reduce((a, s) => a + s.quality_score, 0) / scored.length) : 0;
  const displayName = master?.name || group.author_name;
  const who = isOrg ? "organization behind" : "author of";
  const verifiedLine = master?.is_verified
    ? ` ${esc(displayName)} is a <strong>Verified Creator</strong> on AgentSkillsHub.`
    : "";
  const bioLine = master?.bio ? `<p>${esc(master.bio)}</p>` : "";
  const xLink = master?.x_handle
    ? ` · <a href="https://x.com/${esc(String(master.x_handle).replace(/^@/, ""))}" rel="noopener">Follow on X</a>`
    : "";
  return `
    <noscript>
      <h1>${esc(displayName)} — ${group.skills.length} Open-Source AI Agent Skills</h1>
      <p><strong>${esc(displayName)}</strong> is the ${who} ${group.skills.length} open-source AI agent skills and MCP servers${cats ? ` spanning ${esc(cats)}` : ""}, with a combined ${group.total_stars.toLocaleString()}+ GitHub stars. On AgentSkillsHub each is quality-scored (avg ${avgQ}/100) and security-graded${safeN ? ` — ${safeN} verified safe` : ""}.${verifiedLine}</p>
      ${bioLine}
      <h2>Top skills by ${esc(displayName)}</h2>
      <ul>${listItems}</ul>
      <p><a href="https://github.com/${esc(group.author_name)}">View ${esc(group.author_name)} on GitHub</a>${xLink} · <a href="${SITE}/">Explore audited agent skills</a></p>
    </noscript>`;
}

/** Generate HTML file for one author. */
function writeAuthorHtml(group, baseHtml, { masterMap, orgSet }) {
  const key = String(group.author_name).toLowerCase();
  const master = masterMap.get(key) || null;
  const isOrg = orgSet.has(key);
  const displayName = master?.name || group.author_name;
  // Name-search intent title (LobeHub pattern: "Guizang – Top 3 AI Agent
  // Skills"): people Google the creator's NAME — lead with it, add the
  // security angle only we can claim.
  const safeCountForTitle = group.skills.filter((s) => s.security_grade === "safe").length;
  const title = `${displayName} — Top ${group.skills.length} AI Agent Skills${safeCountForTitle ? " (Security-Graded)" : ""} · Agent Skills Hub`;
  const description = `${displayName}'s AI agent skills: ${group.skills.length} open-source skills & MCP servers, ${group.total_stars.toLocaleString()}+ GitHub stars${safeCountForTitle ? `, ${safeCountForTitle} security-verified safe` : ""}. Quality-scored on AgentSkillsHub.`;
  // Orgs live at /organization/{name}/ (their canonical); people at /author/.
  const ns = isOrg ? "organization" : "author";
  const canonical = `${SITE}/${ns}/${group.author_name}/`;
  const noscript = buildSeoNoScript(group, master, isOrg);
  const jsonLd = buildCreatorJsonLd(group, master, isOrg);

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

  // Inject Person/Organization + ItemList JSON-LD before </head>, and the
  // SEO noscript right before closing </body>
  html = html.replace("</head>", `${jsonLd}\n</head>`);
  html = html.replace("</body>", `${noscript}\n  </body>`);

  const outDir = join(DIST, ns, group.author_name);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, "index.html"), html);

  // Orgs briefly lived at /author/{org}/ (deployed 2026-07-03 morning) — leave
  // a redirect stub there so old links and any early crawls consolidate onto
  // the /organization/ canonical. Static hosting = meta refresh + canonical.
  if (isOrg) {
    const stubDir = join(DIST, "author", group.author_name);
    mkdirSync(stubDir, { recursive: true });
    writeFileSync(
      join(stubDir, "index.html"),
      `<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>${esc(displayName)} — moved</title>
<link rel="canonical" href="${canonical}">
<meta http-equiv="refresh" content="0;url=${canonical}">
<meta name="robots" content="noindex">
</head><body><p>Moved to <a href="${canonical}">${canonical}</a></p></body></html>`,
    );
  }
}

async function main() {
  console.log("👤 Generating author pages...");
  const baseHtml = readFileSync(join(DIST, "index.html"), "utf-8");
  console.log("  Fetching skills...");
  const skills = await fetchAuthorSkills();
  console.log(`  Loaded ${skills.length} skills`);

  const profiles = await fetchCreatorProfiles();
  const forceInclude = new Set([...profiles.masterMap.keys(), ...profiles.orgSet]);
  const groups = groupByAuthor(skills, forceInclude);
  console.log(`  Qualified authors: ${groups.length} (≥${MIN_SKILLS} skills & ≥${MIN_TOTAL_STARS}★, or ≥${SOLO_STAR_FLOOR}★ solo, or curated master/org; cap ${AUTHOR_LIMIT})`);

  let generated = 0;
  for (const g of groups) {
    try {
      writeAuthorHtml(g, baseHtml, profiles);
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
    is_org: profiles.orgSet.has(String(g.author_name).toLowerCase()),
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
