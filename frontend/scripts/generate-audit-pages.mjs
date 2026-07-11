/**
 * Build-time /audit/{owner}/{repo}/ pages — the "is X safe?" pSEO moat.
 *
 * Only AgentSkillsHub can answer "is <skill> safe to install" at scale (117K
 * scanned, security-graded). Each page is a focused audit answer: grade,
 * plain-English verdict, red flags, quality score, check-before-install list,
 * FAQPage JSON-LD — distinct framing from the /skill/ detail page (which is
 * about WHAT the skill is; this is about WHETHER to trust it).
 *
 * PURE STATIC (no SPA bundle): the app has no /audit/ route, so hydrating
 * would client-redirect to / and Google would treat the page as a soft
 * redirect. Links route humans to /analyzer (live scan) and /skill/ (detail).
 *
 * Scope: graded (non-unknown) skills with stars >= MIN_STARS_FOR_AUDIT.
 * Un-audited skills get no page — a page whose answer is "nobody knows" is
 * thin content; the long tail is served by the live /analyzer instead.
 *
 * Run: node scripts/generate-audit-pages.mjs  (after vite build)
 */

import { mkdirSync, writeFileSync, existsSync } from "fs";
import { join } from "path";
import {
  SITE, CATEGORY_LABELS, esc, starsK, formatDate, parseJsonArray,
  fetchAllSkills,
} from "./shared-utils.mjs";

// Matches MIN_STARS_FOR_PAGE (skill pages). At 20 this produced 11.7K pages /
// 99MB, pushing dist toward GitHub Pages' 1GB cap — 50 keeps the head of the
// "is X safe" query volume and leaves the long tail to the live /analyzer.
const MIN_STARS_FOR_AUDIT = 50;

const GRADES = {
  safe: {
    label: "SAFE",
    color: "#16a34a",
    bg: "#f0fdf4",
    icon: "✓",
    verdictEn:
      "Reviewed, no blocking issues found — reasonable for general use. Still confirm credential handling before production use.",
    verdictZh:
      "已审查，未发现阻断性问题 —— 一般使用没问题。上生产前仍需确认凭证的处理方式。",
    answerEn: (name) =>
      `Yes — ${name} passed AgentSkillsHub's rule-based security scan with no dangerous patterns detected. As with any third-party skill, confirm what credentials it requests before production use.`,
  },
  caution: {
    label: "CAUTION",
    color: "#d97706",
    bg: "#fffbeb",
    icon: "⚠",
    verdictEn:
      "Has caution flags — fine for personal trials; review credentials and maintainer before brand or production use.",
    verdictZh:
      "存在需注意的信号 —— 个人尝试可以；接入品牌或生产环境前，请先核查凭证与维护者。",
    answerEn: (name) =>
      `Use with caution — ${name} triggered warning flags in AgentSkillsHub's security scan. It may be fine for personal trials, but review its credential handling and maintainer before brand or production use.`,
  },
  unsafe: {
    label: "UNSAFE",
    color: "#dc2626",
    bg: "#fef2f2",
    icon: "✕",
    verdictEn:
      "Flagged unsafe — do NOT run against real credentials or production data.",
    verdictZh: "被标记为不安全 —— 不要用真实凭证或生产数据运行它。",
    answerEn: (name) =>
      `No — ${name} was flagged UNSAFE by AgentSkillsHub's security scan. Do not run it against real credentials or production data.`,
  },
  reject: {
    label: "REJECT",
    color: "#b91c1c",
    bg: "#fef2f2",
    icon: "⛔",
    verdictEn: "Rejected — known serious problems. Avoid.",
    verdictZh: "已拒绝 —— 存在已知严重问题，请避开。",
    answerEn: (name) =>
      `No — ${name} is REJECTED by AgentSkillsHub: known serious security problems. Avoid it.`,
  },
};

/** Human-readable red-flag names (scanner emits snake_case identifiers). */

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

function flagLabel(f) {
  return String(f).replace(/[_-]+/g, " ");
}

function pageHtml(skill, related = []) {
  const {
    repo_full_name, repo_name, author_name, description, stars, category,
    language, license, last_commit_at, quality_score, security_grade,
  } = skill;
  const g = GRADES[security_grade];
  const catLabel = CATEGORY_LABELS[category] || category || "AI agent tool";
  const categoryUrl = category ? `/category/${category}/` : "/";
  const pageUrl = `${SITE}/audit/${repo_full_name}/`;
  const skillUrl = `${SITE}/skill/${repo_full_name}/`;
  const analyzerUrl = `/analyzer?repo=${encodeURIComponent(`https://github.com/${repo_full_name}`)}`;
  const flags = parseJsonArray(skill.security_flags);

  const title = `Is ${repo_name} Safe? Security Audit of ${repo_full_name} — Agent Skills Hub`;
  const metaDesc = `${repo_full_name} security audit: graded ${g.label} by AgentSkillsHub's scan of 130,000+ AI agent skills & MCP servers. ${
    flags.length ? `${flags.length} flag${flags.length > 1 ? "s" : ""} found. ` : "No dangerous patterns found. "
  }Quality score ${Math.round(quality_score || 0)}/100.`;

  const faqLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: `Is ${repo_full_name} safe to install?`,
        acceptedAnswer: { "@type": "Answer", text: g.answerEn(repo_name) },
      },
      {
        "@type": "Question",
        name: `What security grade does ${repo_name} have?`,
        acceptedAnswer: {
          "@type": "Answer",
          text: `${repo_name} is graded ${g.label} by AgentSkillsHub's rule-based security scan (SlowMist 11 red-flag categories). ${g.verdictEn}`,
        },
      },
    ],
  }, null, 2);

  const breadcrumbLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE },
      { "@type": "ListItem", position: 2, name: catLabel, item: `${SITE}${categoryUrl}` },
      { "@type": "ListItem", position: 3, name: repo_full_name, item: pageUrl },
    ],
  }, null, 2);

  const flagsHtml = flags.length
    ? `<h2 style="font-size:18px;margin:24px 0 8px">Red flags detected (${flags.length})</h2>
      <ul style="line-height:1.8;color:#475569;padding-left:20px">
        ${flags.map((f) => `<li>\u{1F6A9} <code>${esc(flagLabel(f))}</code></li>`).join("\n        ")}
      </ul>`
    : `<p style="color:#475569;line-height:1.6">No dangerous patterns were detected: no credential exfiltration, no obfuscated downloads, no sandbox-escape attempts, no prompt-injection markers.</p>`;

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(metaDesc)}" />
  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(metaDesc)}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="${esc(pageUrl)}" />
  <meta property="og:site_name" content="Agent Skills Hub" />
  <meta property="og:image" content="${SITE}/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:site" content="@GoSailGlobal" />
  <link rel="canonical" href="${esc(pageUrl)}" />
  <script type="application/ld+json">
${faqLd}
  </script>
  <script type="application/ld+json">
${breadcrumbLd}
  </script>
  <script defer data-domain="agentskillshub.top" src="https://plausible.io/js/script.js"></script>
  <script type="text/javascript">(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window, document, "clarity", "script", "wh16g932g8");</script>
</head>
<body style="margin:0;font-family:system-ui,-apple-system,sans-serif;color:#1e293b;background:#fff">
  <div style="max-width:760px;margin:0 auto;padding:32px 20px">
    <nav style="font-size:13px;color:#64748b;margin-bottom:20px">
      <a href="/" style="color:#4f46e5;text-decoration:none">Home</a>
      <span style="margin:0 6px">&gt;</span>
      <a href="${esc(categoryUrl)}" style="color:#4f46e5;text-decoration:none">${esc(catLabel)}</a>
      <span style="margin:0 6px">&gt;</span>
      <span>${esc(repo_full_name)}</span>
    </nav>

    <h1 style="font-size:26px;margin:0 0 6px">Is ${esc(repo_name)} safe to install?</h1>
    <p style="color:#64748b;margin:0 0 20px">
      Security audit of <a href="https://github.com/${esc(repo_full_name)}" rel="noopener" style="color:#4f46e5;text-decoration:none">${esc(repo_full_name)}</a>
      &middot; ${esc(catLabel)} by ${creatorLinkHtml(author_name)} &middot; ★ ${starsK(stars)}
    </p>

    <!-- Verdict card -->
    <div style="border:1px solid ${g.color}33;background:${g.bg};border-radius:12px;padding:20px;margin-bottom:24px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        <span style="background:${g.color};color:#fff;font-weight:700;font-size:14px;padding:4px 14px;border-radius:999px">${g.icon} ${g.label}</span>
        <span style="font-size:13px;color:#64748b">Basic audit &middot; rule-based scan &middot; SlowMist 11 red-flag categories</span>
      </div>
      <p style="margin:0;line-height:1.6;color:#334155;font-size:15px"><strong>${g.answerEn(esc(repo_name))}</strong></p>
    </div>

    ${description ? `<p style="line-height:1.6;color:#475569"><strong>What it is:</strong> ${esc(description)}</p>` : ""}

    ${flagsHtml}

    <h2 style="font-size:18px;margin:24px 0 8px">Audit summary</h2>
    <table style="border-collapse:collapse;width:100%;font-size:14px">
      <tbody>
        <tr><td style="padding:6px 12px 6px 0;color:#64748b">Security grade</td><td style="padding:6px 0;font-weight:600;color:${g.color}">${g.icon} ${g.label}</td></tr>
        <tr><td style="padding:6px 12px 6px 0;color:#64748b">Quality score</td><td style="padding:6px 0">${Math.round(quality_score || 0)}/100</td></tr>
        <tr><td style="padding:6px 12px 6px 0;color:#64748b">GitHub stars</td><td style="padding:6px 0">${starsK(stars)}</td></tr>
        ${language ? `<tr><td style="padding:6px 12px 6px 0;color:#64748b">Language</td><td style="padding:6px 0">${esc(language)}</td></tr>` : ""}
        ${license ? `<tr><td style="padding:6px 12px 6px 0;color:#64748b">License</td><td style="padding:6px 0">${esc(license)}</td></tr>` : ""}
        ${last_commit_at ? `<tr><td style="padding:6px 12px 6px 0;color:#64748b">Last updated</td><td style="padding:6px 0"><time datetime="${last_commit_at}">${formatDate(last_commit_at)}</time></td></tr>` : ""}
      </tbody>
    </table>

    <h2 style="font-size:18px;margin:24px 0 8px">Check before you install</h2>
    <ul style="line-height:1.8;color:#475569;padding-left:20px">
      <li>What credentials does it ask for, and where are they stored?</li>
      <li>Is the maintainer identifiable and the repo actively maintained?</li>
      <li>Read the install scripts and network calls before trusting it.</li>
    </ul>

    <div style="display:flex;flex-wrap:wrap;gap:12px;margin:28px 0">
      <a href="${analyzerUrl}" style="background:#4f46e5;color:#fff;text-decoration:none;padding:10px 20px;border-radius:10px;font-weight:600;font-size:14px">Run a live scan →</a>
      <a href="${skillUrl}" style="border:1px solid #cbd5e1;color:#334155;text-decoration:none;padding:10px 20px;border-radius:10px;font-weight:600;font-size:14px">Full details &amp; install</a>
      <a href="/enterprise/" style="border:1px solid #cbd5e1;color:#334155;text-decoration:none;padding:10px 20px;border-radius:10px;font-weight:600;font-size:14px">5-dimension deep audit</a>
    </div>
${related.length ? `
    <h2 style="font-size:18px;margin:24px 0 8px">Related ${esc(catLabel)} audits</h2>
    <ul style="line-height:1.9;color:#475569;padding-left:20px;font-size:14px">
      ${related.map((r) => `<li><a href="/audit/${esc(r.repo_full_name)}/" style="color:#4f46e5;text-decoration:none">Is ${esc(r.repo_name)} safe?</a> <span style="color:#94a3b8">— ${GRADES[r.security_grade]?.label || "?"} · ★ ${starsK(r.stars)}</span></li>`).join("\n      ")}
    </ul>
    <p style="font-size:13px;margin:4px 0 0"><a href="${esc(categoryUrl)}" style="color:#4f46e5;text-decoration:none">Browse all ${esc(catLabel)} skills &rarr;</a></p>
` : ""}
    <p style="font-size:12px;color:#94a3b8;line-height:1.6;border-top:1px solid #e2e8f0;padding-top:16px;margin-top:28px">
      This is AgentSkillsHub's free basic audit: an automated rule-based scan covering SlowMist's 11 red-flag
      categories (credential exfiltration, obfuscated payloads, sandbox escape, prompt injection, and more) across
      130,000+ open-source AI agent skills and MCP servers, refreshed every 8 hours. A ${g.label} grade is a scan
      result, not a guarantee &mdash; deep 5-dimension audits (code &middot; credentials &middot; vendor &middot;
      supply-chain &middot; operational) are available for <a href="/enterprise/" style="color:#4f46e5">enterprise</a>.
      Audited: ${formatDate(new Date().toISOString())}.
    </p>
  </div>
</body>
</html>`;
}

async function main() {
  console.log("Generating /audit/ pages…");
  const skills = await fetchAllSkills();
  const graded = skills.filter(
    (s) =>
      s.security_grade &&
      GRADES[s.security_grade] &&
      (s.stars || 0) >= MIN_STARS_FOR_AUDIT &&
      s.repo_full_name?.includes("/"),
  );
  console.log(
    `  ${graded.length} graded skills (stars >= ${MIN_STARS_FOR_AUDIT}) of ${skills.length} total`,
  );

  // Index audit-eligible skills by category so each audit page can link to its
  // category's strongest siblings — turns the 7,900 dead-end audit pages into a
  // connected mesh (internal-link equity flows instead of orphaning).
  const RELATED_COUNT = 6;
  const byCategory = new Map();
  for (const s of graded) {
    const c = s.category || "other";
    if (!byCategory.has(c)) byCategory.set(c, []);
    byCategory.get(c).push(s);
  }
  for (const arr of byCategory.values()) {
    arr.sort((a, b) => (b.stars || 0) - (a.stars || 0));
  }

  const distDir = "dist";
  let written = 0;
  for (const skill of graded) {
    const related = (byCategory.get(skill.category || "other") || [])
      .filter((s) => s.repo_full_name !== skill.repo_full_name)
      .slice(0, RELATED_COUNT);
    const dir = join(distDir, "audit", ...skill.repo_full_name.split("/"));
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, "index.html"), pageHtml(skill, related));
    written++;
  }
  console.log(`  ✓ ${written} audit pages → dist/audit/`);

  // Sitemap for the audit pages (registered in the sitemap index separately).
  const today = new Date().toISOString().slice(0, 10);
  const urls = graded
    .map(
      (s) =>
        `  <url><loc>${SITE}/audit/${esc(s.repo_full_name)}/</loc><lastmod>${today}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>`,
    )
    .join("\n");
  writeFileSync(
    join(distDir, "sitemap-audit.xml"),
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
  );
  console.log("  ✓ sitemap-audit.xml");
}

main().catch((err) => {
  console.error("generate-audit-pages failed:", err);
  process.exit(1);
});
