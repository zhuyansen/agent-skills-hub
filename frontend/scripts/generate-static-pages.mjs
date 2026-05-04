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
const STATIC_ROUTES = [
  {
    path: "verified-creator",
    title:
      "Verified Creator Program — AgentSkillsHub",
    description:
      "AgentSkillsHub Verified Creator program. For serious Skill authors who commercialize via consulting, subscriptions, or community. Authenticated badge, trending boost, creator analytics, leads channel.",
  },
  {
    path: "business",
    title: "For Business — AgentSkillsHub Enterprise Skill Directory",
    description:
      "Enterprise-grade AI Agent Skill directory with security audits, SBOM export, license compliance, and on-prem mirroring. Trusted source for Fortune 500 legal + security teams.",
  },
];

const indexHtml = readFileSync(join(DIST, "index.html"), "utf-8");

for (const route of STATIC_ROUTES) {
  // Customize title + description per route for better SEO
  let html = indexHtml
    .replace(
      /<title>[^<]+<\/title>/,
      `<title>${route.title}</title>`,
    )
    .replace(
      /<meta name="description" content="[^"]+"/,
      `<meta name="description" content="${route.description}"`,
    )
    .replace(
      /<link rel="canonical" href="[^"]+"/,
      `<link rel="canonical" href="https://agentskillshub.top/${route.path}/"`,
    );

  const outDir = join(DIST, route.path);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, "index.html"), html);
  console.log(`  ✓ /${route.path}/index.html`);
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
      <nav>
        <a href="/">AgentSkillsHub</a> ›
        <a href="/about/">About</a>
      </nav>
      <h1>About AgentSkillsHub</h1>
      <p class="tagline">An open-source directory for Claude Skills, MCP Servers &amp; Agent Tools — built in public, scored transparently.</p>
    </header>

    <section>
      <h2>Who runs this</h2>
      <div class="card">
        <p><strong>AgentSkillsHub</strong> is built and maintained by <strong>Jason Zhu</strong> (<a href="https://x.com/GoSailGlobal" rel="author">@GoSailGlobal</a> on X), an independent researcher tracking open-source AI agent ecosystems since 2024.</p>
        <p>Jason is also the author of the <a href="https://github.com/zhuyansen/skill-blue-book">Blue Book of Agent Skills 2026</a> — an in-depth analysis of the Claude Skills / MCP / Codex ecosystem based on 62,000+ indexed repositories, published openly on GitHub with reproducible Python scripts.</p>
        <p>The Hub is a solo project without external funding. There is no sales team, no "pay for placement" tier, and no dark patterns. All editorial decisions and scoring formulas live in public on <a href="https://github.com/ZhuYansen/agent-skills-hub">GitHub</a> under MIT license.</p>
      </div>
    </section>

    <section>
      <h2>What we track</h2>
      <div class="metrics">
        <div class="metric"><div class="num">62,000+</div><div class="label">indexed skills</div></div>
        <div class="metric"><div class="num">7</div><div class="label">categories</div></div>
        <div class="metric"><div class="num">58</div><div class="label">scenario pages</div></div>
        <div class="metric"><div class="num">8h</div><div class="label">refresh cadence</div></div>
        <div class="metric"><div class="num">10</div><div class="label">quality dimensions</div></div>
        <div class="metric"><div class="num">MIT</div><div class="label">source license</div></div>
      </div>
      <p>Every GitHub repository matching our search patterns flows through a 6-phase pipeline every 8 hours: search → metadata enrichment → README fetch → quality scoring → category classification → composability analysis. No manual curation is applied to ranking — all signals are data-driven to avoid editorial bias.</p>
    </section>

    <section>
      <h2>Editorial methodology</h2>
      <div class="card">
        <h3>The 10-dimension quality score</h3>
        <p>Every skill receives a composite <strong>quality score (0-100)</strong> based on ten weighted signals. The formula and weights are fully documented in <a href="https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/app/services/scorer.py">services/scorer.py</a>:</p>
        <ul>
          <li><strong>Completeness (15%)</strong> — README depth, license, description, stars</li>
          <li><strong>Clarity (15%)</strong> — description quality, topic tags, naming conventions</li>
          <li><strong>Specificity (15%)</strong> — language + topic count + category + size</li>
          <li><strong>Examples (12%)</strong> — code samples, commit frequency, contributor count</li>
          <li><strong>README structure (23%)</strong> — sections, code blocks, badges, TOC</li>
          <li><strong>Agent readiness (20%)</strong> — SKILL.md presence, install command, MCP compliance</li>
        </ul>
        <p>On top of the quality score, a separate <strong>composite score</strong> weighs nine additional signals including stars, recency, forks, commit velocity, issue resolution rate, star momentum (Z-score normalized), author followers, and a size bonus favoring atomic skills. See <a href="https://github.com/ZhuYansen/agent-skills-hub#3-evaluation">the full methodology</a>.</p>

        <h3>Daily &amp; weekly curation</h3>
        <p>Daily reports feature skills newly indexed in the last 48 hours with at least 20 GitHub stars. The weekly "Trending" list ranks by <code>star_velocity</code> (stars per day over the last 7 days). Both are automated but the final Top 10 is human-reviewed to exclude obvious forks, batch spam accounts, and misclassified non-skills.</p>

        <h3>How decisions are made transparently</h3>
        <p>Editorial judgement is required in exactly three places:</p>
        <ol>
          <li><strong>Category classification corrections</strong> — when keyword inference misfires</li>
          <li><strong>Spam &amp; batch-farming exclusion</strong> — documented in <a href="https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/discover_candidates.py">discover_candidates.py</a></li>
          <li><strong>Verified Creator decisions</strong> (Q2 2026 launch) — criteria and outcomes logged publicly</li>
        </ol>
        <p>Every other ranking decision is purely data-driven and reproducible from the open-source codebase.</p>
      </div>
    </section>

    <section>
      <h2>Source code &amp; data</h2>
      <p>Every line of code and every data snapshot used for the Blue Book is public:</p>
      <ul>
        <li><a href="https://github.com/ZhuYansen/agent-skills-hub">Source code</a> — frontend (React + Vite), backend (FastAPI), scoring pipeline (Python)</li>
        <li><a href="https://github.com/zhuyansen/skill-blue-book">Blue Book of Agent Skills 2026</a> — 12-chapter research report with reproducible Python analysis</li>
        <li><a href="/sitemap.xml">Sitemap</a> — 5,700+ indexed URLs across skills, categories, scenarios, authors</li>
      </ul>
    </section>

    <section>
      <h2>Contact</h2>
      <p>Questions, corrections, or tips? Reach out via:</p>
      <ul>
        <li>X DM: <a href="https://x.com/GoSailGlobal">@GoSailGlobal</a></li>
        <li>Email: <a href="mailto:m17551076169@gmail.com">m17551076169@gmail.com</a></li>
        <li>GitHub issues: <a href="https://github.com/ZhuYansen/agent-skills-hub/issues">agent-skills-hub/issues</a></li>
      </ul>
      <a class="cta" href="/">← Back to Explore All Skills</a>
    </section>

    <footer>
      <p>Last updated: 2026-04-24 · Published by Jason Zhu · MIT licensed · <a href="/">Back to Home</a></p>
    </footer>
  </div>
</body>
</html>`;

const aboutDir = join(DIST, "about");
mkdirSync(aboutDir, { recursive: true });
writeFileSync(join(aboutDir, "index.html"), aboutHtml);
console.log(`  ✓ /about/index.html (standalone E-E-A-T page)`);

console.log(`Static routes: ${STATIC_ROUTES.length + 1} HTML files generated`);
