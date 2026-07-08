# 网站开发 Skills 全景(带安全评级)

> 汇总:我们目录 132K 库 + 三条高赞推文的点名
> (@jingwangtalk 722❤ harness 对比 · @Vincent_AINotes 803❤ 四组 skills · @dingyi 2311❤ design skills)。
> 星数为 2026-07-08 库内实时值,评级 🟢=safe。链接一律用我们的 /skill/ 页(有评级+安装)。

## 第 0 层 · Harness(AI 的工作方式,装一个别叠三个)

| Skill | ⭐ | 评级 | 一句话 |
|---|---|---|---|
| obra/superpowers | **249,249** | 🟢 | 头脑风暴→计划→TDD→验证 全流程纪律,最重也最全 |
| garrytan/gstack | 120,402 | 🟢 | ship/qa/review/retro 一套斜杠命令,偏"创业节奏" |
| EveryInc/compound-engineering-plugin | — | ⚠️ 未收录 | @jingwangtalk 三选一里的第三个(收录缺口,待 sync)|

## 第 1 层 · 元能力(让 AI 会造 skill)

- anthropics/skills 里的 **skill-creator**(官方)
- FrancyJGLisboa/agent-skill-creator(1,464★ 🟢)任意工作流→可安装 skill
- revfactory/harness(6,706★ 🟢)meta-skill:按领域设计 agent 团队

## 第 2 层 · 规格驱动(需求→PRD→架构→测试→部署)

- **github/spec-kit**(118,682★ 🟢)官方规格驱动工具包
- gsd-build/get-shit-done(63,801★ 🟢)轻量元提示流
- Pimzino/spec-workflow-mcp(4,255★ 🟢)MCP 形态

## 第 3 层 · 克隆对标

- **JCodesMore/ai-website-cloner-template**(25,382★ 🟢)品类第一
- bergside/design-md-chrome(2,062★ 🟢)只抽样式不整站克隆

## 第 4 层 · 设计系统提取(和第 3 层串行:先抽 tokens 再克隆)

- **Manavarya09/design-extract / designlang**(3,334★ 🟢)8 格式全出:Tailwind/shadcn/Figma/DTCG
- dembrandt/dembrandt(2,076★ 🟢)MCP 原生,对话内直接调
- dominikmartn/hue(689★ 🟢)品牌固化成 skill,后续生成全贴牌
- zanwei/design-dna(575★ 🟢)截图→定性风格 JSON(3 个月未更新)

## 第 5 层 · UI 设计(@dingyi 那条的主场)

- **nexu-io/open-design**(76,136★ 🟢)开源版 Claude Design
- **pbakaus/impeccable**(44,457★ 🟢)17 个设计命令 /polish /audit /distill —— dingyi 榜首
- alchaincyf/huashu-design(21,066★ 🟢)花叔 HTML 原生设计
- Nutlope/hallmark(3,400★ 🟢)反 AI 味
- "UI Skills"(dingyi #2,15 个独立 skills 含 baseline-ui;库内未精确匹配到仓库)

## 第 6 层 · 测试 + 部署

- mattzcarey/shippie(2,444★ 🟢)code review + QA agent
- **vercel-labs/agent-skills**(28,776★ 🟢)Vercel 官方合集
- glitternetwork/pinme(3,702★ 🟢)一条命令上线前端

## 第 7 层 · 上线后增长(大多数清单漏的)

- **AgriciDaniel/claude-seo**(10,655★ 🟢)25 子技能全套 SEO
- **zubair-trabzada/geo-seo-claude**(7,568★ 🟢)GEO:让 AI 搜索引用你

## 装前铁律

任何第三方 skill 跑在你机器上、带着 agent 全部权限。**装之前看评级**:
`agentskillshub.top/audit/{owner}/{repo}/` —— 132K 库,每 30 个就有 1 个带危险模式。

---
*用法:0-1 走 2→3→4→5 层;全程罩一个第 0 层 harness;上线立刻接第 7 层。*
