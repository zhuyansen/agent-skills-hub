// Blue Book of Agent Skills 2026 — chapter manifest (all 12 chapters published)
// Mirror copy of /Users/zhuyansen/content/skill-blue-book chapters into Hub.
// Source repo: https://github.com/zhuyansen/skill-blue-book

export interface BookChapter {
  slug: string;
  number: number;
  part: string;
  title: string;
  summary: string;
  status: "published" | "draft" | "todo";
  wordCount: number;
}

export const BOOK_CHAPTERS: BookChapter[] = [
  {
    slug: "ch01-mahesh-to-barry",
    number: 1,
    part: "Part 1 · 基础",
    title: "为什么需要 Skill：从 Mahesh 到 Barry",
    summary:
      "Mahesh vs Barry——聪明的大模型 vs 30 年老会计。Skill 要解决的本质问题：Agent 的「每次从零开始」。",
    status: "published",
    wordCount: 8000,
  },
  {
    slug: "ch02-three-layer-loading",
    number: 2,
    part: "Part 1 · 基础",
    title: "三层渐进加载：Skill 的真正魔法",
    summary:
      "description / instructions / resources 三层按需加载——Skill 区别于 System Prompt / RAG / Tool / MCP 的核心机制，也是它能在不爆上下文的前提下无限扩展的技术底座。",
    status: "published",
    wordCount: 4500,
  },
  {
    slug: "ch03-market-landscape",
    number: 3,
    part: "Part 1 · 基础",
    title: "Skill 市场全景 2026",
    summary:
      "67K skills · 33K creators · Gini 0.983（破 AppStore 纪录）· Top 1% 占 83% stars · 54% 的 Skill 拿 0 star。含 Hub 4 个漏洞的自我解剖。",
    status: "published",
    wordCount: 8500,
  },
  {
    slug: "ch04-baoyu-four-principles",
    number: 4,
    part: "Part 2 · 实战",
    title: "宝玉四条 Skill 设计哲学（Hub 数据回测）",
    summary:
      "宝玉零散提的 4 条哲学（Agent 视角 / 原子化 / 自我迭代 / 脚本优先）放在 67K 数据里跑——每一条都有可量化 delta，叠加放大效应 +16 分。",
    status: "published",
    wordCount: 6500,
  },
  {
    slug: "ch05-iteration-loop",
    number: 5,
    part: "Part 2 · 实战",
    title: "迭代优化的闭环：从踩坑到飞轮",
    summary:
      "Anthropic 的「评估驱动开发」+ 宝玉的「Skill 自我优化」机制。用 Hub star_velocity 数据画持续迭代 vs 一次性发布的生存曲线。",
    status: "published",
    wordCount: 6500,
  },
  {
    slug: "ch06-types-and-tiers",
    number: 6,
    part: "Part 2 · 实战",
    title: "9 种 Skill 类型 × 4 级分享路径",
    summary:
      "67K 真实数据：mcp-server 37% / agent-tool 26% / claude-skill 16%。9 种功能类型只有 3 种推荐新作者长期投入，4 级分享里 Hub 只能看到第 4 级。",
    status: "published",
    wordCount: 6500,
  },
  {
    slug: "ch07-four-frameworks",
    number: 7,
    part: "Part 3 · 生态",
    title: "四大框架的对标与选择",
    summary:
      "anthropic/skills、obra/superpowers、garrytan/gstack、kentcdodds/compound-engineering 四大 Skill 元框架。同一任务跑分对比 + 怎么选。",
    status: "published",
    wordCount: 5500,
  },
  {
    slug: "ch08-skill-eats-pillars",
    number: 8,
    part: "Part 3 · 生态",
    title: "Skill 正在吞噬其他柱子",
    summary:
      "Memory、Harness、Safety、Observability——这些原本独立 pillar 正在被 Skill 一一吃掉。从「prompt 片段」到「Agent 系统中枢」的演化时间线 + 谁会被淘汰。",
    status: "published",
    wordCount: 5500,
  },
  {
    slug: "ch09-distribution-fourth-edge",
    number: 9,
    part: "Part 3 · 生态",
    title: "Distribution：商业化三角少的那条边",
    summary:
      "南川的商业化三角是对的，但 99% 的 Skill 作者根本进不到三角里——卡在更前面：找不到用户。Distribution 是必须先解决的第四条边。",
    status: "published",
    wordCount: 6500,
  },
  {
    slug: "ch10-verified-creator",
    number: 10,
    part: "Part 4 · Hub 实操",
    title: "Verified Creator：不是花钱买的认证",
    summary:
      "公开的 verified_score 公式 + 完整申请表 + Founding Members 翻车复盘 + 5 条撤销条件 + 4 条「我不会做的事」明示。",
    status: "published",
    wordCount: 6500,
  },
  {
    slug: "ch11-consulting-and-enterprise",
    number: 11,
    part: "Part 4 · Hub 实操",
    title: "咨询撮合 + 企业目录：Service-on-Open 怎么跑",
    summary:
      "两个商业化产品：Skill 咨询撮合（C2C，Hub 抽 10%） + 企业订阅目录（B2B，¥9,999 / ¥29,999 / 定制三档）。完整定价推导 + 第一年收入预测 + 不会做的事。",
    status: "published",
    wordCount: 5500,
  },
  {
    slug: "ch12-when-claude-writes-skills",
    number: 12,
    part: "Part 4 · Hub 实操",
    title: "当 Claude 自己开始创建 Skills",
    summary:
      "Claude 自创 Skill 的 4 阶段演化模型 + 给 4 类作者的 2026-2028 生存指南 + 一个让人焦虑但必须诚实的预测：Hub 自己也会变形。",
    status: "published",
    wordCount: 4500,
  },
  {
    slug: "A-skill-design-cheatsheet",
    number: 13,
    part: "附录",
    title: "附录 A · Skill 设计速查表（一页纸）",
    summary:
      "12 章浓缩成可打印 cheatsheet：写 description 的 10 条金科玉律 + 9×4 推荐矩阵 + 5 设计模式 × 9 类型交叉表 + 14 项发布前自检 + SKILL.md 骨架。",
    status: "published",
    wordCount: 1500,
  },
  {
    slug: "B-hub-user-guide",
    number: 14,
    part: "附录",
    title: "附录 B · AgentSkillsHub 使用指南",
    summary:
      "5 分钟上手 + 提交 Skill 流程 + 评分算法透明化（Quality Score 6 维 + Score 10 信号）+ RSS/API/Sitemap + Hub 不做的 6 件事。",
    status: "published",
    wordCount: 2000,
  },
  {
    slug: "C-verified-creator-application",
    number: 15,
    part: "附录",
    title: "附录 C · Verified Creator 申请流程",
    summary:
      "5 分钟自检 + Python 计算器 + 完整 YAML 申请表 + 审核时间线 + 撤销条件 + 给企业团队的批量路径。",
    status: "published",
    wordCount: 2000,
  },
  {
    slug: "D-references-and-reading",
    number: 16,
    part: "附录",
    title: "附录 D · 参考文献 + 延伸阅读",
    summary:
      "Anthropic 官方资料 + 中英 KOL 代表作 + 行业关键论文 + 每一章的「想深挖」推荐路径 + CC BY-NC-SA 4.0 授权 + 致谢。",
    status: "published",
    wordCount: 1500,
  },
];

export const PUBLISHED_CHAPTERS = BOOK_CHAPTERS.filter(
  (c) => c.status === "published",
);

export function findChapterBySlug(slug: string): BookChapter | undefined {
  return BOOK_CHAPTERS.find((c) => c.slug === slug);
}

export function nextChapter(current: BookChapter): BookChapter | undefined {
  const idx = PUBLISHED_CHAPTERS.findIndex((c) => c.slug === current.slug);
  return idx >= 0 && idx < PUBLISHED_CHAPTERS.length - 1
    ? PUBLISHED_CHAPTERS[idx + 1]
    : undefined;
}

export function prevChapter(current: BookChapter): BookChapter | undefined {
  const idx = PUBLISHED_CHAPTERS.findIndex((c) => c.slug === current.slug);
  return idx > 0 ? PUBLISHED_CHAPTERS[idx - 1] : undefined;
}
