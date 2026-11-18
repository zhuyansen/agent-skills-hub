/**
 * Copy dist/index.html into subdirectories for SPA routes that need
 * direct-access 200 status (instead of the 404.html SPA redirect).
 *
 * This gives us clean URLs, correct HTTP status codes, and proper SEO
 * without needing full pre-rendering.
 *
 * Special case: /about/ is rendered as a fully standalone content page
 * (not SPA) to maximize E-E-A-T signals for Google — the About content
 * is visible to both users and crawlers without JavaScript.
 */

import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { analyticsTags, esc, replaceShellContent } from "./shared-utils.mjs";
import { HOW_WE_GRADE_LINK, HOW_WE_GRADE_PATH, RULE_COUNT } from "../src/lib/howWeGradeMeta.mjs";
import { QUALITY_WEIGHTS } from "../src/lib/howWeGradeContent.mjs";
import { pick } from "../src/lib/proseContent.mjs";

const DIST = "dist";
const SITE = "https://agentskillshub.top";
const SERVICES = "https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/app/services";
const QUALITY_DIMENSIONS = QUALITY_WEIGHTS.rows.length;

/** One row of the How-we-grade weights table ("Name: what it covers", weight) as an /about/ list item. */
function dimensionHtml([dimension, weight], lang) {
  const [name, covers] = pick(dimension, lang).split(lang === "zh" ? "：" : ": ");
  return lang === "zh"
    ? `<strong>${name}（${weight}）</strong>——${covers}`
    : `<strong>${name} (${weight})</strong> — ${covers}`;
}

/** The quality score's dimensions, with the names and weights /how-we-grade/ shows. */
function qualityItems() {
  return QUALITY_WEIGHTS.rows.map((row) => {
    const en = dimensionHtml(row, "en");
    return `<li data-en="${esc(en)}" data-zh="${esc(dimensionHtml(row, "zh"))}">${en}</li>`;
  }).join("\n          ");
}

// SPA routes that need a real 200 status (own title/description/canonical)
// instead of relying on the 404.html fallback. The shell meta is English for
// SEO; the SPA hydrates and switches language per the user's preference.
// Freshness signal (GEO audit 2026-07-28): AI engines weight recency, but a
// hardcoded dateModified rots into a lie. Stamp it at build time instead —
// deploy runs on every push AND after each 8-hourly sync, so the date stays
// honest on its own. Written back to dist/index.html so the SPA entry and every
// shell generated from it below carry the same value.
const BUILD_DATE = new Date().toISOString().slice(0, 10);
let indexHtml = readFileSync(join(DIST, "index.html"), "utf-8");
if (indexHtml.includes("__BUILD_DATE__")) {
  indexHtml = indexHtml.replaceAll("__BUILD_DATE__", BUILD_DATE);
  writeFileSync(join(DIST, "index.html"), indexHtml);
  console.log(`  ✓ dateModified stamped ${BUILD_DATE}`);
}
const SHELLS = [
  {
    path: "enterprise",
    title:
      "Enterprise · The Trust Layer for AI Agent & MCP Deployment | Agent Skills Hub",
    description:
      "Audit open-source agent skills and MCP servers before production — deploy-time scanning, sandbox validation, license/SBOM compliance, on-prem mirroring, and SOC 2 / ISO 42001 / EU AI Act evidence.",
  },
  {
    // Core free tool — was missing a shell, so GitHub Pages served 404.html for
    // /analyzer (and every /analyzer?repo=… share link). GSC 2026-07-28 listed
    // those among "未找到 404": an indexable, linkable tool page that Google
    // could never index and that produced no unfurl card when shared.
    path: "analyzer",
    title:
      "Is This AI Skill or MCP Server Safe? Free Security Check — Agent Skills Hub",
    description:
      `Paste any GitHub repo URL for an instant security analysis: ${RULE_COUNT} published rules built on the SlowMist agent-security framework, trust tier, and quality score. Runs in your browser, no signup.`,
  },
  {
    // Batch-audit tool (Pro ladder), shipped 2026-09-09 WITHOUT a shell — so
    // GitHub Pages served 404.html for /org-audit/ and every /org-audit/?owner=…
    // share link. A live HTTP 404 renders fine for a click-through (the SPA
    // fallback hydrates) but never produces an unfurl card, which kills the
    // whole "share an org's audit" loop. noindex to match the page's own Helmet.
    path: "org-audit",
    title:
      "Batch Security Audit — Vet a Whole GitHub Org · Agent Skills Hub",
    description:
      "Enter a GitHub org or user to see the security grade of every skill and MCP server it ships — vet your whole stack at once instead of one repo at a time.",
    noindex: true,
  },
  {
    path: "ci-gate",
    title:
      "Team CI Skill Gate — Block Risky AI Skills & MCP Configs in PRs · Agent Skills Hub",
    description:
      "GitHub Action + SARIF security gate for SKILL.md, AGENTS.md, CLAUDE.md, .cursorrules, and .mcp.json. Built on 43 SlowMist & agent-era rules.",
  },
  {
    path: "submit",
    title: "Submit to the Hub — AgentSkillsHub",
    description:
      "Submit a Skill, compose a Workflow, or apply for Verified Creator. Three ways to contribute to the AgentSkillsHub directory.",
  },
  {
    path: "verified-creator/apply",
    title: "Apply for Verified Creator — AgentSkillsHub",
    description:
      "Apply for the AgentSkillsHub Verified Creator badge. For serious Skill authors who want recognition, trending boost, and consulting matchmaking.",
  },
  // Member (noindex) pages — shells only for a clean 200 on direct links; the
  // page itself carries robots=noindex so these don't enter the index.
  {
    path: "pro",
    title: "Pro Deep Search — Agent Skills Hub",
    description:
      "Member-only deep search: full README-text search across the catalog's agent skills and MCP servers, 200 results per page, CSV/JSON export, and API access.",
    noindex: true,
  },
  {
    path: "pro/board",
    title: "Pro Picks — Member Curation Board · Agent Skills Hub",
    description:
      "Pro members nominate and vote for the best agent skills; the top 3 each week get featured. Only SAFE-graded repos are eligible.",
    noindex: true,
  },
  {
    // Landing page for newsletter verification links. Transactional, so
    // noindex — but it MUST return 200: subscribers arrive here straight from
    // their inbox, and link-checkers/security scanners treat a 404 as broken.
    path: "verify-email",
    title: "Verify your email — Agent Skills Hub",
    description:
      "Confirm your subscription to the Agent Skills Hub weekly newsletter.",
    noindex: true,
  },
  {
    // Per-device localStorage page — zero SEO value, but a shell keeps it out
    // of GSC's 404 bucket and makes shared links resolve cleanly.
    path: "favorites",
    title: "My favorites — Agent Skills Hub",
    description:
      "Skills you saved on this device. Stored locally in your browser, never uploaded.",
    noindex: true,
  },
];

// index.html no longer ships a hardcoded canonical (dual-tag fix) — inject a
// placeholder once so the per-shell replace always has a target.
const indexHtmlWithCanonical = indexHtml.includes('rel="canonical"')
  ? indexHtml
  : indexHtml.replace("</head>", '<link rel="canonical" href="__CANONICAL__" />\n</head>');

for (const s of SHELLS) {
  let html = indexHtmlWithCanonical
    .replace(/<title>[^<]+<\/title>/, `<title>${s.title}</title>`)
    .replace(
      /<meta name="description" content="[^"]+"/,
      `<meta name="description" content="${s.description}"`,
    )
    .replace(
      /<link rel="canonical" href="[^"]+"/,
      `<link rel="canonical" href="https://agentskillshub.top/${s.path}/"`,
    );
  // Member pages want a clean 200 (they're linked to directly) but must NOT be
  // indexed — bake robots=noindex into the raw shell so non-JS crawlers obey it
  // too, not only the Helmet tag after hydration.
  if (s.noindex) {
    html = html.replace(
      "</head>",
      '<meta name="robots" content="noindex" />\n</head>',
    );
  }
  // Give the shell its OWN pre-hydration content. Without this it is a verbatim
  // copy of index.html, so /analyzer/, /pro/ and /enterprise/ each painted the
  // homepage — its <h1>, category grid and scenario list — until React mounted
  // and replaced the lot. Same defect Clarity caught on author pages
  // (2026-08-05: 26 dead clicks in one session); these shells carried it too,
  // and /analyzer/ is the busiest page on the site.
  const heading = s.h1 || s.title.split(/[·—|]/)[0].trim();
  html = replaceShellContent(
    html,
    `<h1>${heading}</h1>\n      <p>${s.description}</p>\n      <p><a href="/">Agent Skills Hub</a></p>`,
  );
  mkdirSync(join(DIST, s.path), { recursive: true });
  writeFileSync(join(DIST, s.path, "index.html"), html);
  console.log(`  ✓ /${s.path}/index.html (SPA shell)`);
}

// /business/ and /verified-creator/ were consolidated into /enterprise/.
// Emit static redirect stubs so crawlers pass authority to /enterprise/ and
// any direct hit bounces immediately (canonical + meta-refresh + JS replace).
const REDIRECTS = [
  { path: "business", to: "/enterprise/" },
  { path: "verified-creator", to: "/enterprise/" },
  // Legacy route: the SPA client-side-redirects /arena → /, but with no static
  // file Google only ever saw a 404. A stub passes the authority instead.
  { path: "arena", to: "/" },
  // Renamed scenario pages: same content at a new URL, so the old one points
  // there instead of returning 404 (opus-5-5-video renamed 2026-09-27;
  // ppt-skills merged into ppt-presentation 2026-07-06).
  { path: "best/opus-5-5-video", to: "/best/claude-video-skills/" },
  { path: "best/ppt-skills", to: "/best/ppt-presentation/" },
];

for (const r of REDIRECTS) {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Redirecting… — AgentSkillsHub</title>
<link rel="canonical" href="https://agentskillshub.top${r.to}" />
<meta http-equiv="refresh" content="0; url=${r.to}" />
<meta name="robots" content="noindex,follow" />
<script>location.replace(${JSON.stringify(r.to)});</script>
</head>
<body>Redirecting to <a href="${r.to}">${r.to}</a>…</body>
</html>`;
  const outDir = join(DIST, r.path);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, "index.html"), html);
  console.log(`  ✓ /${r.path}/ → ${r.to} (redirect stub)`);
}

// ── Special standalone /about/ page — E-E-A-T focused ─────────────
const aboutHtml = `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <title>About &amp; Methodology — AgentSkillsHub</title>
  ${analyticsTags()}
  <meta name="description" content="AgentSkillsHub is built by Jason Zhu, an independent researcher tracking open-source AI agent ecosystems. Learn about the team, how the quality and ranking scores work, and editorial principles." />
  <meta name="keywords" content="agentskillshub about, jason zhu, claude skills methodology, skill quality scoring, editorial team" />
  <link rel="canonical" href="https://agentskillshub.top/about/" />

  <meta property="og:title" content="About &amp; Methodology — AgentSkillsHub" />
  <meta property="og:description" content="The team, the methodology, the transparent scoring system behind AgentSkillsHub." />
  <meta property="og:type" content="profile" />
  <meta property="og:url" content="https://agentskillshub.top/about/" />
  <meta property="og:image" content="https://agentskillshub.top/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:site" content="@GoSailGlobal" />

  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "AboutPage",
    "name": "About AgentSkillsHub",
    "url": "https://agentskillshub.top/about/",
    "mainEntity": {
      "@type": "Person",
      "name": "Jason Zhu",
      "url": "https://x.com/GoSailGlobal",
      "sameAs": [
        "https://x.com/GoSailGlobal",
        "https://github.com/ZhuYansen",
        "https://www.youtube.com/@JasonZhuGoSail"
      ],
      "jobTitle": "Independent Researcher · Founder of AgentSkillsHub",
      "knowsAbout": [
        "Claude Skills",
        "Model Context Protocol",
        "AI Agent Ecosystem Analysis",
        "Open Source Quality Scoring"
      ]
    }
  }
  </script>

  <style>
    :root { color-scheme: light dark; }
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
      line-height: 1.65;
      color: #1e293b;
      background: #fafafa;
      margin: 0;
      padding: 0;
    }
    @media (prefers-color-scheme: dark) {
      body { color: #e2e8f0; background: #0a0e1a; }
      a { color: #818cf8; }
      .card { background: #111827; border-color: #1f2937; }
      .metric { background: #0f172a; }
    }
    .container { max-width: 780px; margin: 0 auto; padding: 40px 24px 80px; }
    header { border-bottom: 1px solid rgba(148, 163, 184, 0.2); padding-bottom: 16px; margin-bottom: 32px; }
    header nav { font-size: 14px; color: #64748b; }
    header nav a { color: inherit; margin-right: 12px; text-decoration: none; }
    header nav a:hover { color: #4f46e5; }
    h1 { font-size: 36px; line-height: 1.15; margin: 12px 0 8px; }
    .tagline { font-size: 17px; color: #64748b; margin: 0; }
    h2 { font-size: 22px; margin-top: 36px; margin-bottom: 12px; }
    h3 { font-size: 16px; margin-top: 20px; margin-bottom: 8px; color: #475569; }
    p { margin: 10px 0; }
    a { color: #4f46e5; }
    .card { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 22px; margin: 20px 0; }
    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 18px 0; }
    .metric { background: #f1f5f9; padding: 14px 16px; border-radius: 8px; }
    .metric .num { font-size: 24px; font-weight: 700; color: #0f172a; }
    .metric .label { font-size: 12px; color: #64748b; margin-top: 2px; }
    @media (prefers-color-scheme: dark) {
      .metric .num { color: #f8fafc; }
    }
    ul { padding-left: 22px; }
    li { margin: 6px 0; }
    footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid rgba(148,163,184,0.2); font-size: 13px; color: #64748b; }
    .cta { display: inline-block; padding: 10px 18px; background: #4f46e5; color: white !important; border-radius: 8px; text-decoration: none; font-weight: 500; margin-top: 8px; }
    .cta:hover { background: #4338ca; }
  </style>

</head>
<body>
  <div class="container">
    <header>
      <nav style="display:flex;align-items:center;gap:8px">
        <a href="/">AgentSkillsHub</a> ›
        <a href="/about/" data-en="About" data-zh="关于">About</a>
        <button id="lang-toggle" onclick="(function(b){var c=document.documentElement.lang==='zh-CN'?'en':'zh';localStorage.setItem('lang',c);document.documentElement.lang=c==='zh'?'zh-CN':'en';document.querySelectorAll('[data-zh]').forEach(function(el){el.innerHTML=c==='zh'?el.getAttribute('data-zh'):el.getAttribute('data-en')});b.textContent=c==='zh'?'EN':'中文'})(this)" style="margin-left:auto;cursor:pointer;border:1px solid rgba(148,163,184,0.4);background:transparent;color:inherit;border-radius:6px;padding:2px 10px;font-size:12px;font-weight:600">中文</button>
      </nav>
      <h1 data-en="About AgentSkillsHub" data-zh="关于 AgentSkillsHub">About AgentSkillsHub</h1>
      <p class="tagline" data-en="An open-source directory for Claude Skills, MCP Servers &amp; Agent Tools — built in public, scored transparently." data-zh="Claude 技能、MCP 服务器与 Agent 工具的开源目录——公开构建,透明评分。">An open-source directory for Claude Skills, MCP Servers &amp; Agent Tools — built in public, scored transparently.</p>
    </header>

    <section>
      <h2 data-en="Who runs this" data-zh="谁在运营">Who runs this</h2>
      <div class="card">
        <p data-en="<strong>AgentSkillsHub</strong> is built and maintained by <strong>Jason Zhu</strong> (<a href='https://x.com/GoSailGlobal' rel='author'>@GoSailGlobal</a> on X), an independent researcher tracking open-source AI agent ecosystems since 2024." data-zh="<strong>AgentSkillsHub</strong> 由 <strong>Jason Zhu</strong>(X 上的 <a href='https://x.com/GoSailGlobal' rel='author'>@GoSailGlobal</a>)构建并维护，他是自 2024 年起追踪开源 AI agent 生态的独立研究者。"><strong>AgentSkillsHub</strong> is built and maintained by <strong>Jason Zhu</strong> (<a href="https://x.com/GoSailGlobal" rel="author">@GoSailGlobal</a> on X), an independent researcher tracking open-source AI agent ecosystems since 2024.</p>
        <p data-en="Jason is also the author of the <a href='https://github.com/zhuyansen/skill-blue-book'>Blue Book of Agent Skills 2026</a> — an in-depth analysis of the Claude Skills / MCP / Codex ecosystem based on 62,000+ indexed repositories, published openly on GitHub with reproducible Python scripts." data-zh="Jason 也是 <a href='https://github.com/zhuyansen/skill-blue-book'>《Agent Skills 蓝皮书 2026》</a> 的作者——基于 62,000+ 已收录仓库对 Claude Skills / MCP / Codex 生态的深度分析，在 GitHub 公开发布并附可复现的 Python 脚本。">Jason is also the author of the <a href="https://github.com/zhuyansen/skill-blue-book">Blue Book of Agent Skills 2026</a> — an in-depth analysis of the Claude Skills / MCP / Codex ecosystem based on 62,000+ indexed repositories, published openly on GitHub with reproducible Python scripts.</p>
        <p data-en="The Hub is a solo project without external funding. There is no sales team, no 'pay for placement' tier, and no dark patterns. All editorial decisions and scoring formulas live in public on <a href='https://github.com/ZhuYansen/agent-skills-hub'>GitHub</a> under MIT license." data-zh="Hub 是一个无外部融资的个人项目。没有销售团队、没有“花钱买排名”档位、也没有暗黑模式。所有编辑决策与评分公式都以 MIT 许可公开在 <a href='https://github.com/ZhuYansen/agent-skills-hub'>GitHub</a> 上。">The Hub is a solo project without external funding. There is no sales team, no "pay for placement" tier, and no dark patterns. All editorial decisions and scoring formulas live in public on <a href="https://github.com/ZhuYansen/agent-skills-hub">GitHub</a> under MIT license.</p>
      </div>
    </section>

    <section>
      <h2 data-en="What we track" data-zh="我们追踪什么">What we track</h2>
      <div class="metrics">
        <div class="metric"><div class="num"><span data-count="total">267,000+</span></div><div class="label" data-en="indexed skills" data-zh="已收录技能">indexed skills</div></div>
        <div class="metric"><div class="num">7</div><div class="label" data-en="categories" data-zh="分类">categories</div></div>
        <div class="metric"><div class="num">58</div><div class="label" data-en="scenario pages" data-zh="场景页">scenario pages</div></div>
        <div class="metric"><div class="num">8h</div><div class="label" data-en="refresh cadence" data-zh="刷新频率">refresh cadence</div></div>
        <div class="metric"><div class="num">${QUALITY_DIMENSIONS}</div><div class="label" data-en="quality dimensions" data-zh="质量维度">quality dimensions</div></div>
        <div class="metric"><div class="num">MIT</div><div class="label" data-en="source license" data-zh="源码许可">source license</div></div>
      </div>
      <p data-en="Every GitHub repository matching our search patterns flows through a 6-phase pipeline every 8 hours: search → metadata enrichment → README fetch → quality scoring → category classification → composability analysis. No manual curation is applied to ranking — all signals are data-driven to avoid editorial bias." data-zh="每个匹配搜索模式的 GitHub 仓库每 8 小时流经一条 6 阶段流水线：搜索 → 元数据增强 → README 抓取 → 质量评分 → 分类归类 → 可组合性分析。排名不做人工干预——所有信号皆数据驱动，以避免编辑偏见。">Every GitHub repository matching our search patterns flows through a 6-phase pipeline every 8 hours: search → metadata enrichment → README fetch → quality scoring → category classification → composability analysis. No manual curation is applied to ranking — all signals are data-driven to avoid editorial bias.</p>
    </section>

    <section>
      <h2 data-en="Editorial methodology" data-zh="编辑方法论">Editorial methodology</h2>
      <div class="card">
        <h3 data-en="The quality score" data-zh="质量分">The quality score</h3>
        <p data-en="Every skill gets a <strong>quality score (0–100)</strong>: how well its README and metadata prepare a person or an agent to use it. It weighs ${QUALITY_DIMENSIONS} dimensions, set in <a href='${SERVICES}/quality_analyzer.py'>services/quality_analyzer.py</a>:" data-zh="每个技能都有一个<strong>质量分（0–100）</strong>，衡量它的 README 和元数据能不能让人或 agent 顺利用上它。它按 ${QUALITY_DIMENSIONS} 个维度加权，权重写在 <a href='${SERVICES}/quality_analyzer.py'>services/quality_analyzer.py</a>：">Every skill gets a <strong>quality score (0–100)</strong>: how well its README and metadata prepare a person or an agent to use it. It weighs ${QUALITY_DIMENSIONS} dimensions, set in <a href="${SERVICES}/quality_analyzer.py">services/quality_analyzer.py</a>:</p>
        <ul>
          ${qualityItems()}
        </ul>
        <h3 data-en="The ranking score" data-zh="排名分">The ranking score</h3>
        <p data-en="Rankings use a separate <strong>ranking score (0–100)</strong> that blends ten weighted signals: stars, forks, the author's followers, resolved issues, commits, recency, the quality score above, recent star momentum, size and a bonus for specialised domains. The weights are in <a href='${SERVICES}/scorer.py'>services/scorer.py</a> and on <a href='${HOW_WE_GRADE_PATH}#how-lists-are-ordered'>${HOW_WE_GRADE_LINK.en}</a>." data-zh="排名用的是另一个<strong>排名分（0–100）</strong>，综合十个加权信号：星数、fork 数、作者的关注者数、已解决的 issue、提交数、最近更新、上面的质量分、近期涨星势头、体量，以及细分领域加分。权重见 <a href='${SERVICES}/scorer.py'>services/scorer.py</a> 和<a href='${HOW_WE_GRADE_PATH}#how-lists-are-ordered'>${HOW_WE_GRADE_LINK.zh}</a>页。">Rankings use a separate <strong>ranking score (0–100)</strong> that blends ten weighted signals: stars, forks, the author's followers, resolved issues, commits, recency, the quality score above, recent star momentum, size and a bonus for specialised domains. The weights are in <a href="${SERVICES}/scorer.py">services/scorer.py</a> and on <a href="${HOW_WE_GRADE_PATH}#how-lists-are-ordered">${HOW_WE_GRADE_LINK.en}</a>.</p>

        <h3 data-en="Daily &amp; weekly curation" data-zh="日报与周报精选">Daily &amp; weekly curation</h3>
        <p data-en="Daily reports feature skills newly indexed in the last 48 hours with at least 20 GitHub stars. The weekly 'Trending' list ranks by <code>star_velocity</code> (stars per day over the last 7 days). Both are automated but the final Top 10 is human-reviewed to exclude obvious forks, batch spam accounts, and misclassified non-skills." data-zh="日报精选过去 48 小时内新收录、且至少 20 个 GitHub Star 的技能。周报“趋势榜”按 <code>star_velocity</code>（过去 7 天每日 Star 增量）排序。两者均自动化，但最终 Top 10 经人工复核，剔除明显的 fork、批量刷号与误分类的非技能项目。">Daily reports feature skills newly indexed in the last 48 hours with at least 20 GitHub stars. The weekly "Trending" list ranks by <code>star_velocity</code> (stars per day over the last 7 days). Both are automated but the final Top 10 is human-reviewed to exclude obvious forks, batch spam accounts, and misclassified non-skills.</p>

        <h3 data-en="How decisions are made transparently" data-zh="决策如何保持透明">How decisions are made transparently</h3>
        <p data-en="Editorial judgement is required in exactly three places:" data-zh="编辑判断仅在三处需要：">Editorial judgement is required in exactly three places:</p>
        <ol>
          <li data-en="<strong>Category classification corrections</strong> — when keyword inference misfires" data-zh="<strong>分类归类修正</strong>——当关键词推断出错时"><strong>Category classification corrections</strong> — when keyword inference misfires</li>
          <li data-en="<strong>Spam &amp; batch-farming exclusion</strong> — documented in <a href='https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/discover_candidates.py'>discover_candidates.py</a>" data-zh="<strong>垃圾与批量刷号剔除</strong>——记录在 <a href='https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/discover_candidates.py'>discover_candidates.py</a>"><strong>Spam &amp; batch-farming exclusion</strong> — documented in <a href="https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/discover_candidates.py">discover_candidates.py</a></li>
          <li data-en="<strong>Verified Creator decisions</strong> — authors <a href='/verified-creator/apply/'>apply</a>, and each application is reviewed by hand within 5 business days" data-zh="<strong>认证创作者决策</strong>——作者<a href='/verified-creator/apply/'>提交申请</a>，每份申请都在 5 个工作日内人工审核"><strong>Verified Creator decisions</strong> — authors <a href="/verified-creator/apply/">apply</a>, and each application is reviewed by hand within 5 business days</li>
        </ol>
        <p data-en="Every other ranking decision is purely data-driven and reproducible from the open-source codebase." data-zh="其余所有排名决策纯由数据驱动，可从开源代码库复现。">Every other ranking decision is purely data-driven and reproducible from the open-source codebase.</p>
      </div>
    </section>

    <section>
      <h2 data-en="Source code &amp; data" data-zh="源码与数据">Source code &amp; data</h2>
      <p data-en="Every line of code and every data snapshot used for the Blue Book is public:" data-zh="蓝皮书用到的每一行代码与每一份数据快照都是公开的：">Every line of code and every data snapshot used for the Blue Book is public:</p>
      <ul>
        <li data-en="<a href='https://github.com/ZhuYansen/agent-skills-hub'>Source code</a> — frontend (React + Vite), backend (FastAPI), scoring pipeline (Python)" data-zh="<a href='https://github.com/ZhuYansen/agent-skills-hub'>源代码</a>——前端（React + Vite）、后端（FastAPI）、评分流水线（Python）"><a href="https://github.com/ZhuYansen/agent-skills-hub">Source code</a> — frontend (React + Vite), backend (FastAPI), scoring pipeline (Python)</li>
        <li data-en="<a href='https://github.com/zhuyansen/skill-blue-book'>Blue Book of Agent Skills 2026</a> — 12-chapter research report with reproducible Python analysis" data-zh="<a href='https://github.com/zhuyansen/skill-blue-book'>《Agent Skills 蓝皮书 2026》</a>——12 章研究报告，附可复现的 Python 分析"><a href="https://github.com/zhuyansen/skill-blue-book">Blue Book of Agent Skills 2026</a> — 12-chapter research report with reproducible Python analysis</li>
        <li data-en="<a href='/sitemap.xml'>Sitemap</a> — 5,700+ indexed URLs across skills, categories, scenarios, authors" data-zh="<a href='/sitemap.xml'>站点地图</a>——覆盖技能、分类、场景、作者的 5,700+ 个已收录 URL"><a href="/sitemap.xml">Sitemap</a> — 5,700+ indexed URLs across skills, categories, scenarios, authors</li>
      </ul>
    </section>

    <section>
      <h2 data-en="Contact" data-zh="联系">Contact</h2>
      <p data-en="Questions, corrections, or tips? Reach out via:" data-zh="有疑问、纠错或线索？通过以下方式联系：">Questions, corrections, or tips? Reach out via:</p>
      <ul>
        <li data-en="X DM: <a href='https://x.com/GoSailGlobal'>@GoSailGlobal</a>" data-zh="X 私信：<a href='https://x.com/GoSailGlobal'>@GoSailGlobal</a>">X DM: <a href="https://x.com/GoSailGlobal">@GoSailGlobal</a></li>
        <li data-en="Email: <a href='mailto:m17551076169@gmail.com'>m17551076169@gmail.com</a>" data-zh="邮箱：<a href='mailto:m17551076169@gmail.com'>m17551076169@gmail.com</a>">Email: <a href="mailto:m17551076169@gmail.com">m17551076169@gmail.com</a></li>
        <li data-en="GitHub issues: <a href='https://github.com/ZhuYansen/agent-skills-hub/issues'>agent-skills-hub/issues</a>" data-zh="GitHub issues：<a href='https://github.com/ZhuYansen/agent-skills-hub/issues'>agent-skills-hub/issues</a>">GitHub issues: <a href="https://github.com/ZhuYansen/agent-skills-hub/issues">agent-skills-hub/issues</a></li>
      </ul>
      <a class="cta" href="/" data-en="← Back to Explore All Skills" data-zh="← 返回探索全部技能">← Back to Explore All Skills</a>
    </section>

    <footer>
      <p data-en="Last updated: 2026-11-16 · Published by Jason Zhu · MIT licensed · <a href='/ai-info/'>AI Info</a> · <a href='/'>Back to Home</a>" data-zh="最后更新：2026-11-16 · 发布者 Jason Zhu · MIT 许可 · <a href='/ai-info/'>AI 事实页</a> · <a href='/'>返回首页</a>">Last updated: 2026-11-16 · Published by Jason Zhu · MIT licensed · <a href="/ai-info/">AI Info</a> · <a href="/">Back to Home</a></p>
    </footer>
  </div>
  <script>(function(){var l=localStorage.getItem('lang')||(navigator.language&&navigator.language.toLowerCase().indexOf('zh')===0?'zh':'en');document.documentElement.lang=l==='zh'?'zh-CN':'en';var b=document.getElementById('lang-toggle');if(b)b.textContent=l==='zh'?'EN':'中文';if(l==='zh')document.querySelectorAll('[data-zh]').forEach(function(el){el.innerHTML=el.getAttribute('data-zh')});})();</script>
</body>
</html>`;

const aboutDir = join(DIST, "about");
mkdirSync(aboutDir, { recursive: true });
writeFileSync(join(aboutDir, "index.html"), aboutHtml);
console.log(`  ✓ /about/index.html (standalone E-E-A-T page)`);

// ────────────────────────────────────────────────────────────────
// Standalone /ai-info/index.html — machine-readable signed facts page
// for AI crawlers, answer engines, and automated fact verification.
// ────────────────────────────────────────────────────────────────
const aiInfoTitle = "AI Info — Official Entity & Platform Facts | Agent Skills Hub";
const aiInfoDesc =
  "Signed, machine-readable platform facts for AI agents and answer engines: operated by BRICKAI / GoSailGlobal LLC, 267,000+ indexed AI agent skills & MCP servers security-graded against 43 published rules, Zenodo dataset DOI 10.5281/zenodo.21292799.";
const aiInfoUrl = `${SITE}/ai-info/`;

const aiInfoHtml = `<!doctype html>
<html lang="en">
<head>
  <script>(function(){var t=localStorage.getItem('theme');if(t==='dark'||(t!=='light'&&window.matchMedia('(prefers-color-scheme:dark)').matches)){document.documentElement.classList.add('dark')}})();</script>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${aiInfoTitle}</title>
  <meta name="description" content="${aiInfoDesc}" />
  <link rel="canonical" href="${aiInfoUrl}" />
  <meta property="og:title" content="${aiInfoTitle}" />
  <meta property="og:description" content="${aiInfoDesc}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="${aiInfoUrl}" />
  <meta property="og:site_name" content="Agent Skills Hub" />
  <meta property="og:image" content="${SITE}/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${aiInfoTitle}" />
  <meta name="twitter:description" content="${aiInfoDesc}" />
  <meta name="twitter:site" content="@GoSailGlobal" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "AboutPage",
    "name": "Agent Skills Hub — Official AI Info & Platform Facts",
    "url": "${aiInfoUrl}",
    "dateModified": "${BUILD_DATE}",
    "mainEntity": {
      "@type": "Organization",
      "@id": "${SITE}/#organization",
      "name": "Agent Skills Hub",
      "alternateName": ["AgentSkillsHub", "agentskillshub.top", "BRICKAI"],
      "legalName": "BRICKAI (GoSailGlobal LLC)",
      "url": "${SITE}/",
      "description": "AI Agent Skills & MCP Trust Layer — open-source directory and security-grading platform for Claude skills, MCP servers, and AI agent tools.",
      "foundingDate": "2026-03-08",
      "founder": {
        "@type": "Person",
        "name": "Jason Zhu",
        "url": "https://x.com/GoSailGlobal"
      },
      "sameAs": [
        "https://github.com/ZhuYansen/agent-skills-hub",
        "https://x.com/GoSailGlobal",
        "https://www.npmjs.com/package/@agentskillshub/cli",
        "https://www.npmjs.com/package/@agentskillshub/mcp",
        "https://www.crunchbase.com/organization/agent-skills-hub",
        "https://www.wikidata.org/wiki/Q141986406"
      ]
    },
    "about": {
      "@type": "Dataset",
      "name": "AI Agent Skills Security Grades Dataset",
      "description": "Security grades (Safe / Caution / Unsafe / Reject), red flags and quality scores for 130,173 open-source AI agent skills and MCP servers indexed from GitHub (CC BY 4.0 snapshot).",
      "identifier": "https://doi.org/10.5281/zenodo.21292799",
      "url": "https://doi.org/10.5281/zenodo.21292799",
      "license": "https://creativecommons.org/licenses/by/4.0/",
      "datePublished": "2026-07-10",
      "creator": {
        "@type": "Person",
        "name": "Jason Zhu",
        "url": "https://x.com/GoSailGlobal"
      },
      "publisher": {
        "@id": "${SITE}/#organization"
      },
      "isAccessibleForFree": true,
      "sameAs": [
        "https://www.wikidata.org/wiki/Q141735092",
        "https://huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades",
        "https://www.kaggle.com/datasets/yansenzhu/agent-skills-security-grades"
      ]
    }
  }
  </script>
  <style>
    :root { --bg:#ffffff; --fg:#0f172a; --muted:#475569; --border:#e2e8f0; --accent:#2563eb; --card:#f8fafc; }
    html.dark { --bg:#0b1220; --fg:#e2e8f0; --muted:#94a3b8; --border:#1e293b; --accent:#60a5fa; --card:#111c2d; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif; background:var(--bg); color:var(--fg); line-height:1.65; }
    .wrap { max-width: 820px; margin: 0 auto; padding: 48px 24px 80px; }
    header { border-bottom: 1px solid var(--border); padding-bottom: 24px; margin-bottom: 32px; }
    nav { font-size: 14px; margin-bottom: 16px; display:flex; align-items:center; flex-wrap:wrap; gap:16px; }
    nav a { color: var(--accent); text-decoration: none; }
    h1 { font-size: 30px; margin: 0 0 8px; line-height: 1.25; }
    h2 { font-size: 20px; margin: 32px 0 12px; padding-top: 8px; border-top: 1px solid var(--border); }
    p, li { color: var(--fg); font-size: 15px; }
    .tagline { color: var(--muted); font-size: 16px; margin: 0; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px; margin: 16px 0; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }
    th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
    th { width: 220px; color: var(--muted); font-weight: 600; background: var(--card); }
    code { background: var(--card); border: 1px solid var(--border); padding: 1px 6px; border-radius: 4px; font-size: 13px; }
    a { color: var(--accent); }
    footer { margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--border); color: var(--muted); font-size: 13px; }
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <nav aria-label="Breadcrumb">
        <a href="/" data-en="← Home" data-zh="← 首页">← Home</a>
        <a href="/about/" data-en="About" data-zh="关于">About</a>
        <a href="${HOW_WE_GRADE_PATH}" data-en="How We Grade" data-zh="怎么评级">How We Grade</a>
        <a href="/enterprise/" data-en="Enterprise" data-zh="企业版">Enterprise</a>
        <a href="/llms.txt">llms.txt</a>
        <button id="lang-toggle" onclick="(function(b){var c=document.documentElement.lang==='zh-CN'?'en':'zh';localStorage.setItem('lang',c);document.documentElement.lang=c==='zh'?'zh-CN':'en';document.querySelectorAll('[data-zh]').forEach(function(el){el.innerHTML=c==='zh'?el.getAttribute('data-zh'):el.getAttribute('data-en')});b.textContent=c==='zh'?'EN':'中文'})(this)" style="margin-left:auto;cursor:pointer;border:1px solid rgba(148,163,184,0.4);background:transparent;color:inherit;border-radius:6px;padding:2px 10px;font-size:12px;font-weight:600">中文</button>
      </nav>
      <h1 data-en="Agent Skills Hub — Official AI Info &amp; Signed Facts" data-zh="Agent Skills Hub — 官方 AI 机器可读事实页">Agent Skills Hub — Official AI Info &amp; Signed Facts</h1>
      <p class="tagline" data-en="Canonical, first-party reference facts for AI assistants, search engines, and researchers citing Agent Skills Hub (agentskillshub.top)." data-zh="供 AI 助手、搜索引擎与研究人员引用 Agent Skills Hub（agentskillshub.top）的官方第一方签字版事实。">Canonical, first-party reference facts for AI assistants, search engines, and researchers citing Agent Skills Hub (agentskillshub.top).</p>
    </header>

    <div class="card">
      <p style="margin:0" data-en="<strong>TL;DR (BLUF):</strong> <strong>Agent Skills Hub</strong> (<code>agentskillshub.top</code>), operated by <strong>BRICKAI</strong> (GoSailGlobal LLC) and founded by <strong>Jason Zhu</strong>, is the open-source <strong>AI Agent Skills &amp; MCP Trust Layer</strong>. It indexes <span data-count='total'>267,000+</span> open-source AI agent skills, MCP servers, and tools from GitHub (refreshed every 8 hours), security-grades <span data-count='graded'>132,000+</span> repositories (<span data-count='graded-over-100'>99%</span> of skills over 100★ and <span data-count='graded-over-1000'>99%</span> over 1,000★) against <a href='${HOW_WE_GRADE_PATH}'>43 published rules</a>, and publishes the full security census under CC-BY-4.0 at <a href='https://doi.org/10.5281/zenodo.21292799'>DOI 10.5281/zenodo.21292799</a>." data-zh="<strong>核心事实（BLUF）：</strong> <strong>Agent Skills Hub</strong>（<code>agentskillshub.top</code>）由 <strong>BRICKAI</strong>（GoSailGlobal LLC）运营、<strong>Jason Zhu</strong> 创立，定位为开源 <strong>AI Agent Skills &amp; MCP Trust Layer（信任层）</strong>。平台每 8 小时从 GitHub 同步并收录 <span data-count='total'>267,000+</span> 个 AI Agent 技能与 MCP 服务器，基于 <a href='${HOW_WE_GRADE_PATH}'>43 条公开规则</a>对 <span data-count='graded'>132,000+</span> 个项目进行安全评级（覆盖 <span data-count='graded-over-100'>99%</span> 的百星项目与 <span data-count='graded-over-1000'>99%</span> 的千星项目），并以 CC-BY-4.0 协议发布可引用数据集 <a href='https://doi.org/10.5281/zenodo.21292799'>DOI 10.5281/zenodo.21292799</a>。"><strong>TL;DR (BLUF):</strong> <strong>Agent Skills Hub</strong> (<code>agentskillshub.top</code>), operated by <strong>BRICKAI</strong> (GoSailGlobal LLC) and founded by <strong>Jason Zhu</strong>, is the open-source <strong>AI Agent Skills &amp; MCP Trust Layer</strong>. It indexes <span data-count="total">267,000+</span> open-source AI agent skills, MCP servers, and tools from GitHub (refreshed every 8 hours), security-grades <span data-count="graded">132,000+</span> repositories (<span data-count="graded-over-100">99%</span> of skills over 100★ and <span data-count="graded-over-1000">99%</span> over 1,000★) against <a href="${HOW_WE_GRADE_PATH}">43 published rules</a>, and publishes the full security census under CC-BY-4.0 at <a href="https://doi.org/10.5281/zenodo.21292799">DOI 10.5281/zenodo.21292799</a>.</p>
    </div>

    <section>
      <h2 data-en="1. Entity &amp; Positioning" data-zh="1. 主体与定位">1. Entity &amp; Positioning</h2>
      <table>
        <tbody>
          <tr><th data-en="Platform Name" data-zh="平台名称">Platform Name</th><td>Agent Skills Hub (<code>AgentSkillsHub</code>)</td></tr>
          <tr><th data-en="Canonical Domain" data-zh="官方域名">Canonical Domain</th><td><a href="${SITE}/">${SITE}</a> (not affiliated with other similarly named domains)</td></tr>
          <tr><th data-en="Operating Entity" data-zh="运营主体">Operating Entity</th><td><strong>BRICKAI</strong> / GoSailGlobal LLC</td></tr>
          <tr><th data-en="Founder &amp; Maintainer" data-zh="创始人与维护者">Founder &amp; Maintainer</th><td>Jason Zhu (<a href="https://x.com/GoSailGlobal">@GoSailGlobal</a> · <a href="https://github.com/ZhuYansen">GitHub</a>)</td></tr>
          <tr><th data-en="Positioning" data-zh="核心定位">Positioning</th><td data-en="AI Agent Skills &amp; MCP Trust Layer — security-graded directory, hands-on scenario benchmarks, and enterprise pre-deployment audit." data-zh="AI Agent Skills &amp; MCP Trust Layer（信任层）—— 安全评级目录、场景端到端实测基准与企业部署前审计。">AI Agent Skills &amp; MCP Trust Layer — security-graded directory, hands-on scenario benchmarks, and enterprise pre-deployment audit.</td></tr>
          <tr><th data-en="Launch Date" data-zh="上线日期">Launch Date</th><td>2026-03-08</td></tr>
          <tr><th data-en="Source Code License" data-zh="开源协议">Source Code License</th><td>MIT (<a href="https://github.com/ZhuYansen/agent-skills-hub">github.com/ZhuYansen/agent-skills-hub</a>)</td></tr>
          <tr><th data-en="Knowledge Graph / Wikidata" data-zh="知识图谱 / Wikidata">Knowledge Graph / Wikidata</th><td>Organization: <a href="https://www.wikidata.org/wiki/Q141986406">Q141986406</a> · Dataset: <a href="https://www.wikidata.org/wiki/Q141735092">Q141735092</a></td></tr>
        </tbody>
      </table>
    </section>

    <section>
      <h2 data-en="2. Catalog Scale &amp; Security Grading Rules" data-zh="2. 收录规模与安全评级规则">2. Catalog Scale &amp; Security Grading Rules</h2>
      <table>
        <tbody>
          <tr><th data-en="Indexed Repositories" data-zh="收录仓库总数">Indexed Repositories</th><td><span data-count="total">267,000+</span> open-source AI agent skills, MCP servers, Claude Code skills, Codex skills, and agent tools</td></tr>
          <tr><th data-en="Security-Graded Count" data-zh="已安全评级数量">Security-Graded Count</th><td><span data-count="graded">132,000+</span> repositories graded (<span data-count="graded-over-100">99%</span> of repos &gt; 100★; <span data-count="graded-over-1000">99%</span> of repos &gt; 1,000★)</td></tr>
          <tr><th data-en="Refresh Cadence" data-zh="数据刷新频率">Refresh Cadence</th><td>Every 8 hours via automated 6-phase GitHub pipeline</td></tr>
          <tr><th data-en="Security Grading Rules" data-zh="公开安全评级规则">Security Grading Rules</th><td><a href="${HOW_WE_GRADE_PATH}">43 published rules</a> across 11 red-flag categories modeled on the SlowMist Agent Security taxonomy (data exfiltration, credential harvesting, sensitive directory access, agent memory/config theft, dynamic code execution, privilege escalation, persistence, reverse shell, destructive commands, obfuscation, supply-chain installers) + 5-tier source trust hierarchy</td></tr>
          <tr><th data-en="Security Grades" data-zh="安全等级划分">Security Grades</th><td><code>SAFE</code> · <code>CAUTION</code> · <code>UNSAFE</code> · <code>REJECT</code> (unfetched/README-less repos stay <code>UNAUDITED</code>)</td></tr>
          <tr><th data-en="Quality &amp; Ranking Scores" data-zh="质量分与排名分">Quality &amp; Ranking Scores</th><td>0–100 Quality Score (${QUALITY_DIMENSIONS} documentation &amp; agent-readiness dimensions) + 0–100 Ranking Score (10 weighted signals); full weights documented at <a href="${HOW_WE_GRADE_PATH}">${HOW_WE_GRADE_PATH}</a></td></tr>
          <tr><th data-en="Hands-On Scenario Benchmarks" data-zh="场景端到端实测">Hands-On Scenario Benchmarks</th><td>34 live <a href="/best/">/best/&lt;scenario&gt;/</a> guides (16 with end-to-end task run tables in <code>scenario-runs.json</code>, 12 with formal <code>method</code> rubrics, 15 mirrored as open-source GitHub lists)</td></tr>
        </tbody>
      </table>
    </section>

    <section>
      <h2 data-en="3. Open Datasets &amp; Citations" data-zh="3. 开放数据集与学术引用">3. Open Datasets &amp; Citations</h2>
      <ul>
        <li><strong>Zenodo (Canonical DOI):</strong> <a href="https://doi.org/10.5281/zenodo.21292799">https://doi.org/10.5281/zenodo.21292799</a> (DOI: <code>10.5281/zenodo.21292799</code>, CC-BY-4.0, 130,173 graded skills/servers snapshot)</li>
        <li><strong>Hugging Face Mirror:</strong> <a href="https://huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades">https://huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades</a></li>
        <li><strong>Kaggle Mirror:</strong> <a href="https://www.kaggle.com/datasets/yansenzhu/agent-skills-security-grades">https://www.kaggle.com/datasets/yansenzhu/agent-skills-security-grades</a></li>
        <li><strong>Blue Book of Agent Skills 2026:</strong> <a href="${SITE}/book/">${SITE}/book/</a> · <a href="https://github.com/zhuyansen/skill-blue-book">github.com/zhuyansen/skill-blue-book</a></li>
        <li><strong>Monthly Ecosystem Report:</strong> <a href="${SITE}/stats/">${SITE}/stats/</a> (State of Agent Skills)</li>
      </ul>
    </section>

    <section>
      <h2 data-en="4. Machine &amp; Agent Entry Points" data-zh="4. 机器与 Agent 接入入口">4. Machine &amp; Agent Entry Points</h2>
      <ul>
        <li><strong>CLI (zero-install, offline search + live audit):</strong> <code>npx @agentskillshub/cli search "&lt;query&gt;" --safe</code> · <code>npx @agentskillshub/cli audit &lt;owner/repo&gt;</code></li>
        <li><strong>MCP Server (for Claude Desktop, Cursor, Windsurf, Claude Code):</strong> <code>npx -y @agentskillshub/mcp</code></li>
        <li><strong>Agent Skill File:</strong> <a href="${SITE}/skill.md">${SITE}/skill.md</a></li>
        <li><strong>LLM Index:</strong> <a href="${SITE}/llms.txt">${SITE}/llms.txt</a></li>
        <li><strong>Enterprise Stack Audit (48h turnaround):</strong> <a href="${SITE}/enterprise/">${SITE}/enterprise/</a></li>
      </ul>
    </section>

    <footer>
      <p data-en="Signed by BRICKAI (GoSailGlobal LLC) · Last verified &amp; updated: ${BUILD_DATE} · <a href='/about/'>About</a> · <a href='${HOW_WE_GRADE_PATH}'>How We Grade</a> · <a href='/'>Home</a>" data-zh="BRICKAI（GoSailGlobal LLC）签字版事实 · 最后核实与更新：${BUILD_DATE} · <a href='/about/'>关于</a> · <a href='${HOW_WE_GRADE_PATH}'>怎么评级</a> · <a href='/'>首页</a>">Signed by BRICKAI (GoSailGlobal LLC) · Last verified &amp; updated: ${BUILD_DATE} · <a href="/about/">About</a> · <a href="${HOW_WE_GRADE_PATH}">How We Grade</a> · <a href="/">Home</a></p>
    </footer>
  </div>
  <script>(function(){var l=localStorage.getItem('lang')||(navigator.language&&navigator.language.toLowerCase().indexOf('zh')===0?'zh':'en');document.documentElement.lang=l==='zh'?'zh-CN':'en';var b=document.getElementById('lang-toggle');if(b)b.textContent=l==='zh'?'EN':'中文';if(l==='zh')document.querySelectorAll('[data-zh]').forEach(function(el){el.innerHTML=el.getAttribute('data-zh')});})();</script>
</body>
</html>`;

const aiInfoDir = join(DIST, "ai-info");
mkdirSync(aiInfoDir, { recursive: true });
writeFileSync(join(aiInfoDir, "index.html"), aiInfoHtml);
console.log(`  ✓ /ai-info/index.html (standalone machine-readable facts page)`);

console.log(
  `Static pages: ${SHELLS.length} SPA shells + ${REDIRECTS.length} redirect stubs + /about/ + /ai-info/ generated`,
);
