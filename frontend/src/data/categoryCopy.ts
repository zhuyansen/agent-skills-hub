/**
 * Hand-written per-category SEO copy (the LobeHub "Security by Default" pattern):
 * a unique H1, a distinct title, and a 2-sentence value-prop per category — so
 * each /category/ page reads as a purpose-built landing page, not a generic
 * "Best X Tools" template. Consumed by CategoryPage.tsx (SPA Helmet + intro).
 */
export interface CategoryCopy {
  /** SEO <title> (before the "| Agent Skills Hub" suffix) */
  title: string;
  titleZh: string;
  /** <h1> — search-intent led */
  heading: string;
  headingZh: string;
  /** 2-sentence intro paragraph shown under the H1 */
  intro: string;
  introZh: string;
}

export const CATEGORY_COPY: Record<string, CategoryCopy> = {
  "mcp-server": {
    title: "Best Open-Source MCP Servers — Security-Graded & Compared",
    titleZh: "最佳开源 MCP 服务器 — 安全评级与对比",
    heading: "MCP Servers, Security-Graded Before You Connect",
    headingZh: "MCP 服务器 —— 连接前先看安全评级",
    intro:
      "An MCP server hands an AI agent real capabilities — and often real credentials. Every server here is scored on 10 quality signals and carries a security grade (SAFE / CAUTION / UNSAFE), so you know what you're wiring into your agent before you connect it.",
    introZh:
      "一个 MCP 服务器给 AI agent 的是真实能力 —— 往往还有真实凭证。这里每个服务器都按 10 项质量信号评分并带安全评级(SAFE / CAUTION / UNSAFE),让你在接进 agent 之前就知道自己接的是什么。",
  },
  "claude-skill": {
    title: "Best Claude Skills — Open-Source, Quality-Scored",
    titleZh: "最佳 Claude Skills — 开源、质量评分",
    heading: "Claude Skills That Are Safe to Drop Into Claude Code",
    headingZh: "可以放心装进 Claude Code 的 Claude Skills",
    intro:
      "A Claude Skill runs with your agent's full permissions, so trust matters as much as usefulness. These are the top open-source Claude Skills, each quality-scored on documentation and structure and security-graded before you add it to Claude Code or Cursor.",
    introZh:
      "一个 Claude Skill 以你 agent 的完整权限运行,所以可信度和好用同样重要。这里是顶级开源 Claude Skills,每个都按文档与结构做了质量评分,并在你装进 Claude Code / Cursor 之前完成安全评级。",
  },
  "codex-skill": {
    title: "OpenClaw Ecosystem Skills — Open-Source & Graded",
    titleZh: "OpenClaw 生态 Skills — 开源与评级",
    heading: "OpenClaw & Codex Ecosystem Skills, Trust-Checked",
    headingZh: "OpenClaw 与 Codex 生态 Skills,附信任检查",
    intro:
      "Tools built for the OpenClaw and Codex agent runtimes, indexed from GitHub and refreshed every 8 hours. Each is quality-scored and security-graded so you can extend your coding agent without importing a black box.",
    introZh:
      "面向 OpenClaw 与 Codex agent 运行时的工具,从 GitHub 收录、每 8 小时刷新。每个都有质量评分与安全评级,让你扩展编程 agent 时不必引入一个黑盒。",
  },
  "agent-tool": {
    title: "Best AI Agent Tools — Open-Source, Security-Graded",
    titleZh: "最佳 AI Agent 工具 — 开源、安全评级",
    heading: "AI Agent Tools, Ranked by Signal Not Hype",
    headingZh: "AI Agent 工具 —— 按信号而非热度排序",
    intro:
      "Standalone tools that give agents new abilities — automation, retrieval, orchestration, and more. Ranked by a 10-signal composite (not raw stars) and security-graded, so the top of the list is what's actually worth installing.",
    introZh:
      "给 agent 带来新能力的独立工具 —— 自动化、检索、编排等等。按 10 信号综合分排序(不是纯 star 数)并带安全评级,让榜首真正是值得装的那个。",
  },
  "prompt-library": {
    title: "Best AI Prompt Libraries — Open-Source & Ranked",
    titleZh: "最佳 AI 提示词库 — 开源与排名",
    heading: "Open-Source Prompt Libraries Worth Reusing",
    headingZh: "值得复用的开源提示词库",
    intro:
      "Curated, reusable prompt collections for agents and LLM apps. Each library is quality-scored on structure and coverage so you can build on a well-organized set instead of copy-pasting from scattered gists.",
    introZh:
      "面向 agent 与 LLM 应用的、精选可复用的提示词集合。每个库都按结构与覆盖度做了质量评分,让你在一个组织良好的集合上搭建,而不是从零散 gist 里复制粘贴。",
  },
  "ai-coding-assistant": {
    title: "Best AI Coding Assistants — Open-Source, Compared",
    titleZh: "最佳 AI 编程助手 — 开源、对比",
    heading: "Open-Source AI Coding Assistants, Head to Head",
    headingZh: "开源 AI 编程助手,正面对比",
    intro:
      "Agent frameworks and assistants that write, review, and ship code. Each is quality-scored and security-graded, and you can compare any two side by side before you commit your workflow to one.",
    introZh:
      "会写代码、审代码、发代码的 agent 框架与助手。每个都有质量评分与安全评级,你还能把任意两个并排对比,再决定把工作流押在哪一个上。",
  },
  uncategorized: {
    title: "AI Tools & Agent Skills — Open-Source Directory",
    titleZh: "AI 工具与 Agent Skills — 开源目录",
    heading: "AI Tools & Agent Skills",
    headingZh: "AI 工具与 Agent Skills",
    intro:
      "Open-source AI tools indexed from GitHub, quality-scored and security-graded, refreshed every 8 hours.",
    introZh:
      "从 GitHub 收录的开源 AI 工具,带质量评分与安全评级,每 8 小时刷新。",
  },
};
