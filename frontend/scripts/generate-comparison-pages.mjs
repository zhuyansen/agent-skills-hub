/**
 * Build-time comparison page generator.
 *
 * Generates static HTML pages at /compare/{slug}/ for SEO.
 * Reads comparison pairs from comparison-pairs.json, fetches both skills
 * from Supabase, and outputs side-by-side comparison HTML.
 *
 * Run: node scripts/generate-comparison-pages.mjs  (after vite build)
 */

import { readFileSync, mkdirSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import {
  SUPABASE_URL, SUPABASE_ANON_KEY, SITE, CATEGORY_LABELS,
  esc, starsK, formatDate, stripMarkdown, truncate,
  extractAssetTags,
} from "./shared-utils.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DIST = "dist";

/* ── Fetch a single skill by repo_full_name ───── */

async function fetchSkill(repoFullName) {
  const fields = [
    "id", "repo_full_name", "repo_name", "author_name", "author_avatar_url",
    "stars", "forks", "description", "category", "language", "score", "license",
    "readme_content", "last_commit_at", "created_at", "topics",
    "quality_score", "platforms", "star_momentum", "estimated_tokens",
    "open_issues", "total_commits",
  ].join(",");

  const url = `${SUPABASE_URL}/rest/v1/skills?select=${fields}&repo_full_name=eq.${encodeURIComponent(repoFullName)}&limit=1`;
  const res = await fetch(url, {
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    },
  });
  const data = await res.json();
  if (!Array.isArray(data) || data.length === 0) return null;
  const skill = data[0];
  if (skill.readme_content) {
    skill.readme_content = skill.readme_content.slice(0, 1500);
  }
  return skill;
}

/* ── Static header ─────────────────────────────── */

function buildStaticHeader() {
  return `<header id="site-header" class="bp-header">
    <div class="bp-header-inner">
      <a href="/" style="display:flex;align-items:center;gap:8px;text-decoration:none">
        <svg style="width:24px;height:24px;color:#3b82f6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2" stroke-width="1.5"/><circle cx="9" cy="16" r="1.5" fill="currentColor"/><circle cx="15" cy="16" r="1.5" fill="currentColor"/><path d="M12 2v4M8 7h8a2 2 0 012 2v2H6V9a2 2 0 012-2z" stroke-width="1.5" stroke-linecap="round"/></svg>
        <span class="bp-brand">Agent Skills Hub</span>
      </a>
      <nav class="bp-nav-links">
        <a href="/" class="bp-nav-link">Home</a>
        <a href="/compare/" class="bp-nav-link bp-nav-link--active">Compare</a>
        <a href="/best/" class="bp-nav-link">Best Tools</a>
        <a href="https://github.com/ZhuYansen/agent-skills-hub" target="_blank" rel="noopener noreferrer" class="bp-nav-link" style="display:flex;align-items:center;gap:4px">
          <svg style="width:16px;height:16px" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
          GitHub
        </a>
        <span style="color:var(--bp-border);font-size:16px">|</span>
        <button id="theme-toggle" onclick="(function(){var d=document.documentElement,t=d.classList.toggle('dark');localStorage.setItem('theme',t?'dark':'light');document.getElementById('theme-icon-light').style.display=t?'none':'block';document.getElementById('theme-icon-dark').style.display=t?'block':'none'})()" class="bp-icon-btn" title="Toggle dark mode" style="display:flex;align-items:center">
          <svg id="theme-icon-light" style="width:16px;height:16px" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
          <svg id="theme-icon-dark" style="width:16px;height:16px;display:none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
        </button>
        <button id="lang-toggle" onclick="(function(){var c=document.documentElement.lang==='zh-CN'?'en':'zh';localStorage.setItem('lang',c);document.documentElement.lang=c==='zh'?'zh-CN':'en';document.querySelectorAll('[data-zh]').forEach(function(el){el.textContent=c==='zh'?el.getAttribute('data-zh'):el.getAttribute('data-en')});document.getElementById('lang-toggle').textContent=c==='zh'?'EN':'中文'})()" class="bp-icon-btn" style="font-size:12px;font-weight:600">中文</button>
      </nav>
    </div>
  </header>
  <script>
    (function(){
      var t=localStorage.getItem('theme');
      if(t==='dark'||(t!=='light'&&window.matchMedia('(prefers-color-scheme:dark)').matches)){
        document.documentElement.classList.add('dark');
        var il=document.getElementById('theme-icon-light');
        var id=document.getElementById('theme-icon-dark');
        if(il)il.style.display='none';
        if(id)id.style.display='block';
      }
      var l=localStorage.getItem('lang')||'en';
      document.documentElement.lang=l==='zh'?'zh-CN':'en';
      var lb=document.getElementById('lang-toggle');
      if(lb)lb.textContent=l==='zh'?'EN':'中文';
      document.querySelectorAll('[data-zh]').forEach(function(el){
        el.textContent=l==='zh'?el.getAttribute('data-zh'):el.getAttribute('data-en');
      });
    })();
  </script>`;
}

/* ── Newsletter CTA ────────────────────────────── */

function buildNewsletterCta() {
  return `<div class="bp-newsletter">
    <h3 data-zh="订阅每周 AI 工具精选" data-en="Get Weekly AI Tool Picks">Get Weekly AI Tool Picks</h3>
    <p data-zh="每周一发送 Top 20 增速最快的 AI 工具，免费订阅。" data-en="Top 20 fastest-growing AI tools delivered every Monday. Free.">Top 20 fastest-growing AI tools delivered every Monday. Free.</p>
    <form id="nl-form" onsubmit="return (function(e){e.preventDefault();var em=document.getElementById('nl-email').value;if(!em)return false;var btn=document.getElementById('nl-btn');btn.textContent='Subscribing...';btn.disabled=true;fetch('https://vknzzecmzsfmohglpfgm.supabase.co/rest/v1/subscribers',{method:'POST',headers:{'Content-Type':'application/json','apikey':'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo','Authorization':'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo','Prefer':'return=minimal'},body:JSON.stringify({email:em})}).then(function(r){if(r.ok||r.status===409){btn.textContent='Subscribed!';btn.style.background='#059669'}else{btn.textContent='Try again';btn.disabled=false}}).catch(function(){btn.textContent='Try again';btn.disabled=false});return false})(event)" class="bp-newsletter-form" style="max-width:400px;margin:0 auto">
      <input id="nl-email" type="email" placeholder="your@email.com" required class="bp-newsletter-input" style="flex:1" />
      <button id="nl-btn" type="submit" class="bp-newsletter-btn cta-btn" data-zh="订阅" data-en="Subscribe">Subscribe</button>
    </form>
    <p style="margin:8px 0 0;font-size:11px;color:var(--bp-text-muted)" data-zh="无垃圾邮件，随时退订。" data-en="No spam, unsubscribe anytime.">No spam, unsubscribe anytime.</p>
  </div>`;
}

/* ── Verdict generator ─────────────────────────── */

function generateVerdict(skillA, skillB) {
  const factors = [];

  // Stars comparison
  if (skillA.stars > skillB.stars * 1.5) {
    factors.push({ winner: "a", reason: `${skillA.repo_name} has significantly more community adoption with ${starsK(skillA.stars)} stars vs ${starsK(skillB.stars)}` });
  } else if (skillB.stars > skillA.stars * 1.5) {
    factors.push({ winner: "b", reason: `${skillB.repo_name} has significantly more community adoption with ${starsK(skillB.stars)} stars vs ${starsK(skillA.stars)}` });
  } else {
    factors.push({ winner: "tie", reason: `Both have comparable community adoption (${starsK(skillA.stars)} vs ${starsK(skillB.stars)} stars)` });
  }

  // Quality score
  const qA = skillA.quality_score || 0;
  const qB = skillB.quality_score || 0;
  if (qA > qB + 10) {
    factors.push({ winner: "a", reason: `${skillA.repo_name} has a higher quality score (${qA} vs ${qB})` });
  } else if (qB > qA + 10) {
    factors.push({ winner: "b", reason: `${skillB.repo_name} has a higher quality score (${qB} vs ${qA})` });
  }

  // Recent activity
  const lastA = skillA.last_commit_at ? new Date(skillA.last_commit_at).getTime() : 0;
  const lastB = skillB.last_commit_at ? new Date(skillB.last_commit_at).getTime() : 0;
  const thirtyDays = 30 * 24 * 60 * 60 * 1000;
  if (lastA > lastB + thirtyDays) {
    factors.push({ winner: "a", reason: `${skillA.repo_name} was updated more recently (${formatDate(skillA.last_commit_at)})` });
  } else if (lastB > lastA + thirtyDays) {
    factors.push({ winner: "b", reason: `${skillB.repo_name} was updated more recently (${formatDate(skillB.last_commit_at)})` });
  }

  // Overall score
  const scoreA = skillA.score || 0;
  const scoreB = skillB.score || 0;
  if (scoreA > scoreB + 5) {
    factors.push({ winner: "a", reason: `${skillA.repo_name} has a higher overall score (${Math.round(scoreA)} vs ${Math.round(scoreB)})` });
  } else if (scoreB > scoreA + 5) {
    factors.push({ winner: "b", reason: `${skillB.repo_name} has a higher overall score (${Math.round(scoreB)} vs ${Math.round(scoreA)})` });
  }

  return factors;
}

/* ── Friendly name from slug ───────────────────── */

function friendlyName(repoName) {
  return repoName.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ── Comparison page HTML builder ──────────────── */

function buildComparisonHtml(pair, skillA, skillB, assetTags, allPairs) {
  const year = new Date().getFullYear();
  const nameA = skillA.repo_name;
  const nameB = skillB.repo_name;
  const catLabelA = CATEGORY_LABELS[skillA.category] || "AI Tool";
  const catLabelB = CATEGORY_LABELS[skillB.category] || "AI Tool";
  const pageUrl = `${SITE}/compare/${pair.slug}/`;
  const ogImage = `${SITE}/og-image.png`;

  const title = `${nameA} vs ${nameB}: Which AI Tool to Choose in ${year}?`;
  const metaDesc = `Compare ${nameA} and ${nameB} side by side. Stars, language, license, quality score, and community activity. Find the best ${pair.keywords[0] || "AI tool"} for your project.`;
  const keywords = [...pair.keywords, nameA, nameB, "comparison", "AI tools", "agent skills"].join(", ");

  const { linkTags } = assetTags;

  const descA = stripMarkdown(skillA.readme_content) || skillA.description || "";
  const descB = stripMarkdown(skillB.readme_content) || skillB.description || "";
  const excerptA = truncate(descA, 400);
  const excerptB = truncate(descB, 400);

  const verdict = generateVerdict(skillA, skillB);

  // JSON-LD: BreadcrumbList
  const breadcrumbLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE },
      { "@type": "ListItem", position: 2, name: "Compare", item: `${SITE}/compare/` },
      { "@type": "ListItem", position: 3, name: `${nameA} vs ${nameB}`, item: pageUrl },
    ],
  });

  // FAQ items
  const faqItems = [
    {
      q: `What is the difference between ${nameA} and ${nameB}?`,
      a: `${nameA} is a ${catLabelA.toLowerCase()} with ${starsK(skillA.stars)} GitHub stars${skillA.language ? `, primarily written in ${skillA.language}` : ""}. ${nameB} is a ${catLabelB.toLowerCase()} with ${starsK(skillB.stars)} GitHub stars${skillB.language ? `, primarily written in ${skillB.language}` : ""}. ${skillA.description ? skillA.description.slice(0, 100) : ""}`
    },
    {
      q: `Which is more popular, ${nameA} or ${nameB}?`,
      a: skillA.stars > skillB.stars
        ? `${nameA} currently has more GitHub stars (${starsK(skillA.stars)}) compared to ${nameB} (${starsK(skillB.stars)}), indicating broader community adoption.`
        : skillB.stars > skillA.stars
          ? `${nameB} currently has more GitHub stars (${starsK(skillB.stars)}) compared to ${nameA} (${starsK(skillA.stars)}), indicating broader community adoption.`
          : `Both ${nameA} and ${nameB} have similar community adoption with approximately ${starsK(skillA.stars)} GitHub stars each.`
    },
    {
      q: `Should I use ${nameA} or ${nameB} for my project?`,
      a: `The best choice depends on your specific needs. ${nameA}${skillA.language ? ` is built with ${skillA.language}` : ""} and categorized as ${catLabelA}. ${nameB}${skillB.language ? ` is built with ${skillB.language}` : ""} and categorized as ${catLabelB}. Consider your tech stack, project requirements, and community support when deciding.`
    },
    {
      q: `Are ${nameA} and ${nameB} free to use?`,
      a: `${skillA.license && skillA.license !== "NOASSERTION" ? `${nameA} is released under the ${skillA.license} license.` : `Check ${nameA}'s repository for license details.`} ${skillB.license && skillB.license !== "NOASSERTION" ? `${nameB} is released under the ${skillB.license} license.` : `Check ${nameB}'s repository for license details.`}`
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

  // Comparison table helper
  function cellVal(val, fallback) {
    return val ? esc(String(val)) : (fallback || "\u2014");
  }

  function highlightCell(valA, valB, higherIsBetter = true) {
    if (valA == null && valB == null) return ["", ""];
    const a = Number(valA) || 0;
    const b = Number(valB) || 0;
    const better = higherIsBetter ? (a > b ? "a" : b > a ? "b" : "") : (a < b ? "a" : b < a ? "b" : "");
    const styleWin = "font-weight:600;color:var(--bp-badge-green-text)";
    return [
      better === "a" ? styleWin : "",
      better === "b" ? styleWin : "",
    ];
  }

  const [starStyleA, starStyleB] = highlightCell(skillA.stars, skillB.stars);
  const [forkStyleA, forkStyleB] = highlightCell(skillA.forks, skillB.forks);
  const [scoreStyleA, scoreStyleB] = highlightCell(skillA.score, skillB.score);
  const [qualStyleA, qualStyleB] = highlightCell(skillA.quality_score, skillB.quality_score);
  const [issueStyleA, issueStyleB] = highlightCell(skillA.open_issues, skillB.open_issues, false);

  // Verdict HTML
  const verdictHtml = verdict.map((v) => {
    const icon = v.winner === "a" ? `<span style="color:var(--bp-badge-green-text)">&#9679;</span>` :
                 v.winner === "b" ? `<span style="color:var(--bp-link)">&#9679;</span>` :
                 `<span style="color:var(--bp-text-muted)">&#9679;</span>`;
    return `<li style="margin:6px 0;display:flex;align-items:flex-start;gap:8px">${icon} <span>${esc(v.reason)}</span></li>`;
  }).join("\n          ");

  // Related comparisons
  const relatedPairs = allPairs.filter((p) => p.slug !== pair.slug).slice(0, 4);
  const relatedHtml = relatedPairs.map((p) => {
    const parts = p.slug.split("-vs-");
    const labelA = parts[0] ? friendlyName(parts[0]) : p.slug;
    const labelB = parts[1] ? friendlyName(parts[1]) : "";
    return `<a href="/compare/${esc(p.slug)}/" class="bp-related-tag">${esc(labelA)} vs ${esc(labelB)}</a>`;
  }).join("\n        ");

  // FAQ HTML
  const faqHtml = faqItems.map((f) => `<details style="margin:8px 0;border:1px solid var(--bp-border);border-radius:8px;padding:12px;background:var(--bp-card-bg)">
        <summary style="cursor:pointer;font-weight:500;color:var(--bp-text)">${esc(f.q)}</summary>
        <p style="margin:8px 0 0;color:var(--bp-text-secondary);line-height:1.6">${esc(f.a)}</p>
      </details>`).join("\n      ");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(metaDesc)}" />
  <meta name="keywords" content="${esc(keywords)}" />

  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(metaDesc)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="${esc(pageUrl)}" />
  <meta property="og:site_name" content="Agent Skills Hub" />
  <meta property="og:image" content="${esc(ogImage)}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${esc(title)}" />
  <meta name="twitter:description" content="${esc(metaDesc)}" />
  <meta name="twitter:site" content="@GoSailGlobal" />
  <meta name="twitter:image" content="${esc(ogImage)}" />

  <link rel="canonical" href="${esc(pageUrl)}" />

  <script type="application/ld+json">
${breadcrumbLd}
  </script>
  <script type="application/ld+json">
${faqLd}
  </script>

  <link rel="stylesheet" href="/best-pages.css" />
  ${linkTags.filter(t => t.includes('stylesheet')).join("\n  ")}
  <script defer data-domain="agentskillshub.top" src="https://plausible.io/js/script.js"></script>
</head>
<body class="bp-body">
  ${buildStaticHeader()}
  <div class="bp-container">
    <!-- Breadcrumb -->
    <nav class="bp-breadcrumb">
      <a href="/" data-zh="首页" data-en="Home">Home</a>
      <span style="margin:0 6px">&gt;</span>
      <a href="/compare/" data-zh="对比" data-en="Compare">Compare</a>
      <span style="margin:0 6px">&gt;</span>
      <span>${esc(nameA)} vs ${esc(nameB)}</span>
    </nav>

    <!-- Hero -->
    <div class="bp-hero">
      <h1 data-zh="${esc(nameA)} vs ${esc(nameB)}：${year} 年该选哪个？" data-en="${esc(nameA)} vs ${esc(nameB)}: Which to Choose in ${year}?">${esc(nameA)} vs ${esc(nameB)}: Which to Choose in ${year}?</h1>
      <p data-zh="全面对比 ${esc(nameA)} 和 ${esc(nameB)} 的 Stars、语言、许可证、质量分数和社区活跃度，帮你选择最适合的工具。" data-en="A comprehensive side-by-side comparison of ${esc(nameA)} and ${esc(nameB)} covering stars, language, license, quality, and community activity.">A comprehensive side-by-side comparison of ${esc(nameA)} and ${esc(nameB)} covering stars, language, license, quality, and community activity.</p>
    </div>

    <!-- Side-by-side Comparison Table -->
    <section style="margin-top:24px">
      <h2 class="bp-section-title" data-zh="对比表" data-en="Comparison Table">Comparison Table</h2>
      <div class="bp-table-wrap">
        <table class="bp-table">
          <thead>
            <tr>
              <th data-zh="特性" data-en="Feature">Feature</th>
              <th><a href="/skill/${esc(skillA.repo_full_name)}/" style="color:var(--bp-link);text-decoration:none">${esc(nameA)}</a></th>
              <th><a href="/skill/${esc(skillB.repo_full_name)}/" style="color:var(--bp-link);text-decoration:none">${esc(nameB)}</a></th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td data-zh="Stars" data-en="Stars">Stars</td>
              <td style="${starStyleA}">&#9733; ${starsK(skillA.stars)}</td>
              <td style="${starStyleB}">&#9733; ${starsK(skillB.stars)}</td>
            </tr>
            <tr>
              <td data-zh="Forks" data-en="Forks">Forks</td>
              <td style="${forkStyleA}">${(skillA.forks || 0).toLocaleString()}</td>
              <td style="${forkStyleB}">${(skillB.forks || 0).toLocaleString()}</td>
            </tr>
            <tr>
              <td data-zh="分类" data-en="Category">Category</td>
              <td><a href="/category/${esc(skillA.category)}/" style="color:var(--bp-link);text-decoration:none">${esc(catLabelA)}</a></td>
              <td><a href="/category/${esc(skillB.category)}/" style="color:var(--bp-link);text-decoration:none">${esc(catLabelB)}</a></td>
            </tr>
            <tr>
              <td data-zh="语言" data-en="Language">Language</td>
              <td>${cellVal(skillA.language)}</td>
              <td>${cellVal(skillB.language)}</td>
            </tr>
            <tr>
              <td data-zh="许可证" data-en="License">License</td>
              <td>${cellVal(skillA.license && skillA.license !== "NOASSERTION" ? skillA.license : null)}</td>
              <td>${cellVal(skillB.license && skillB.license !== "NOASSERTION" ? skillB.license : null)}</td>
            </tr>
            <tr>
              <td data-zh="最后更新" data-en="Last Updated">Last Updated</td>
              <td>${formatDate(skillA.last_commit_at) || "\u2014"}</td>
              <td>${formatDate(skillB.last_commit_at) || "\u2014"}</td>
            </tr>
            <tr>
              <td data-zh="综合评分" data-en="Overall Score">Overall Score</td>
              <td style="${scoreStyleA}">${skillA.score ? Math.round(skillA.score) + "/100" : "\u2014"}</td>
              <td style="${scoreStyleB}">${skillB.score ? Math.round(skillB.score) + "/100" : "\u2014"}</td>
            </tr>
            <tr>
              <td data-zh="质量分数" data-en="Quality Score">Quality Score</td>
              <td style="${qualStyleA}">${skillA.quality_score ? skillA.quality_score + "/100" : "\u2014"}</td>
              <td style="${qualStyleB}">${skillB.quality_score ? skillB.quality_score + "/100" : "\u2014"}</td>
            </tr>
            <tr>
              <td data-zh="开放 Issues" data-en="Open Issues">Open Issues</td>
              <td style="${issueStyleA}">${skillA.open_issues != null ? skillA.open_issues.toLocaleString() : "\u2014"}</td>
              <td style="${issueStyleB}">${skillB.open_issues != null ? skillB.open_issues.toLocaleString() : "\u2014"}</td>
            </tr>
            <tr>
              <td data-zh="总提交数" data-en="Total Commits">Total Commits</td>
              <td>${skillA.total_commits ? skillA.total_commits.toLocaleString() : "\u2014"}</td>
              <td>${skillB.total_commits ? skillB.total_commits.toLocaleString() : "\u2014"}</td>
            </tr>
            <tr>
              <td data-zh="创建时间" data-en="Created">Created</td>
              <td>${formatDate(skillA.created_at) || "\u2014"}</td>
              <td>${formatDate(skillB.created_at) || "\u2014"}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Description comparison -->
    <section style="margin-top:32px;display:grid;grid-template-columns:1fr 1fr;gap:20px">
      <div class="bp-card" style="padding:16px">
        <h3 style="margin:0 0 8px;font-size:16px">
          <a href="/skill/${esc(skillA.repo_full_name)}/" style="color:var(--bp-link);text-decoration:none">${esc(nameA)}</a>
        </h3>
        <p style="color:var(--bp-text-secondary);font-size:14px;margin:0;line-height:1.6">${esc(excerptA)}</p>
        <div style="margin-top:12px;display:flex;gap:12px">
          <a href="/skill/${esc(skillA.repo_full_name)}/" style="color:var(--bp-link);font-size:13px;text-decoration:none" data-zh="查看详情" data-en="View Details">View Details &rarr;</a>
          <a href="https://github.com/${esc(skillA.repo_full_name)}" style="color:var(--bp-text-secondary);font-size:13px;text-decoration:none">GitHub &rarr;</a>
        </div>
      </div>
      <div class="bp-card" style="padding:16px">
        <h3 style="margin:0 0 8px;font-size:16px">
          <a href="/skill/${esc(skillB.repo_full_name)}/" style="color:var(--bp-link);text-decoration:none">${esc(nameB)}</a>
        </h3>
        <p style="color:var(--bp-text-secondary);font-size:14px;margin:0;line-height:1.6">${esc(excerptB)}</p>
        <div style="margin-top:12px;display:flex;gap:12px">
          <a href="/skill/${esc(skillB.repo_full_name)}/" style="color:var(--bp-link);font-size:13px;text-decoration:none" data-zh="查看详情" data-en="View Details">View Details &rarr;</a>
          <a href="https://github.com/${esc(skillB.repo_full_name)}" style="color:var(--bp-text-secondary);font-size:13px;text-decoration:none">GitHub &rarr;</a>
        </div>
      </div>
    </section>

    <!-- Quick Verdict -->
    <section style="margin-top:32px">
      <h2 class="bp-section-title" data-zh="快速结论" data-en="Quick Verdict">Quick Verdict</h2>
      <div class="bp-card" style="padding:16px 20px">
        <ul style="list-style:none;padding:0;margin:0">
          ${verdictHtml}
        </ul>
        <p style="margin:16px 0 0;color:var(--bp-text-secondary);font-size:14px;line-height:1.6" data-zh="最终选择取决于你的具体需求、技术栈和项目规模。两个工具各有优势。" data-en="The best choice ultimately depends on your specific needs, tech stack, and project scale. Both tools have their strengths.">The best choice ultimately depends on your specific needs, tech stack, and project scale. Both tools have their strengths.</p>
      </div>
    </section>

    <!-- FAQ -->
    <section style="margin-top:32px" class="bp-faq">
      <h2 class="bp-section-title" style="font-size:18px" data-zh="常见问题" data-en="Frequently Asked Questions">Frequently Asked Questions</h2>
      ${faqHtml}
    </section>

    <!-- Related Comparisons -->
    ${relatedHtml ? `<section style="margin-top:32px">
      <h2 class="bp-section-title" style="font-size:18px" data-zh="更多对比" data-en="Related Comparisons">Related Comparisons</h2>
      <div class="bp-related">
        ${relatedHtml}
      </div>
    </section>` : ""}

    <!-- Newsletter -->
    ${buildNewsletterCta()}

    <!-- CTA -->
    <div style="margin:32px 0;text-align:center">
      <a href="/" class="bp-newsletter-btn cta-btn" style="display:inline-block;padding:10px 24px;border-radius:8px;text-decoration:none;font-size:14px" data-zh="探索全部 25,000+ 技能" data-en="Explore All 25,000+ Skills on Agent Skills Hub">Explore All 25,000+ Skills on Agent Skills Hub</a>
    </div>
  </div>
</body>
</html>`;
}

/* ── Index page builder (/compare/) ────────────── */

function buildIndexHtml(pairs, fetchedPairs, assetTags) {
  const year = new Date().getFullYear();
  const pageUrl = `${SITE}/compare/`;
  const ogImage = `${SITE}/og-image.png`;
  const title = `AI Tool Comparisons (${year}) | Agent Skills Hub`;
  const metaDesc = `Compare popular AI agent tools side by side. ${pairs.length} head-to-head comparisons of frameworks, MCP servers, and developer tools.`;

  const { linkTags } = assetTags;

  const breadcrumbLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE },
      { "@type": "ListItem", position: 2, name: "Compare", item: pageUrl },
    ],
  });

  const cardsHtml = fetchedPairs.map(({ pair, skillA, skillB }) => {
    const catLabelA = CATEGORY_LABELS[skillA.category] || "AI Tool";
    const catLabelB = CATEGORY_LABELS[skillB.category] || "AI Tool";
    return `<a href="/compare/${esc(pair.slug)}/" class="bp-card" style="display:block;padding:16px;text-decoration:none;margin:12px 0">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
          <div style="flex:1;min-width:200px">
            <div class="bp-card-title" style="font-size:16px">${esc(skillA.repo_name)} <span style="color:var(--bp-text-muted);font-weight:400">vs</span> ${esc(skillB.repo_name)}</div>
            <div style="margin-top:4px;display:flex;gap:8px;flex-wrap:wrap;font-size:13px;color:var(--bp-text-secondary)">
              <span>&#9733; ${starsK(skillA.stars)} vs ${starsK(skillB.stars)}</span>
              <span>${esc(catLabelA)}${catLabelA !== catLabelB ? ` / ${esc(catLabelB)}` : ""}</span>
            </div>
          </div>
          <span style="color:var(--bp-link);font-size:13px;font-weight:500;white-space:nowrap">Compare &rarr;</span>
        </div>
      </a>`;
  }).join("\n      ");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(metaDesc)}" />
  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(metaDesc)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="${esc(pageUrl)}" />
  <meta property="og:image" content="${esc(ogImage)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="canonical" href="${esc(pageUrl)}" />
  <script type="application/ld+json">
${breadcrumbLd}
  </script>
  <link rel="stylesheet" href="/best-pages.css" />
  ${linkTags.filter(t => t.includes('stylesheet')).join("\n  ")}
  <script defer data-domain="agentskillshub.top" src="https://plausible.io/js/script.js"></script>
</head>
<body class="bp-body">
  ${buildStaticHeader()}
  <div class="bp-container">
    <nav class="bp-breadcrumb">
      <a href="/" data-zh="首页" data-en="Home">Home</a>
      <span style="margin:0 6px">&gt;</span>
      <span data-zh="对比" data-en="Compare">Compare</span>
    </nav>
    <div class="bp-hero">
      <h1 data-zh="AI 工具对比" data-en="AI Tool Comparisons">AI Tool Comparisons</h1>
      <p data-zh="热门 AI Agent 工具的一对一对比。Stars、质量、活跃度一目了然。" data-en="Head-to-head comparisons of popular AI agent tools. Stars, quality, and activity at a glance.">Head-to-head comparisons of popular AI agent tools. Stars, quality, and activity at a glance.</p>
    </div>
    <section>
      <h2 class="bp-section-title" data-zh="全部对比" data-en="All Comparisons">All Comparisons</h2>
      ${cardsHtml}
    </section>
    ${buildNewsletterCta()}
    <div style="margin:32px 0;text-align:center">
      <a href="/" class="bp-newsletter-btn cta-btn" style="display:inline-block;padding:10px 24px;border-radius:8px;text-decoration:none;font-size:14px" data-zh="探索全部 25,000+ 技能" data-en="Explore All 25,000+ Skills on Agent Skills Hub">Explore All 25,000+ Skills on Agent Skills Hub</a>
    </div>
  </div>
</body>
</html>`;
}

/* ── Main ──────────────────────────────────────── */

async function main() {
  console.log("=== Comparison Page Generator ===\n");

  // Load comparison pairs
  const pairsPath = join(__dirname, "comparison-pairs.json");
  if (!existsSync(pairsPath)) {
    console.error("comparison-pairs.json not found!");
    process.exit(1);
  }
  const pairs = JSON.parse(readFileSync(pairsPath, "utf-8"));
  console.log(`Loaded ${pairs.length} comparison pairs`);

  // Load asset tags from built index.html
  const indexHtml = readFileSync(join(DIST, "index.html"), "utf-8");
  const assetTags = extractAssetTags(indexHtml);

  // Fetch skills for each pair
  let generated = 0;
  let skipped = 0;
  const fetchedPairs = [];
  const t0 = Date.now();

  for (const pair of pairs) {
    const [skillA, skillB] = await Promise.all([
      fetchSkill(pair.a),
      fetchSkill(pair.b),
    ]);

    if (!skillA) {
      console.log(`  SKIP ${pair.slug}: could not find ${pair.a}`);
      skipped++;
      continue;
    }
    if (!skillB) {
      console.log(`  SKIP ${pair.slug}: could not find ${pair.b}`);
      skipped++;
      continue;
    }

    fetchedPairs.push({ pair, skillA, skillB });

    const dir = join(DIST, "compare", pair.slug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(
      join(dir, "index.html"),
      buildComparisonHtml(pair, skillA, skillB, assetTags, pairs),
    );
    console.log(`  \u2713 /compare/${pair.slug}/ (${skillA.repo_name} vs ${skillB.repo_name})`);
    generated++;
  }

  // Generate /compare/ index page
  const compareDir = join(DIST, "compare");
  mkdirSync(compareDir, { recursive: true });
  writeFileSync(
    join(compareDir, "index.html"),
    buildIndexHtml(pairs, fetchedPairs, assetTags),
  );
  console.log(`  \u2713 /compare/ (index page, ${fetchedPairs.length} comparisons)`);

  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`\nComparison pages: ${generated} generated + 1 index, ${skipped} skipped (${elapsed}s)`);
}

main().catch((err) => {
  console.error("Failed to generate comparison pages:", err);
  process.exit(1);
});
