/**
 * Thematic internal linking for /best/<slug>/ pages.
 *
 * Keeps crawl equity and topical authority tightly connected across live /best/
 * guides, /compare/ matchups, /blog/ tutorials & empirical reports, and core
 * trust/directory hub pages — without ever linking a live page to a retired one.
 */
import { readFileSync } from "fs";
import { esc } from "./shared-utils.mjs";
import { relatedScenarios } from "./scenario-related.mjs";
import { comparisonsFor } from "./scenario-compare-links.mjs";

const PAIRS = JSON.parse(readFileSync(new URL("./comparison-pairs.json", import.meta.url), "utf8"));
const PAIR_BY_SLUG = new Map(PAIRS.map((p) => [p.slug, p]));

const repoName = (fullName) => fullName.split("/").pop();
const pairLabel = (p) => p.keywords?.[0] || `${repoName(p.a)} vs ${repoName(p.b)}`;

/** Curated topic clusters for peer discovery & relevant comparisons. */
const TOPIC_CLUSTERS = [
  {
    id: "claude-coding",
    slugs: [
      "claude-code-skills", "claude-code-hooks", "skill-management-tools", "codex-skills",
      "code-review", "vibe-coding", "refactoring", "cli-tools", "typesafe-jev", "prompt-engineering",
    ],
    bridges: ["ai-design", "mcp-database", "anti-slop", "browser-automation"],
    comparisons: ["claude-code-vs-claude-skills", "browser-use-vs-claude-code", "official-mcp-vs-awesome-mcp"],
  },
  {
    id: "visual-media",
    slugs: [
      "ai-design", "ppt-presentation", "claude-video-skills", "animation-skills",
      "claude-motion-alternatives", "image-generation", "3d-mcp",
    ],
    bridges: ["claude-code-skills", "codex-skills", "anti-slop", "skill-management-tools"],
    comparisons: ["openmotion-vs-hyperframes", "openmotion-vs-remotion", "hyperframes-vs-remotion", "claude-code-vs-claude-skills"],
  },
  {
    id: "mcp-data",
    slugs: [
      "mcp-database", "mcp-api", "mcp-for-github", "mcp-for-google",
      "browser-automation", "web-scraping", "knowledge-base", "obsidian-second-brain",
    ],
    bridges: ["claude-code-skills", "claude-code-hooks", "code-review", "cli-tools"],
    comparisons: ["official-mcp-vs-awesome-mcp", "github-mcp-vs-n8n-mcp", "browser-use-vs-claude-code", "n8n-vs-langflow"],
  },
  {
    id: "writing-growth",
    slugs: [
      "anti-slop", "seo-tools", "content-writing", "content-syndication", "summarization",
    ],
    bridges: ["claude-code-skills", "ai-design", "ppt-presentation", "image-generation", "prompt-engineering", "knowledge-base"],
    comparisons: ["claude-code-vs-claude-skills", "official-mcp-vs-awesome-mcp"],
  },
  {
    id: "agents-runtime",
    slugs: [
      "multi-agent", "local-llm", "voice-agent", "telegram-bot",
    ],
    bridges: ["claude-code-skills", "claude-code-hooks", "browser-automation", "mcp-api", "prompt-engineering", "typesafe-jev"],
    comparisons: ["langgraph-vs-crewai", "autogen-vs-crewai", "ollama-vs-open-webui", "deepagents-vs-autogen"],
  },
  {
    id: "security-audit",
    slugs: [
      "secret-detection", "authentication", "ai-reverse-engineering",
    ],
    bridges: ["code-review", "claude-code-skills", "skill-management-tools", "mcp-api", "mcp-database", "cli-tools", "browser-automation"],
    comparisons: ["claude-code-vs-claude-skills", "official-mcp-vs-awesome-mcp"],
  },
];

const SLUG_TO_CLUSTER = new Map();
for (const c of TOPIC_CLUSTERS) {
  for (const s of c.slugs) SLUG_TO_CLUSTER.set(s, c);
}

/** Verified /blog/ guides mapped to the scenario clusters/slugs where readers benefit most. */
export const BLOG_GUIDES = [
  {
    href: "/blog/make-powerpoint-with-claude/",
    en: "How to Make a PowerPoint with Claude (2026 Tutorial)",
    zh: "用 Claude 做 PPT 教程（2026）",
    slugs: ["ppt-presentation", "ai-design", "image-generation", "content-writing", "claude-code-skills", "codex-skills"],
    clusters: ["visual-media"],
  },
  {
    href: "/blog/make-claude-animations-that-dont-look-alike/",
    en: "How to Make Claude Animations That Don't All Look Alike",
    zh: "如何用 Claude 做出不千篇一律的动画",
    slugs: ["animation-skills", "claude-video-skills", "claude-motion-alternatives", "ai-design", "3d-mcp", "image-generation"],
    clusters: ["visual-media"],
  },
  {
    href: "/blog/skill-stack-solo-saas-2026/",
    en: "Build a SaaS Solo in 6 Weeks With AI Skills (2026 Stack)",
    zh: "2026 独立开发 AI Skills 技术栈",
    slugs: ["vibe-coding", "claude-code-skills", "claude-code-hooks", "codex-skills", "ai-design", "seo-tools", "code-review", "mcp-database", "cli-tools", "anti-slop", "content-writing", "content-syndication"],
    clusters: ["claude-coding", "writing-growth", "mcp-data"],
  },
  {
    href: "/blog/check-claude-skill-safety/",
    en: "How to Check if a Claude Skill Is Safe (2026 Data)",
    zh: "如何检查 Claude Skill 是否安全（2026 数据）",
    slugs: ["claude-code-skills", "claude-code-hooks", "skill-management-tools", "secret-detection", "authentication", "ai-reverse-engineering", "codex-skills", "typesafe-jev"],
    clusters: ["claude-coding", "security-audit", "mcp-data", "agents-runtime"],
  },
  {
    href: "/blog/securing-117k-ai-skills/",
    en: "We Security-Graded 117,854 AI Agent Skills: What We Found",
    zh: "117,854 个 AI Skill 安全评级报告",
    slugs: [],
    clusters: ["claude-coding", "visual-media", "mcp-data", "writing-growth", "agents-runtime", "security-audit"],
  },
  {
    href: "/blog/securing-43k-ai-tools/",
    en: "How We Built a 44-Rule Security Scanner for AI Tools",
    zh: "44 条规则的 AI 工具安全扫描器拆解",
    slugs: ["secret-detection", "authentication", "ai-reverse-engineering", "code-review", "mcp-api", "mcp-database"],
    clusters: ["security-audit"],
  },
  {
    href: "/blog/pivot-to-trust-layer/",
    en: "Why Agent Skills Hub Became an AI Skill Trust Layer",
    zh: "为什么 Agent Skills Hub 转型做安全信任层",
    slugs: ["skill-management-tools", "secret-detection", "authentication"],
    clusters: ["security-audit", "agents-runtime"],
  },
];

/** Core trust, benchmark, and directory pillars cross-linked from every live /best/ page. */
export const PILLAR_RESOURCES = [
  { href: "/how-we-grade/", en: "How We Grade (44 Security Rules)", zh: "安全评级方法（44 条规则）" },
  { href: "/analyzer/", en: "Scan Any Repo Before Installing", zh: "安装前在线扫描任意仓库" },
  { href: "/agent-skills-directories/", en: "AI Agent Skills Directories Compared", zh: "AI Agent Skills 目录站横向对比" },
  { href: "/stats/", en: "Live Ecosystem & Safety Stats", zh: "实时生态与安全统计" },
];

/**
 * Expands a live page's Related Categories from its 3 direct picks to up to `limit`
 * thematically connected live pages:
 *   1. Direct relatedScenarios (preserves curated order)
 *   2. Reverse-related live pages (bidirectional equity — fixes low-inbound pages)
 *   3. 2nd-hop graph neighbors (ranked by shared neighbor count)
 *   4. Same topic-cluster live peers
 *
 * Retired pages keep their original relatedScenarios list unchanged.
 */
export function expandedRelatedScenarios(scenario, allScenarios, { limit = 10 } = {}) {
  const direct = relatedScenarios(scenario, allScenarios);
  if (scenario.retired) return direct;

  const liveBySlug = new Map(
    allScenarios.filter((s) => s && s.title && !s.retired).map((s) => [s.slug, s]),
  );
  const picked = [];
  const seen = new Set([scenario.slug]);

  const add = (sc) => {
    if (!sc || sc.retired || !sc.title || seen.has(sc.slug)) return false;
    seen.add(sc.slug);
    picked.push(sc);
    return true;
  };

  // 1. Direct curated links
  for (const rel of direct) {
    if (picked.length >= limit) return picked;
    add(rel);
  }

  // 2. Reverse-related live scenarios pointing to this page
  for (const other of allScenarios) {
    if (picked.length >= limit) return picked;
    if (!other || other.retired || other.slug === scenario.slug) continue;
    if ((other.related || []).includes(scenario.slug)) add(other);
  }

  // 3. 2nd-hop neighbors via our direct links (ranked by overlap frequency)
  const hopScore = new Map();
  for (const rel of direct) {
    for (const hopSlug of rel.related || []) {
      if (seen.has(hopSlug) || !liveBySlug.has(hopSlug)) continue;
      hopScore.set(hopSlug, (hopScore.get(hopSlug) || 0) + 1);
    }
  }
  const hops = [...hopScore.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([slug]) => liveBySlug.get(slug));
  for (const sc of hops) {
    if (picked.length >= limit) return picked;
    add(sc);
  }

  // 4. Same topic-cluster peers, then adjacent bridge hubs
  const cluster = SLUG_TO_CLUSTER.get(scenario.slug);
  if (cluster) {
    for (const slug of [...cluster.slugs, ...(cluster.bridges || [])]) {
      if (picked.length >= limit) return picked;
      add(liveBySlug.get(slug));
    }
  }

  return picked;
}

/**
 * Head-to-head comparisons relevant to a scenario page:
 * direct repo matches first, supplemented up to `minCluster` from its topic cluster
 * when a live page has fewer than 2 direct matches.
 */
export function scenarioComparisons(scenario, skills, { minCluster = 3 } = {}) {
  const direct = comparisonsFor(skills);
  if (scenario.retired || direct.length >= 2) return direct;

  const cluster = SLUG_TO_CLUSTER.get(scenario.slug);
  if (!cluster) return direct;

  const out = [...direct];
  const seen = new Set(out.map((p) => p.slug));
  for (const slug of cluster.comparisons || []) {
    if (out.length >= minCluster) break;
    const pair = PAIR_BY_SLUG.get(slug);
    if (pair && !seen.has(pair.slug)) {
      seen.add(pair.slug);
      out.push(pair);
    }
  }
  return out;
}

/** Renders the Head-to-head comparisons section using direct + cluster-matched pairs. */
export function scenarioComparisonsHtml(scenario, skills) {
  const pairs = scenarioComparisons(scenario, skills);
  if (!pairs.length) return "";
  const links = pairs
    .map((p) => `<a href="/compare/${esc(p.slug)}/" class="bp-related-tag">${esc(pairLabel(p))}</a>`)
    .join("\n        ");
  return `<section style="margin-top:32px">
        <h2 class="bp-section-title" style="font-size:18px" data-zh="正面对比" data-en="Head-to-head comparisons">Head-to-head comparisons</h2>
        <div class="bp-related">
        ${links}
        </div>
      </section>`;
}

/** Picks topic-matched /blog/ guides + core trust/directory pillars for a scenario. */
export function resourcesFor(scenario, { maxBlogs = 4 } = {}) {
  const cluster = SLUG_TO_CLUSTER.get(scenario.slug);
  const direct = [];
  const clusterMatched = [];

  for (const post of BLOG_GUIDES) {
    if (post.slugs.includes(scenario.slug)) direct.push(post);
    else if (cluster && post.clusters.includes(cluster.id)) clusterMatched.push(post);
  }

  const blogs = [...direct, ...clusterMatched].slice(0, maxBlogs);
  if (blogs.length === 0) {
    // Fallback for any new unclustered slug: link our flagship safety report
    const flagship = BLOG_GUIDES.find((p) => p.href === "/blog/securing-117k-ai-skills/");
    if (flagship) blogs.push(flagship);
  }

  return [...blogs, ...PILLAR_RESOURCES];
}

/** Renders the Guides & Security Resources section (live pages only). */
export function resourcesHtml(scenario) {
  if (scenario.retired) return "";
  const items = resourcesFor(scenario);
  if (!items.length) return "";
  const links = items
    .map((r) => `<a href="${esc(r.href)}" class="bp-related-tag" data-en="${esc(r.en)}" data-zh="${esc(r.zh)}">${esc(r.en)}</a>`)
    .join("\n        ");
  return `<section style="margin-top:32px">
        <h2 class="bp-section-title" style="font-size:18px" data-zh="深度指南与安全评测" data-en="Guides &amp; Security Resources">Guides &amp; Security Resources</h2>
        <div class="bp-related">
        ${links}
        </div>
      </section>`;
}
