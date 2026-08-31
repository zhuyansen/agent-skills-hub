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

import { readFileSync, mkdirSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import {
  SUPABASE_URL, SUPABASE_ANON_KEY, SITE, CATEGORY_LABELS,
  esc, starsK, formatDate, stripMarkdown, truncate, parseJsonArray, biAttrs,
  extractAssetTags, shouldIndex, fetchAllSkills, fetchReadmeMap, MIN_STARS_FOR_PAGE, trustBlock,
} from "./shared-utils.mjs";

// Hand-written per-category copy (mirror of src/data/categoryCopy.ts); the
// static /category/ shell shows this title + intro so Google reads the
// purpose-built landing copy, not the generic template.
const CATEGORY_COPY = JSON.parse(
  readFileSync(join(dirname(fileURLToPath(import.meta.url)), "category-copy.json"), "utf-8"),
);

// Reverse index: repo_full_name (lowercased) → scenarios that feature it. Lets
// each skill page link UP to the /best/ scenario guides it anchors — feeds the
// scenario pages internal-link equity from the high-star skill catalog. Uses
// the curated `featured` list (precise, cheap), not the full keyword match.
const FEATURED_IN_SCENARIOS = (() => {
  const scenarios = JSON.parse(
    readFileSync(join(dirname(fileURLToPath(import.meta.url)), "scenario-keywords.json"), "utf-8"),
  );
  const map = new Map();
  for (const sc of scenarios) {
    for (const repo of sc.match?.featured || []) {
      const key = repo.toLowerCase();
      if (!map.has(key)) map.set(key, []);
      map.get(key).push({ slug: sc.slug, title: sc.title });
    }
  }
  return map;
})();

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

/* ── Alternatives: topic-overlap + size-similar ── */

/**
 * Find alternative skills to the current one.
 * Strategy:
 *   1) Prefer same-category skills with overlapping topics (intent match).
 *   2) Filter: different author, star range 0.2x..5x (similar scale).
 *   3) Fall back to same-category top-star if not enough topic overlap.
 * Returns up to `limit` skills.
 */

/** Internal creator-page link when the static page exists (author pages are
 *  generated first in the build chain); falls back to GitHub. Un-orphans
 *  /author/ + /organization/ pages — Ahrefs 2026-07-11 found them link-less. */
function creatorLinkHtml(author) {
  const name = esc(author);
  if (existsSync(`dist/organization/${author}/index.html`))
    return `<a href="/organization/${name}/" style="color:#4f46e5;text-decoration:none">${name}</a>`;
  if (existsSync(`dist/author/${author}/index.html`))
    return `<a href="/author/${name}/" style="color:#4f46e5;text-decoration:none">${name}</a>`;
  return `<a href="https://github.com/${name}" style="color:#4f46e5;text-decoration:none">${name}</a>`;
}

function findAlternatives(skill, categoryIndex, topicIndex, limit = 6) {
  const currentTopics = parseJsonArray(skill.topics).map((t) => t.toLowerCase());
  const minStars = Math.max(50, Math.floor(skill.stars * 0.2));
  const maxStars = Math.max(100, Math.ceil(skill.stars * 5));

  const scored = new Map(); // repo_full_name -> {skill, score}

  const consider = (candidate, baseScore) => {
    if (!candidate) return;
    if (candidate.repo_full_name === skill.repo_full_name) return;
    if (candidate.author_name && skill.author_name && candidate.author_name === skill.author_name) return;
    if (candidate.stars < minStars || candidate.stars > maxStars) return;
    if (!shouldIndex(candidate)) return;

    // Topic overlap bonus
    const candTopics = parseJsonArray(candidate.topics).map((t) => t.toLowerCase());
    let overlap = 0;
    for (const t of currentTopics) {
      if (candTopics.includes(t)) overlap++;
    }

    const starsBoost = Math.log10(Math.max(candidate.stars, 1));
    const total = baseScore + overlap * 4 + starsBoost;
    const existing = scored.get(candidate.repo_full_name);
    if (!existing || existing.score < total) {
      scored.set(candidate.repo_full_name, { skill: candidate, score: total });
    }
  };

  // Pass 1: skills sharing any topic
  for (const topic of currentTopics) {
    const sharers = topicIndex.get(topic) || [];
    for (const s of sharers) consider(s, 5);
  }

  // Pass 2: same-category top-star fallback (weighted lower so topic matches win)
  const sameCat = categoryIndex.get(skill.category) || [];
  for (const s of sameCat) consider(s, 1);

  const sorted = [...scored.values()]
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((x) => x.skill);

  return sorted;
}

/* ── build HTML for one skill ──────────────────── */

function buildSkillHtml(skill, assetTags, compositions, skillById, categoryIndex, languageIndex, topicIndex) {
  const {
    repo_full_name, repo_url, repo_name, author_name, author_avatar_url,
    stars, forks, description, category, language, score, license,
    readme_content, last_commit_at, created_at, topics,
    quality_score, platforms, estimated_tokens, open_issues, total_commits,
    security_grade,
  } = skill;

  const indexed = shouldIndex(skill);
  const catLabel = CATEGORY_LABELS[category] || "AI Tool";
  const pageUrl = `${SITE}/skill/${repo_full_name}/`;
  // repo_url, not a re-derivation from repo_full_name: the two diverge when a
  // repo's canonical home moves and we retarget the link while freezing the
  // indexed page slug. The SPA already reads repo_url — the static shell used
  // to disagree with it, so crawlers saw a stale link the hydrated page didn't.
  const ghUrl = repo_url || `https://github.com/${repo_full_name}`;
  const ghLabel = ghUrl.replace(/^https?:\/\//, "");
  // Repos that 404 on GitHub (deleted, or the owning account was removed).
  // These pages stay indexed on purpose: "what happened to <repo>?" is a real
  // query with real volume — /skill/Manavarya09/design-extract/ still ranks
  // pos 4.3 for its own name — and nowhere else on the web answers it. What we
  // owe the visitor is an honest label, not a link that dumps them on a 404.
  const isGone = skill.repo_status === "gone";
  // Human-readable red-flag names. §20.0 of Google's rater guidelines says a
  // result that gives "reviews and reputation information" is very helpful for
  // a URL query, while one offering "usage statistics" usually is not. Naming
  // what the scan actually found is review information; a star count is not.
  const FLAG_COPY = {
    sudo_usage: "sudo usage", service_persistence: "installs a background service",
    curl_pipe_shell: "curl | sh installer", agent_config_theft: "reads agent config files",
    tunnel_service: "opens a tunnel service", eval_usage: "dynamic eval()",
    sensitive_env_vars: "reads sensitive env vars", agent_memory_theft: "reads agent memory",
    env_access: "environment access", subprocess_spawn: "spawns subprocesses",
    cron_persistence: "installs a cron job", sensitive_dir_access: "sensitive directory access",
    docker_privileged: "privileged Docker", backdoor_install: "backdoor install pattern",
    chmod_dangerous: "dangerous chmod", ssl_disabled: "disables SSL verification",
    env_file_read: "reads .env files", etc_sensitive_read: "reads /etc secrets",
    wget_pipe_shell: "wget | sh installer", runtime_install_exec: "installs at runtime",
    privilege_escalation: "privilege escalation", reverse_shell: "reverse shell",
    raw_ip_request: "hardcoded IP request", exfil_secrets_combo: "secret-exfiltration combo",
    rm_rf_root: "rm -rf on root paths", dev_tcp: "/dev/tcp socket", data_exfiltration: "data exfiltration",
    write_etc: "writes to /etc", shell_rc_inject: "injects into shell rc",
  };
  const flagList = (() => {
    let v = skill.security_flags;
    try {
      if (typeof v === "string") v = JSON.parse(v);
      if (typeof v === "string") v = JSON.parse(v);
    } catch { return []; }
    return Array.isArray(v) ? v : [];
  })();
  const flagNames = flagList.map((f) => FLAG_COPY[f] || f.replace(/_/g, " "));

  // The verdict, above the fold. This is the review information §20.0 rewards:
  // what was scanned, what was found, what was not. A SAFE grade with an empty
  // flag list is itself a finding — "we looked for these 11 categories and
  // found none" — and stating it is the whole reason to prefer this page over
  // the repo's own README, which cannot make that claim about itself.
  const GRADE_STYLE = {
    safe: ["#065f46", "#ecfdf5", "#a7f3d0"],
    caution: ["#92400e", "#fffbeb", "#fde68a"],
    unsafe: ["#991b1b", "#fef2f2", "#fecaca"],
    reject: ["#991b1b", "#fef2f2", "#fecaca"],
  };
  // A dead entry whose repo_url was retargeted at a DIFFERENT repository. The
  // two changes that produce this shipped days apart and neither knew about the
  // other, so /skill/Manavarya09/design-extract/ ended up saying "this repo
  // returns 404" directly above a "View on GitHub" button pointing at
  // arvindrk/extract-design-system — a live repo by a different author, with
  // nothing marking it as a different project. A reader can only conclude the
  // project moved there. It did not: different owner, different creation date,
  // different name, 3,334 stars against 167. Implying succession is a worse
  // failure for a trust-layer site than either the dead link or the bare label.
  const substitute = isGone && repo_url &&
    !repo_url.toLowerCase().endsWith(`/${repo_full_name.toLowerCase()}`)
    ? repo_url.replace(/^https?:\/\/github\.com\//, "")
    : null;
  const goneEn = `— ${repo_full_name} returns 404 on GitHub. It was deleted, or its owner's account was removed. The data below is our last successful snapshot.`;
  const goneZh = `—— ${repo_full_name} 在 GitHub 上已返回 404,可能是仓库被删除或作者账号已注销。下方数据是我们最后一次成功抓取的快照。`;
  const subEn = substitute
    ? ` The GitHub link below points to ${substitute}, a SEPARATE project by a different author that solves the same problem — not a continuation of this one.`
    : "";
  const subZh = substitute
    ? ` 下方 GitHub 链接指向 ${substitute},那是另一位作者解决同类问题的**独立项目**,并非本项目的延续。`
    : "";
  const goneBanner = isGone
    ? `<div style="margin:16px 0;padding:12px 16px;border:1px solid #fecaca;background:#fef2f2;border-radius:8px;font-size:14px;color:#991b1b">
        <strong ${biAttrs("Repository no longer available", "仓库已下架")}>Repository no longer available</strong>
        <span ${biAttrs(goneEn + subEn, goneZh + subZh)}>${esc(goneEn + subEn)}</span>
      </div>`
    : "";
  // /audit/ page exists only for graded skills (stars >= 50 + a real grade).
  // Link to it so the audit island gets inbound equity from skill pages.
  const hasAudit = ["safe", "caution", "unsafe", "reject"].includes(
    security_grade,
  );
  const auditUrl = `/audit/${repo_full_name}/`;
  const scenariosFeaturing =
    FEATURED_IN_SCENARIOS.get(repo_full_name.toLowerCase()) || [];
  const ogImage = `${SITE}/og-image.png`;

  // SEO-optimized title: exact repo_full_name matches brand-name queries
  // (e.g. "higgsfield-seedance2-jineng" hit 19.1% CTR in GSC data 2026-04).
  // Full name goes first so Google SERP shows it at line 1.
  const title = `${repo_full_name} — security grade & quality score | Agent Skills Hub`;
  // Lead the snippet with the VERDICT, not the repo's own blurb.
  //
  // Nearly every query these pages win is what Google's rater guidelines call a
  // Website query — specifically an "imperfect URL query" (§12.7.3): strings
  // like [manavarya09/design-extract] or [ppt master codex] that look like a
  // URL but do not load. The user has one specific page in mind, and its target
  // is the GitHub repo, which will always outrank us for it.
  //
  // §20.0 says what the runner-up slot is for: "Results that give reviews and
  // reputation information can be very helpful for a URL query" — a review site
  // rates Highly Meets for [potterybarn.com]. And it draws the line we were on
  // the wrong side of: "websites that offer usage statistics about a website
  // are not usually helpful results for URL queries."
  //
  // The old description was exactly that — the repo's own blurb (which GitHub
  // already shows, so zero added value) plus a star count. It never stated the
  // one thing only we have. The grade goes first now; the blurb only fills the
  // remaining room.
  const GRADE_COPY = {
    safe: "SAFE",
    caution: "CAUTION",
    unsafe: "UNSAFE",
    reject: "REJECT",
  };
  const gradeLabel = GRADE_COPY[security_grade];

  const verdictBlock = (() => {
    if (isGone || !gradeLabel) return "";
    const [fg, bg, br] = GRADE_STYLE[security_grade] || GRADE_STYLE.caution;
    const finding = flagNames.length
      ? `Flagged: ${flagNames.slice(0, 4).map(esc).join(", ")}${flagNames.length > 4 ? ` and ${flagNames.length - 4} more` : ""}.`
      : "No red flags found in any of the 11 categories \u2014 no credential harvesting, no data exfiltration, no curl-pipe-shell installer.";
    const q = typeof quality_score === "number" ? Math.round(quality_score) : null;
    return `<section style="margin:0 0 16px;padding:14px 16px;border:1px solid ${br};background:${bg};border-radius:10px">
        <h2 style="font-size:16px;color:${fg};margin:0 0 6px">Security audit verdict: ${esc(gradeLabel)}${q !== null ? ` \u00b7 quality ${q}/100` : ""}</h2>
        <p style="margin:0;line-height:1.6;color:${fg};font-size:14px">${finding} Scanned against the SlowMist agent-security taxonomy, refreshed every 8 hours.${hasAudit ? ` <a href="${esc(auditUrl)}" style="color:${fg};font-weight:600">Full audit &rarr;</a>` : ""}</p>
      </section>`;
  })();
  const qualityPart = typeof quality_score === "number"
    ? ` · quality ${Math.round(quality_score)}/100`
    : "";
  // A deleted repo must not be advertised as SAFE. That grade describes a
  // snapshot of code that no longer exists, and this is the highest-CTR page
  // type we have — /skill/Manavarya09/design-extract/ runs 18.6% at position
  // 3.7 precisely because it answers "what happened to this repo?" honestly.
  // Saying "SAFE" in the snippet and "no longer available" on the page would
  // trade that away.
  const verdict = isGone
    ? `Repository deleted from GitHub. Last audit before removal: ${gradeLabel || "ungraded"}${qualityPart}.`
    : gradeLabel
      ? `Security grade: ${gradeLabel}${qualityPart}.`
      : `Not yet audited${qualityPart}.`;
  // Measure the real prefix rather than estimating it — the previous arithmetic
  // undercounted the fixed clause and produced 185-189 char descriptions, which
  // Google truncates around 155.
  // Build in priority order and stop when the budget runs out, so a long repo
  // name can never push the description past what Google shows (~155). The
  // verdict is never sacrificed; the clause after it is, then the blurb.
  const LIMIT = 155;
  const clause = isGone
    ? ` Archived record of ${repo_full_name} on Agent Skills Hub.`
    : ` Independent audit of ${repo_full_name} against 11 red-flag categories.`;
  let metaDesc = verdict;
  if (metaDesc.length + clause.length <= LIMIT) metaDesc += clause;
  const room = LIMIT - metaDesc.length - 1;
  if (description && room > 25) {
    metaDesc += ` ${description.slice(0, room).trim()}${description.length > room ? "…" : ""}`;
  }

  // README excerpt — expanded to 1200 chars for content depth (improves indexability)
  const readmeText = stripMarkdown(readme_content);
  const excerpt = readmeText
    ? truncate(readmeText, 1200)
    : (description || `${repo_name} is a ${catLabel.toLowerCase()} by ${author_name}.`);

  const topicsList = parseJsonArray(topics);
  const platformsList = parseJsonArray(platforms);
  const keywords = [repo_name, author_name, catLabel, ...topicsList.slice(0, 5), "Agent Skills", "GitHub"].join(", ");

  // Compatible skills internal links (only to indexed pages)
  const compLinks = compositions.slice(0, 8).map((c) => {
    const target = skillById.get(c.compatible_skill_id);
    if (!target || !shouldIndex(target)) return null;
    return { name: target.repo_name, slug: target.repo_full_name, score: c.compatibility_score, reason: c.reason };
  }).filter(Boolean).slice(0, 5);

  // Same-category links (top 10, excluding self, only indexed pages)
  const sameCatSkills = (categoryIndex.get(category) || [])
    .filter((s) => s.repo_full_name !== repo_full_name && shouldIndex(s))
    .slice(0, 10);

  // Same-language links (top 5, excluding self, only indexed pages)
  const sameLangSkills = language
    ? (languageIndex.get(language) || [])
      .filter((s) => s.repo_full_name !== repo_full_name && shouldIndex(s))
      .slice(0, 5)
    : [];

  // Alternatives — topic overlap + similar size, different author, same category preferred
  const alternatives = findAlternatives(skill, categoryIndex, topicIndex, 6);

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
    a: `You can find installation instructions and usage details in the ${repo_name} GitHub repository at ${ghLabel}. The project has ${starsK(stars)} stars and ${forks} forks, indicating an active community.`,
  });
  if (license && license !== "NOASSERTION") {
    faqItems.push({
      q: `What license does ${repo_name} use?`,
      a: `${repo_name} is released under the ${license} license, making it free to use and modify according to the license terms.`,
    });
  }
  if (alternatives.length > 0) {
    const altNames = alternatives.slice(0, 3).map((a) => a.repo_name).join(", ");
    faqItems.push({
      q: `What are the best alternatives to ${repo_name}?`,
      a: `The top alternatives to ${repo_name} on Agent Skills Hub include ${altNames}. Each offers a different approach to the same problem space — compare them side-by-side by stars, quality score, and community activity.`,
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
    interactionStatistic: stars > 0 ? {
      "@type": "InteractionCounter",
      interactionType: "https://schema.org/LikeAction",
      userInteractionCount: stars,
    } : undefined,
  }, null, 2);

  // JSON-LD: BreadcrumbList
  const breadcrumbLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE },
      { "@type": "ListItem", position: 2, name: catLabel, item: `${SITE}/category/${category}/` },
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
    `<tr><td>Category</td><td><a href="/category/${esc(category)}/">${esc(catLabel)}</a></td></tr>`,
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
          <li style="margin:6px 0"><a href="/skill/${esc(c.slug)}/" style="color:#4f46e5;text-decoration:none;font-weight:500">${esc(c.name)}</a> <span style="color:#94a3b8;font-size:13px">— ${esc(c.reason)} (${Math.round(c.score * 100)}%)</span></li>`).join("")}
        </ul>
      </section>`
    : "";

  // Alternatives HTML — explicitly targets "{repo_name} alternative" queries
  // (exact-phrase match matters for SERP snippets — per aaron-he-zhu audit).
  const alternativesHtml = alternatives.length > 0
    ? `<section style="margin-top:20px">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">${esc(repo_name)} alternative? Top ${alternatives.length} similar tools</h2>
        <p style="color:#64748b;font-size:14px;margin-bottom:12px">Looking for a ${esc(repo_name)} alternative? If you're comparing ${esc(repo_name)} with other ${esc(catLabel.toLowerCase())} tools, these ${alternatives.length} projects are the closest alternatives on Agent Skills Hub — ranked by topic overlap, star count, and community traction.</p>
        <ul style="list-style:none;padding:0">${alternatives.map((a) => {
          const altDesc = a.description ? esc(a.description.slice(0, 110)) : "";
          return `
          <li style="margin:8px 0;padding:10px 12px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0">
            <a href="/skill/${esc(a.repo_full_name)}/" style="color:#4f46e5;text-decoration:none;font-weight:600">${esc(a.repo_name)}</a>
            <span style="color:#94a3b8;font-size:13px"> by ${esc(a.author_name)} · ⭐ ${starsK(a.stars)}</span>
            ${altDesc ? `<p style="margin:4px 0 0;color:#475569;font-size:13px;line-height:1.5">${altDesc}</p>` : ""}
          </li>`;
        }).join("")}
        </ul>
      </section>`
    : "";

  // Same-category links HTML
  const sameCatHtml = sameCatSkills.length > 0
    ? `<section style="margin-top:20px">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">More ${esc(catLabel)} Tools</h2>
        <p style="color:#64748b;font-size:14px;margin-bottom:8px">Explore other popular ${esc(catLabel.toLowerCase())} tools:</p>
        <ul style="list-style:none;padding:0">${sameCatSkills.map((s) => `
          <li style="margin:4px 0"><a href="/skill/${esc(s.repo_full_name)}/" style="color:#4f46e5;text-decoration:none">${esc(s.repo_name)}</a> <span style="color:#94a3b8;font-size:13px">⭐ ${starsK(s.stars)}</span></li>`).join("")}
        </ul>
        <a href="/category/${esc(category)}/" style="color:#4f46e5;font-size:14px">View all ${esc(catLabel)} tools →</a>
      </section>`
    : "";

  // Same-language links HTML
  const sameLangHtml = sameLangSkills.length > 0
    ? `<section style="margin-top:20px">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">Popular ${esc(language)} Agent Tools</h2>
        <ul style="list-style:none;padding:0">${sameLangSkills.map((s) => `
          <li style="margin:4px 0"><a href="/skill/${esc(s.repo_full_name)}/" style="color:#4f46e5;text-decoration:none">${esc(s.repo_name)}</a> <span style="color:#94a3b8;font-size:13px">⭐ ${starsK(s.stars)} · ${esc(CATEGORY_LABELS[s.category] || "AI Tool")}</span></li>`).join("")}
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
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />${robotsMeta}
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
  <script defer data-domain="agentskillshub.top" src="https://plausible.io/js/script.js"></script>
</head>
<body>
  <div id="root">
    <!-- Static SEO content — replaced by React on hydration -->
    <div style="max-width:800px;margin:40px auto;font-family:system-ui,-apple-system,sans-serif;padding:0 20px;color:#1e293b">
      <!-- Breadcrumb -->
      <nav style="font-size:13px;color:#64748b;margin-bottom:16px">
        <a href="/" style="color:#4f46e5;text-decoration:none">Home</a>
        <span style="margin:0 6px">&gt;</span>
        <a href="/category/${esc(category)}/" style="color:#4f46e5;text-decoration:none">${esc(catLabel)}</a>
        <span style="margin:0 6px">&gt;</span>
        <span>${esc(repo_name)}</span>
      </nav>

      <!-- Title & Author -->
      <!-- h1 keeps repo_name first so it still matches the query verbatim, then
           states the verdict. Google's §20.0 puts "reviews and reputation
           information" in the helpful bucket for URL queries and "usage
           statistics" in the unhelpful one; the old heading ("X — Codex Skill
           by Y") was neither, and the audit result — the only thing here that
           GitHub does not already show — appeared nowhere above the fold. -->
      <h1 style="font-size:28px;margin:0 0 8px">${esc(repo_name)}${
        isGone
          ? " — repository deleted, archived audit"
          : gradeLabel
            ? ` — security grade ${esc(gradeLabel)}${typeof quality_score === "number" ? `, quality ${Math.round(quality_score)}/100` : ""}`
            : " — not yet audited"
      }</h1>
      ${goneBanner}
      ${verdictBlock}
      <p style="color:#64748b;margin:0 0 8px">
        by ${creatorLinkHtml(author_name)}
        &middot; <a href="/category/${esc(category)}/" style="color:#4f46e5;text-decoration:none">${esc(catLabel)}</a>
        &middot; &#9733; ${starsK(stars)}
      </p>
      <!-- Freshness signal for E-E-A-T -->
      <p style="color:#94a3b8;font-size:13px;margin:0 0 16px">
        ${last_commit_at ? `Last updated: <time datetime="${last_commit_at}">${formatDate(last_commit_at)}</time> &middot; ` : ""}Indexed by AgentSkillsHub &middot; Auto-synced every 8h
      </p>
      ${hasAudit ? `<p style="margin:0 0 16px">
        <a href="${esc(auditUrl)}" style="display:inline-flex;align-items:center;gap:6px;font-size:14px;font-weight:600;color:#4f46e5;text-decoration:none">&#128274; Is ${esc(repo_name)} safe to install? View the security audit &rarr;</a>
      </p>` : ""}
      ${scenariosFeaturing.length ? `<p style="margin:0 0 16px;font-size:14px;color:#475569">
        Featured in: ${scenariosFeaturing.map((s) => `<a href="/best/${esc(s.slug)}/" style="color:#4f46e5;text-decoration:none">${esc(s.title)}</a>`).join(" &middot; ")}
      </p>` : ""}

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

      <!-- Alternatives (directly targets "X alternative" queries) -->
      ${alternativesHtml}

      <!-- Same Category -->
      ${sameCatHtml}

      <!-- Same Language -->
      ${sameLangHtml}

      <!-- FAQ -->
      ${faqHtml}

      <!-- Trust / methodology (E-E-A-T: how the grade is made, who is responsible) -->
      ${trustBlock()}

      <!-- Links -->
      <div style="margin:24px 0;display:flex;gap:16px;flex-wrap:wrap">
        <a href="${esc(ghUrl)}" style="display:inline-block;padding:8px 20px;background:#1e293b;color:#fff;border-radius:8px;text-decoration:none;font-size:14px" ${
          substitute
            ? biAttrs(`View alternative: ${substitute} →`, `查看替代项目:${substitute} →`)
            : biAttrs("View on GitHub →", "在 GitHub 上查看 →")
        }>${substitute ? `View alternative: ${esc(substitute)} &rarr;` : "View on GitHub &rarr;"}</a>
        <a href="/category/${esc(category)}/" style="display:inline-block;padding:8px 20px;background:#f0f0ff;color:#4f46e5;border-radius:8px;text-decoration:none;font-size:14px">Browse ${esc(catLabel)} tools</a>
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
  const pageUrl = `${SITE}/category/${catSlug}/`;
  const copy = CATEGORY_COPY[catSlug];
  const title = copy
    ? `${copy.title} | Agent Skills Hub`
    : `Best ${catLabel} — ${catSkills.length}+ Open-Source Skills & MCP Servers | Agent Skills Hub`;
  const metaDesc = copy
    ? copy.intro
    : `Browse ${catSkills.length}+ open-source ${catLabel} — quality-scored, ranked by stars, compared side-by-side. Updated every 8 hours.`;
  const catHeading = copy ? copy.heading : `Best ${catLabel}`;

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
        url: `${SITE}/skill/${s.repo_full_name}/`,
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
        <td style="padding:8px"><a href="/skill/${esc(s.repo_full_name)}/" style="color:#4f46e5;text-decoration:none;font-weight:500">${esc(s.repo_name)}</a><br><span style="color:#94a3b8;font-size:13px">${desc}</span></td>
        <td style="padding:8px;text-align:right;white-space:nowrap;font-size:14px">&#9733; ${starsK(s.stars)}</td>
        <td style="padding:8px;color:#64748b;font-size:13px">${esc(s.language || "")}</td>
      </tr>`;
  }).join("\n      ");

  const otherCats = allCategories
    .filter((c) => c !== catSlug)
    .map((c) => `<a href="/category/${esc(c)}/" style="display:inline-block;padding:4px 12px;margin:3px;border-radius:16px;background:#f8fafc;border:1px solid #e2e8f0;color:#475569;font-size:13px;text-decoration:none">${esc(CATEGORY_LABELS[c] || c)}</a>`)
    .join("");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
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
  <script defer data-domain="agentskillshub.top" src="https://plausible.io/js/script.js"></script>
</head>
<body>
  <div id="root">
    <div style="max-width:900px;margin:40px auto;font-family:system-ui,-apple-system,sans-serif;padding:0 20px;color:#1e293b">
      <nav style="font-size:13px;color:#64748b;margin-bottom:16px">
        <a href="/" style="color:#4f46e5;text-decoration:none">Home</a>
        <span style="margin:0 6px">&gt;</span>
        <span>${esc(catLabel)}</span>
      </nav>

      <h1 style="font-size:28px;margin:0 0 8px">${esc(catHeading)}</h1>
      <p style="color:#64748b;margin:0 0 16px">${catSkills.length}+ open-source ${esc(catLabel.toLowerCase())} tools ranked by stars</p>

      <section style="margin:0 0 24px;padding:16px 20px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;line-height:1.7">
        <h2 style="font-size:16px;margin:0 0 8px;color:#334155">What are ${esc(catLabel)} tools?</h2>
        <p style="margin:0 0 8px;font-size:14px;color:#475569">${copy ? esc(copy.intro) : `${esc(catLabel)} tools are open-source packages that extend AI coding agents like Claude Code, OpenAI Codex, Gemini CLI, and other AI assistants. They provide specialized capabilities ranging from code generation and debugging to API integration and workflow automation.`}</p>
        <p style="margin:0;font-size:14px;color:#475569">Agent Skills Hub indexes ${catSkills.length}+ ${esc(catLabel.toLowerCase())} tools from GitHub, ranked by community adoption (stars), code quality scores, and compatibility with popular AI agents. The top languages in this category are ${catSkills.slice(0, 50).reduce((langs, s) => { if (s.language && !langs.includes(s.language)) langs.push(s.language); return langs; }, []).slice(0, 5).join(", ") || "various languages"}.</p>
      </section>

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

  // readme_content is no longer in the bulk catalog — pull it only for the
  // stars-gated subset that actually renders a page, then attach by id.
  const readmes = await fetchReadmeMap(MIN_STARS_FOR_PAGE);
  for (const s of skills) {
    const r = readmes.get(s.id);
    if (r) s.readme_content = r;
  }

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

  // Build topic index: topic(lowercase) → top skills (by stars) that have it.
  // Cap per-topic list to keep Alternatives lookup O(topics * limit).
  const topicIndex = new Map();
  for (const s of skills) {
    if (!s.topics) continue;
    const topics = parseJsonArray(s.topics);
    for (const t of topics) {
      const key = t.toLowerCase();
      if (!topicIndex.has(key)) topicIndex.set(key, []);
      const arr = topicIndex.get(key);
      if (arr.length < 40) arr.push(s); // already sorted by stars desc
    }
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

    // Phase 2.1: Only generate pages for skills worth crawling (stars >= MIN_STARS_FOR_PAGE)
    const indexed = shouldIndex(skill);
    if (skill.stars < MIN_STARS_FOR_PAGE) {
      skipped++;
      continue;
    }

    const [owner, repo] = parts;
    const dir = join(distDir, "skill", owner, repo);
    mkdirSync(dir, { recursive: true });

    const skillComps = compositions.get(skill.id) || [];
    writeFileSync(
      join(dir, "index.html"),
      buildSkillHtml(skill, assetTags, skillComps, skillById, categoryIndex, languageIndex, topicIndex),
    );
    ok++;

    if (indexed) indexedCount++;
    else noindexCount++;
  }

  const elapsed1 = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`Skill pages: ${ok} generated (${indexedCount} indexed, ${noindexCount} noindex), ${skipped} skipped (${elapsed1}s)`);

  // Generate category pages — use actual categories from data, not hardcoded list
  const t1 = Date.now();
  const allCategories = [...new Set(skills.map((s) => s.category))].filter(Boolean);
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

  // Update dist/index.html with actual skill count (for SEO meta tags)
  const indexPath = join(distDir, "index.html");
  try {
    let indexHtml = readFileSync(indexPath, "utf-8");
    const countK = Math.floor(skills.length / 1000) * 1000;
    const countStr = countK.toLocaleString() + "+";
    // Replace any "X,000+" pattern in meta descriptions
    const updated = indexHtml.replace(/\d{1,3},000\+/g, countStr);
    if (updated !== indexHtml) {
      writeFileSync(indexPath, updated);
      console.log(`Updated dist/index.html: skill count → ${countStr}`);
    }
  } catch (e) {
    console.warn("Could not update index.html count:", e.message);
  }
}

main().catch((err) => {
  console.error("Failed to generate pages:", err);
  process.exit(1);
});
