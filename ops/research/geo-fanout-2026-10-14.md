# GEO 20 题 Fan-out 与引用源实测纪要（2026-10-14）

> **来源说明**：本文档汇总 2026-10-14 针对 AI 搜索引擎（ChatGPT、Perplexity、Gemini、豆包）的 20 题 fan-out 与引用源实测结论（原于 `ops/seo-watersystem-model.md` v5 增量表中引用，2026-11-16 补齐归档文件以消除悬空引用）。

## 一、实测设计（20 个真实查询）

围绕两类核心商业/工具查询对主流 AI 回答引擎做引用拆解：
1. **Skill / MCP 选型类查询（10 题）**：如 `best claude code skills`、`best mcp servers for postgres`、`best ppt skill for claude code`、`how to audit mcp server security` 等。
2. **API / 开发者工具对比类查询（10 题）**：如 `best web scraping api for llm`、`claude code vs codex skills` 等。

## 二、核心实测发现

| 维度 | 实测数据 | 结论与动作含义 |
|---|---|---|
| **Skill 类问题引用源分布** | **GitHub 仓库 / Awesome 列表占 43%** | AI 搜 skill 类问题时优先抓取 GitHub 原生仓库与结构化合集，而非普通营销博客；因此我们的 GitHub 每日自动更新合集（`video-daily.yml` 等）本身就是高权重 GEO 进水口。 |
| **API / 工具类问题引用源分布** | **官方文档 + 定价页占 63%** | AI 回答引擎极度偏爱带明确规格、参数、价格与对比表格的一手文档页，而非泛泛而谈的资讯文。 |
| **ChatGPT 品牌直接出现率** | **0 / 20** | 在未指定站名的 20 个泛词查询中，ChatGPT 当日抽样未直接引用 `agentskillshub.top`。 |
| **站内 AI 引荐真实来源（GA 对照）** | **主要来自 Gemini 与豆包**（外加 Perplexity / ChatGPT 少量会话） | 不同 AI 引擎检索底座不同（Google 系 / Bing 系 / 自建索引），不能只盯单一引擎；水位表需同时看 **GA AI 引荐会话数** 与 **20 题搜索实测出现率**。 |

## 三、对站点改版的直接指导

1. **场景页（`/best/<slug>/`）向“可抽取事实 + 实测表格”对齐**：
   - 首屏前 100 词直接给出肯定句结论（`The best <X> in 2026 is <Y>...`）与适用人群。
   - 保留真实实测对比表（`scenario-runs.json`）与方法论（`scenario-method.mjs`）。
2. **新增机器可读事实页 `/ai-info/`**：
   - 集中提供主体（BRICKAI / GoSailGlobal LLC）、收录与安全评级规模、43 条公开规则（`/how-we-grade/`）、Zenodo DOI（`10.5281/zenodo.21292799`）等结构化事实。
3. **GitHub 合集与主站双向承接**：
   - 15 个热门场景同步维护开源 GitHub 列表并署名回链 `agentskillshub.top`。
