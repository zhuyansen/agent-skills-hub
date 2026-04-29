/**
 * Generate static SEO pages for the Blue Book at:
 *   - dist/book/index.html
 *   - dist/book/{slug}/index.html  (one per published chapter)
 *
 * Each is a copy of dist/index.html with customized <title>, description,
 * canonical, and a <noscript> body with the chapter prose so crawlers
 * see the content without executing JS.
 *
 * Run after vite build, before generate-sitemap.mjs.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { join } from "path";

const DIST = "dist";
const BOOK_DIR = "content/book";
const SITE = "https://agentskillshub.top";

// Mirror the manifest in src/data/bookChapters.ts (all 12 chapters)
const CHAPTERS = [
  { slug: "ch01-mahesh-to-barry", number: 1, part: "Part 1 · 基础",
    title: "为什么需要 Skill：从 Mahesh 到 Barry",
    summary: "Mahesh vs Barry——聪明的大模型 vs 30 年老会计。Skill 要解决的本质问题：Agent 的「每次从零开始」。" },
  { slug: "ch02-three-layer-loading", number: 2, part: "Part 1 · 基础",
    title: "三层渐进加载：Skill 的真正魔法",
    summary: "description / instructions / resources 三层按需加载——Skill 区别于 System Prompt / RAG / Tool / MCP 的核心机制，也是它能在不爆上下文的前提下无限扩展的技术底座。" },
  { slug: "ch03-market-landscape", number: 3, part: "Part 1 · 基础",
    title: "Skill 市场全景 2026",
    summary: "67K skills · 33K creators · Gini 0.983（破 AppStore 纪录）· Top 1% 占 83% stars · 54% 的 Skill 拿 0 star。含 Hub 4 个漏洞的自我解剖。" },
  { slug: "ch04-baoyu-four-principles", number: 4, part: "Part 2 · 实战",
    title: "宝玉四条 Skill 设计哲学（Hub 数据回测）",
    summary: "宝玉零散提的 4 条哲学（Agent 视角 / 原子化 / 自我迭代 / 脚本优先）放在 67K 数据里跑——每一条都有可量化 delta，叠加放大效应 +16 分。" },
  { slug: "ch05-iteration-loop", number: 5, part: "Part 2 · 实战",
    title: "迭代优化的闭环：从踩坑到飞轮",
    summary: "Anthropic 的「评估驱动开发」+ 宝玉的「Skill 自我优化」机制。用 Hub star_velocity 数据画持续迭代 vs 一次性发布的生存曲线。" },
  { slug: "ch06-types-and-tiers", number: 6, part: "Part 2 · 实战",
    title: "9 种 Skill 类型 × 4 级分享路径",
    summary: "67K 真实数据：mcp-server 37% / agent-tool 26% / claude-skill 16%。9 种功能类型只有 3 种推荐新作者长期投入，4 级分享里 Hub 只能看到第 4 级。" },
  { slug: "ch07-four-frameworks", number: 7, part: "Part 3 · 生态",
    title: "四大框架的对标与选择",
    summary: "anthropic/skills、obra/superpowers、garrytan/gstack、kentcdodds/compound-engineering 四大 Skill 元框架。同一任务跑分对比 + 怎么选。" },
  { slug: "ch08-skill-eats-pillars", number: 8, part: "Part 3 · 生态",
    title: "Skill 正在吞噬其他柱子",
    summary: "Memory、Harness、Safety、Observability——这些原本独立 pillar 正在被 Skill 一一吃掉。从「prompt 片段」到「Agent 系统中枢」的演化时间线 + 谁会被淘汰。" },
  { slug: "ch09-distribution-fourth-edge", number: 9, part: "Part 3 · 生态",
    title: "Distribution：商业化三角少的那条边",
    summary: "南川的商业化三角是对的，但 99% 的 Skill 作者根本进不到三角里——卡在更前面：找不到用户。Distribution 是必须先解决的第四条边。" },
  { slug: "ch10-verified-creator", number: 10, part: "Part 4 · Hub 实操",
    title: "Verified Creator：不是花钱买的认证",
    summary: "公开的 verified_score 公式 + 完整申请表 + Founding Members 翻车复盘 + 5 条撤销条件 + 4 条「我不会做的事」明示。" },
  { slug: "ch11-consulting-and-enterprise", number: 11, part: "Part 4 · Hub 实操",
    title: "咨询撮合 + 企业目录：Service-on-Open 怎么跑",
    summary: "两个商业化产品：Skill 咨询撮合（C2C，Hub 抽 10%） + 企业订阅目录（B2B，¥9,999 / ¥29,999 / 定制三档）。完整定价推导 + 第一年收入预测 + 不会做的事。" },
  { slug: "ch12-when-claude-writes-skills", number: 12, part: "Part 4 · Hub 实操",
    title: "当 Claude 自己开始创建 Skills",
    summary: "Claude 自创 Skill 的 4 阶段演化模型 + 给 4 类作者的 2026-2028 生存指南 + 一个让人焦虑但必须诚实的预测：Hub 自己也会变形。" },
  { slug: "A-skill-design-cheatsheet", number: 13, part: "附录",
    title: "附录 A · Skill 设计速查表（一页纸）",
    summary: "12 章浓缩成可打印 cheatsheet：写 description 的 10 条金科玉律 + 9×4 推荐矩阵 + 5 设计模式 × 9 类型交叉表 + 14 项发布前自检 + SKILL.md 骨架。" },
  { slug: "B-hub-user-guide", number: 14, part: "附录",
    title: "附录 B · AgentSkillsHub 使用指南",
    summary: "5 分钟上手 + 提交 Skill 流程 + 评分算法透明化（Quality Score 6 维 + Score 10 信号）+ RSS/API/Sitemap + Hub 不做的 6 件事。" },
  { slug: "C-verified-creator-application", number: 15, part: "附录",
    title: "附录 C · Verified Creator 申请流程",
    summary: "5 分钟自检 + Python 计算器 + 完整 YAML 申请表 + 审核时间线 + 撤销条件 + 给企业团队的批量路径。" },
  { slug: "D-references-and-reading", number: 16, part: "附录",
    title: "附录 D · 参考文献 + 延伸阅读",
    summary: "Anthropic 官方资料 + 中英 KOL 代表作 + 行业关键论文 + 每一章的「想深挖」推荐路径 + CC BY-NC-SA 4.0 授权 + 致谢。" },
];

function esc(s) {
  if (!s) return "";
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function stripFrontmatter(md) {
  if (md.startsWith("---")) {
    const end = md.indexOf("\n---", 3);
    if (end > 0) return md.slice(end + 4).trimStart();
  }
  return md;
}

/**
 * Tiny, dependency-free markdown → HTML for the SEO noscript body.
 * Not perfect — it's only for Google to see paragraphs/headings/code.
 * The runtime React render uses react-markdown for the real version.
 */
function mdToHtml(md) {
  const lines = stripFrontmatter(md).split("\n");
  const out = [];
  let inCode = false;
  let codeBuf = [];
  let inList = false;
  let listType = null;

  const flushList = () => {
    if (inList) {
      out.push(`</${listType}>`);
      inList = false;
      listType = null;
    }
  };

  for (let raw of lines) {
    const line = raw.replace(/\r$/, "");

    // Fenced code block
    if (line.startsWith("```")) {
      if (inCode) {
        out.push(`<pre><code>${esc(codeBuf.join("\n"))}</code></pre>`);
        codeBuf = [];
        inCode = false;
      } else {
        flushList();
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeBuf.push(line);
      continue;
    }

    // Headings
    const h = line.match(/^(#{1,4})\s+(.+)$/);
    if (h) {
      flushList();
      const level = h[1].length;
      out.push(`<h${level}>${esc(h[2])}</h${level}>`);
      continue;
    }

    // Lists
    const ul = line.match(/^[-*]\s+(.+)$/);
    const ol = line.match(/^\d+\.\s+(.+)$/);
    if (ul || ol) {
      const type = ul ? "ul" : "ol";
      if (!inList || listType !== type) {
        flushList();
        out.push(`<${type}>`);
        inList = true;
        listType = type;
      }
      out.push(`<li>${esc((ul || ol)[1])}</li>`);
      continue;
    }

    // Blockquote
    if (line.startsWith("> ")) {
      flushList();
      out.push(`<blockquote>${esc(line.slice(2))}</blockquote>`);
      continue;
    }

    // Horizontal rule
    if (/^---+\s*$/.test(line)) {
      flushList();
      out.push(`<hr>`);
      continue;
    }

    // Paragraph (or empty line)
    if (line.trim() === "") {
      flushList();
      continue;
    }
    flushList();
    out.push(`<p>${esc(line)}</p>`);
  }
  flushList();
  if (inCode && codeBuf.length) {
    out.push(`<pre><code>${esc(codeBuf.join("\n"))}</code></pre>`);
  }
  return out.join("\n");
}

function customizeHtml(baseHtml, { title, description, canonical, ogImage, noscriptBody }) {
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

  if (ogImage) {
    html = html.replace(
      /<meta property="og:image" content="[^"]+"/,
      `<meta property="og:image" content="${ogImage}"`,
    );
  }

  if (noscriptBody) {
    html = html.replace(
      "</body>",
      `<noscript>\n${noscriptBody}\n</noscript>\n</body>`,
    );
  }

  return html;
}

async function main() {
  console.log("📖 Generating Blue Book pages...");
  if (!existsSync(join(DIST, "index.html"))) {
    throw new Error("dist/index.html not found — run vite build first");
  }
  const baseHtml = readFileSync(join(DIST, "index.html"), "utf-8");
  const coverImg = `${SITE}/book/assets/cover.png`;

  // 1. Index page /book/
  const indexTitle = "Skill 蓝皮书 2026 · 67K Skill 数据原生研究 · AgentSkillsHub";
  const indexDesc = `Skill 蓝皮书 2026：基于 AgentSkillsHub 67,000+ 真实 Skill 数据的原生研究。${CHAPTERS.length}/12 章已发布，含 Mahesh vs Barry / Gini 0.983 / 9 种类型 × 4 级路径 / Verified Creator 公式。`;
  const indexNoScript = `<h1>Skill 蓝皮书 2026</h1>
<p>${esc(indexDesc)}</p>
<h2>已发布章节（${CHAPTERS.length}/12）</h2>
<ol>${CHAPTERS.map((c) => `<li><a href="${SITE}/book/${c.slug}/">第 ${c.number} 章 · ${esc(c.title)}</a> — ${esc(c.summary)}</li>`).join("")}
</ol>
<p><a href="https://github.com/zhuyansen/skill-blue-book">GitHub 全本 →</a></p>`;
  const indexHtml = customizeHtml(baseHtml, {
    title: indexTitle,
    description: indexDesc,
    canonical: `${SITE}/book/`,
    ogImage: coverImg,
    noscriptBody: indexNoScript,
  });
  mkdirSync(join(DIST, "book"), { recursive: true });
  writeFileSync(join(DIST, "book", "index.html"), indexHtml);
  console.log(`  ✓ /book/index.html`);

  // 2. Each chapter
  for (const c of CHAPTERS) {
    const mdPath = join(BOOK_DIR, `${c.slug}.md`);
    if (!existsSync(mdPath)) {
      console.warn(`  ⚠ Missing ${mdPath}, skipping`);
      continue;
    }
    const md = readFileSync(mdPath, "utf-8");
    const noscriptBody = mdToHtml(md);
    const title = `第 ${c.number} 章 · ${c.title} · Skill 蓝皮书 2026`;
    const html = customizeHtml(baseHtml, {
      title,
      description: c.summary,
      canonical: `${SITE}/book/${c.slug}/`,
      ogImage: coverImg,
      noscriptBody,
    });
    mkdirSync(join(DIST, "book", c.slug), { recursive: true });
    writeFileSync(join(DIST, "book", c.slug, "index.html"), html);
    console.log(`  ✓ /book/${c.slug}/index.html (${(noscriptBody.length / 1024).toFixed(1)} KB SEO body)`);
  }

  console.log(`✅ Generated ${1 + CHAPTERS.length} book pages → dist/book/`);
}

main().catch((err) => {
  console.error("Book page generation failed:", err);
  process.exit(1);
});
