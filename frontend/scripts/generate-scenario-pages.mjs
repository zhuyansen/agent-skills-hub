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
  const m = scenario.match;
  const categories = m.categories || [];
  const min_results = m.min_results || 5;
  const max_results = m.max_results || 10;

  // Support tiered keywords: primary (+8), secondary/keywords (+3)
  const primaryKw = (m.primary_keywords || []).map((k) => k.toLowerCase());
  const secondaryKw = (m.secondary_keywords || m.keywords || []).map((k) => k.toLowerCase());
  // If no primary_keywords defined, treat keywords as secondary (backward compat)
  if (primaryKw.length === 0 && m.keywords) {
    // Legacy format: all keywords are secondary
  }
  const excludeKw = (m.exclude_keywords || []).map((k) => k.toLowerCase());
  const topicMatches = (m.topic_matches || []).map((k) => k.toLowerCase());

  const scored = [];
  for (const skill of allSkills) {
    if (!shouldIndex(skill)) continue;

    let matchScore = 0;

    // Category match (weight: 15)
    if (categories.length > 0 && categories.includes(skill.category)) {
      matchScore += 15;
    }

    // Build searchable text
    const desc = (skill.description || "").toLowerCase();
    const name = (skill.repo_name || "").toLowerCase();
    const topicsArr = parseJsonArray(skill.topics).map((t) => t.toLowerCase());
    const topicSet = new Set(topicsArr);
    const allText = `${desc} ${name} ${topicsArr.join(" ")}`;

    // Exclude keywords — hard negative
    let excluded = false;
    for (const kw of excludeKw) {
      if (allText.includes(kw)) {
        excluded = true;
        break;
      }
    }
    if (excluded) continue;

    // Primary keywords (+8 each)
    for (const kw of primaryKw) {
      if (allText.includes(kw)) matchScore += 8;
    }

    // Secondary keywords (+3 each)
    for (const kw of secondaryKw) {
      if (allText.includes(kw)) matchScore += 3;
    }

    // Topic exact match (+5 each, GitHub topics are author-curated)
    for (const tm of topicMatches) {
      if (topicSet.has(tm)) matchScore += 5;
    }

    if (matchScore > 0) {
      // Quality boost (0~1)
      const qualityBoost = (skill.score || 0) / 100;
      // Stars log boost (100★=2, 1K★=3, 10K★=4)
      const starsBoost = Math.log10(Math.max(skill.stars || 1, 1));
      scored.push({ skill, matchScore: matchScore + qualityBoost + starsBoost });
    }
  }

  // Sort by matchScore desc, then by stars desc
  scored.sort((a, b) => b.matchScore - a.matchScore || b.skill.stars - a.skill.stars);

  const results = scored.slice(0, max_results).map((s) => s.skill);
  if (results.length < min_results) return null;

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

/* ── Static header (shared across /best/* pages) ── */

function buildStaticHeader() {
  return `<header id="site-header" class="bp-header">
    <div class="bp-header-inner">
      <a href="/" style="display:flex;align-items:center;gap:8px;text-decoration:none">
        <svg style="width:24px;height:24px;color:#3b82f6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2" stroke-width="1.5"/><circle cx="9" cy="16" r="1.5" fill="currentColor"/><circle cx="15" cy="16" r="1.5" fill="currentColor"/><path d="M12 2v4M8 7h8a2 2 0 012 2v2H6V9a2 2 0 012-2z" stroke-width="1.5" stroke-linecap="round"/></svg>
        <span class="bp-brand">Agent Skills Hub</span>
      </a>
      <nav class="bp-nav-links">
        <a href="/" class="bp-nav-link">Home</a>
        <a href="/best/" class="bp-nav-link bp-nav-link--active">Best Tools</a>
        <a href="https://github.com/ZhuYansen/agent-skills-hub" target="_blank" rel="noopener noreferrer" class="bp-nav-link" style="display:flex;align-items:center;gap:4px">
          <svg style="width:16px;height:16px" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
          GitHub
        </a>
        <a href="https://x.com/GoSailGlobal" target="_blank" rel="noopener noreferrer" class="bp-nav-link" style="display:flex;align-items:center;gap:4px">
          <svg style="width:14px;height:14px" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
          X
        </a>
        <span style="color:var(--bp-border);font-size:16px">|</span>
        <!-- Dark mode toggle -->
        <button id="theme-toggle" onclick="(function(){var d=document.documentElement,t=d.classList.toggle('dark');localStorage.setItem('theme',t?'dark':'light');document.getElementById('theme-icon-light').style.display=t?'none':'block';document.getElementById('theme-icon-dark').style.display=t?'block':'none'})()" class="bp-icon-btn" title="Toggle dark mode" style="display:flex;align-items:center">
          <svg id="theme-icon-light" style="width:16px;height:16px" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
          <svg id="theme-icon-dark" style="width:16px;height:16px;display:none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
        </button>
        <!-- Language toggle -->
        <button id="lang-toggle" onclick="(function(){var c=document.documentElement.lang==='zh-CN'?'en':'zh';localStorage.setItem('lang',c);document.documentElement.lang=c==='zh'?'zh-CN':'en';document.querySelectorAll('[data-zh]').forEach(function(el){el.textContent=c==='zh'?el.getAttribute('data-zh'):el.getAttribute('data-en')});document.getElementById('lang-toggle').textContent=c==='zh'?'EN':'中文'})()" class="bp-icon-btn" style="font-size:12px;font-weight:600">中文</button>
      </nav>
    </div>
  </header>
  <script>
    // Apply saved theme
    (function(){
      var t=localStorage.getItem('theme');
      if(t==='dark'||(t!=='light'&&window.matchMedia('(prefers-color-scheme:dark)').matches)){
        document.documentElement.classList.add('dark');
        var il=document.getElementById('theme-icon-light');
        var id=document.getElementById('theme-icon-dark');
        if(il)il.style.display='none';
        if(id)id.style.display='block';
      }
      // Apply saved lang
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

/* ── Newsletter CTA (shared) ─────────────────────── */

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

/* ── Index page builder (/best/) ────────────────── */

function buildIndexHtml(scenarios, scenarioSkillCounts, assetTags) {
  const pageUrl = `${SITE}/best/`;
  const year = new Date().getFullYear();
  const title = `Best AI Agent Tools by Scenario (${year}) | Agent Skills Hub`;
  const metaDesc = "Browse 40+ curated scenario guides to find the best AI agent tools, MCP servers, and Claude skills for your specific use case.";
  const ogImage = `${SITE}/og-image.png`;

  const { linkTags } = assetTags;

  // Group scenarios by rough category
  const groups = [
    { label: "MCP Tools", zh: "MCP 工具", icon: "🔌", slugs: ["mcp-database", "mcp-browser", "mcp-filesystem", "mcp-api", "mcp-memory", "mcp-for-notion", "mcp-for-github", "mcp-for-google"] },
    { label: "Code & Development", zh: "代码开发", icon: "💻", slugs: ["code-review", "code-completion", "test-generation", "debugging", "refactoring", "git-tools", "cli-tools", "ai-code-editor", "web-development", "api-testing"] },
    { label: "AI & ML", zh: "AI 与机器学习", icon: "🤖", slugs: ["ai-agent-framework", "multi-agent", "prompt-engineering", "model-evaluation", "local-llm", "claude-code-skills", "codex-skills"] },
    { label: "Security", zh: "安全", icon: "🔒", slugs: ["security-audit", "secret-detection", "authentication"] },
    { label: "Data & Search", zh: "数据与搜索", icon: "📊", slugs: ["web-scraping", "semantic-search", "vector-database", "data-pipeline", "document-parsing", "data-visualization", "knowledge-base", "database-migration"] },
    { label: "Content & Writing", zh: "内容创作", icon: "✍️", slugs: ["content-writing", "translation", "summarization", "image-generation", "text-to-speech"] },
    { label: "DevOps & Automation", zh: "DevOps 与自动化", icon: "⚙️", slugs: ["workflow-automation", "ci-cd", "monitoring", "container-management", "browser-automation"] },
    { label: "Communication", zh: "通讯集成", icon: "💬", slugs: ["slack-integration", "discord-bot", "telegram-bot", "email-automation", "social-media", "notification", "rss-monitoring"] },
  ];

  const groupsHtml = groups.map((g) => {
    const items = g.slugs
      .map((slug) => {
        const sc = scenarios.find((s) => s.slug === slug);
        if (!sc || !scenarioSkillCounts[slug]) return null;
        const count = scenarioSkillCounts[slug];
        return `<a href="/best/${esc(slug)}/" class="bp-card" style="display:flex;align-items:center;justify-content:space-between;padding:10px 16px;text-decoration:none">
          <div>
            <div class="bp-card-title" style="font-size:14px">${esc(sc.title)}</div>
            <div class="bp-card-desc" style="font-size:12px;margin-top:2px;margin-bottom:0">${esc(sc.description.slice(0, 80))}${sc.description.length > 80 ? "..." : ""}</div>
          </div>
          <span style="color:var(--bp-link);font-size:12px;font-weight:500;white-space:nowrap;margin-left:12px">${count} tools &rarr;</span>
        </a>`;
      })
      .filter(Boolean)
      .join("\n        ");

    if (!items) return "";

    return `<div style="margin-bottom:28px">
      <h2 class="bp-section-title" style="font-size:18px;display:flex;align-items:center;gap:8px">
        <span>${g.icon}</span> <span data-zh="${esc(g.zh)}" data-en="${esc(g.label)}">${esc(g.label)}</span>
      </h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px">
        ${items}
      </div>
    </div>`;
  }).join("\n    ");

  const breadcrumbLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE },
      { "@type": "ListItem", position: 2, name: "Best Tools", item: pageUrl },
    ],
  });

  const totalScenarios = Object.keys(scenarioSkillCounts).length;

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
      <span data-zh="最佳工具" data-en="Best Tools">Best Tools</span>
    </nav>
    <div class="bp-hero">
      <h1 data-zh="按场景发现最佳 AI Agent 工具" data-en="Best AI Agent Tools by Scenario">Best AI Agent Tools by Scenario</h1>
      <p data-zh="浏览 ${totalScenarios} 个精选场景指南，找到最适合你需求的 AI Agent 工具、MCP 服务器和 Claude 技能。" data-en="Browse ${totalScenarios} curated scenario guides to find the perfect AI agent tools, MCP servers, and Claude skills for your specific use case.">Browse ${totalScenarios} curated scenario guides to find the perfect AI agent tools, MCP servers, and Claude skills for your specific use case.</p>
    </div>
    ${groupsHtml}
    ${buildNewsletterCta()}
    <div style="margin:32px 0;text-align:center">
      <a href="/" class="bp-newsletter-btn cta-btn" style="display:inline-block;padding:10px 24px;border-radius:8px;text-decoration:none;font-size:14px" data-zh="探索全部 25,000+ 技能" data-en="Explore All 25,000+ Skills on Agent Skills Hub">Explore All 25,000+ Skills on Agent Skills Hub</a>
    </div>
  </div>
</body>
</html>`;
}

/* ── AEO Content Section ────────────────────────────── */

function buildAeoSection(scenario, skills, year) {
  const scenarioTitle = scenario.title;
  const top3 = skills.slice(0, 3).map(s => s.repo_name);
  const topLanguages = [...new Set(skills.map(s => s.language).filter(Boolean))].slice(0, 3);
  const avgStars = Math.round(skills.reduce((sum, s) => sum + (s.stars || 0), 0) / skills.length);
  const openSourceCount = skills.filter(s => s.license && s.license !== 'NOASSERTION').length;

  return `<!-- AEO: Answer Engine Optimization Section -->
      <section class="bp-aeo-section" style="margin:32px 0;padding:24px;background:var(--bp-bg-alt);border-radius:12px;border:1px solid var(--bp-border)">
        <h2 class="bp-section-title" style="font-size:20px;margin-bottom:20px" data-zh="${esc(scenarioTitle)} 完整指南 (${year})" data-en="The Complete Guide to ${esc(scenarioTitle)} Tools (${year})">The Complete Guide to ${esc(scenarioTitle)} Tools (${year})</h2>

        <!-- What -->
        <div style="margin-bottom:24px">
          <h3 style="font-size:17px;font-weight:600;color:var(--bp-text);margin-bottom:8px" data-zh="什么是 ${esc(scenarioTitle)} 工具？" data-en="What Are ${esc(scenarioTitle)} Tools?">What Are ${esc(scenarioTitle)} Tools?</h3>
          <p style="color:var(--bp-text-secondary);line-height:1.8;font-size:15px" data-zh="${esc(scenarioTitle)} 工具是一类专注于帮助开发者和团队解决 ${esc(scenarioTitle.toLowerCase())} 相关任务的 AI 驱动软件。这些工具通常以开源形式发布在 GitHub 上，支持通过 MCP（Model Context Protocol）、Claude Skills 或独立 Agent 框架集成到现有工作流中。在 Agent Skills Hub 上，我们收录了 ${skills.length} 个经过质量评分的 ${esc(scenarioTitle.toLowerCase())} 工具，覆盖${topLanguages.join('、')}等主流编程语言。" data-en="${esc(scenarioTitle)} tools are AI-powered software designed to help developers and teams tackle ${esc(scenarioTitle.toLowerCase())}-related tasks more efficiently. These tools are typically published as open-source projects on GitHub and can be integrated into existing workflows via MCP (Model Context Protocol), Claude Skills, or standalone agent frameworks. On Agent Skills Hub, we index ${skills.length} quality-scored ${esc(scenarioTitle.toLowerCase())} tools across languages including ${topLanguages.join(', ')}.">${esc(scenarioTitle)} tools are AI-powered software designed to help developers and teams tackle ${esc(scenarioTitle.toLowerCase())}-related tasks more efficiently. These tools are typically published as open-source projects on GitHub and can be integrated into existing workflows via MCP (Model Context Protocol), Claude Skills, or standalone agent frameworks. On Agent Skills Hub, we index ${skills.length} quality-scored ${esc(scenarioTitle.toLowerCase())} tools across languages including ${topLanguages.join(', ')}.</p>
        </div>

        <!-- Why -->
        <div style="margin-bottom:24px">
          <h3 style="font-size:17px;font-weight:600;color:var(--bp-text);margin-bottom:8px" data-zh="为什么需要 ${esc(scenarioTitle)} 工具？" data-en="Why Use ${esc(scenarioTitle)} Tools?">Why Use ${esc(scenarioTitle)} Tools?</h3>
          <p style="color:var(--bp-text-secondary);line-height:1.8;font-size:15px" data-zh="在 ${year} 年，AI Agent 生态系统正在快速成熟。${esc(scenarioTitle)} 工具能够显著提升开发效率：自动化重复任务、减少人为错误、并提供智能建议。排名前三的工具——${top3.join('、')}——平均获得了 ${avgStars.toLocaleString()} 个 GitHub Star，体现了开发者社区的高度认可。其中 ${openSourceCount} 个工具提供了明确的开源许可证，确保你可以自由使用和修改。" data-en="In ${year}, the AI agent ecosystem is maturing rapidly. ${esc(scenarioTitle)} tools can significantly boost development efficiency by automating repetitive tasks, reducing human error, and providing intelligent suggestions. The top 3 tools — ${top3.join(', ')} — have earned an average of ${avgStars.toLocaleString()} GitHub stars, reflecting strong community validation. ${openSourceCount} of the listed tools come with clear open-source licenses, ensuring freedom to use and modify.">In ${year}, the AI agent ecosystem is maturing rapidly. ${esc(scenarioTitle)} tools can significantly boost development efficiency by automating repetitive tasks, reducing human error, and providing intelligent suggestions. The top 3 tools — ${top3.join(', ')} — have earned an average of ${avgStars.toLocaleString()} GitHub stars, reflecting strong community validation. ${openSourceCount} of the listed tools come with clear open-source licenses, ensuring freedom to use and modify.</p>
        </div>

        <!-- How -->
        <div>
          <h3 style="font-size:17px;font-weight:600;color:var(--bp-text);margin-bottom:8px" data-zh="如何选择最佳 ${esc(scenarioTitle)} 工具？" data-en="How to Choose the Best ${esc(scenarioTitle)} Tool?">How to Choose the Best ${esc(scenarioTitle)} Tool?</h3>
          <p style="color:var(--bp-text-secondary);line-height:1.8;font-size:15px" data-zh="选择 ${esc(scenarioTitle.toLowerCase())} 工具时，建议考虑以下因素：1️⃣ 社区活跃度（GitHub Star 数和最近提交频率）；2️⃣ 集成方式（是否支持 MCP、Claude 或你使用的 Agent 框架）；3️⃣ 编程语言兼容性（本列表中最常见的语言是 ${topLanguages[0] || 'Python'}）；4️⃣ 质量评分（Agent Skills Hub 的综合评分考量了代码质量、文档完整性和维护活跃度）。我们的推荐是从 ${top3[0]} 开始——它在 Star 数和质量评分上都名列前茅。" data-en="When choosing a ${esc(scenarioTitle.toLowerCase())} tool, consider these factors: 1) Community activity — GitHub stars and recent commit frequency indicate reliability; 2) Integration method — check if it supports MCP, Claude, or your preferred agent framework; 3) Language compatibility — the most common language in this list is ${topLanguages[0] || 'Python'}; 4) Quality score — Agent Skills Hub's composite score evaluates code quality, documentation completeness, and maintenance activity. Our recommendation: start with ${top3[0]} — it ranks highest in both star count and quality score.">When choosing a ${esc(scenarioTitle.toLowerCase())} tool, consider these factors: 1) Community activity — GitHub stars and recent commit frequency indicate reliability; 2) Integration method — check if it supports MCP, Claude, or your preferred agent framework; 3) Language compatibility — the most common language in this list is ${topLanguages[0] || 'Python'}; 4) Quality score — Agent Skills Hub's composite score evaluates code quality, documentation completeness, and maintenance activity. Our recommendation: start with ${top3[0]} — it ranks highest in both star count and quality score.</p>
        </div>
      </section>`;
}

/* ── HTML builder ────────────────────────────────── */

function buildScenarioHtml(scenario, skills, assetTags, allScenarios) {
  const pageUrl = `${SITE}/best/${scenario.slug}/`;
  const year = new Date().getFullYear();
  const title = `Best ${skills.length} AI Tools for ${scenario.title} in ${year} | Agent Skills Hub`;
  const metaDesc = scenario.description;
  const ogImage = `${SITE}/og-image.png`;

  const { scriptTags, linkTags } = assetTags;

  // JSON-LD: ItemList (top 10 items max)
  const itemListSkills = skills.slice(0, 10);
  const itemListLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: `Best ${scenario.title} Tools ${year}`,
    numberOfItems: itemListSkills.length,
    itemListElement: itemListSkills.map((s, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: s.repo_name,
      url: `${SITE}/skill/${s.repo_full_name}/`,
    })),
  }, null, 2);

  // JSON-LD: BreadcrumbList (3-level)
  const breadcrumbLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: `${SITE}/` },
      { "@type": "ListItem", position: 2, name: "Best Tools", item: `${SITE}/best/` },
      { "@type": "ListItem", position: 3, name: scenario.title },
    ],
  });

  // FAQ
  const scenarioLower = scenario.title.toLowerCase();
  const top3Names = skills.slice(0, 3).map((s) => s.repo_name).join(", ");
  const faqItems = [
    {
      q: `What are the best ${scenarioLower} tools in ${year}?`,
      a: `The top ${scenarioLower} tools in ${year} include ${top3Names}. These tools are ranked by community adoption (GitHub stars) and quality metrics.`,
    },
    {
      q: `How many ${scenarioLower} tools are available?`,
      a: `Agent Skills Hub indexes ${skills.length} ${scenarioLower} tools, updated daily from GitHub. Browse the full list at agentskillshub.top.`,
    },
    {
      q: `Are these ${scenarioLower} tools free to use?`,
      a: `Most tools listed are open source and free. Check each tool's license on its GitHub repository for specific terms.`,
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
  const twoWeeksAgo = Date.now() - 14 * 24 * 60 * 60 * 1000;
  const skillCardsHtml = skills.map((s, i) => {
    const catLabel = CATEGORY_LABELS[s.category] || "AI Tool";
    const isNew = s.created_at && new Date(s.created_at).getTime() > twoWeeksAgo;
    const qs = extractQuickStart(s.readme_content);
    const qsHtml = qs
      ? `<div style="margin-top:8px;padding:8px 12px;background:var(--bp-bg-alt);border-radius:6px;font-size:13px">
          <strong style="color:var(--bp-text-slate)">Quick Start:</strong>
          <span style="color:var(--bp-text-slate)"> ${esc(qs.text.slice(0, 150))}${qs.text.length > 150 ? "..." : ""}</span>
          ${qs.code ? `<pre class="bp-code"><code>${esc(qs.code.slice(0, 300))}</code></pre>` : ""}
        </div>`
      : "";

    return `<div class="bp-card" style="margin:16px 0">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
          <div>
            <span class="bp-rank ${i < 3 ? "bp-rank--gold" : "bp-rank--gray"}" style="display:inline-flex;margin-right:8px;font-size:14px">${i + 1}</span>
            <a class="bp-card-title" href="/skill/${esc(s.repo_full_name)}/" style="font-size:18px;display:inline">${esc(s.repo_name)}</a>${isNew ? `<span class="bp-badge-new">NEW</span>` : ""}
            <span style="color:var(--bp-text-muted);font-size:13px;margin-left:8px">by ${esc(s.author_name)}</span>
          </div>
          <div class="bp-card-meta">
            <span>&#9733; ${starsK(s.stars)}</span>
            ${s.language ? `<span>${esc(s.language)}</span>` : ""}
            <span class="bp-badge-category" style="color:var(--bp-badge-purple-text);background:var(--bp-badge-purple-bg)">${esc(catLabel)}</span>
          </div>
        </div>
        <p class="bp-card-desc" style="margin:8px 0 0">${esc(s.description || "")}</p>
        ${qsHtml}
        <div style="margin-top:10px;display:flex;gap:12px">
          <a href="/skill/${esc(s.repo_full_name)}/" style="color:var(--bp-link);font-size:13px;text-decoration:none">View Details &rarr;</a>
          <a href="https://github.com/${esc(s.repo_full_name)}" style="color:var(--bp-text-secondary);font-size:13px;text-decoration:none">GitHub &rarr;</a>
        </div>
      </div>`;
  }).join("\n      ");

  // Comparison table
  const compRows = skills.map((s) => {
    return `<tr>
          <td><a href="/skill/${esc(s.repo_full_name)}/" style="font-weight:500">${esc(s.repo_name)}</a></td>
          <td style="text-align:right">&#9733; ${starsK(s.stars)}</td>
          <td>${esc(s.language || "\u2014")}</td>
          <td>${esc(s.license && s.license !== "NOASSERTION" ? s.license : "\u2014")}</td>
          <td style="text-align:right">${s.score ? Math.round(s.score) : "\u2014"}</td>
        </tr>`;
  }).join("\n        ");

  // Related scenarios
  const relatedHtml = (scenario.related || [])
    .map((slug) => {
      const rel = allScenarios.find((s) => s.slug === slug);
      if (!rel) return null;
      return `<a href="/best/${esc(slug)}/" class="bp-related-tag">${esc(rel.title)}</a>`;
    })
    .filter(Boolean)
    .join("\n        ");

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

  <!-- Static page: no SPA JavaScript, CSS only -->
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
        <a href="/best/" data-zh="最佳工具" data-en="Best Tools">Best Tools</a>
        <span style="margin:0 6px">&gt;</span>
        <span>${esc(scenario.title)}</span>
      </nav>

      <!-- Hero -->
      <div class="bp-hero">
        <h1 data-zh="最佳 ${esc(scenario.title)} AI 工具 (${year})" data-en="Best AI Agent Skills for ${esc(scenario.title)} in ${year}">Best AI Agent Skills for ${esc(scenario.title)} in ${year}</h1>
        <p>${esc(scenario.description)}</p>
      </div>

      <!-- Quick Pick -->
      ${skills.length > 0 ? `<div class="bp-quick-pick">
        <span style="font-size:20px">⚡</span>
        <div style="flex:1;min-width:200px">
          <span class="bp-quick-pick-label" data-zh="快速推荐" data-en="Quick Pick">Quick Pick</span>
          <span class="bp-quick-pick-text" data-zh="— 只选一个的话，用" data-en="— If you only pick one, go with"> — If you only pick one, go with </span>
          <a href="${SITE}/skill/${esc(skills[0].repo_full_name)}/" style="color:var(--bp-link);font-weight:700;text-decoration:none">${esc(skills[0].repo_name)}</a>
          <span style="color:var(--bp-text-muted);font-size:13px;margin-left:4px">★ ${starsK(skills[0].stars)}</span>
          ${skills[0].description ? `<span style="color:var(--bp-text-secondary);font-size:13px"> — ${esc((skills[0].description || "").slice(0, 80))}</span>` : ""}
        </div>
      </div>` : ""}

      ${buildAeoSection(scenario, skills, year)}

      <!-- Skill Cards -->
      <section>
        <h2 class="bp-section-title" data-zh="Top ${skills.length} ${esc(scenario.title)} 工具" data-en="Top ${skills.length} ${esc(scenario.title)} Tools">Top ${skills.length} ${esc(scenario.title)} Tools</h2>
      ${skillCardsHtml}
      </section>

      <!-- Comparison Table -->
      <section style="margin-top:32px">
        <h2 class="bp-section-title" data-zh="对比" data-en="Comparison">Comparison</h2>
        <div class="bp-table-wrap">
          <table class="bp-table">
            <thead>
              <tr>
                <th>Tool</th>
                <th style="text-align:right">Stars</th>
                <th>Language</th>
                <th>License</th>
                <th style="text-align:right">Score</th>
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
        <h2 class="bp-section-title" style="font-size:18px" data-zh="相关场景" data-en="Related Categories">Related Categories</h2>
        <div class="bp-related">
        ${relatedHtml}
        </div>
      </section>` : ""}

      <!-- FAQ -->
      <section style="margin-top:32px" class="bp-faq">
        <h2 class="bp-section-title" style="font-size:18px" data-zh="常见问题" data-en="Frequently Asked Questions">Frequently Asked Questions</h2>
      ${faqHtml}
      </section>

      <!-- Newsletter -->
      ${buildNewsletterCta()}

      <!-- CTA -->
      <div style="margin:32px 0;text-align:center">
        <a href="/" class="bp-newsletter-btn cta-btn" style="display:inline-block;padding:10px 24px;border-radius:8px;text-decoration:none;font-size:14px" data-zh="探索全部 25,000+ 技能" data-en="Explore All 25,000+ Skills on Agent Skills Hub">Explore All 25,000+ Skills on Agent Skills Hub</a>
      </div>

      <!-- Footer -->
      <footer style="margin-top:48px;padding:24px 0;border-top:1px solid var(--bp-border);text-align:center;font-size:13px;color:var(--bp-text-muted)">
        <div style="display:flex;justify-content:center;gap:16px;flex-wrap:wrap;margin-bottom:8px">
          <a href="/about/" style="color:var(--bp-text-secondary);text-decoration:none">About</a>
          <a href="/blog/" style="color:var(--bp-text-secondary);text-decoration:none">Blog</a>
          <a href="/privacy/" style="color:var(--bp-text-secondary);text-decoration:none">Privacy</a>
          <a href="/terms/" style="color:var(--bp-text-secondary);text-decoration:none">Terms</a>
          <a href="https://github.com/ZhuYansen/agent-skills-hub" style="color:var(--bp-text-secondary);text-decoration:none">GitHub</a>
        </div>
        <p style="margin:0">&copy; ${year} Agent Skills Hub. Open-source project.</p>
      </footer>
    </div>
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
  const scenarioSkillCounts = {};
  const t0 = Date.now();

  for (const scenario of scenarios) {
    const skills = matchSkills(scenario, allSkills);
    if (!skills) {
      console.log(`  SKIP ${scenario.slug}: fewer than ${scenario.match.min_results} matches`);
      skipped++;
      continue;
    }

    scenarioSkillCounts[scenario.slug] = skills.length;

    const dir = join(DIST, "best", scenario.slug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(
      join(dir, "index.html"),
      buildScenarioHtml(scenario, skills, assetTags, scenarios),
    );
    console.log(`  \u2713 /best/${scenario.slug}/ (${skills.length} skills)`);
    generated++;
  }

  // Generate /best/ index page
  const bestDir = join(DIST, "best");
  mkdirSync(bestDir, { recursive: true });
  writeFileSync(
    join(bestDir, "index.html"),
    buildIndexHtml(scenarios, scenarioSkillCounts, assetTags),
  );
  console.log(`  \u2713 /best/ (index page, ${Object.keys(scenarioSkillCounts).length} scenarios)`);

  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`\nScenario pages: ${generated} generated + 1 index, ${skipped} skipped (${elapsed}s)`);
}

main().catch((err) => {
  console.error("Failed to generate scenario pages:", err);
  process.exit(1);
});
