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

const DIST = "dist";

// SPA routes that need a real 200 status (own title/description/canonical)
// instead of relying on the 404.html fallback. The shell meta is English for
// SEO; the SPA hydrates and switches language per the user's preference.
const indexHtml = readFileSync(join(DIST, "index.html"), "utf-8");
const SHELLS = [
  {
    path: "enterprise",
    title:
      "Enterprise · The Trust Layer for AI Agent & MCP Deployment | Agent Skills Hub",
    description:
      "Audit 130,000+ open-source agent skills and MCP servers before production — deploy-time scanning, sandbox validation, license/SBOM compliance, on-prem mirroring, and SOC 2 / ISO 42001 / EU AI Act evidence.",
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
];

// index.html no longer ships a hardcoded canonical (dual-tag fix) — inject a
// placeholder once so the per-shell replace always has a target.
const indexHtmlWithCanonical = indexHtml.includes('rel="canonical"')
  ? indexHtml
  : indexHtml.replace("</head>", '<link rel="canonical" href="__CANONICAL__" />\n</head>');

for (const s of SHELLS) {
  const html = indexHtmlWithCanonical
    .replace(/<title>[^<]+<\/title>/, `<title>${s.title}</title>`)
    .replace(
      /<meta name="description" content="[^"]+"/,
      `<meta name="description" content="${s.description}"`,
    )
    .replace(
      /<link rel="canonical" href="[^"]+"/,
      `<link rel="canonical" href="https://agentskillshub.top/${s.path}/"`,
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
  <meta name="description" content="AgentSkillsHub is built by Jason Zhu, an independent researcher tracking open-source AI agent ecosystems. Learn about the team, 10-dimension quality scoring methodology, and editorial principles." />
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
        "https://github.com/ZhuYansen"
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

  <script defer data-domain="agentskillshub.top" src="https://plausible.io/js/script.outbound-links.js"></script>
  <script type="text/javascript">(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window, document, "clarity", "script", "wh16g932g8");</script>
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
        <div class="metric"><div class="num">130,000+</div><div class="label" data-en="indexed skills" data-zh="已收录技能">indexed skills</div></div>
        <div class="metric"><div class="num">7</div><div class="label" data-en="categories" data-zh="分类">categories</div></div>
        <div class="metric"><div class="num">58</div><div class="label" data-en="scenario pages" data-zh="场景页">scenario pages</div></div>
        <div class="metric"><div class="num">8h</div><div class="label" data-en="refresh cadence" data-zh="刷新频率">refresh cadence</div></div>
        <div class="metric"><div class="num">10</div><div class="label" data-en="quality dimensions" data-zh="质量维度">quality dimensions</div></div>
        <div class="metric"><div class="num">MIT</div><div class="label" data-en="source license" data-zh="源码许可">source license</div></div>
      </div>
      <p data-en="Every GitHub repository matching our search patterns flows through a 6-phase pipeline every 8 hours: search → metadata enrichment → README fetch → quality scoring → category classification → composability analysis. No manual curation is applied to ranking — all signals are data-driven to avoid editorial bias." data-zh="每个匹配搜索模式的 GitHub 仓库每 8 小时流经一条 6 阶段流水线：搜索 → 元数据增强 → README 抓取 → 质量评分 → 分类归类 → 可组合性分析。排名不做人工干预——所有信号皆数据驱动，以避免编辑偏见。">Every GitHub repository matching our search patterns flows through a 6-phase pipeline every 8 hours: search → metadata enrichment → README fetch → quality scoring → category classification → composability analysis. No manual curation is applied to ranking — all signals are data-driven to avoid editorial bias.</p>
    </section>

    <section>
      <h2 data-en="Editorial methodology" data-zh="编辑方法论">Editorial methodology</h2>
      <div class="card">
        <h3 data-en="The 10-dimension quality score" data-zh="10 维质量评分">The 10-dimension quality score</h3>
        <p data-en="Every skill receives a composite <strong>quality score (0-100)</strong> based on ten weighted signals. The formula and weights are fully documented in <a href='https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/app/services/scorer.py'>services/scorer.py</a>:" data-zh="每个技能基于十个加权信号获得一个综合<strong>质量分（0-100）</strong>。公式与权重完整记录在 <a href='https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/app/services/scorer.py'>services/scorer.py</a>：">Every skill receives a composite <strong>quality score (0-100)</strong> based on ten weighted signals. The formula and weights are fully documented in <a href="https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/app/services/scorer.py">services/scorer.py</a>:</p>
        <ul>
          <li data-en="<strong>Completeness (15%)</strong> — README depth, license, description, stars" data-zh="<strong>完整度（15%）</strong>——README 深度、许可、描述、Star 数"><strong>Completeness (15%)</strong> — README depth, license, description, stars</li>
          <li data-en="<strong>Clarity (15%)</strong> — description quality, topic tags, naming conventions" data-zh="<strong>清晰度（15%）</strong>——描述质量、主题标签、命名规范"><strong>Clarity (15%)</strong> — description quality, topic tags, naming conventions</li>
          <li data-en="<strong>Specificity (15%)</strong> — language + topic count + category + size" data-zh="<strong>专指度（15%）</strong>——语言 + 主题数 + 分类 + 体量"><strong>Specificity (15%)</strong> — language + topic count + category + size</li>
          <li data-en="<strong>Examples (12%)</strong> — code samples, commit frequency, contributor count" data-zh="<strong>示例（12%）</strong>——代码样例、提交频率、贡献者数"><strong>Examples (12%)</strong> — code samples, commit frequency, contributor count</li>
          <li data-en="<strong>README structure (23%)</strong> — sections, code blocks, badges, TOC" data-zh="<strong>README 结构（23%）</strong>——小节、代码块、徽章、目录"><strong>README structure (23%)</strong> — sections, code blocks, badges, TOC</li>
          <li data-en="<strong>Agent readiness (20%)</strong> — SKILL.md presence, install command, MCP compliance" data-zh="<strong>Agent 就绪度（20%）</strong>——SKILL.md、安装命令、MCP 合规"><strong>Agent readiness (20%)</strong> — SKILL.md presence, install command, MCP compliance</li>
        </ul>
        <p data-en="On top of the quality score, a separate <strong>composite score</strong> weighs nine additional signals including stars, recency, forks, commit velocity, issue resolution rate, star momentum (Z-score normalized), author followers, and a size bonus favoring atomic skills. See <a href='https://github.com/ZhuYansen/agent-skills-hub#3-evaluation'>the full methodology</a>." data-zh="在质量分之上，另有一个<strong>综合分</strong>权衡九个额外信号，包括 Star、近期活跃、Fork、提交速度、issue 解决率、Star 动量（Z 分数归一化）、作者粉丝数，以及偏好原子化技能的体量加分。详见<a href='https://github.com/ZhuYansen/agent-skills-hub#3-evaluation'>完整方法论</a>。">On top of the quality score, a separate <strong>composite score</strong> weighs nine additional signals including stars, recency, forks, commit velocity, issue resolution rate, star momentum (Z-score normalized), author followers, and a size bonus favoring atomic skills. See <a href="https://github.com/ZhuYansen/agent-skills-hub#3-evaluation">the full methodology</a>.</p>

        <h3 data-en="Daily &amp; weekly curation" data-zh="日报与周报精选">Daily &amp; weekly curation</h3>
        <p data-en="Daily reports feature skills newly indexed in the last 48 hours with at least 20 GitHub stars. The weekly 'Trending' list ranks by <code>star_velocity</code> (stars per day over the last 7 days). Both are automated but the final Top 10 is human-reviewed to exclude obvious forks, batch spam accounts, and misclassified non-skills." data-zh="日报精选过去 48 小时内新收录、且至少 20 个 GitHub Star 的技能。周报“趋势榜”按 <code>star_velocity</code>（过去 7 天每日 Star 增量）排序。两者均自动化，但最终 Top 10 经人工复核，剔除明显的 fork、批量刷号与误分类的非技能项目。">Daily reports feature skills newly indexed in the last 48 hours with at least 20 GitHub stars. The weekly "Trending" list ranks by <code>star_velocity</code> (stars per day over the last 7 days). Both are automated but the final Top 10 is human-reviewed to exclude obvious forks, batch spam accounts, and misclassified non-skills.</p>

        <h3 data-en="How decisions are made transparently" data-zh="决策如何保持透明">How decisions are made transparently</h3>
        <p data-en="Editorial judgement is required in exactly three places:" data-zh="编辑判断仅在三处需要：">Editorial judgement is required in exactly three places:</p>
        <ol>
          <li data-en="<strong>Category classification corrections</strong> — when keyword inference misfires" data-zh="<strong>分类归类修正</strong>——当关键词推断出错时"><strong>Category classification corrections</strong> — when keyword inference misfires</li>
          <li data-en="<strong>Spam &amp; batch-farming exclusion</strong> — documented in <a href='https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/discover_candidates.py'>discover_candidates.py</a>" data-zh="<strong>垃圾与批量刷号剔除</strong>——记录在 <a href='https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/discover_candidates.py'>discover_candidates.py</a>"><strong>Spam &amp; batch-farming exclusion</strong> — documented in <a href="https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/discover_candidates.py">discover_candidates.py</a></li>
          <li data-en="<strong>Verified Creator decisions</strong> (Q2 2026 launch) — criteria and outcomes logged publicly" data-zh="<strong>认证创作者决策</strong>（2026 Q2 上线）——标准与结果公开记录"><strong>Verified Creator decisions</strong> (Q2 2026 launch) — criteria and outcomes logged publicly</li>
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
      <p data-en="Last updated: 2026-04-24 · Published by Jason Zhu · MIT licensed · <a href='/'>Back to Home</a>" data-zh="最后更新：2026-04-24 · 发布者 Jason Zhu · MIT 许可 · <a href='/'>返回首页</a>">Last updated: 2026-04-24 · Published by Jason Zhu · MIT licensed · <a href="/">Back to Home</a></p>
    </footer>
  </div>
  <script>(function(){var l=localStorage.getItem('lang')||'en';document.documentElement.lang=l==='zh'?'zh-CN':'en';var b=document.getElementById('lang-toggle');if(b)b.textContent=l==='zh'?'EN':'中文';if(l==='zh')document.querySelectorAll('[data-zh]').forEach(function(el){el.innerHTML=el.getAttribute('data-zh')});})();</script>
</body>
</html>`;

const aboutDir = join(DIST, "about");
mkdirSync(aboutDir, { recursive: true });
writeFileSync(join(aboutDir, "index.html"), aboutHtml);
console.log(`  ✓ /about/index.html (standalone E-E-A-T page)`);

console.log(
  `Static pages: ${SHELLS.length} SPA shells + ${REDIRECTS.length} redirect stubs + /about/ generated`,
);
