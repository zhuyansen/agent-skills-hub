/**
 * Build-time static HTML generator for /author/{username}/ pages.
 *
 * Strategy:
 *   - Aggregate skills by author_name.
 *   - Pre-render the Top N authors by total_stars (N = AUTHOR_LIMIT).
 *   - Each file is index.html with customized <title>, description, canonical,
 *     and a shell body listing the author's top skills (crawlers + first paint).
 *   - Everyone else still works via the SPA fallback at runtime.
 *
 * Run: node scripts/generate-author-pages.mjs  (after vite build)
 */

import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import {
  SUPABASE_URL, SUPABASE_ANON_KEY, SITE, CATEGORY_LABELS, esc, starsK, formatDate, analyticsTags,
  replaceShellContent, hasAuditPage,
} from "./shared-utils.mjs";
import { cleanDescription, fitClause } from "../src/lib/skillMeta.mjs";
import {
  THIN_AUTHOR_MAX_SKILLS, countNoun, authorDescription, authorIndexable, authorTitle,
} from "../src/lib/authorMeta.mjs";
import { skillPageRule } from "./skill-page-rule.mjs";

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
// The pre-hydration list: the first page AuthorPage.tsx shows once React mounts (its PAGE_SIZE).
// 8 until 2026-11-20, which left a creator's other repos reachable only through "related" links.
const SHELL_SKILLS = 30;
const SHELL_DESCRIPTION_WIDTH = 140;
const SHELL_LANGUAGES = 3;
// What a repo of each category is called in a sentence: [one, many].
const CATEGORY_NOUNS = {
  "mcp-server": ["MCP server", "MCP servers"],
  "claude-skill": ["Claude skill", "Claude skills"],
  "codex-skill": ["Codex skill", "Codex skills"],
  "agent-tool": ["agent tool", "agent tools"],
  "ai-skill": ["AI skill", "AI skills"],
  "llm-plugin": ["LLM plugin", "LLM plugins"],
  "youmind-plugin": ["YouMind plugin", "YouMind plugins"],
  education: ["education resource", "education resources"],
  uncategorized: ["AI tool", "AI tools"],
};

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

// A Skill under the 50-star floor has no /skill/ page (skill-page-rule.mjs). Until 2026-11-20
// every listed Skill linked to one: 308 dead links on 170 of the 500 author pages.
const hasSkillPage = skillPageRule();

/** Where a Skill's name leads: its /skill/ page when the build writes one, else the Repo on GitHub. */
function repoUrl(s) {
  return hasSkillPage(s) ? `${SITE}/skill/${s.repo_full_name}/` : (s.repo_url || `https://github.com/${s.repo_full_name}`);
}

function repoLink(s) {
  const outside = hasSkillPage(s) ? "" : ' rel="nofollow noopener" target="_blank"';
  return `<a href="${esc(repoUrl(s))}"${outside}>${esc(s.repo_name)}</a>`;
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
      url: repoUrl(s),
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
  // Superset of every field SkillCard renders — the creator-data snapshot
  // feeds real <SkillCard>s, and a missing numeric field (e.g. forks)
  // crashes on .toLocaleString(). Keep in sync with SkillCard's accesses.
  const fields = [
    "id", "repo_full_name", "repo_name", "author_name", "author_avatar_url",
    "stars", "forks", "description", "category", "score",
    "quality_score", "security_grade", "repo_url", "language", "topics",
    "platforms", "size_category", "repo_size_kb", "last_commit_at",
    "first_seen", "star_momentum",
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

/** Build the author's own pre-hydration shell content. Unique per author
 *  (intro + trust summary + what the repos have in common + up to SHELL_SKILLS
 *  skills, each with its kind, language and audit link) so Google has a reason
 *  to index it, not a thin near-duplicate list. 2026-11-20: the OpenSEO audit
 *  counted under 150 words on 97 of the 165 creator pages it reached; with one
 *  or two repos a page stays short, there is no more to say about them.
 *
 *  This used to be wrapped in <noscript>, which meant real visitors never saw
 *  it — they saw the HOMEPAGE copy that came along with index.html (its own
 *  <h1>, category grid and scenario list all live inside #root), and then
 *  watched React swap the whole thing out for the author page. Clarity caught
 *  the result on 2026-08-05: /author/asgeirtj/ logged 26 dead clicks and 7
 *  rage clicks in a SINGLE session — someone clicking homepage tiles that
 *  hydration had already replaced. Rendering it for real also stops every
 *  author page from shipping a duplicate homepage <h1> and body. */
function buildSeoNoScript(group, master = null, isOrg = false) {
  const count = group.skills.length;
  const listItems = group.skills
    .slice(0, SHELL_SKILLS)
    .map((s) => {
      const safe = esc(s.repo_full_name);
      const kind = [CATEGORY_LABELS[s.category], s.language].filter(Boolean).join(", ");
      const desc = esc(fitClause(cleanDescription(s.description, s.repo_name), SHELL_DESCRIPTION_WIDTH));
      const what = [kind && esc(kind), desc].filter(Boolean).join(". ");
      const q = typeof s.quality_score === "number" ? ` · quality ${Math.round(s.quality_score)}/100` : "";
      // The grade links to the repo's audit page where one exists (generate-audit-pages.mjs
      // applies the same hasAuditPage rule later in the build).
      const graded = s.security_grade && s.security_grade !== "unknown";
      const grade = !graded
        ? ""
        : hasAuditPage(s)
          ? ` · <a href="${SITE}/audit/${safe}/">security audit: ${esc(s.security_grade)}</a>`
          : ` · security: ${esc(s.security_grade)}`;
      return `<li>${repoLink(s)}${what ? ` — ${what}` : ""} (${starsK(s.stars || 0)}★${q}${grade})</li>`;
    })
    .join("");
  // trust summary
  const safeN = group.skills.filter((s) => s.security_grade === "safe").length;
  // Author pages list long tails; only claim "security-graded" for what actually is.
  const gradedN = group.skills.filter((s) => s.security_grade && s.security_grade !== "unknown").length;
  const gradedPhrase = count === 1
    ? (gradedN ? `security-graded${safeN ? " — verified safe" : ""}` : "has no security grade yet")
    : `${gradedN === count ? "security-graded" : `security-graded where a README exists (${gradedN} of ${count})`}${safeN ? ` — ${safeN} verified safe` : ""}`;
  const scored = group.skills.filter((s) => typeof s.quality_score === "number");
  const avgQ = scored.length ? Math.round(scored.reduce((a, s) => a + s.quality_score, 0) / scored.length) : 0;
  const displayName = master?.name || group.author_name;
  const who = isOrg ? "organization behind" : "author of";
  const breakdown = kindBreakdown(group.skills);
  const stars = `${group.total_stars.toLocaleString("en-US")}+ GitHub stars`;
  const made = count === 1
    ? `1 open-source ${CATEGORY_NOUNS[group.skills[0].category]?.[0] || "AI agent skill or MCP server"}, with ${stars}`
    : `${count} open-source AI agent skills and MCP servers${breakdown ? ` (${breakdown})` : ""}, with a combined ${stars}`;
  const scoredPhrase = count === 1 ? `it is quality-scored (${avgQ}/100)` : `each is quality-scored (avg ${avgQ}/100)`;
  const verifiedLine = master?.is_verified
    ? ` ${esc(displayName)} is a <strong>Verified Creator</strong> on AgentSkillsHub.`
    : "";
  const bioLine = master?.bio ? `<p>${esc(master.bio)}</p>` : "";
  const xLink = master?.x_handle
    ? ` · <a href="https://x.com/${esc(String(master.x_handle).replace(/^@/, ""))}" rel="noopener">Follow on X</a>`
    : "";
  const more = count > SHELL_SKILLS ? `<p>${SHELL_SKILLS} of ${count} shown, most-starred first.</p>` : "";
  return `
      <h1>${esc(displayName)} — ${countNoun(count, "Open-Source AI Agent Skill", "Open-Source AI Agent Skills")}</h1>
      <p><strong>${esc(displayName)}</strong> is the ${who} ${made}. On AgentSkillsHub ${scoredPhrase} and ${gradedPhrase}.${verifiedLine}</p>
      ${bioLine}
      ${factsLine(group)}
      <h2>${count === 1 ? "Skill" : "Top skills"} by ${esc(displayName)}</h2>
      <ul>${listItems}</ul>
      ${more}
      <p><a href="https://github.com/${esc(group.author_name)}">View ${esc(group.author_name)} on GitHub</a>${xLink} · <a href="${SITE}/">Explore audited agent skills</a></p>`;
}

/** "4 MCP servers, 2 agent tools, 1 Claude skill": what the repos are, most common first. */
function kindBreakdown(skills) {
  const counts = new Map();
  for (const s of skills) {
    if (CATEGORY_NOUNS[s.category]) counts.set(s.category, (counts.get(s.category) || 0) + 1);
  }
  return [...counts]
    .sort((a, b) => b[1] - a[1])
    .map(([category, n]) => countNoun(n, ...CATEGORY_NOUNS[category]))
    .join(", ");
}

/** What the repos have in common, from the catalog's own fields: most-starred repo, languages,
 *  latest commit. Empty when none of the three is known. */
function factsLine(group) {
  const facts = [];
  const [top] = group.skills;
  if (group.skills.length > 1 && top) {
    facts.push(`Most starred: ${repoLink(top)} (${starsK(top.stars || 0)}★).`);
  }
  const byLanguage = new Map();
  for (const s of group.skills) {
    if (s.language) byLanguage.set(s.language, (byLanguage.get(s.language) || 0) + 1);
  }
  const languages = [...byLanguage].sort((a, b) => b[1] - a[1]).slice(0, SHELL_LANGUAGES);
  if (languages.length) {
    const named = languages.map(([name, n]) => (group.skills.length > 1 ? `${esc(name)} (${n})` : esc(name))).join(", ");
    facts.push(`${languages.length === 1 ? "Language" : "Languages"}: ${named}.`);
  }
  const latest = group.skills.map((s) => s.last_commit_at).filter(Boolean).sort().pop();
  if (latest) facts.push(`Latest commit: <time datetime="${esc(latest)}">${formatDate(latest)}</time>.`);
  return facts.length ? `<p>${facts.join(" ")}</p>` : "";
}

/** Generate HTML file for one author. Returns whether the page asks to be indexed. */
function writeAuthorHtml(group, baseHtml, { masterMap, orgSet }) {
  const key = String(group.author_name).toLowerCase();
  const master = masterMap.get(key) || null;
  const isOrg = orgSet.has(key);
  const displayName = master?.name || group.author_name;
  // Name-search intent title (LobeHub pattern: "Guizang – Top 3 AI Agent
  // Skills"): people Google the creator's NAME — lead with it, add the
  // security angle only we can claim. Cut to what a results page shows in authorMeta.mjs.
  const safeCount = group.skills.filter((s) => s.security_grade === "safe").length;
  const title = authorTitle(displayName, group.skills.length, safeCount);
  const description = authorDescription(displayName, group.skills.length, safeCount, group.total_stars);
  // Orgs live at /organization/{name}/ (their canonical); people at /author/.
  const ns = isOrg ? "organization" : "author";
  const canonical = `${SITE}/${ns}/${group.author_name}/`;
  const shellBody = buildSeoNoScript(group, master, isOrg);
  const jsonLd = buildCreatorJsonLd(group, master, isOrg);

  let html = baseHtml;
  // index.html no longer ships a hardcoded canonical (dual-tag fix) — inject
  // a placeholder so the replace below always has a target.
  if (!html.includes('rel="canonical"')) {
    html = html.replace("</head>", '<link rel="canonical" href="__CANONICAL__" />\n</head>');
  }
  html = html
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
    )
    // X reads its own two tags before the og ones. Until 2026-11-20 they stayed the home
    // page's, so a creator page shared on X showed the home page's title and description.
    .replace(/<meta name="twitter:title" content="[^"]+"/, () => `<meta name="twitter:title" content="${esc(title)}"`)
    .replace(/<meta name="twitter:description" content="[^"]+"/, () => `<meta name="twitter:description" content="${esc(description)}"`);

  if (group.author_avatar_url) {
    html = html.replace(
      /<meta property="og:image" content="[^"]+"/,
      `<meta property="og:image" content="${esc(group.author_avatar_url)}"`,
    );
  }

  // One or two Skills and nobody wrote about the Author: live, linked, not indexed
  // (authorIndexable in authorMeta.mjs). index.html carries no robots tag of its own.
  const indexable = authorIndexable(group.skills.length, master);
  if (!indexable) {
    html = html.replace("</head>", '<meta name="robots" content="noindex, follow" />\n</head>');
  }

  // Inject Person/Organization + ItemList JSON-LD + analytics before </head>.
  // Author pages derive from index.html but stripped GA — see analyticsTags()
  // note (2026-07-29).
  html = html.replace("</head>", `${jsonLd}\n${analyticsTags()}\n</head>`);
  // Swap the homepage placeholder inside #root for this author's own content,
  // rather than appending after it — see replaceShellContent().
  html = replaceShellContent(html, shellBody);

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
${analyticsTags()}
</head><body><p>Moved to <a href="${canonical}">${canonical}</a></p></body></html>`,
    );
  }
  return indexable;
}

/** Static per-creator data snapshot → dist/creator-data/{name}.json.
 *  AuthorPage fetches this FIRST and only falls back to Supabase on a miss —
 *  creator pages stop depending on a live DB that (observed 2026-07-03) can
 *  take 6.5s/request or close connections outright. One flat namespace so the
 *  client never has to guess /author/ vs /organization/. */
function writeCreatorJson(group, { masterMap, orgSet }) {
  const key = String(group.author_name).toLowerCase();
  const master = masterMap.get(key) || null;
  const isOrg = orgSet.has(key);
  const items = group.skills.slice(0, 300).map((s) => ({
    id: s.id,
    repo_full_name: s.repo_full_name,
    repo_name: s.repo_name,
    repo_url: s.repo_url || `https://github.com/${s.repo_full_name}`,
    author_name: s.author_name,
    author_avatar_url: s.author_avatar_url || "",
    description: s.description || "",
    stars: s.stars || 0,
    forks: s.forks || 0,
    category: s.category || "",
    language: s.language || null,
    topics: s.topics || "[]",
    platforms: s.platforms || "[]",
    size_category: s.size_category || "unknown",
    repo_size_kb: s.repo_size_kb || 0,
    last_commit_at: s.last_commit_at || null,
    first_seen: s.first_seen || null,
    star_momentum: s.star_momentum ?? 0,
    score: s.score ?? 0,
    quality_score: s.quality_score ?? 0,
    security_grade: s.security_grade || null,
  }));
  const payload = {
    v: 1,
    generated_at: new Date().toISOString(),
    author_name: group.author_name,
    display_name: master?.name || group.author_name,
    avatar: group.author_avatar_url || "",
    is_org: isOrg,
    verified: !!master?.is_verified,
    bio: master?.bio || null,
    x_handle: master?.x_handle || null,
    total: group.skills.length,
    total_stars: group.total_stars,
    items,
  };
  const dir = join(DIST, "creator-data");
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, `${group.author_name}.json`), JSON.stringify(payload));
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
  const noindexed = new Set();
  for (const g of groups) {
    try {
      if (!writeAuthorHtml(g, baseHtml, profiles)) noindexed.add(g.author_name);
      writeCreatorJson(g, profiles);
      generated++;
    } catch (err) {
      console.warn(`  ⚠ Failed to generate ${g.author_name}: ${err.message}`);
    }
  }

  console.log(`✅ Generated ${generated} author pages (+ creator-data JSON) → dist/`);
  console.log(`  ${noindexed.size} noindex: ${THIN_AUTHOR_MAX_SKILLS} Skills or fewer, no Master bio or Verified Creator badge`);

  // Write author list for sitemap generator to consume
  const sitemapList = groups.map((g) => ({
    author_name: g.author_name,
    total_stars: g.total_stars,
    skill_count: g.skills.length,
    is_org: profiles.orgSet.has(String(g.author_name).toLowerCase()),
    indexable: !noindexed.has(g.author_name),
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
